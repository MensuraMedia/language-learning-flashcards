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
from .expressions import EXPRESSIONS
from .hiragana import HIRAGANA
from .kanji_frequency import KANJI_BY_FREQUENCY
from .kanji_n1 import KANJI_N1
from .kanji_n2 import KANJI_N2
from .kanji_n3 import KANJI_N3
from .kanji_n4 import KANJI_N4
from .kanji_n5 import KANJI_N5
from .katakana import KATAKANA
from .phrases import PHRASES
from .vocabulary import VOCABULARY

__all__ = ["ALL_SEEDS", "apply_frequency_ranks", "seed_content"]

#: Every bundled seed, in the order rows are created. Kanji stay in frequency
#: order so that the ``kanji:top200`` / ``kanji:top500`` tiers slice correctly.
ALL_SEEDS: tuple[CharacterSeed, ...] = (
    *HIRAGANA,
    *KATAKANA,
    *KANJI_N5,
    *KANJI_N4,
    *KANJI_N3,
    *KANJI_N2,
    *KANJI_N1,
    *VOCABULARY,
    *EXPRESSIONS,
    *PHRASES,
)

_UPSERT = """
INSERT INTO characters (
    glyph, script, romaji, meaning, onyomi, kunyomi,
    kana_group, jlpt_level, category, stroke_count
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(glyph, script) DO UPDATE SET
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
    """Keep the last seed declared for each ``(glyph, script)``, in first-seen order.

    Keyed on the pair, not the glyph: は exists as both a hiragana character and
    a particle, and deduplicating on glyph alone would drop one of them.
    """
    order: dict[tuple[str, str], int] = {}
    unique: list[CharacterSeed] = []
    for seed in seeds:
        index = order.get((seed.glyph, seed.script))
        if index is None:
            order[(seed.glyph, seed.script)] = len(unique)
            unique.append(seed)
        else:
            unique[index] = seed
    return unique


_RANK = "UPDATE characters SET frequency_rank = ? WHERE glyph = ? AND script = 'kanji'"


async def apply_frequency_ranks(db: Database) -> int:
    """Stamp the teaching-order rank onto every glyph in the Top 500.

    Kept separate from the seed upsert because the ranking is a property of the
    curriculum, not of a character: the same glyph is seeded once, by level, and
    then ranked. Rows outside the Top 500 keep ``NULL``, which is what excludes
    them from the volume tiers.
    """
    await db.execute_many(
        _RANK, [(rank, glyph) for rank, glyph in enumerate(KANJI_BY_FREQUENCY, start=1)]
    )
    return len(KANJI_BY_FREQUENCY)


async def seed_content(db: Database, seeds: Sequence[CharacterSeed] | None = None) -> int:
    """Upsert every bundled character seed. Returns the number of seeds applied.

    Safe to call on every start-up: existing rows keep their ids and are simply
    refreshed from the content modules.
    """
    batch = _deduplicate(list(ALL_SEEDS) if seeds is None else list(seeds))
    if not batch:
        return 0
    await db.execute_many(_UPSERT, [_params(seed) for seed in batch])
    await apply_frequency_ranks(db)
    return len(batch)
