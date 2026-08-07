"""Exercise session engine.

Builds decks, records attempts and finalises sessions. Scoring itself lives in
:mod:`japanese_practice.scoring`; this module owns the persistence and the
ordering policy.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from .db import Database, characters_for_difficulty, get_character
from .models import Character, Session
from .scoring import next_review, score_attempt, validate_scheme

CHALLENGES = ("recognition", "recall", "timed", "listening", "mixed")

DEFAULT_DECK_LIMIT = 20


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_challenge(challenge: str) -> str:
    """Return ``challenge`` unchanged, raising ``ValueError`` if unknown."""
    if challenge not in CHALLENGES:
        raise ValueError(
            f"unknown challenge: {challenge!r} (expected one of {', '.join(CHALLENGES)})"
        )
    return challenge


async def build_deck(
    db: Database,
    difficulty: str,
    challenge: str,
    limit: int = DEFAULT_DECK_LIMIT,
    character_ids: list[int] | None = None,
) -> list[Character]:
    """Select and order the cards for a session.

    When ``character_ids`` is given it wins outright — that is the drill path,
    where the learner has clicked a weak character on the dashboard. Otherwise
    cards come from ``difficulty``, ordered by the scheme most useful for the
    challenge type.
    """
    if character_ids:
        cards: list[Character] = []
        for cid in character_ids:
            character = await get_character(db, cid)
            if character is not None:
                cards.append(character)
        return cards

    pool = await characters_for_difficulty(db, difficulty)
    if not pool:
        return []

    # Weakest-first ordering so a session spends its attention where it counts.
    weak = {row["character_id"]: row["miss_rate"] for row in await db.fetch_all("""
            SELECT character_id,
                   CAST(SUM(1 - correct) AS REAL) / COUNT(*) AS miss_rate
            FROM attempts GROUP BY character_id
            """)}
    unseen = [c for c in pool if c.id not in weak]
    seen = sorted((c for c in pool if c.id in weak), key=lambda c: -weak[c.id])

    ordered = seen[: max(1, limit // 2)] + unseen
    random.shuffle(unseen)
    if challenge == "mixed":
        random.shuffle(ordered)
    return ordered[:limit] if limit else ordered


async def start_session(db: Database, challenge: str, scoring: str, difficulty: str) -> Session:
    """Create and return a new session row."""
    validate_challenge(challenge)
    validate_scheme(scoring)
    session_id = await db.execute(
        "INSERT INTO sessions(started_at, challenge, scoring, difficulty)" " VALUES (?, ?, ?, ?)",
        (_now(), challenge, scoring, difficulty),
    )
    row = await db.fetch_one("SELECT * FROM sessions WHERE id = ?", (session_id,))
    return Session.from_row(row)


async def record_attempt(
    db: Database,
    session_id: int,
    character_id: int,
    correct: bool,
    latency_ms: int | None = None,
    given_answer: str | None = None,
    streak: int = 0,
) -> dict[str, Any]:
    """Persist one answer, update scheduling, and return the running totals."""
    session_row = await db.fetch_one("SELECT * FROM sessions WHERE id = ?", (session_id,))
    if session_row is None:
        raise ValueError(f"no such session: {session_id}")
    scheme = session_row["scoring"]

    state = await db.fetch_one("SELECT * FROM review_state WHERE character_id = ?", (character_id,))
    reps = state["reps"] if state else 0

    new_streak = streak + 1 if correct else 0
    awarded = score_attempt(
        scheme,
        correct=correct,
        latency_ms=latency_ms,
        streak=new_streak,
        reps=reps,
    )

    await db.execute(
        "INSERT INTO attempts(session_id, character_id, answered_at, correct,"
        " latency_ms, first_attempt, given_answer) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            session_id,
            character_id,
            _now(),
            1 if correct else 0,
            latency_ms,
            1,
            given_answer,
        ),
    )

    ease = state["ease"] if state else 2.5
    interval = state["interval_days"] if state else 0.0
    lapses = state["lapses"] if state else 0
    ease, interval, reps = next_review(ease, interval, reps, correct)
    if not correct:
        lapses += 1
    await db.execute(
        "INSERT INTO review_state(character_id, ease, interval_days, due_at,"
        " lapses, reps, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(character_id) DO UPDATE SET ease=excluded.ease,"
        " interval_days=excluded.interval_days, due_at=excluded.due_at,"
        " lapses=excluded.lapses, reps=excluded.reps, last_seen=excluded.last_seen",
        (character_id, ease, interval, None, lapses, reps, _now()),
    )

    await db.execute(
        "UPDATE sessions SET total = total + 1, correct = correct + ?,"
        " score = score + ?, max_streak = MAX(max_streak, ?) WHERE id = ?",
        (1 if correct else 0, awarded, new_streak, session_id),
    )

    row = await db.fetch_one("SELECT * FROM sessions WHERE id = ?", (session_id,))
    return {
        "awarded": awarded,
        "streak": new_streak,
        "score": row["score"],
        "total": row["total"],
        "correct": row["correct"],
    }


async def end_session(db: Database, session_id: int) -> Session:
    """Stamp the session as finished and return the final record."""
    await db.execute(
        "UPDATE sessions SET ended_at = ? WHERE id = ? AND ended_at IS NULL",
        (_now(), session_id),
    )
    row = await db.fetch_one("SELECT * FROM sessions WHERE id = ?", (session_id,))
    if row is None:
        raise ValueError(f"no such session: {session_id}")
    return Session.from_row(row)
