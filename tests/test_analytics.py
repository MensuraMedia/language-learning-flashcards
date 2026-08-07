"""Analytics engine.

Every metric is asserted against a hand-built history whose correct answer is
known by construction — no "returns something plausible" assertions. Each
function is also exercised against an empty database, because a fresh install
must render a dashboard rather than crash.
"""

from __future__ import annotations

import pytest

from japanese_practice import analytics
from japanese_practice.analytics import MASTERY_MAX_MISS_RATE, MASTERY_MIN_SEEN
from japanese_practice.db import Database

pytestmark = pytest.mark.asyncio


# -- helpers ---------------------------------------------------------------


async def add_session(
    db: Database,
    started_at: str,
    *,
    challenge: str = "recognition",
    scoring: str = "accuracy",
    difficulty: str = "hiragana:gojuon",
    total: int = 0,
    correct: int = 0,
) -> int:
    return await db.execute(
        "INSERT INTO sessions(started_at, challenge, scoring, difficulty, total, correct)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (started_at, challenge, scoring, difficulty, total, correct),
    )


async def add_attempt(
    db: Database,
    session_id: int,
    character_id: int,
    answered_at: str,
    *,
    correct: bool,
    latency_ms: int | None = 1000,
    given_answer: str | None = None,
    first_attempt: int = 1,
) -> None:
    await db.execute(
        "INSERT INTO attempts(session_id, character_id, answered_at, correct,"
        " latency_ms, first_attempt, given_answer) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            session_id,
            character_id,
            answered_at,
            1 if correct else 0,
            latency_ms,
            first_attempt,
            given_answer,
        ),
    )


async def char_id(db: Database, glyph: str) -> int:
    row = await db.fetch_one("SELECT id FROM characters WHERE glyph = ?", (glyph,))
    return row["id"]


# -- empty database --------------------------------------------------------


EMPTY_LIST_FUNCS = [
    analytics.accuracy_by_session,
    analytics.per_character_miss_rate,
    analytics.confusion_pairs,
    analytics.weakest_characters,
    analytics.streak_calendar,
    analytics.mastery_by_group,
    analytics.leeches,
    analytics.progress_velocity,
]


@pytest.mark.parametrize("func", EMPTY_LIST_FUNCS, ids=lambda f: f.__name__)
async def test_list_metrics_return_empty_on_a_fresh_install(db: Database, func):
    result = await func(db)
    assert result == []


async def test_retention_curve_returns_all_buckets_when_empty(db: Database):
    """Shape must be stable so the chart axis does not collapse."""
    rows = await analytics.retention_curve(db)
    assert len(rows) == len(analytics.RETENTION_BUCKETS)
    assert all(r["samples"] == 0 and r["accuracy"] == 0.0 for r in rows)


async def test_time_of_day_always_returns_24_hours(db: Database):
    rows = await analytics.time_of_day_performance(db)
    assert [r["hour"] for r in rows] == list(range(24))
    assert all(r["attempts"] == 0 for r in rows)


async def test_latency_distribution_returns_all_buckets_when_empty(db: Database):
    rows = await analytics.latency_distribution(db)
    assert len(rows) == len(analytics.LATENCY_BUCKETS)
    assert all(r["count"] == 0 for r in rows)


async def test_first_vs_eventual_does_not_divide_by_zero(db: Database):
    result = await analytics.first_vs_eventual(db)
    assert result == {
        "first_attempt_accuracy": 0.0,
        "eventual_accuracy": 0.0,
        "gap": 0.0,
    }


async def test_totals_are_zeroed_on_a_fresh_install(db: Database):
    totals = await analytics.totals(db)
    assert totals["sessions"] == 0
    assert totals["attempts"] == 0
    assert totals["accuracy"] == 0.0


async def test_dashboard_summary_assembles_without_data(db: Database):
    summary = await analytics.dashboard_summary(db)
    expected_keys = {
        "totals",
        "accuracy_by_session",
        "per_character_miss_rate",
        "confusion_pairs",
        "retention_curve",
        "time_of_day",
        "weakest_characters",
        "latency_distribution",
        "streak_calendar",
        "mastery_by_group",
        "leeches",
        "first_vs_eventual",
        "progress_velocity",
    }
    assert set(summary) == expected_keys


# -- per-character miss rate ----------------------------------------------


async def test_miss_rate_is_computed_exactly(seeded_db: Database, iso):
    db = seeded_db
    shi = await char_id(db, "し")
    a = await char_id(db, "あ")
    sid = await add_session(db, iso(0))

    # し: 3 of 4 wrong -> 0.75.  あ: 0 of 2 wrong -> 0.0
    for correct in (False, False, False, True):
        await add_attempt(db, sid, shi, iso(0), correct=correct)
    for _ in range(2):
        await add_attempt(db, sid, a, iso(0), correct=True)

    rows = {r["glyph"]: r for r in await analytics.per_character_miss_rate(db)}
    assert rows["し"]["seen"] == 4
    assert rows["し"]["missed"] == 3
    assert rows["し"]["miss_rate"] == pytest.approx(0.75)
    assert rows["あ"]["miss_rate"] == 0.0


async def test_miss_rate_is_sorted_worst_first(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "あ"), iso(0), correct=True)
    await add_attempt(db, sid, await char_id(db, "し"), iso(0), correct=False)

    rows = await analytics.per_character_miss_rate(db)
    assert [r["glyph"] for r in rows] == ["し", "あ"]


async def test_miss_rate_excludes_never_seen_characters(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "あ"), iso(0), correct=True)

    rows = await analytics.per_character_miss_rate(db)
    assert [r["glyph"] for r in rows] == ["あ"]


async def test_miss_rate_can_be_filtered_by_script(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "あ"), iso(0), correct=False)
    await add_attempt(db, sid, await char_id(db, "ア"), iso(0), correct=False)

    rows = await analytics.per_character_miss_rate(db, script="katakana")
    assert [r["glyph"] for r in rows] == ["ア"]


# -- confusion pairs -------------------------------------------------------


async def test_confusion_pairs_count_what_a_glyph_is_mistaken_for(seeded_db: Database, iso):
    db = seeded_db
    shi = await char_id(db, "し")
    sid = await add_session(db, iso(0))
    for _ in range(3):
        await add_attempt(db, sid, shi, iso(0), correct=False, given_answer="つ")
    await add_attempt(db, sid, shi, iso(0), correct=False, given_answer="あ")

    rows = await analytics.confusion_pairs(db)
    top = rows[0]
    assert top["glyph"] == "し"
    assert top["mistaken_for"] == "つ"
    assert top["count"] == 3


async def test_confusion_pairs_ignore_correct_answers(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "し"), iso(0), correct=True, given_answer="し")
    assert await analytics.confusion_pairs(db) == []


async def test_confusion_pairs_ignore_missing_given_answers(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "し"), iso(0), correct=False, given_answer=None)
    assert await analytics.confusion_pairs(db) == []


async def test_confusion_pairs_resolve_a_romaji_answer_to_its_glyph(seeded_db: Database, iso):
    """Answering 'tsu' for し should register as confusion with つ."""
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "し"), iso(0), correct=False, given_answer="tsu")
    rows = await analytics.confusion_pairs(db)
    assert rows[0]["mistaken_for"] == "つ"


# -- accuracy by session ---------------------------------------------------


async def test_accuracy_by_session_computes_and_orders_oldest_first(seeded_db: Database, iso):
    db = seeded_db
    await add_session(db, iso(5), total=10, correct=5)
    await add_session(db, iso(1), total=4, correct=3)

    rows = await analytics.accuracy_by_session(db)
    assert [r["accuracy"] for r in rows] == [pytest.approx(0.5), pytest.approx(0.75)]


async def test_accuracy_by_session_skips_empty_sessions(seeded_db: Database, iso):
    db = seeded_db
    await add_session(db, iso(1), total=0, correct=0)
    assert await analytics.accuracy_by_session(db) == []


async def test_accuracy_by_session_honours_the_limit(seeded_db: Database, iso):
    db = seeded_db
    for day in range(5):
        await add_session(db, iso(day), total=2, correct=1)
    assert len(await analytics.accuracy_by_session(db, limit=3)) == 3


# -- latency ---------------------------------------------------------------


async def test_latency_buckets_bin_correctly(seeded_db: Database, iso):
    db = seeded_db
    a = await char_id(db, "あ")
    sid = await add_session(db, iso(0))
    for latency in (100, 600, 1500, 3000, 9000):
        await add_attempt(db, sid, a, iso(0), correct=True, latency_ms=latency)

    counts = {r["bucket_ms"]: r["count"] for r in await analytics.latency_distribution(db)}
    assert counts == {0: 1, 500: 1, 1000: 1, 2000: 1, 4000: 1}


async def test_latency_ignores_untimed_attempts(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "あ"), iso(0), correct=True, latency_ms=None)
    assert sum(r["count"] for r in await analytics.latency_distribution(db)) == 0


# -- time of day -----------------------------------------------------------


async def test_time_of_day_buckets_by_hour(seeded_db: Database, iso):
    db = seeded_db
    a = await char_id(db, "あ")
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, a, iso(0, hour=9), correct=True)
    await add_attempt(db, sid, a, iso(0, hour=9), correct=False)
    await add_attempt(db, sid, a, iso(0, hour=21), correct=True)

    rows = {r["hour"]: r for r in await analytics.time_of_day_performance(db)}
    assert rows[9]["attempts"] == 2
    assert rows[9]["accuracy"] == pytest.approx(0.5)
    assert rows[21]["accuracy"] == 1.0


# -- weakest characters ----------------------------------------------------


async def test_weakest_characters_excludes_perfect_characters(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "あ"), iso(0), correct=True)
    await add_attempt(db, sid, await char_id(db, "し"), iso(0), correct=False)

    rows = await analytics.weakest_characters(db)
    assert [r["glyph"] for r in rows] == ["し"]


async def test_weakest_characters_weights_recent_misses_higher(seeded_db: Database, iso):
    """A miss today must outrank an equally-bad miss from months ago."""
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "し"), iso(0), correct=False)
    await add_attempt(db, sid, await char_id(db, "つ"), iso(120), correct=False)

    rows = await analytics.weakest_characters(db)
    assert rows[0]["glyph"] == "し"
    assert rows[0]["weighted_miss"] > rows[1]["weighted_miss"]


async def test_weakest_characters_honours_the_limit(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    for glyph in ("あ", "し", "つ"):
        await add_attempt(db, sid, await char_id(db, glyph), iso(0), correct=False)
    assert len(await analytics.weakest_characters(db, limit=2)) == 2


# -- streak calendar -------------------------------------------------------


async def test_streak_calendar_groups_by_day(seeded_db: Database, iso):
    db = seeded_db
    a = await char_id(db, "あ")
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, a, iso(0), correct=True)
    await add_attempt(db, sid, a, iso(0), correct=False)
    await add_attempt(db, sid, a, iso(3), correct=True)

    rows = await analytics.streak_calendar(db)
    assert len(rows) == 2
    assert rows[-1]["attempts"] == 2
    assert rows[-1]["accuracy"] == pytest.approx(0.5)


async def test_streak_calendar_respects_the_window(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0))
    await add_attempt(db, sid, await char_id(db, "あ"), iso(200), correct=True)
    assert await analytics.streak_calendar(db, days=90) == []


# -- mastery ---------------------------------------------------------------


async def test_mastery_requires_both_exposure_and_accuracy(seeded_db: Database, iso):
    """Mastery is `seen >= 3 AND miss_rate <= 0.15` — both halves matter."""
    db = seeded_db
    a = await char_id(db, "あ")  # seen 4, all correct -> mastered
    shi = await char_id(db, "し")  # seen 1, correct -> too few exposures
    tsu = await char_id(db, "つ")  # seen 4, half wrong -> too inaccurate
    sid = await add_session(db, iso(0))

    for _ in range(4):
        await add_attempt(db, sid, a, iso(0), correct=True)
    await add_attempt(db, sid, shi, iso(0), correct=True)
    for correct in (True, True, False, False):
        await add_attempt(db, sid, tsu, iso(0), correct=correct)

    rows = {(r["script"], r["group"]): r for r in await analytics.mastery_by_group(db)}
    gojuon = rows[("hiragana", "gojuon")]
    assert gojuon["total"] == 3
    assert gojuon["mastered"] == 1


async def test_mastery_thresholds_are_the_documented_constants():
    assert MASTERY_MIN_SEEN == 3
    assert MASTERY_MAX_MISS_RATE == 0.15


async def test_mastery_includes_untouched_groups(seeded_db: Database):
    """A group with no attempts still reports its total, so progress reads 0/N."""
    rows = {(r["script"], r["group"]): r for r in await analytics.mastery_by_group(seeded_db)}
    assert rows[("hiragana", "dakuon")]["total"] == 1
    assert rows[("hiragana", "dakuon")]["mastered"] == 0


# -- leeches ---------------------------------------------------------------


async def test_leeches_surface_repeatedly_relearned_characters(seeded_db: Database, iso):
    db = seeded_db
    shi = await char_id(db, "し")
    a = await char_id(db, "あ")
    await db.execute(
        "INSERT INTO review_state(character_id, ease, interval_days, lapses, reps)"
        " VALUES (?, 1.9, 0, 6, 1)",
        (shi,),
    )
    await db.execute(
        "INSERT INTO review_state(character_id, ease, interval_days, lapses, reps)"
        " VALUES (?, 2.5, 6, 1, 4)",
        (a,),
    )

    rows = await analytics.leeches(db)
    assert [r["glyph"] for r in rows] == ["し"]  # 1 lapse is below the threshold
    assert rows[0]["lapses"] == 6


# -- first vs eventual -----------------------------------------------------


async def test_first_vs_eventual_separates_recall_from_recognition(seeded_db: Database, iso):
    db = seeded_db
    a = await char_id(db, "あ")
    sid = await add_session(db, iso(0))
    # first attempts: 1 of 2 correct.  repeats: 2 of 2 correct.
    await add_attempt(db, sid, a, iso(0), correct=True, first_attempt=1)
    await add_attempt(db, sid, a, iso(0), correct=False, first_attempt=1)
    await add_attempt(db, sid, a, iso(0), correct=True, first_attempt=0)
    await add_attempt(db, sid, a, iso(0), correct=True, first_attempt=0)

    result = await analytics.first_vs_eventual(db)
    assert result["first_attempt_accuracy"] == pytest.approx(0.5)
    assert result["eventual_accuracy"] == pytest.approx(0.75)
    assert result["gap"] == pytest.approx(0.25)


# -- retention -------------------------------------------------------------


async def test_retention_curve_buckets_by_gap_since_last_review(seeded_db: Database, iso):
    db = seeded_db
    a = await char_id(db, "あ")
    sid = await add_session(db, iso(0))
    # Three reviews of the same character: 7 days apart, then 1 day apart.
    await add_attempt(db, sid, a, iso(8), correct=True)
    await add_attempt(db, sid, a, iso(1), correct=False)  # gap ~7d
    await add_attempt(db, sid, a, iso(0), correct=True)  # gap ~1d

    rows = {r["days_since_last"]: r for r in await analytics.retention_curve(db)}
    assert rows[7]["samples"] == 1
    assert rows[7]["accuracy"] == 0.0
    assert rows[1]["samples"] == 1
    assert rows[1]["accuracy"] == 1.0


# -- totals ----------------------------------------------------------------


async def test_totals_aggregate_across_sessions(seeded_db: Database, iso):
    db = seeded_db
    a = await char_id(db, "あ")
    sid = await add_session(db, iso(0), total=2, correct=1)
    await add_attempt(db, sid, a, iso(0), correct=True)
    await add_attempt(db, sid, a, iso(0), correct=False)

    totals = await analytics.totals(db)
    assert totals["sessions"] == 1
    assert totals["attempts"] == 2
    assert totals["accuracy"] == pytest.approx(0.5)
    assert totals["characters"] == 6


# -- summary ---------------------------------------------------------------


async def test_dashboard_summary_carries_real_values(seeded_db: Database, iso):
    db = seeded_db
    sid = await add_session(db, iso(0), total=1, correct=0)
    await add_attempt(db, sid, await char_id(db, "し"), iso(0), correct=False, given_answer="つ")

    summary = await analytics.dashboard_summary(db)
    assert summary["totals"]["attempts"] == 1
    assert summary["per_character_miss_rate"][0]["glyph"] == "し"
    assert summary["confusion_pairs"][0]["mistaken_for"] == "つ"
    assert summary["weakest_characters"][0]["glyph"] == "し"
