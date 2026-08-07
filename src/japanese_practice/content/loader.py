"""Seed the ``characters`` table from the bundled content modules.

Seeding is idempotent: rows are upserted on the unique ``glyph`` column, so
re-running it refreshes readings and metadata without renumbering ids or
orphaning the ``attempts`` / ``review_state`` rows that reference them.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..db import Database
from ..models import CharacterSeed
from .hiragana import HIRAGANA
from .kanji_n5 import KANJI_N5
from .katakana import KATAKANA

__all__ = ["ALL_SEEDS", "seed_content"]

#: Every bundled seed, in the order rows are created. Kanji stay in frequency
#: order so that the ``kanji:top200`` / ``kanji:top500`` tiers slice correctly.
ALL_SEEDS: tuple[CharacterSeed, ...] = (*HIRAGANA, *KATAKANA, *KANJI_N5)

_UPSERT = """
INSERT INTO characters (
    glyph, script, romaji, meaning, onyomi, kunyomi,
    kana_group, jlpt_level, category, stroke_count
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(glyph) DO UPDATE SET
    script       = excluded.script,
    romaji       = excluded.romaji,
    meaning      = excluded.meaning,
    onyomi       = excluded.onyomi,
    kunyomi      = excluded.kunyomi,
    kana_group   = excluded.kana_group,
    jlpt_level   = excluded.jlpt_level,
    category     = excluded.category,
    stroke_count = excluded.stroke_count
"""


def _params(seed: CharacterSeed) -> tuple[Any, ...]:
    return (
        seed.glyph,
        seed.script,
        seed.romaji,
        seed.meaning,
        seed.onyomi,
        seed.kunyomi,
        seed.kana_group,
        seed.jlpt_level,
        seed.category,
        seed.stroke_count,
    )


def _deduplicate(seeds: Sequence[CharacterSeed]) -> list[CharacterSeed]:
    """Keep the last seed declared for each glyph, preserving first-seen order."""
    order: dict[str, int] = {}
    unique: list[CharacterSeed] = []
    for seed in seeds:
        index = order.get(seed.glyph)
        if index is None:
            order[seed.glyph] = len(unique)
            unique.append(seed)
        else:
            unique[index] = seed
    return unique


async def seed_content(db: Database, seeds: Sequence[CharacterSeed] | None = None) -> int:
    """Upsert every bundled character seed. Returns the number of seeds applied.

    Safe to call on every start-up: existing rows keep their ids and are simply
    refreshed from the content modules.
    """
    batch = _deduplicate(list(ALL_SEEDS) if seeds is None else list(seeds))
    if not batch:
        return 0
    await db.execute_many(_UPSERT, [_params(seed) for seed in batch])
    return len(batch)
