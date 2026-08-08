"""Exercise session engine.

Builds decks, records attempts and finalises sessions. Scoring itself lives in
:mod:`japanese_practice.scoring`; this module owns the persistence and the
ordering policy.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from .content.confusions import CONFUSION_PAIRS
from .db import Database, characters_for_difficulty, get_character
from .kana import to_romaji
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

    # Shuffle BEFORE concatenating: shuffling `unseen` afterwards mutates a list
    # that `ordered` has already copied from, so it was a no-op and every
    # session dealt あ い う え お in id order.
    random.shuffle(unseen)
    ordered = seen[: max(1, limit // 2)] + unseen
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
    skipped: bool = False,
) -> dict[str, Any]:
    """Persist one answer, update scheduling, and return the running totals.

    A skip is stored as an incorrect attempt carrying ``skipped = 1``. That
    keeps every "did not get it" signal in one place for the weakness
    analytics, while still letting the UI and scoring treat a pass differently
    from a wrong guess.
    """
    if skipped:
        correct = False
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
        skipped=skipped,
    )

    # first_attempt is only true the first time this character is answered in
    # this session. Hardcoding 1 made first_vs_eventual() structurally zero.
    seen_before = await db.fetch_value(
        "SELECT COUNT(*) FROM attempts WHERE session_id = ? AND character_id = ?",
        (session_id, character_id),
    )
    await db.execute(
        "INSERT INTO attempts(session_id, character_id, answered_at, correct,"
        " skipped, latency_ms, first_attempt, given_answer)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            session_id,
            character_id,
            _now(),
            1 if correct else 0,
            1 if skipped else 0,
            latency_ms,
            0 if seen_before else 1,
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
        "skipped": bool(skipped),
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


#: How many options a card offers. Three is enough to make a guess meaningful
#: without turning the card into a reading exercise.
CHOICE_COUNT = 3


#: Scripts graded on meaning rather than sound. A kana card asks "what does this
#: sound like"; a kanji or a word asks "what does this mean".
MEANING_SCRIPTS = ("kanji", "vocab")


def answer_text(character: Character) -> str:
    """What the learner is choosing between: romaji for kana, meaning otherwise."""
    if character.script in MEANING_SCRIPTS:
        return character.meaning or character.glyph
    return character.romaji or character.glyph


async def choice_readings(db: Database, script: str, options: list[str]) -> dict[str, str]:
    """Map each kanji option to the reading of the character it stands for.

    A kanji card asks for a meaning, so its options are English — which tells a
    learner nothing about how any of them sound. Carrying the reading on the
    option turns three English phrases into three characters you could actually
    say, at no cost to what is graded: this is display only, and the answer is
    still matched on the meaning text.

    Where several characters share a meaning the first by id wins. That is
    arbitrary, but the alternative is showing two readings for one option, which
    would imply a distinction the card is not making.
    """
    if script != "kanji" or not options:
        return {}

    rows = await db.fetch_all(
        f"""
        SELECT meaning, onyomi, kunyomi FROM characters
        WHERE script = 'kanji' AND meaning IN ({",".join("?" * len(options))})
        ORDER BY id
        """,
        tuple(options),
    )
    out: dict[str, str] = {}
    for row in rows:
        if row["meaning"] in out:
            continue
        # On'yomi first: it is the reading a kanji is named by, and the one that
        # appears in the compounds a learner meets next.
        primary = (row["onyomi"] or row["kunyomi"] or "").split("/")[0]
        reading = to_romaji(primary)
        if reading:
            out[row["meaning"]] = reading
    return out


async def build_choices(db: Database, character: Character, count: int = CHOICE_COUNT) -> list[str]:
    """Return ``count`` shuffled options, exactly one of which is correct.

    Distractors are drawn from the same script so the choice tests recall of
    this character rather than the ability to spot the odd one out — offering
    an English meaning beside two romaji would give the answer away.
    """
    correct = answer_text(character)
    column = "meaning" if character.script in MEANING_SCRIPTS else "romaji"
    wanted = max(0, count - 1)

    # Prefer distractors from the same kana group (or JLPT level for kanji):
    # offering "hyo" and "bi" against "a" can be solved by elimination, which
    # tests nothing. Same-group options force actual recall.
    # Distractors come from the same set: a "Monday" card offering "March"
    # can be solved by category rather than by knowing the word.
    if character.script == "vocab":
        peer_column, peer_value = "category", character.category
    elif character.script == "kanji":
        peer_column, peer_value = "jlpt_level", character.jlpt_level
    else:
        peer_column, peer_value = "kana_group", character.kana_group

    options: list[str] = []

    # 1. The curated visual-confusion partners first. These 45 pairs are the
    #    real traps (シ/ツ, ソ/ン, る/ろ, ぬ/め, き/さ, は/ほ) and they were
    #    sitting unused while distractors were drawn at random. A card that
    #    offers シ against ヌ and ラ tests nothing; one that offers ツ tests
    #    the exact discrimination the learner keeps failing.
    partners = _confusion_partners(character.glyph)
    if partners:
        rows = await db.fetch_all(
            f"""
            SELECT DISTINCT {column} AS option FROM characters
            WHERE glyph IN ({",".join("?" * len(partners))})
              AND {column} IS NOT NULL AND {column} <> '' AND {column} <> ?
            ORDER BY RANDOM() LIMIT ?
            """,
            (*partners, correct, wanted),
        )
        options = [row["option"] for row in rows]

    # 2. Voicing siblings — the contrast a dakuon/han-dakuon deck exists to
    #    teach. Without this the p- row only ever competes against itself.
    if len(options) < wanted and character.script != "kanji":
        siblings = voicing_siblings(correct)
        if siblings:
            rows = await db.fetch_all(
                f"""
                SELECT DISTINCT {column} AS option FROM characters
                WHERE script = ? AND {column} IN ({",".join("?" * len(siblings))})
                  AND {column} <> ?
                ORDER BY RANDOM() LIMIT ?
                """,
                (character.script, *siblings, correct, wanted - len(options)),
            )
            for row in rows:
                if row["option"] not in options:
                    options.append(row["option"])

    if len(options) < wanted and peer_value:
        rows = await db.fetch_all(
            f"""
            SELECT DISTINCT {column} AS option
            FROM characters
            WHERE script = ? AND {peer_column} = ?
              AND {column} IS NOT NULL AND {column} <> '' AND {column} <> ?
            ORDER BY RANDOM() LIMIT ?
            """,
            (character.script, peer_value, correct, wanted - len(options)),
        )
        for row in rows:
            if row["option"] not in options:
                options.append(row["option"])

    # Top up from the wider script when the group is too small to fill the row.
    if len(options) < wanted:
        rows = await db.fetch_all(
            f"""
            SELECT DISTINCT {column} AS option
            FROM characters
            WHERE script = ? AND {column} IS NOT NULL AND {column} <> ''
              AND {column} <> ?
            ORDER BY RANDOM() LIMIT ?
            """,
            (character.script, correct, wanted * 3),
        )
        for row in rows:
            if len(options) >= wanted:
                break
            if row["option"] not in options:
                options.append(row["option"])
    options.append(correct)
    random.shuffle(options)
    return options


#: Consonants that alternate through the dakuten/handakuten marks. A dakuon or
#: han-dakuon card exists to teach exactly this contrast — は / ば / ぱ — so its
#: distractors must vary the consonant. Drawing from `kana_group` alone gives
#: han-dakuon a five-member pool where every option is p-, which turns the
#: hardest rung into a pure vowel test and never asks the question the deck is for.
VOICING_FAMILIES: tuple[tuple[str, ...], ...] = (
    ("k", "g"),
    ("s", "z"),
    ("sh", "j"),
    ("t", "d"),
    ("ch", "j"),
    ("ts", "z"),
    ("h", "b", "p"),
    ("f", "b", "p"),
)


def voicing_siblings(romaji: str) -> list[str]:
    """Readings that differ from ``romaji`` only by the voicing mark.

    ``"pa"`` -> ``["ha", "ba"]``; ``"gi"`` -> ``["ki"]``.
    """
    if not romaji:
        return []
    out: list[str] = []
    for family in VOICING_FAMILIES:
        for onset in family:
            if romaji.startswith(onset):
                rest = romaji[len(onset) :]
                for other in family:
                    if other == onset:
                        continue
                    candidate = other + rest
                    if candidate not in out:
                        out.append(candidate)
    return out


def _confusion_partners(glyph: str) -> list[str]:
    """Every glyph curated as visually confusable with ``glyph``."""
    partners: list[str] = []
    for a, b in CONFUSION_PAIRS:
        if a == glyph and b not in partners:
            partners.append(b)
        elif b == glyph and a not in partners:
            partners.append(a)
    return partners
