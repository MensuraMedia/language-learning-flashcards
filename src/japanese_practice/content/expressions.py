"""Closed grammatical sets: demonstratives and particles.

These are **not** extracted from the reference worksheets, which do not cover
them. They are authored here because both are closed, rigidly structured systems
that every N5 course teaches identically — unlike open vocabulary, where writing
entries from memory would produce confident, plausible, unverifiable data.

The こそあど series is a 4 × 5 grid: four distances (near me / near you / over
there / which) across five word classes. Its regularity is the thing worth
drilling, and it is also what makes the set safe to author — a missing or wrong
cell is visible as a hole in the grid.

Particles are the "multi-function words": a dozen or so items that appear in
almost every sentence and whose job is grammatical rather than lexical. A
learner who knows は from が can read far more than one who knows another fifty
nouns, which is why they get their own deck.
"""

from __future__ import annotations

from ..models import CharacterSeed

__all__ = ["EXPRESSIONS"]

_DEMONSTRATIVE = "Demonstratives"
_PARTICLE = "Particles"


def _e(glyph: str, romaji: str, meaning: str, category: str) -> CharacterSeed:
    return CharacterSeed(
        glyph=glyph,
        script="vocab",
        romaji=romaji,
        meaning=meaning,
        category=category,
    )


#: こそあど, as a grid. Rows are word class, columns are distance:
#: ko- (near the speaker) · so- (near the listener) · a- (away from both) ·
#: do- (the question form).
_KOSOADO = (
    # thing
    ("これ", "kore", "this one (near me)"),
    ("それ", "sore", "that one (near you)"),
    ("あれ", "are", "that one (over there)"),
    ("どれ", "dore", "which one"),
    # place
    ("ここ", "koko", "here"),
    ("そこ", "soko", "there (near you)"),
    ("あそこ", "asoko", "over there"),
    ("どこ", "doko", "where"),
    # modifier — always precedes a noun
    ("この", "kono", "this ... (near me)"),
    ("その", "sono", "that ... (near you)"),
    ("あの", "ano", "that ... (over there)"),
    ("どの", "dono", "which ..."),
    # manner
    ("こう", "kou", "like this"),
    ("そう", "sou", "like that"),
    ("ああ", "aa", "like that (over there)"),
    ("どう", "dou", "how"),
    # kind of
    ("こんな", "konna", "this kind of"),
    ("そんな", "sonna", "that kind of"),
    ("あんな", "anna", "that kind of (over there)"),
    ("どんな", "donna", "what kind of"),
)

#: The particles a beginner meets first, with the job each one does. Meanings
#: are functional descriptions rather than translations, because most of these
#: have no English word — they mark a role in the sentence.
_PARTICLES = (
    ("は", "wa", "topic marker (written ha)"),
    ("が", "ga", "subject marker"),
    ("を", "o", "direct object marker (written wo)"),
    ("に", "ni", "to / at / in — destination or time"),
    ("で", "de", "by means of / at — location of action"),
    ("と", "to", "and / with (complete list)"),
    ("も", "mo", "also / too"),
    ("の", "no", "possessive — links two nouns"),
    ("へ", "e", "toward (written he)"),
    ("から", "kara", "from / because"),
    ("まで", "made", "until / as far as"),
    ("や", "ya", "and (incomplete list)"),
    ("ね", "ne", "isn't it — seeking agreement"),
    ("よ", "yo", "emphasis — telling you something"),
    ("か", "ka", "question marker"),
)

#: 35 entries across two sets.
EXPRESSIONS: tuple[CharacterSeed, ...] = (
    *(_e(g, r, m, _DEMONSTRATIVE) for g, r, m in _KOSOADO),
    *(_e(g, r, m, _PARTICLE) for g, r, m in _PARTICLES),
)
