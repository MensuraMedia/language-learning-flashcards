"""Kana → romaji, the reading reference on a kanji card."""

from __future__ import annotations

import pytest

from japanese_practice.content.loader import ALL_SEEDS
from japanese_practice.kana import to_romaji


@pytest.mark.parametrize(
    "kana,expected",
    [
        # Hepburn consonants, never the kunrei forms
        ("シ", "shi"),
        ("チ", "chi"),
        ("ツ", "tsu"),
        ("フ", "fu"),
        ("ジ", "ji"),
        ("ヲ", "wo"),
        ("ン", "n"),
        # digraphs beat the monographs they contain
        ("シュウ", "shuu"),
        ("チョウ", "chou"),
        ("キョ", "kyo"),
        ("リュウ", "ryuu"),
        ("ギョウ", "gyou"),
        # hiragana and katakana fold onto one table
        ("あに", "ani"),
        ("おとうと", "otouto"),
        ("みずから", "mizukara"),
        # geminates double the following consonant
        ("おっと", "otto"),
        ("がっこう", "gakkou"),
        ("いっち", "itchi"),
        # structure is preserved, not transliterated
        ("ひと(つ)", "hito(tsu)"),
        ("よっ(つ)/よん", "yot(tsu)/yon"),
        ("セイ/サイ", "sei/sai"),
        # the long mark repeats the vowel before it
        ("ラーメン", "raamen"),
    ],
)
def test_transliterations(kana, expected):
    assert to_romaji(kana) == expected


def test_absent_readings_need_no_guard():
    assert to_romaji(None) == ""
    assert to_romaji("") == ""


def test_every_seeded_reading_transliterates_completely():
    """No kanji reading may leave kana behind in its romaji."""
    leftovers = []
    for seed in ALL_SEEDS:
        for reading in (seed.onyomi, seed.kunyomi, seed.romaji):
            out = to_romaji(reading)
            if any("ぁ" <= c <= "ヿ" for c in out):
                leftovers.append((seed.glyph, reading, out))
    assert not leftovers, f"untransliterated kana: {leftovers[:8]}"
