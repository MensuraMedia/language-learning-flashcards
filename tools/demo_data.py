#!/usr/bin/env python3
"""Generate a plausible study history, for screenshots and manual QA.

Every analytics panel in this application derives from the `attempts` table, so
on a fresh install they all correctly render empty states — which makes them
impossible to photograph and awkward to eyeball. This writes a history that
exercises each one: repeats (so the retention curve has buckets), a stable set
of problem characters (so the drill queue and leeches have something to rank),
skips, slow-corrects, and a run of consecutive days (so the streak is real).

**This is fabricated data.** It is not a recording of anyone studying. Point it
at a throwaway database, never at your own:

    python tools/demo_data.py --db /tmp/demo.db
    JP_DB_PATH=/tmp/demo.db python -m japanese_practice

Deterministic by default, so regenerating the screenshots does not silently
change every number in them.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from japanese_practice.content.loader import seed_content  # noqa: E402
from japanese_practice.db import Database, characters_for_difficulty  # noqa: E402

#: Decks the imaginary learner has been working through, in the order they
#: started them. Weighted so early decks accumulate more history.
PLAN = [
    ("hiragana:gojuon", "recognition", "accuracy", 34),
    ("hiragana:dakuon", "recall", "streak", 24),
    ("hiragana:yoon", "recall", "speed", 16),
    ("katakana:gojuon", "recognition", "accuracy", 22),
    ("katakana:dakuon", "recall", "streak", 12),
    ("kanji:N5", "recognition", "accuracy", 18),
    ("kanji:top200", "mixed", "srs", 9),
]

SPAN_DAYS = 34
SESSIONS = 46


async def build(db_path: Path, seed: int) -> None:
    rng = random.Random(seed)
    db = Database(db_path)
    await db.connect()
    await db.init_schema()
    await seed_content(db)

    pools: dict[str, list] = {}
    for key, *_ in PLAN:
        pools[key] = await characters_for_difficulty(db, key)

    # A stable minority the learner keeps getting wrong, so the weakest-character
    # queue and the leech list rank something real rather than noise.
    stubborn = {
        c.id
        for key in ("hiragana:gojuon", "katakana:gojuon", "kanji:N5")
        for c in rng.sample(pools[key], k=6)
    }

    today = date.today()
    # Two gaps early on, then an unbroken run up to today — a streak worth showing.
    study_days = [today - timedelta(days=d) for d in range(SPAN_DAYS) if d not in (26, 25, 19)]
    study_days.sort()

    weights = [n for *_, n in PLAN]
    total_attempts = 0

    for index in range(SESSIONS):
        day = study_days[min(int(index / SESSIONS * len(study_days)), len(study_days) - 1)]
        key, challenge, scoring, _ = rng.choices(PLAN, weights=weights, k=1)[0]
        pool = pools[key]
        if not pool:
            continue

        # Skill rises over the span: early sessions sit near the chance floor,
        # later ones near mastery.
        progress = index / max(SESSIONS - 1, 1)
        base_accuracy = 0.66 + 0.28 * progress

        started = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc) + timedelta(
            hours=rng.choice([8, 12, 19, 21]), minutes=rng.randrange(60)
        )

        card_count = rng.randrange(14, 26)
        cards = rng.sample(pool, k=min(card_count, len(pool)))

        session_id = await db.execute(
            """
            INSERT INTO sessions
                (started_at, ended_at, challenge, scoring, difficulty,
                 score, total, correct, max_streak)
            VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0)
            """,
            (started.isoformat(), None, challenge, scoring, key),
        )

        score = correct_count = streak = best_streak = 0
        at = started
        seen_this_session: set[int] = set()

        for card in cards:
            at += timedelta(seconds=rng.randrange(3, 14))
            chance = base_accuracy * (0.52 if card.id in stubborn else 1.0)
            skipped = rng.random() < 0.04
            correct = (not skipped) and rng.random() < min(chance, 0.97)

            # Repeats inside a session are what make first-vs-eventual meaningful.
            first_attempt = card.id not in seen_this_session
            seen_this_session.add(card.id)

            latency = rng.randrange(600, 1800) if correct else rng.randrange(1800, 5200)
            await db.execute(
                """
                INSERT INTO attempts
                    (session_id, character_id, answered_at, correct, skipped,
                     latency_ms, first_attempt, given_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    card.id,
                    at.isoformat(),
                    int(correct),
                    int(skipped),
                    None if skipped else latency,
                    int(first_attempt),
                    None if correct or skipped else rng.choice(pool).glyph,
                ),
            )
            total_attempts += 1

            if correct:
                correct_count += 1
                streak += 1
                best_streak = max(best_streak, streak)
                score += 10
            else:
                streak = 0
                if skipped:
                    score -= 1

            # A missed card comes round again, which is what builds the repeat
            # history the retention curve reads.
            if not correct and rng.random() < 0.5:
                cards.append(card)

        await db.execute(
            """
            UPDATE sessions
               SET ended_at = ?, score = ?, total = ?, correct = ?, max_streak = ?
             WHERE id = ?
            """,
            (at.isoformat(), score, len(cards), correct_count, best_streak, session_id),
        )

    # Review state, so the SRS panels and the leech list have something to read.
    rows = await db.fetch_all("""
        SELECT character_id,
               COUNT(*) AS reps,
               SUM(1 - correct) AS lapses,
               MAX(answered_at) AS last_seen
        FROM attempts GROUP BY character_id
        """)
    for row in rows:
        lapses = row["lapses"] or 0
        ease = max(1.3, 2.5 - 0.14 * lapses)
        interval = max(1, int(round(2.2 ** max(0, row["reps"] - lapses - 1))))
        due = datetime.fromisoformat(row["last_seen"]) + timedelta(days=interval)
        await db.execute(
            """
            INSERT INTO review_state
                (character_id, ease, interval_days, due_at, reps, lapses)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(character_id) DO UPDATE SET
                ease = excluded.ease, interval_days = excluded.interval_days,
                due_at = excluded.due_at, reps = excluded.reps, lapses = excluded.lapses
            """,
            (row["character_id"], round(ease, 2), interval, due.isoformat(), row["reps"], lapses),
        )

    summary = await db.fetch_one("""
        SELECT COUNT(*) AS sessions,
               (SELECT COUNT(*) FROM attempts) AS attempts,
               (SELECT ROUND(AVG(CAST(correct AS REAL)), 3) FROM attempts) AS accuracy,
               (SELECT COUNT(DISTINCT date(answered_at)) FROM attempts) AS days
        FROM sessions
        """)
    print(
        f"  {summary['sessions']} sessions · {summary['attempts']} attempts · "
        f"{summary['accuracy']:.1%} accuracy · {summary['days']} study days"
    )
    print(f"  written to {db_path}")
    await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path, help="throwaway database path")
    parser.add_argument("--seed", type=int, default=20260808, help="RNG seed")
    args = parser.parse_args()

    if args.db.exists():
        args.db.unlink()
    asyncio.run(build(args.db, args.seed))


if __name__ == "__main__":
    main()
