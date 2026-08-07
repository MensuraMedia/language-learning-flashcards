"""VOICEVOX provider — configuration, graceful absence, and the resolution chain.

The engine is optional, so every test here must pass on a machine without one.
Tests that need a live engine skip themselves rather than fail.
"""

from __future__ import annotations

import pytest

from japanese_practice import tts_voicevox as vv


async def engine_up() -> bool:
    vv.reset_availability()
    return await vv.is_available()


# -- configuration ---------------------------------------------------------


def test_default_speakers_are_the_chosen_narrators():
    """Chosen on measured per-character consistency — see the audition in
    docs/VOICEVOX-EVALUATION.md."""
    assert vv.speaker_for("female").style_id == 30  # No.7 アナウンス
    assert vv.speaker_for("male").style_id == 13  # 青山龍星


def test_speaker_ids_can_be_overridden(monkeypatch):
    monkeypatch.setenv("JP_VOICEVOX_FEMALE", "30")
    assert vv.speaker_for("female").style_id == 30


def test_a_non_numeric_override_is_ignored(monkeypatch):
    """A typo must not take the engine down — fall back to the default."""
    monkeypatch.setenv("JP_VOICEVOX_MALE", "not-an-id")
    assert vv.speaker_for("male").style_id == 13


def test_engine_url_is_configurable(monkeypatch):
    monkeypatch.setenv("JP_VOICEVOX_URL", "http://elsewhere:1234/")
    assert vv.engine_url() == "http://elsewhere:1234"


def test_speed_defaults_and_survives_a_bad_value(monkeypatch):
    assert vv.speed() == pytest.approx(0.85)
    monkeypatch.setenv("JP_VOICEVOX_SPEED", "wildly wrong")
    assert vv.speed() == pytest.approx(0.85)


def test_credit_names_the_speaker():
    """The licence requires attribution naming the voice, not just the engine."""
    assert vv.credit("female") == "VOICEVOX:No.7（アナウンス）"
    assert vv.credit("male") == "VOICEVOX:青山龍星"


# -- graceful absence ------------------------------------------------------


@pytest.mark.asyncio
async def test_absent_engine_is_reported_not_raised(monkeypatch):
    monkeypatch.setenv("JP_VOICEVOX_URL", "http://127.0.0.1:59999")
    vv.reset_availability()
    assert await vv.is_available() is False


@pytest.mark.asyncio
async def test_synthesis_returns_none_when_absent(monkeypatch):
    """The caller falls through to the next provider; it must not except."""
    monkeypatch.setenv("JP_VOICEVOX_URL", "http://127.0.0.1:59999")
    vv.reset_availability()
    assert await vv.synthesize("あ") is None


@pytest.mark.asyncio
async def test_accessors_are_empty_when_absent(monkeypatch):
    monkeypatch.setenv("JP_VOICEVOX_URL", "http://127.0.0.1:59999")
    vv.reset_availability()
    assert await vv.speakers() == []
    assert await vv.audio_query("あ") is None
    assert await vv.accent_pattern("あ") == []


@pytest.mark.asyncio
async def test_availability_is_memoised(monkeypatch):
    monkeypatch.setenv("JP_VOICEVOX_URL", "http://127.0.0.1:59999")
    vv.reset_availability()
    assert await vv.is_available() is False
    # Second call must not re-probe — a dead engine should cost nothing.
    monkeypatch.setenv("JP_VOICEVOX_URL", "http://127.0.0.1:1")
    assert await vv.is_available() is False


# -- live engine (skipped when absent) -------------------------------------


@pytest.mark.asyncio
async def test_synthesises_real_audio():
    if not await engine_up():
        pytest.skip("no local VOICEVOX engine")
    result = await vv.synthesize("あ")
    assert result is not None
    audio, mimetype = result
    assert mimetype == vv.MIME_WAV
    assert audio[:4] == b"RIFF"
    assert len(audio) > 1000


@pytest.mark.asyncio
async def test_exposes_per_mora_phonology():
    """The capability that motivated adopting VOICEVOX at all."""
    if not await engine_up():
        pytest.skip("no local VOICEVOX engine")
    pattern = await vv.accent_pattern("きょう")
    assert [m["mora"] for m in pattern] == ["キョ", "オ"]
    assert all("pitch" in m and "vowel_length" in m for m in pattern)


@pytest.mark.asyncio
async def test_distinguishes_a_pitch_accent_minimal_pair():
    """箸 (HL) and 橋 (LH) differ only by accent position in speech."""
    if not await engine_up():
        pytest.skip("no local VOICEVOX engine")
    hashi_chopsticks = await vv.accent_pattern("箸")
    hashi_bridge = await vv.accent_pattern("橋")

    assert [m["is_accent"] for m in hashi_chopsticks] == [True, False]
    assert [m["is_accent"] for m in hashi_bridge] == [False, True]


@pytest.mark.asyncio
async def test_geminate_is_a_timed_silent_mora():
    """っ occupies a beat with no pitch — the beat English speakers drop."""
    if not await engine_up():
        pytest.skip("no local VOICEVOX engine")
    pattern = await vv.accent_pattern("学校")
    small_tsu = [m for m in pattern if m["mora"] == "ッ"]
    assert small_tsu, "geminate not represented as its own mora"
    assert small_tsu[0]["pitch"] == 0.0
