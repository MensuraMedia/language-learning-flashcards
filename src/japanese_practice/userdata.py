"""Export, import and reset of a learner's progress.

**Glyphs, not ids.** An export keys every row by the character's glyph rather
than its database id. Ids are an artefact of seed order, and seed order has
already changed once in this project's life — anything exported before the kanji
expansion would silently point at different characters after it. A glyph is the
character, so an export stays readable by a future version, by a different
install, and by anything else that wants to read it.

Progress means `sessions`, `attempts` and `review_state`. The `characters` table
is content, not progress: it is reseeded from the bundled modules on every start
and is never exported, which is also what keeps an export small.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .db import Database

__all__ = [
    "EXPORT_VERSION",
    "export_progress",
    "import_progress",
    "reset_progress",
    "summarise",
]

#: Bump when the shape changes incompatibly. Readers refuse a version they do
#: not know rather than guessing at it.
EXPORT_VERSION = 1

#: The tables a reset clears, children first so foreign keys never block it.
_PROGRESS_TABLES = ("attempts", "review_state", "sessions")


async def summarise(db: Database) -> dict[str, Any]:
    """Row counts and the date range, for confirming a destructive action."""
    row = await db.fetch_one("""
        SELECT (SELECT COUNT(*) FROM sessions)     AS sessions,
               (SELECT COUNT(*) FROM attempts)     AS attempts,
               (SELECT COUNT(*) FROM review_state) AS review_state,
               (SELECT MIN(answered_at) FROM attempts) AS first_attempt,
               (SELECT MAX(answered_at) FROM attempts) AS last_attempt
        """)
    return dict(row or {})


async def export_progress(db: Database) -> dict[str, Any]:
    """Everything a learner would lose, in one portable document."""
    sessions = await db.fetch_all("""
        SELECT id, started_at, ended_at, challenge, scoring, difficulty,
               score, total, correct, max_streak
        FROM sessions ORDER BY id
        """)
    attempts = await db.fetch_all("""
        SELECT a.session_id, c.glyph, a.answered_at, a.correct, a.skipped,
               a.latency_ms, a.first_attempt, a.given_answer
        FROM attempts a JOIN characters c ON c.id = a.character_id
        ORDER BY a.id
        """)
    review = await db.fetch_all("""
        SELECT c.glyph, r.ease, r.interval_days, r.due_at, r.reps, r.lapses
        FROM review_state r JOIN characters c ON c.id = r.character_id
        ORDER BY r.character_id
        """)
    return {
        "format": "japanese-practice/progress",
        "version": EXPORT_VERSION,
        "exported_at": datetime.now(tz=timezone.utc).isoformat(),
        "counts": {
            "sessions": len(sessions),
            "attempts": len(attempts),
            "review_state": len(review),
        },
        "sessions": [dict(r) for r in sessions],
        "attempts": [dict(r) for r in attempts],
        "review_state": [dict(r) for r in review],
    }


async def reset_progress(db: Database) -> dict[str, Any]:
    """Delete all progress, keeping the seeded characters.

    Returns what was removed so the caller can report it — a destructive action
    that says nothing is indistinguishable from one that failed.
    """
    before = await summarise(db)
    for table in _PROGRESS_TABLES:
        await db.execute(f"DELETE FROM {table}")
    # No AUTOINCREMENT anywhere in the schema, so there is no sqlite_sequence to
    # clear: emptying the tables is enough for ids to restart from 1.
    return {"cleared": before}


async def import_progress(
    db: Database, payload: dict[str, Any], *, replace: bool = True
) -> dict[str, Any]:
    """Load an export back in.

    ``replace`` wipes existing progress first, which is what restoring a backup
    means. With ``replace=False`` the rows are appended instead, for merging a
    second device's history into this one.

    Glyphs absent from this install — an export from a future version with more
    characters seeded — are skipped and counted rather than aborting the whole
    import, so a partial restore still returns the history it can.
    """
    if payload.get("format") != "japanese-practice/progress":
        raise ValueError("not a Japanese Practice progress file")
    version = payload.get("version")
    if version != EXPORT_VERSION:
        raise ValueError(
            f"unsupported export version: {version!r} (this build reads {EXPORT_VERSION})"
        )

    rows = await db.fetch_all("SELECT id, glyph FROM characters")
    by_glyph = {r["glyph"]: r["id"] for r in rows}

    if replace:
        await reset_progress(db)

    # Session ids in the file cannot be trusted to be free here, so each is
    # inserted fresh and its new id remembered for the attempts that follow.
    remap: dict[Any, int] = {}
    for session in payload.get("sessions") or []:
        cursor = await db.execute(
            """
            INSERT INTO sessions
                (started_at, ended_at, challenge, scoring, difficulty,
                 score, total, correct, max_streak)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.get("started_at"),
                session.get("ended_at"),
                session.get("challenge") or "recognition",
                session.get("scoring") or "accuracy",
                session.get("difficulty") or "drill:custom",
                session.get("score") or 0,
                session.get("total") or 0,
                session.get("correct") or 0,
                session.get("max_streak") or 0,
            ),
        )
        remap[session.get("id")] = cursor

    skipped_glyphs = 0
    skipped_sessions = 0
    attempts = 0
    for attempt in payload.get("attempts") or []:
        character_id = by_glyph.get(attempt.get("glyph"))
        if character_id is None:
            skipped_glyphs += 1
            continue
        session_id = remap.get(attempt.get("session_id"))
        if session_id is None:
            skipped_sessions += 1
            continue
        await db.execute(
            """
            INSERT INTO attempts
                (session_id, character_id, answered_at, correct, skipped,
                 latency_ms, first_attempt, given_answer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                character_id,
                attempt.get("answered_at"),
                int(bool(attempt.get("correct"))),
                int(bool(attempt.get("skipped"))),
                attempt.get("latency_ms"),
                int(attempt.get("first_attempt", 1) or 0),
                attempt.get("given_answer"),
            ),
        )
        attempts += 1

    review = 0
    for state in payload.get("review_state") or []:
        character_id = by_glyph.get(state.get("glyph"))
        if character_id is None:
            skipped_glyphs += 1
            continue
        await db.execute(
            """
            INSERT INTO review_state
                (character_id, ease, interval_days, due_at, reps, lapses)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(character_id) DO UPDATE SET
                ease = excluded.ease,
                interval_days = excluded.interval_days,
                due_at = excluded.due_at,
                reps = excluded.reps,
                lapses = excluded.lapses
            """,
            (
                character_id,
                state.get("ease"),
                state.get("interval_days"),
                state.get("due_at"),
                state.get("reps") or 0,
                state.get("lapses") or 0,
            ),
        )
        review += 1

    return {
        "sessions": len(remap),
        "attempts": attempts,
        "review_state": review,
        "skipped_unknown_glyphs": skipped_glyphs,
        "skipped_orphan_attempts": skipped_sessions,
        "replaced": replace,
    }
