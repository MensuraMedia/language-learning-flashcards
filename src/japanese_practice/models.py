"""Frozen data models (BUILD-SPEC section 4).

These are plain value objects: no behaviour beyond construction from a database
row. Field order and names match the schema in ``schema.sql`` exactly.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

__all__ = ["Attempt", "Character", "CharacterSeed", "Session"]


@dataclass(frozen=True, slots=True)
class CharacterSeed:
    """A character as declared in ``content/`` — no database identity yet."""

    glyph: str
    script: str
    romaji: str | None = None
    meaning: str | None = None
    onyomi: str | None = None
    kunyomi: str | None = None
    kana_group: str | None = None
    jlpt_level: str | None = None
    category: str | None = None
    stroke_count: int | None = None


@dataclass(frozen=True, slots=True)
class Character:
    """A persisted row of the ``characters`` table."""

    id: int
    glyph: str
    script: str
    romaji: str | None
    meaning: str | None
    onyomi: str | None
    kunyomi: str | None
    kana_group: str | None
    jlpt_level: str | None
    category: str | None
    stroke_count: int | None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Character:
        """Build a :class:`Character` from a dict-like database row."""
        return cls(
            id=row["id"],
            glyph=row["glyph"],
            script=row["script"],
            romaji=row["romaji"],
            meaning=row["meaning"],
            onyomi=row["onyomi"],
            kunyomi=row["kunyomi"],
            kana_group=row["kana_group"],
            jlpt_level=row["jlpt_level"],
            category=row["category"],
            stroke_count=row["stroke_count"],
        )

    def to_seed(self) -> CharacterSeed:
        """Drop the database identity, yielding the equivalent seed."""
        return CharacterSeed(
            glyph=self.glyph,
            script=self.script,
            romaji=self.romaji,
            meaning=self.meaning,
            onyomi=self.onyomi,
            kunyomi=self.kunyomi,
            kana_group=self.kana_group,
            jlpt_level=self.jlpt_level,
            category=self.category,
            stroke_count=self.stroke_count,
        )


@dataclass(frozen=True, slots=True)
class Attempt:
    """A single answered card within a session."""

    id: int
    session_id: int
    character_id: int
    answered_at: str
    correct: int
    latency_ms: int | None
    first_attempt: int
    given_answer: str | None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Attempt:
        """Build an :class:`Attempt` from a dict-like database row."""
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            character_id=row["character_id"],
            answered_at=row["answered_at"],
            correct=row["correct"],
            latency_ms=row["latency_ms"],
            first_attempt=row["first_attempt"],
            given_answer=row["given_answer"],
        )


@dataclass(frozen=True, slots=True)
class Session:
    """A practice session; ``ended_at`` is ``None`` while it is still running."""

    id: int
    started_at: str
    ended_at: str | None
    challenge: str
    scoring: str
    difficulty: str
    score: int
    total: int
    correct: int
    max_streak: int

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Session:
        """Build a :class:`Session` from a dict-like database row."""
        return cls(
            id=row["id"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            challenge=row["challenge"],
            scoring=row["scoring"],
            difficulty=row["difficulty"],
            score=row["score"],
            total=row["total"],
            correct=row["correct"],
            max_streak=row["max_streak"],
        )

    def with_totals(self, *, score: int, total: int, correct: int, max_streak: int) -> Session:
        """Return a copy carrying updated running totals."""
        return replace(self, score=score, total=total, correct=correct, max_streak=max_streak)
