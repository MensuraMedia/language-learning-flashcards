"""Voice lab — planning, text derivation and resumability.

These tests deliberately never call the API. What matters here is that the
toolset plans the right work, says the right thing for each script, and can be
re-run without re-spending on clips that already exist.
"""

from __future__ import annotations

import pytest

from japanese_practice import audio_library as lib
from japanese_practice import voicelab
from japanese_practice.models import CharacterSeed
from japanese_practice.session import voicing_siblings

# -- what gets spoken ------------------------------------------------------


def test_kana_are_spoken_as_the_glyph():
    seed = CharacterSeed(glyph="あ", script="hiragana", romaji="a", kana_group="gojuon")
    assert voicelab.speech_text_for(seed) == "あ"


def test_kanji_prefer_kunyomi_over_onyomi():
    seed = CharacterSeed(glyph="水", script="kanji", meaning="water", onyomi="スイ", kunyomi="みず")
    assert voicelab.speech_text_for(seed) == "みず"


def test_kanji_fall_back_to_onyomi_when_there_is_no_kunyomi():
    seed = CharacterSeed(glyph="駅", script="kanji", meaning="station", onyomi="エキ")
    assert voicelab.speech_text_for(seed) == "エキ"


def test_okurigana_brackets_are_stripped_and_alternatives_dropped():
    """`ひと(つ)/いち` must be spoken as `ひとつ`, not read literally."""
    seed = CharacterSeed(glyph="一", script="kanji", meaning="one", kunyomi="ひと(つ)/いち")
    assert voicelab.speech_text_for(seed) == "ひとつ"


def test_a_kanji_with_no_readings_falls_back_to_the_glyph():
    seed = CharacterSeed(glyph="々", script="kanji", meaning="repeat")
    assert voicelab.speech_text_for(seed) == "々"


# -- planning --------------------------------------------------------------


def test_plan_covers_every_character_in_every_voice():
    seeds = voicelab.all_seeds()
    jobs = voicelab.plan(("female", "male"))
    assert len(jobs) == len(seeds) * 2
    assert {j.voice for j in jobs} == {"female", "male"}


def test_plan_targets_the_script_voice_glyph_layout():
    job = next(j for j in voicelab.plan(("female",)) if j.glyph == "あ")
    assert job.path.parts[-3:] == ("hiragana", "female", "あ.mp3")


def test_every_planned_job_has_something_to_say():
    assert all(j.text.strip() for j in voicelab.plan(("female",)))


# -- resumability ----------------------------------------------------------


def write_mp3_stub(path):
    """A file that passes the .mp3 gates: ID3 magic and comfortably over the
    size floor. Clip paths are .mp3, so a WAV body would be rejected — which is
    the validator behaving correctly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 4096)
    return path


def test_outstanding_skips_clips_that_already_validate(tmp_path, monkeypatch):
    """A re-run must not re-spend on work already done."""
    monkeypatch.setattr(lib, "LIBRARY_ROOT", tmp_path)

    jobs = voicelab.plan(("female",))[:3]
    assert len(voicelab.outstanding(jobs)) == 3

    write_mp3_stub(jobs[0].path)
    remaining = voicelab.outstanding(jobs)
    assert len(remaining) == 2
    assert jobs[0] not in remaining


def test_outstanding_re_renders_an_invalid_clip(tmp_path, monkeypatch):
    """A silent file is worse than a missing one — it must be redone."""
    monkeypatch.setattr(lib, "LIBRARY_ROOT", tmp_path)
    jobs = voicelab.plan(("female",))[:1]
    jobs[0].path.parent.mkdir(parents=True, exist_ok=True)
    jobs[0].path.write_bytes(b"not audio at all" * 40)  # right name, wrong bytes
    assert voicelab.outstanding(jobs) == jobs


# -- candidate slate -------------------------------------------------------


def test_candidate_slate_offers_both_genders():
    genders = {g for g, _, _ in voicelab.CANDIDATES}
    assert genders == {"female", "male"}


def test_audition_phrase_exercises_the_hard_sounds():
    """Long vowel, moraic n, yoon and geminate — what narrators get wrong."""
    phrase = voicelab.AUDITION_PHRASE
    assert "ん" in phrase, "moraic n absent"
    assert "きょ" in phrase, "yoon absent"
    assert "っ" in phrase, "geminate absent"
    assert all(v in phrase for v in "あいうえお"), "vowel row incomplete"


# -- voicing siblings (distractors, but the same phonology) ----------------


@pytest.mark.parametrize(
    "romaji,expected",
    [("pa", "ha"), ("pa", "ba"), ("ga", "ka"), ("za", "sa"), ("da", "ta"), ("bo", "ho")],
)
def test_voicing_siblings_cross_the_dakuten_families(romaji, expected):
    assert expected in voicing_siblings(romaji)


def test_voicing_siblings_never_returns_the_input():
    for r in ("pa", "ka", "shi", "to"):
        assert r not in voicing_siblings(r)
