"""Local clip library: layout, validation and manifest.

The validator's job is to stop bad audio reaching a learner. A silent clip is
the worst failure mode — nothing plays, and the learner concludes the audio is
broken or, worse, that the character has no sound. These tests assert each
rejection reason explicitly.
"""

from __future__ import annotations

import struct
import wave

import pytest

from japanese_practice import audio_library as lib


def write_tone(path, *, seconds=0.8, rate=22050, amplitude=8000, streaming_header=False):
    """A valid, audible PCM WAV."""
    frames = int(seconds * rate)
    samples = [int(amplitude * (1 if (i // 50) % 2 else -1)) for i in range(frames)]
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(struct.pack(f"<{frames}h", *samples))
    if streaming_header:
        # Emulate espeak-ng: declare an unknown/placeholder length in the header.
        raw = bytearray(path.read_bytes())
        raw[40:44] = (0xFFFFFFF0).to_bytes(4, "little")
        path.write_bytes(bytes(raw))
    return path


def write_silence(path, *, seconds=0.8, rate=22050):
    frames = int(seconds * rate)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(struct.pack(f"<{frames}h", *([0] * frames)))
    return path


# -- path layout -----------------------------------------------------------


def test_clip_path_encodes_script_voice_and_glyph():
    path = lib.clip_path("hiragana", "あ", "female")
    assert path.parts[-3:] == ("hiragana", "female", "あ.mp3")


@pytest.mark.parametrize("voice", lib.VOICES)
def test_both_voices_are_addressable(voice):
    assert lib.clip_path("kanji", "水", voice).parent.name == voice


@pytest.mark.parametrize(
    "script,glyph,voice",
    [
        ("klingon", "あ", "female"),
        ("hiragana", "あ", "robot"),
        ("hiragana", "../etc/passwd", "female"),
        ("hiragana", "a/b", "female"),
        ("hiragana", "", "female"),
    ],
)
def test_unsafe_or_unknown_inputs_are_rejected(script, glyph, voice):
    with pytest.raises(ValueError):
        lib.clip_path(script, glyph, voice)


# -- validation: the accept case -------------------------------------------


def test_a_real_audible_clip_validates(tmp_path):
    report = lib.validate_clip(write_tone(tmp_path / "ok.wav"))
    assert report.ok, report.reason
    assert 700 <= report.duration_ms <= 900
    assert report.peak > lib.MIN_PEAK_AMPLITUDE
    assert len(report.sha256) == 64


def test_streaming_header_duration_is_derived_from_actual_bytes(tmp_path):
    """espeak-ng writes a placeholder length; trusting it gave absurd durations."""
    report = lib.validate_clip(write_tone(tmp_path / "stream.wav", streaming_header=True))
    assert report.ok, report.reason
    assert 700 <= report.duration_ms <= 900


# -- validation: every rejection reason ------------------------------------


def test_silent_clip_is_rejected(tmp_path):
    report = lib.validate_clip(write_silence(tmp_path / "silent.wav"))
    assert not report.ok
    assert "silent" in report.reason


def test_missing_file_is_rejected(tmp_path):
    report = lib.validate_clip(tmp_path / "nope.wav")
    assert not report.ok
    assert report.reason == "missing"


def test_truncated_file_is_rejected(tmp_path):
    path = tmp_path / "trunc.wav"
    path.write_bytes(b"RIFF")
    report = lib.validate_clip(path)
    assert not report.ok
    assert "too small" in report.reason


def test_non_riff_data_is_rejected(tmp_path):
    path = tmp_path / "fake.wav"
    path.write_bytes(b"X" * 4096)
    report = lib.validate_clip(path)
    assert not report.ok
    assert "RIFF" in report.reason


def test_non_mp3_data_is_rejected(tmp_path):
    path = tmp_path / "fake.mp3"
    path.write_bytes(b"definitely not audio" * 100)
    report = lib.validate_clip(path)
    assert not report.ok
    assert "MP3" in report.reason


def test_unsupported_extension_is_rejected(tmp_path):
    path = tmp_path / "clip.ogg"
    path.write_bytes(b"OggS" + b"\x00" * 4096)
    report = lib.validate_clip(path)
    assert not report.ok
    assert "unsupported" in report.reason


@pytest.mark.parametrize("seconds", [0.05, 6.0])
def test_implausible_durations_are_rejected(tmp_path, seconds):
    """Too short is a truncated render; too long means a word, not a mora."""
    report = lib.validate_clip(write_tone(tmp_path / "dur.wav", seconds=seconds))
    assert not report.ok
    assert "duration" in report.reason


def test_validation_never_raises_on_a_directory(tmp_path):
    report = lib.validate_clip(tmp_path)
    assert not report.ok


# -- manifest --------------------------------------------------------------


def test_manifest_separates_accepted_from_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "LIBRARY_ROOT", tmp_path)
    monkeypatch.setattr(lib, "MANIFEST_PATH", tmp_path / "manifest.json")

    write_tone(tmp_path / "hiragana" / "female" / "あ.wav")
    write_silence(tmp_path / "hiragana" / "female" / "い.wav")

    lib.write_manifest()
    manifest = lib.read_manifest()

    assert [c["path"] for c in manifest["clips"]] == ["hiragana/female/あ.wav"]
    assert [r["path"] for r in manifest["rejected"]] == ["hiragana/female/い.wav"]


def test_manifest_detects_content_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "LIBRARY_ROOT", tmp_path)
    monkeypatch.setattr(lib, "MANIFEST_PATH", tmp_path / "manifest.json")

    clip = write_tone(tmp_path / "hiragana" / "female" / "あ.wav")
    lib.write_manifest()
    assert lib.verify_against_manifest() == []

    write_tone(clip, seconds=1.1)  # same path, different content
    problems = lib.verify_against_manifest()
    assert len(problems) == 1
    assert "checksum changed" in problems[0]


def test_manifest_detects_a_deleted_clip(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "LIBRARY_ROOT", tmp_path)
    monkeypatch.setattr(lib, "MANIFEST_PATH", tmp_path / "manifest.json")

    clip = write_tone(tmp_path / "hiragana" / "female" / "あ.wav")
    lib.write_manifest()
    clip.unlink()

    problems = lib.verify_against_manifest()
    assert len(problems) == 1
    assert "missing" in problems[0]


def test_read_manifest_is_safe_when_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "MANIFEST_PATH", tmp_path / "does-not-exist.json")
    assert lib.read_manifest() == {"clips": [], "rejected": []}


# -- is_validated ----------------------------------------------------------


def test_is_validated_requires_the_clip_to_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "LIBRARY_ROOT", tmp_path)

    write_tone(tmp_path / "hiragana" / "female" / "あ.wav")
    write_silence(tmp_path / "hiragana" / "female" / "い.wav")

    assert lib.is_validated("hiragana", "あ") is True
    assert lib.is_validated("hiragana", "い") is False  # present but silent
    assert lib.is_validated("hiragana", "う") is False  # absent


def test_is_validated_is_safe_for_unsafe_glyphs(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "LIBRARY_ROOT", tmp_path)
    assert lib.is_validated("hiragana", "../../etc/passwd") is False


def test_scan_of_an_empty_library_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "LIBRARY_ROOT", tmp_path)
    assert lib.scan_library() == []


CUE_IDS = ("ding", "chime", "bell", "marimba", "arpeggio", "sparkle", "blip")

#: The study view advances 380 ms after a correct answer at its fastest pace, so
#: a longer cue would still be ringing over the next card.
MAX_CUE_SECONDS = 0.38


@pytest.mark.parametrize("cue_id", CUE_IDS)
def test_every_cue_is_audible_prompt_and_short(cue_id):
    """Guards this project's own rule: never infer audio validity from size.

    A silent stub of exactly the right length once passed for working synthesis
    here, so each cue is decoded and measured. Three properties matter:

    * **audible** — the first cue shipped at -8 dBFS and, once multiplied by an
      app gain and system volume, reached the speakers around -19 dBFS. Loud in
      the file, attenuated in code.
    * **prompt** — leading silence is latency between the click and the sound.
    * **short** — see ``MAX_CUE_SECONDS``.
    """
    import shutil
    import struct
    import subprocess
    from pathlib import Path

    cue = (
        Path(__file__).resolve().parent.parent
        / f"src/japanese_practice/static/audio/sounds/cue-{cue_id}.wav"
    )
    assert cue.exists(), f"cue-{cue_id}.wav is missing"

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg unavailable; cannot decode to verify amplitude")

    raw = subprocess.run(
        ["ffmpeg", "-v", "quiet", "-i", str(cue), "-f", "s16le", "-ac", "1", "-ar", "44100", "-"],
        capture_output=True,
        check=True,
    ).stdout
    count = len(raw) // 2
    assert count > 0, "cue decoded to nothing"
    samples = struct.unpack(f"<{count}h", raw[: count * 2])
    peak = max(abs(s) for s in samples) / 32768

    assert peak > 0.80, f"cue-{cue_id} is too quiet to hear (peak {peak:.3f})"
    assert peak <= 0.99, f"cue-{cue_id} is clipping (peak {peak:.3f})"

    duration = count / 44100
    assert duration <= MAX_CUE_SECONDS, f"cue-{cue_id} runs {duration:.3f}s"

    onset = next(
        (i / 44100 for i, s in enumerate(samples) if abs(s) > peak * 32768 * 0.02), duration
    )
    assert onset < 0.02, f"cue-{cue_id} starts {onset * 1000:.0f}ms in — it will feel late"


def test_the_cue_set_offers_real_variety():
    """Seven near-identical sounds would not be a choice worth presenting."""
    import struct
    import wave
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "src/japanese_practice/static/audio/sounds"
    signatures = set()
    for cue_id in CUE_IDS:
        with wave.open(str(root / f"cue-{cue_id}.wav")) as handle:
            frames = handle.getnframes()
            data = struct.unpack(f"<{frames}h", handle.readframes(frames))
        # Duration and energy distribution together separate a marimba from a
        # sparkle without needing a spectral analysis in the test suite.
        early = sum(abs(v) for v in data[: frames // 4]) or 1
        late = sum(abs(v) for v in data[frames // 2 :])
        signatures.add((round(frames / 44100, 2), round(late / early, 1)))
    assert len(signatures) >= 5, f"cues are too alike: {signatures}"
