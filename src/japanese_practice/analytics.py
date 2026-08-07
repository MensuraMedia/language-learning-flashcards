"""Learner-performance analytics.

Every metric is derived from the append-only ``attempts`` table at query time,
so a new metric applies retroactively to all existing history — there is no
denormalised summary to migrate or backfill.

All functions tolerate an empty database and return empty structures rather
than raising or dividing by zero.
"""

from __future__ import annotations

from typing import Any

from .db import Database

# Buckets used by the retention curve, in days since the character was last seen.
RETENTION_BUCKETS = (0, 1, 2, 3, 7, 14, 30)

# Response-time buckets, in milliseconds.
LATENCY_BUCKETS = ((0, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, None))

# A character counts as mastered once it has been seen enough to mean something
# and is missed rarely. Deliberately conservative.
MASTERY_MIN_SEEN = 3
MASTERY_MAX_MISS_RATE = 0.15


async def accuracy_by_session(db: Database, limit: int = 30) -> list[dict[str, Any]]:
    """Per-session accuracy trend, oldest first."""
    rows = await db.fetch_all(
        """
        SELECT s.id AS session_id, s.started_at, s.challenge, s.difficulty,
               s.total, s.correct,
               CASE WHEN s.total > 0
                    THEN ROUND(CAST(s.correct AS REAL) / s.total, 4)
                    ELSE 0 END AS accuracy
        FROM sessions s
        WHERE s.total > 0
        ORDER BY s.started_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    return list(reversed(rows))


async def per_character_miss_rate(db: Database, script: str | None = None) -> list[dict[str, Any]]:
    """The headline weakness view: miss rate per glyph, worst first."""
    sql = """
        SELECT c.id AS character_id, c.glyph, c.script, c.kana_group, c.jlpt_level,
               COUNT(*) AS seen,
               SUM(1 - a.correct) AS missed,
               SUM(a.skipped) AS skipped,
               ROUND(CAST(SUM(1 - a.correct) AS REAL) / COUNT(*), 4) AS miss_rate,
               MAX(a.answered_at) AS last_seen
        FROM attempts a
        JOIN characters c ON c.id = a.character_id
        {where}
        GROUP BY c.id
        ORDER BY miss_rate DESC, seen DESC
    """
    params: tuple[Any, ...] = ()
    where = ""
    if script:
        where = "WHERE c.script = ?"
        params = (script,)
    return await db.fetch_all(sql.format(where=where), params)


async def confusion_pairs(db: Database, limit: int = 20) -> list[dict[str, Any]]:
    """What each character is actually mistaken *for*.

    Mines ``attempts.given_answer`` on wrong answers and resolves it back to a
    glyph where the answer matches a known character or romaji.
    """
    return await db.fetch_all(
        """
        SELECT c.glyph AS glyph,
               COALESCE(g.glyph, a.given_answer) AS mistaken_for,
               COUNT(*) AS count
        FROM attempts a
        JOIN characters c ON c.id = a.character_id
        LEFT JOIN characters g
               ON g.glyph = a.given_answer
               OR (g.romaji IS NOT NULL AND g.romaji = a.given_answer)
        WHERE a.correct = 0
          AND a.given_answer IS NOT NULL
          AND a.given_answer <> ''
        GROUP BY c.glyph, mistaken_for
        ORDER BY count DESC
        LIMIT ?
        """,
        (limit,),
    )


async def retention_curve(db: Database) -> list[dict[str, Any]]:
    """Accuracy as a function of days since that character was last seen."""
    rows = await db.fetch_all("""
        WITH spaced AS (
            SELECT a.correct,
                   CAST(julianday(a.answered_at) - julianday(
                       LAG(a.answered_at) OVER (
                           PARTITION BY a.character_id ORDER BY a.answered_at
                       )
                   ) AS REAL) AS gap_days
            FROM attempts a
        )
        SELECT gap_days, correct FROM spaced WHERE gap_days IS NOT NULL
        """)
    buckets: dict[int, list[int]] = {b: [] for b in RETENTION_BUCKETS}
    for row in rows:
        gap = row["gap_days"] or 0
        chosen = RETENTION_BUCKETS[0]
        for edge in RETENTION_BUCKETS:
            if gap >= edge:
                chosen = edge
        buckets[chosen].append(row["correct"])

    out: list[dict[str, Any]] = []
    for edge in RETENTION_BUCKETS:
        vals = buckets[edge]
        out.append(
            {
                "days_since_last": edge,
                "accuracy": round(sum(vals) / len(vals), 4) if vals else 0.0,
                "samples": len(vals),
            }
        )
    return out


async def time_of_day_performance(db: Database) -> list[dict[str, Any]]:
    """Accuracy by hour of day, 0..23, with every hour present."""
    rows = await db.fetch_all("""
        SELECT CAST(strftime('%H', answered_at) AS INTEGER) AS hour,
               COUNT(*) AS attempts,
               ROUND(AVG(CAST(correct AS REAL)), 4) AS accuracy
        FROM attempts
        GROUP BY hour
        """)
    by_hour = {r["hour"]: r for r in rows}
    return [by_hour.get(h, {"hour": h, "attempts": 0, "accuracy": 0.0}) for h in range(24)]


async def weakest_characters(db: Database, limit: int = 12) -> list[dict[str, Any]]:
    """Recency-weighted drill queue.

    A miss yesterday counts for more than a miss last month, so the queue
    reflects what is failing *now* rather than what once failed.
    """
    return await db.fetch_all(
        """
        SELECT c.id AS character_id, c.glyph, c.script, c.romaji, c.meaning,
               COUNT(*) AS seen,
               SUM(1 - a.correct) AS missed,
               ROUND(CAST(SUM(1 - a.correct) AS REAL) / COUNT(*), 4) AS miss_rate,
               SUM(a.skipped) AS skipped,
               -- A skip weighs more than a wrong guess: guessing wrong still
               -- shows a partial trace, whereas passing means no recall at all.
               ROUND(SUM(
                   (1 - a.correct) * (1.0 + 0.25 * a.skipped)
                   / (1.0 + MAX(julianday('now') - julianday(a.answered_at), 0))
               ), 4) AS weighted_miss,
               MAX(a.answered_at) AS last_seen
        FROM attempts a
        JOIN characters c ON c.id = a.character_id
        GROUP BY c.id
        HAVING missed > 0
        ORDER BY weighted_miss DESC, miss_rate DESC
        LIMIT ?
        """,
        (limit,),
    )


async def latency_distribution(db: Database, script: str | None = None) -> list[dict[str, Any]]:
    """Histogram of response times — the gap between knowing and recalling."""
    sql = "SELECT a.latency_ms FROM attempts a"
    params: tuple[Any, ...] = ()
    if script:
        sql += " JOIN characters c ON c.id = a.character_id WHERE c.script = ?"
        params = (script,)
    rows = await db.fetch_all(sql, params)

    out = []
    for low, high in LATENCY_BUCKETS:
        count = sum(
            1
            for r in rows
            if r["latency_ms"] is not None
            and r["latency_ms"] >= low
            and (high is None or r["latency_ms"] < high)
        )
        out.append(
            {
                "bucket_ms": low,
                "bucket_max": high,
                "label": f"{low // 1000 if low >= 1000 else low}"
                + ("ms" if low < 1000 else "s")
                + ("+" if high is None else ""),
                "count": count,
            }
        )
    return out


async def streak_calendar(db: Database, days: int = 90) -> list[dict[str, Any]]:
    """Per-day activity and accuracy — consistency predicts retention."""
    return await db.fetch_all(
        """
        SELECT date(answered_at) AS date,
               COUNT(*) AS attempts,
               ROUND(AVG(CAST(correct AS REAL)), 4) AS accuracy
        FROM attempts
        WHERE julianday('now') - julianday(answered_at) <= ?
        GROUP BY date
        ORDER BY date
        """,
        (days,),
    )


async def mastery_by_group(db: Database) -> list[dict[str, Any]]:
    """Progress against the real structure of the writing system."""
    return await db.fetch_all(
        """
        WITH stats AS (
            SELECT c.id, c.script,
                   COALESCE(c.kana_group, c.jlpt_level, 'ungrouped') AS grp,
                   COUNT(a.id) AS seen,
                   CASE WHEN COUNT(a.id) > 0
                        THEN CAST(SUM(1 - a.correct) AS REAL) / COUNT(a.id)
                        ELSE 1.0 END AS miss_rate
            FROM characters c
            LEFT JOIN attempts a ON a.character_id = c.id
            GROUP BY c.id
        )
        SELECT script, grp AS "group",
               COUNT(*) AS total,
               SUM(CASE WHEN seen >= ? AND miss_rate <= ? THEN 1 ELSE 0 END) AS mastered,
               ROUND(1.0 - AVG(CASE WHEN seen > 0 THEN miss_rate ELSE 1.0 END), 4) AS accuracy
        FROM stats
        GROUP BY script, grp
        ORDER BY script, grp
        """,
        (MASTERY_MIN_SEEN, MASTERY_MAX_MISS_RATE),
    )


async def leeches(db: Database, limit: int = 10) -> list[dict[str, Any]]:
    """Characters repeatedly learned and re-forgotten.

    High lapses relative to reps means repetition alone is not working — these
    need a different strategy, not more of the same.
    """
    return await db.fetch_all(
        """
        SELECT c.glyph, c.script, c.romaji, c.meaning,
               r.lapses, r.reps,
               ROUND(CAST(r.lapses AS REAL) / MAX(r.lapses + r.reps, 1), 4) AS miss_rate
        FROM review_state r
        JOIN characters c ON c.id = r.character_id
        WHERE r.lapses >= 2
        ORDER BY r.lapses DESC, miss_rate DESC
        LIMIT ?
        """,
        (limit,),
    )


async def first_vs_eventual(db: Database) -> dict[str, Any]:
    """Genuine recall against within-session pattern matching."""
    row = await db.fetch_one("""
        SELECT
            ROUND(AVG(CASE WHEN first_attempt = 1
                           THEN CAST(correct AS REAL) END), 4) AS first_attempt_accuracy,
            ROUND(AVG(CAST(correct AS REAL)), 4) AS eventual_accuracy
        FROM attempts
        """)
    first = (row or {}).get("first_attempt_accuracy") or 0.0
    eventual = (row or {}).get("eventual_accuracy") or 0.0
    return {
        "first_attempt_accuracy": first,
        "eventual_accuracy": eventual,
        "gap": round(eventual - first, 4),
    }


async def progress_velocity(db: Database, weeks: int = 8) -> list[dict[str, Any]]:
    """Newly-mastered characters per week, and the cumulative total."""
    rows = await db.fetch_all(
        """
        WITH per_char AS (
            SELECT character_id,
                   MIN(answered_at) AS first_seen,
                   COUNT(*) AS seen,
                   CAST(SUM(1 - correct) AS REAL) / COUNT(*) AS miss_rate,
                   MAX(answered_at) AS last_seen
            FROM attempts GROUP BY character_id
        )
        SELECT strftime('%Y-%W', last_seen) AS week,
               MIN(date(last_seen)) AS week_start,
               COUNT(*) AS newly_mastered
        FROM per_char
        WHERE seen >= ? AND miss_rate <= ?
          AND julianday('now') - julianday(last_seen) <= ?
        GROUP BY week
        ORDER BY week
        """,
        (MASTERY_MIN_SEEN, MASTERY_MAX_MISS_RATE, weeks * 7),
    )
    cumulative = 0
    out = []
    for row in rows:
        cumulative += row["newly_mastered"]
        out.append({**row, "cumulative": cumulative})
    return out


async def totals(db: Database) -> dict[str, Any]:
    """Headline counters for the dashboard tiles."""
    row = await db.fetch_one("""
        SELECT (SELECT COUNT(*) FROM sessions WHERE total > 0) AS sessions,
               (SELECT COUNT(*) FROM attempts) AS attempts,
               (SELECT COALESCE(SUM(score), 0) FROM sessions) AS score,
               (SELECT COALESCE(MAX(max_streak), 0) FROM sessions) AS best_streak,
               (SELECT COUNT(*) FROM characters) AS characters
        """)
    row = dict(row or {})
    acc = await db.fetch_value("SELECT ROUND(AVG(CAST(correct AS REAL)), 4) FROM attempts")
    row["accuracy"] = acc or 0.0
    row["avg_latency_ms"] = (
        await db.fetch_value(
            "SELECT ROUND(AVG(latency_ms)) FROM attempts WHERE latency_ms IS NOT NULL"
        )
    ) or 0
    return row


async def dashboard_summary(db: Database) -> dict[str, Any]:
    """One payload with everything the dashboard renders."""
    return {
        "totals": await totals(db),
        "accuracy_by_session": await accuracy_by_session(db),
        "per_character_miss_rate": await per_character_miss_rate(db),
        "confusion_pairs": await confusion_pairs(db),
        "retention_curve": await retention_curve(db),
        "time_of_day": await time_of_day_performance(db),
        "weakest_characters": await weakest_characters(db),
        "latency_distribution": await latency_distribution(db),
        "streak_calendar": await streak_calendar(db),
        "mastery_by_group": await mastery_by_group(db),
        "leeches": await leeches(db),
        "first_vs_eventual": await first_vs_eventual(db),
        "progress_velocity": await progress_velocity(db),
        "decks": await deck_shelves(db),
        "shelves": [{"id": i, "title": t, "sub": sub} for i, t, sub in SHELVES],
        "session_history": await session_history(db),
    }


# ── deck shelves ─────────────────────────────────────────────────────────────
#
# The dashboard presents difficulty keys as physical decks on shelves, the way
# the approved design does: a rung badge, a glyph preview, a mastery meter and
# the challenge/scoring pairing the deck defaults to. All of it is derived from
# the same tables the rest of the analytics use — nothing here is decorative
# filler.

#: Which shelf a difficulty key belongs on, its rung label, the Japanese name
#: shown under the deck title, and the challenge/scoring pairing it opens with.
DECK_META: dict[str, dict[str, str]] = {
    "hiragana:gojuon": {
        "shelf": "kana",
        "rung": "LV 1 · GOJUON",
        "jp": "ひらがな 五十音",
        "challenge": "recognition",
        "scoring": "accuracy",
    },
    "hiragana:dakuon": {
        "shelf": "kana",
        "rung": "LV 2 · DAKUON",
        "jp": "濁音",
        "challenge": "recall",
        "scoring": "streak",
    },
    "hiragana:handakuon": {
        "shelf": "kana",
        "rung": "LV 3 · HAN-DAKUON",
        "jp": "半濁音",
        "challenge": "recognition",
        "scoring": "accuracy",
    },
    "hiragana:yoon": {
        "shelf": "kana",
        "rung": "LV 4 · YOON",
        "jp": "拗音",
        "challenge": "recall",
        "scoring": "speed",
    },
    "hiragana:all": {
        "shelf": "kana",
        "rung": "LV 5 · MIXED 104",
        "jp": "ひらがな 全104",
        "challenge": "mixed",
        "scoring": "srs",
    },
    "katakana:gojuon": {
        "shelf": "kana",
        "rung": "LV 1 · GOJUON",
        "jp": "カタカナ 五十音",
        "challenge": "recognition",
        "scoring": "accuracy",
    },
    "katakana:dakuon": {
        "shelf": "kana",
        "rung": "LV 2 · DAKUON",
        "jp": "濁音",
        "challenge": "recall",
        "scoring": "streak",
    },
    "katakana:handakuon": {
        "shelf": "kana",
        "rung": "LV 3 · HAN-DAKUON",
        "jp": "半濁音",
        "challenge": "recognition",
        "scoring": "accuracy",
    },
    "katakana:yoon": {
        "shelf": "kana",
        "rung": "LV 4 · YOON",
        "jp": "拗音",
        "challenge": "recall",
        "scoring": "speed",
    },
    "katakana:all": {
        "shelf": "kana",
        "rung": "LV 5 · MIXED 104",
        "jp": "カタカナ 全104",
        "challenge": "mixed",
        "scoring": "srs",
    },
    "kanji:N5": {
        "shelf": "jlpt",
        "rung": "N5 · FOUNDATION",
        "jp": "漢字 N5",
        "challenge": "recognition",
        "scoring": "accuracy",
    },
    "kanji:N4": {
        "shelf": "jlpt",
        "rung": "N4 · EVERYDAY",
        "jp": "漢字 N4",
        "challenge": "recall",
        "scoring": "srs",
    },
    "kanji:N3": {
        "shelf": "jlpt",
        "rung": "N3 · ABSTRACT",
        "jp": "漢字 N3",
        "challenge": "mixed",
        "scoring": "speed",
    },
    "kanji:N2": {
        "shelf": "jlpt",
        "rung": "N2 · PROFESSIONAL",
        "jp": "漢字 N2",
        "challenge": "timed",
        "scoring": "streak",
    },
    "kanji:N1": {
        "shelf": "jlpt",
        "rung": "N1 · LITERARY",
        "jp": "漢字 N1",
        "challenge": "recall",
        "scoring": "srs",
    },
    # kanji:top200 / kanji:top500 are deliberately absent. Frequency rank is not
    # stored on `characters`, so those keys resolve to "all kanji" and would
    # advertise the 107-character N5 set as the "Top 200" — a label the data
    # cannot back. Restore them once a frequency column exists.
}

SHELVES: tuple[tuple[str, str, str], ...] = (
    ("kana", "Kana Shelf", "gojuon → dakuon → han-dakuon → yoon → 104 mixed"),
    ("jlpt", "Kanji Shelf — Proficiency", "JLPT N5 → N1"),
    ("vol", "Kanji Shelf — Volume", "Top 200 → Top 500"),
)


async def deck_shelves(db: Database) -> list[dict[str, Any]]:
    """Every seeded difficulty key as a deck, with real progress on it."""
    from .db import available_segments

    decks: list[dict[str, Any]] = []
    for segment in await available_segments(db):
        key = segment["key"]
        meta = DECK_META.get(key)
        if meta is None:
            continue

        stats = (
            await db.fetch_one(
                f"""
            WITH per_char AS (
                SELECT c.id,
                       COUNT(a.id) AS seen,
                       CASE WHEN COUNT(a.id) > 0
                            THEN CAST(SUM(1 - a.correct) AS REAL) / COUNT(a.id)
                            ELSE 1.0 END AS miss_rate
                FROM characters c
                LEFT JOIN attempts a ON a.character_id = c.id
                WHERE c.id IN (SELECT id FROM characters WHERE {_segment_clause(key)})
                GROUP BY c.id
            )
            SELECT
                SUM(CASE WHEN seen >= ? AND miss_rate <= ? THEN 1 ELSE 0 END) AS mastered,
                ROUND(1.0 - AVG(CASE WHEN seen > 0 THEN miss_rate ELSE 1.0 END), 4) AS accuracy
            FROM per_char
            """,
                (MASTERY_MIN_SEEN, MASTERY_MAX_MISS_RATE),
            )
            or {}
        )

        glyphs = await db.fetch_all(
            f"SELECT glyph FROM characters WHERE {_segment_clause(key)} ORDER BY id LIMIT 3"
        )
        preview = [row["glyph"] for row in glyphs]
        # Yoon are two-character digraphs (きゃ), so three of them overrun the
        # card and crowd its border. Show two whenever the glyphs are wide.
        if any(len(g) > 1 for g in preview):
            preview = preview[:2]

        decks.append(
            {
                **segment,
                **meta,
                "mastered": int(stats.get("mastered") or 0),
                "accuracy": float(stats.get("accuracy") or 0.0),
                "glyphs": preview,
            }
        )
    return decks


def _segment_clause(key: str) -> str:
    """Inline WHERE fragment for a difficulty key. Keys are a closed set, so
    this cannot carry user input into SQL."""
    script, group = key.split(":", 1)
    if group == "all":
        return f"script = '{script}'"
    if script == "kanji" and group.startswith("N"):
        return f"script = 'kanji' AND jlpt_level = '{group}'"
    if script == "kanji":
        return "script = 'kanji'"
    return f"script = '{script}' AND kana_group = '{group}'"


async def session_history(db: Database, limit: int = 12) -> list[dict[str, Any]]:
    """Recent sessions, newest first, for the history table."""
    return await db.fetch_all(
        """
        SELECT id, started_at, challenge, scoring, difficulty, total, correct,
               score, max_streak,
               CASE WHEN total > 0
                    THEN ROUND(CAST(correct AS REAL) / total, 4) ELSE 0 END AS accuracy,
               (SELECT ROUND(AVG(latency_ms)) FROM attempts a WHERE a.session_id = s.id)
                   AS avg_latency_ms
        FROM sessions s
        WHERE total > 0
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (limit,),
    )
