"""Memory-training card games.

Three board games sharing one engine, all seeded **from the learner's weakest
characters by default** — that is the point of them. A generic memory game with
kana printed on it trains spatial memory; a board built from the characters you
actually keep missing trains the thing you are failing at.

    Match Up    all tiles face up; pair each glyph with its reading
    Pelmanism   the same board face down; classic concentration
    Confusion   pairs drawn from the curated visual-confusion list, so the board
                is deliberately full of look-alikes (シ/ツ, ソ/ン, る/ろ)

**Why these do not feed the drill queue.** As a board empties, elimination
becomes a valid strategy — a late match is nearly free. Counting that as
knowledge would inflate mastery the same way the 3-option chance floor does,
only worse. Wrong pairings *are* recorded, because a mis-pairing is an
unambiguous confusion datum and better evidence than anything the study card
produces.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Literal

from .content.confusions import CONFUSION_PAIRS
from .db import Database, get_character
from .models import Character

GameMode = Literal["matchup", "pelmanism", "confusion"]

MODES: tuple[GameMode, ...] = ("matchup", "pelmanism", "confusion")

#: Pairs per board. Six is 12 tiles — enough to be a memory task, small enough
#: to finish in a sitting.
DEFAULT_PAIRS = 6
MIN_PAIRS = 3
MAX_PAIRS = 12


#: What the dashboard needs to present each game. Kept beside the engine so a
#: new mode cannot be added without describing what it trains.
GAME_CARDS: tuple[dict[str, str], ...] = (
    {
        "mode": "matchup",
        "name": "Match Up",
        "jp": "対応",
        "trains": "Reading → character, the reverse direction no card tests",
        "detail": "All tiles face up. Pair each character with its reading.",
        "motif": "grid",
    },
    {
        "mode": "pelmanism",
        "name": "Pelmanism",
        "jp": "神経衰弱",
        "trains": "Holding a glyph's shape in mind between turns",
        "detail": "Face down. Remember where each one was.",
        "motif": "hidden",
    },
    {
        "mode": "confusion",
        "name": "Confusion Drill",
        "jp": "紛らわしい",
        "trains": "Telling look-alikes apart — シ/ツ, る/ろ, ぬ/め",
        "detail": "A board stacked with the pairs learners actually mix up.",
        "motif": "pairs",
    },
)


@dataclass(frozen=True)
class Tile:
    """One face on the board."""

    pair_id: int
    kind: Literal["glyph", "reading"]
    text: str
    character_id: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "kind": self.kind,
            "text": self.text,
            "character_id": self.character_id,
        }


@dataclass
class Board:
    """A dealt board, ready for the client."""

    mode: GameMode
    tiles: list[Tile] = field(default_factory=list)
    source: str = "weakest"

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "source": self.source,
            "pairs": len(self.tiles) // 2,
            "face_down": self.mode == "pelmanism",
            "tiles": [t.as_dict() for t in self.tiles],
        }


def reading_of(character: Character) -> str:
    """What pairs with the glyph: romaji for kana, meaning for kanji."""
    if character.script == "kanji":
        return character.meaning or character.glyph
    return character.romaji or character.glyph


async def _weakest_character_ids(db: Database, wanted: int) -> list[int]:
    """The characters currently failing, worst first."""
    rows = await db.fetch_all(
        """
        SELECT c.id AS character_id,
               ROUND(SUM(
                   (1 - a.correct) * (1.0 + 0.25 * a.skipped)
                   / (1.0 + MAX(julianday('now') - julianday(a.answered_at), 0))
               ), 4) AS weighted_miss
        FROM attempts a
        JOIN characters c ON c.id = a.character_id
        GROUP BY c.id
        HAVING SUM(1 - a.correct) > 0
        ORDER BY weighted_miss DESC
        LIMIT ?
        """,
        (wanted,),
    )
    return [r["character_id"] for r in rows]


async def _confusable_ids(db: Database, wanted: int) -> list[int]:
    """Characters that appear in the curated visual-confusion list.

    Prefers pairs whose *partner* is also on the board, so the learner is forced
    to discriminate rather than recognise.
    """
    glyphs: list[str] = []
    for a, b in CONFUSION_PAIRS:
        glyphs.extend((a, b))

    seen: set[str] = set()
    ordered = [g for g in glyphs if not (g in seen or seen.add(g))]
    random.shuffle(ordered)

    ids: list[int] = []
    for glyph in ordered:
        row = await db.fetch_one("SELECT id FROM characters WHERE glyph = ?", (glyph,))
        if row:
            ids.append(row["id"])
        if len(ids) >= wanted:
            break
    return ids


async def _fill_from_pool(db: Database, difficulty: str, wanted: int) -> list[int]:
    """Top up from a difficulty key when the weak set is too small."""
    from .db import characters_for_difficulty

    try:
        pool = await characters_for_difficulty(db, difficulty)
    except ValueError:
        pool = []
    ids = [c.id for c in pool]
    random.shuffle(ids)
    return ids[:wanted]


async def build_board(
    db: Database,
    mode: GameMode = "matchup",
    pairs: int = DEFAULT_PAIRS,
    difficulty: str = "hiragana:gojuon",
    character_ids: list[int] | None = None,
) -> Board:
    """Deal a board.

    Selection order: explicit ids, then the learner's weakest characters, then
    the difficulty pool as filler. A brand-new learner has no weak set, so the
    pool is what makes the games usable on day one.
    """
    if mode not in MODES:
        raise ValueError(f"unknown game mode: {mode!r} (expected one of {', '.join(MODES)})")
    pairs = max(MIN_PAIRS, min(MAX_PAIRS, int(pairs)))

    if character_ids:
        chosen, source = list(character_ids)[:pairs], "custom"
    elif mode == "confusion":
        chosen, source = await _confusable_ids(db, pairs), "confusion-pairs"
    else:
        chosen, source = await _weakest_character_ids(db, pairs), "weakest"

    if len(chosen) < pairs:
        source = "weakest+pool" if chosen else "pool"
        for cid in await _fill_from_pool(db, difficulty, pairs * 3):
            if cid not in chosen:
                chosen.append(cid)
            if len(chosen) >= pairs:
                break

    tiles: list[Tile] = []
    for pair_id, cid in enumerate(chosen[:pairs]):
        character = await get_character(db, cid)
        if character is None:
            continue
        tiles.append(Tile(pair_id, "glyph", character.glyph, character.id))
        tiles.append(Tile(pair_id, "reading", reading_of(character), character.id))

    random.shuffle(tiles)
    return Board(mode=mode, tiles=tiles, source=source)
