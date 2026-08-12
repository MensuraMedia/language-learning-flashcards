"""Japanese content-data integrity.

This is the highest-stakes suite in the project. A wrong reading here does not
crash anything — it silently teaches a learner something false. Every assertion
is checked against `mockups/_reference/JAPANESE-CONTENT-MODEL.md`, which is the
authoritative source derived from the MensuraMedia/language-learning workbooks.
"""

from __future__ import annotations

from collections import Counter

import pytest

from japanese_practice.content.confusions import CONFUSION_PAIRS
from japanese_practice.content.hiragana import HIRAGANA
from japanese_practice.content.kanji_n5 import KANJI_N5
from japanese_practice.content.katakana import KATAKANA
from japanese_practice.content.loader import ALL_SEEDS

# Counts from the authoritative reference. These are not "about right" — they
# are the exact figures the workbooks publish.
EXPECTED_HIRAGANA = 104
EXPECTED_KATAKANA = 104
EXPECTED_KANJI_N5 = 113

# 46 gojuon + 20 dakuon + 5 handakuon + 33 yoon = 104
EXPECTED_KANA_GROUPS = {"gojuon": 46, "dakuon": 20, "handakuon": 5, "yoon": 33}

# Unicode blocks. Anything outside these is a script mix-up.
HIRAGANA_RANGE = ("ぁ", "ゟ")
KATAKANA_RANGE = ("゠", "ヿ")

# The romanisation traps. Non-Hepburn forms (si/ti/tu/hu/zi) are wrong here.
HEPBURN_HIRAGANA = {
    "し": "shi",
    "ち": "chi",
    "つ": "tsu",
    "ふ": "fu",
    "じ": "ji",
    "を": "wo",
    "ん": "n",
    "しゃ": "sha",
    "しゅ": "shu",
    "しょ": "sho",
    "じゃ": "ja",
    "じゅ": "ju",
    "じょ": "jo",
    "ちゃ": "cha",
    "ちょ": "cho",
}
HEPBURN_KATAKANA = {
    "シ": "shi",
    "チ": "chi",
    "ツ": "tsu",
    "フ": "fu",
    "ジ": "ji",
    "ヲ": "wo",
    "ン": "n",
    "シャ": "sha",
    "シュ": "shu",
    "ショ": "sho",
}

FORBIDDEN_ROMAJI = {"si", "ti", "tu", "hu", "zi", "sya", "syu", "syo", "tya", "tyu", "tyo"}


# -- counts ----------------------------------------------------------------


@pytest.mark.parametrize(
    "name,seeds,expected",
    [
        ("hiragana", HIRAGANA, EXPECTED_HIRAGANA),
        ("katakana", KATAKANA, EXPECTED_KATAKANA),
        ("kanji_n5", KANJI_N5, EXPECTED_KANJI_N5),
    ],
)
def test_set_sizes_match_the_reference(name, seeds, expected):
    assert len(seeds) == expected, f"{name}: expected {expected}, got {len(seeds)}"


@pytest.mark.parametrize("seeds", [HIRAGANA, KATAKANA])
def test_kana_group_split_matches_the_reference(seeds):
    counts = Counter(s.kana_group for s in seeds)
    assert dict(counts) == EXPECTED_KANA_GROUPS


# -- uniqueness ------------------------------------------------------------


@pytest.mark.parametrize(
    "name,seeds",
    [("hiragana", HIRAGANA), ("katakana", KATAKANA), ("kanji_n5", KANJI_N5)],
)
def test_no_duplicate_glyphs_within_a_set(name, seeds):
    dupes = [g for g, n in Counter(s.glyph for s in seeds).items() if n > 1]
    assert not dupes, f"{name} contains duplicate glyphs: {dupes}"


def test_no_glyph_appears_in_two_scripts():
    """A glyph in both the hiragana and katakana lists is a copy-paste error."""
    overlap = {s.glyph for s in HIRAGANA} & {s.glyph for s in KATAKANA}
    assert not overlap, f"glyphs claimed by both syllabaries: {overlap}"


# -- script correctness ----------------------------------------------------


def test_every_hiragana_glyph_is_in_the_hiragana_block():
    stray = [
        s.glyph
        for s in HIRAGANA
        if not all(HIRAGANA_RANGE[0] <= ch <= HIRAGANA_RANGE[1] for ch in s.glyph)
    ]
    assert not stray, f"non-hiragana characters in HIRAGANA: {stray}"


def test_every_katakana_glyph_is_in_the_katakana_block():
    stray = [
        s.glyph
        for s in KATAKANA
        if not all(KATAKANA_RANGE[0] <= ch <= KATAKANA_RANGE[1] for ch in s.glyph)
    ]
    assert not stray, f"non-katakana characters in KATAKANA: {stray}"


@pytest.mark.parametrize(
    "seeds,script", [(HIRAGANA, "hiragana"), (KATAKANA, "katakana"), (KANJI_N5, "kanji")]
)
def test_script_field_is_set_correctly(seeds, script):
    wrong = [s.glyph for s in seeds if s.script != script]
    assert not wrong, f"wrong script field on: {wrong}"


# -- romanisation ----------------------------------------------------------


@pytest.mark.parametrize("glyph,romaji", sorted(HEPBURN_HIRAGANA.items()))
def test_hiragana_hepburn_traps(glyph, romaji):
    table = {s.glyph: s.romaji for s in HIRAGANA}
    assert table.get(glyph) == romaji


@pytest.mark.parametrize("glyph,romaji", sorted(HEPBURN_KATAKANA.items()))
def test_katakana_hepburn_traps(glyph, romaji):
    table = {s.glyph: s.romaji for s in KATAKANA}
    assert table.get(glyph) == romaji


@pytest.mark.parametrize("seeds", [HIRAGANA, KATAKANA])
def test_no_kunrei_or_nihon_shiki_romanisation(seeds):
    """Guards against si/ti/tu/hu/zi creeping in from a different system."""
    offenders = [(s.glyph, s.romaji) for s in seeds if s.romaji in FORBIDDEN_ROMAJI]
    assert not offenders, f"non-Hepburn romanisation: {offenders}"


@pytest.mark.parametrize("seeds", [HIRAGANA, KATAKANA])
def test_every_kana_has_romaji_and_a_group(seeds):
    missing = [s.glyph for s in seeds if not s.romaji or not s.kana_group]
    assert not missing, f"kana missing romaji or kana_group: {missing}"


@pytest.mark.parametrize("seeds", [HIRAGANA, KATAKANA])
def test_kana_carry_no_kanji_only_fields(seeds):
    bad = [s.glyph for s in seeds if s.meaning or s.onyomi or s.kunyomi]
    assert not bad, f"kana carrying kanji fields: {bad}"


def test_yoon_are_two_character_digraphs():
    """Yoon are contractions like きゃ — a single character is not a yoon."""
    wrong = [s.glyph for s in HIRAGANA if s.kana_group == "yoon" and len(s.glyph) != 2]
    assert not wrong, f"yoon that are not digraphs: {wrong}"


# -- kanji -----------------------------------------------------------------


def test_every_kanji_has_a_meaning():
    missing = [s.glyph for s in KANJI_N5 if not s.meaning]
    assert not missing, f"kanji without a meaning: {missing}"


def test_every_kanji_has_at_least_one_reading():
    missing = [s.glyph for s in KANJI_N5 if not (s.onyomi or s.kunyomi)]
    assert not missing, f"kanji with neither on'yomi nor kun'yomi: {missing}"


def test_every_kanji_is_labelled_n5():
    wrong = [s.glyph for s in KANJI_N5 if s.jlpt_level != "N5"]
    assert not wrong, f"kanji not labelled N5: {wrong}"


def test_onyomi_is_written_in_katakana():
    """Convention: on'yomi in katakana, kun'yomi in hiragana."""
    offenders = []
    for seed in KANJI_N5:
        if not seed.onyomi:
            continue
        letters = [c for c in seed.onyomi if c.isalpha()]
        if any(HIRAGANA_RANGE[0] <= c <= HIRAGANA_RANGE[1] for c in letters):
            offenders.append((seed.glyph, seed.onyomi))
    assert not offenders, f"on'yomi containing hiragana: {offenders}"


def test_kunyomi_is_written_in_hiragana():
    offenders = []
    for seed in KANJI_N5:
        if not seed.kunyomi:
            continue
        letters = [c for c in seed.kunyomi if c.isalpha()]
        if any(KATAKANA_RANGE[0] <= c <= KATAKANA_RANGE[1] for c in letters):
            offenders.append((seed.glyph, seed.kunyomi))
    assert not offenders, f"kun'yomi containing katakana: {offenders}"


@pytest.mark.parametrize(
    "glyph,meaning,onyomi",
    [("水", "water", "スイ"), ("山", "mountain", "サン"), ("人", "person", "ジン")],
)
def test_known_kanji_readings_are_correct(glyph, meaning, onyomi):
    """Spot-check against the reference document's verified table."""
    table = {s.glyph: s for s in KANJI_N5}
    seed = table.get(glyph)
    assert seed is not None, f"{glyph} missing from KANJI_N5"
    assert meaning in seed.meaning.lower()
    assert onyomi in (seed.onyomi or "")


def test_stroke_counts_are_plausible_when_present():
    bad = [
        (s.glyph, s.stroke_count)
        for s in KANJI_N5
        if s.stroke_count is not None and not 1 <= s.stroke_count <= 30
    ]
    assert not bad, f"implausible stroke counts: {bad}"


# -- confusion pairs -------------------------------------------------------


def test_a_glyph_may_repeat_across_scripts_but_never_within_one():
    """は is a hiragana character and the topic particle; 一 is a kanji and 1.

    They are different learning objects with different answers. What must never
    happen is the same glyph twice *inside* one script.
    """
    seen = Counter((s.glyph, s.script) for s in ALL_SEEDS)
    duplicates = [pair for pair, n in seen.items() if n > 1]
    assert not duplicates, f"duplicated within a script: {duplicates[:8]}"

    across = Counter(s.glyph for s in ALL_SEEDS)
    shared = [g for g, n in across.items() if n > 1]
    assert shared, "expected some glyphs to be shared between scripts"


def test_confusion_pairs_reference_known_glyphs():
    # Every bundled set, not just the three original ones — a confusion pair is
    # useless if either half is missing from the database.
    known = {s.glyph for s in ALL_SEEDS}
    unknown = {g for pair in CONFUSION_PAIRS for g in pair if g not in known}
    assert not unknown, f"confusion pairs referencing unknown glyphs: {unknown}"


def test_confusion_pairs_are_not_self_referential():
    same = [p for p in CONFUSION_PAIRS if p[0] == p[1]]
    assert not same, f"a character cannot be confused with itself: {same}"


def test_confusion_pairs_include_the_classic_traps():
    """シ/ツ and ソ/ン are the canonical katakana confusions."""
    normalised = {frozenset(p) for p in CONFUSION_PAIRS}
    for a, b in (("シ", "ツ"), ("ソ", "ン")):
        assert frozenset((a, b)) in normalised, f"missing classic pair {a}/{b}"


def test_documented_totals_match_the_seed_set():
    """Counts appear in the README, the docs and the dashboard subtitle.

    They drifted once already — six characters were added to N5 after the
    figures were written — so the numbers are asserted rather than trusted.
    """
    kanji = [s for s in ALL_SEEDS if s.script == "kanji"]
    vocab = [s for s in ALL_SEEDS if s.script == "vocab"]
    phrases = [s for s in ALL_SEEDS if s.script == "phrase"]
    assert len(ALL_SEEDS) == 1743
    assert len(kanji) == 1251
    assert len(vocab) == 106
    # 93 phrase/social cards plus the 85 General Words cards, which reuse the
    # phrase script — they are short expressions, graded on meaning, and need
    # the wide card and the note that the phrase machinery already provides.
    assert len(phrases) == 178
    by_level = Counter(s.jlpt_level for s in kanji)
    assert by_level == {"N5": 113, "N4": 169, "N3": 396, "N2": 236, "N1": 337}


def test_general_words_sets_are_complete_and_carry_a_sentence():
    """Every General Words card must show a word in use, not just a gloss.

    These sets exist because the English gloss is the *problem*: four words all
    glossed "maybe" are indistinguishable until you see each one working. A card
    without its example sentence teaches nothing the gloss did not.
    """
    from japanese_practice.content.general import GENERAL

    by_set = Counter(card.category for card in GENERAL)
    assert by_set == {
        "Maybe — degrees of certainty": 10,
        "Not bad — faint praise": 10,
        "Seriously — surprise and disbelief": 11,
        "Question words": 14,
        "Sorry — degrees of contrition": 10,
        "Thanks — degrees of gratitude": 10,
        "Very — degrees of intensity": 10,
        "Saying no without saying no": 10,
    }

    for card in GENERAL:
        assert card.note, f"{card.glyph} has no example sentence"
        assert card.romaji, f"{card.glyph} has no reading"
        assert card.meaning, f"{card.glyph} has no meaning"
        # The note must contain Japanese — a note that only paraphrases the
        # gloss in English is the very thing these cards exist to avoid.
        assert any(
            "぀" <= ch <= "ヿ" or "一" <= ch <= "鿿" for ch in card.note
        ), f"{card.glyph}'s note carries no Japanese example"


def test_general_words_glyphs_are_unique_within_the_set():
    from japanese_practice.content.general import GENERAL

    glyphs = [card.glyph for card in GENERAL]
    duplicates = [g for g, n in Counter(glyphs).items() if n > 1]
    assert duplicates == [], f"duplicate glyphs: {duplicates}"
