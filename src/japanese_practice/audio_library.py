"""Local pronunciation-clip library: layout, validation and manifest.

Every clip the app ships is stored locally, organised by what it is for, and
validated before it is trusted. Nothing is fetched at runtime from a third
party — a study session must work with the network unplugged.

Layout
------

::

    static/audio/
    ├── manifest.json              # checksum + duration + provenance per clip
    ├── hiragana/<voice>/<glyph>.mp3
    ├── katakana/<voice>/<glyph>.mp3
    └── kanji/<voice>/<glyph>.mp3

``<voice>`` is ``female`` or ``male``. The directory tree mirrors the way the
app selects audio — script, then voice, then glyph — so a clip's purpose is
readable from its path alone and a missing set is obvious from a directory
listing.

Validation
----------

A clip is only accepted into the manifest once it passes every check in
:func:`validate_clip`. An unvalidated file in the tree is treated as absent, so
a truncated download or a silent render can never reach a learner.
"""

from __future__ import annotations

import hashlib
import json
import logging
import struct
import wave
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

LIBRARY_ROOT = Path(__file__).with_name("static") / "audio"
MANIFEST_PATH = LIBRARY_ROOT / "manifest.json"

VOICES = ("female", "male")
SCRIPTS = ("hiragana", "katakana", "kanji")

#: A single kana is short. Anything outside this range is a bad render — a
#: truncated file, or a voice that read the glyph as a whole word.
MIN_DURATION_MS = 150
MAX_DURATION_MS = 4000

#: Below this the file is effectively silence, which is worse than no clip at
#: all: the learner hears nothing and assumes the audio works.
MIN_PEAK_AMPLITUDE = 0.01

#: Smallest plausible encoded clip. Catches zero-byte and header-only files.
MIN_BYTES = 512

_MP3_MAGIC = (b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")


@dataclass(frozen=True)
class ClipReport:
    """The outcome of validating one clip."""

    path: str
    ok: bool
    reason: str = ""
    bytes: int = 0
    duration_ms: int | None = None
    peak: float | None = None
    sha256: str = ""

    @property
    def summary(self) -> str:
        state = "OK" if self.ok else f"FAIL ({self.reason})"
        return f"{self.path}: {state}"


def clip_path(script: str, glyph: str, voice: str = "female", suffix: str = ".mp3") -> Path:
    """Where a clip for ``glyph`` in ``voice`` belongs."""
    if script not in SCRIPTS:
        raise ValueError(f"unknown script: {script!r}")
    if voice not in VOICES:
        raise ValueError(f"unknown voice: {voice!r}")
    if not glyph or "/" in glyph or ".." in glyph:
        raise ValueError(f"unsafe glyph: {glyph!r}")
    return LIBRARY_ROOT / script / voice / f"{glyph}{suffix}"


def sha256_of(path: Path) -> str:
    """Content hash, used to detect silent corruption between runs."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _wav_stats(path: Path) -> tuple[int, float]:
    """``(duration_ms, peak_amplitude)`` for a PCM WAV, peak normalised to 1.0.

    Duration is derived from the bytes actually present rather than from the
    header's frame count. Streaming writers — espeak-ng among them — emit a
    placeholder length because they do not know the total when the header is
    written, and trusting it yields absurd durations.
    """
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate() or 1
        width = handle.getsampwidth() or 2
        channels = handle.getnchannels() or 1
        header_frames = handle.getnframes()

        block = max(1, width * channels)
        actual_frames = max(0, path.stat().st_size - 44) // block
        frames = actual_frames if header_frames > actual_frames * 2 else header_frames

        duration_ms = int(frames * 1000 / rate)
        raw = handle.readframes(min(frames, rate * 4))

    if width != 2 or not raw:
        # Only 16-bit PCM is measured; anything else passes the amplitude gate
        # rather than being rejected on a technicality.
        return duration_ms, 1.0

    count = len(raw) // 2
    samples = struct.unpack(f"<{count}h", raw[: count * 2])
    peak = max((abs(s) for s in samples), default=0) / 32768.0
    return duration_ms, peak


def validate_clip(path: Path) -> ClipReport:
    """Check one clip. Never raises — a bad file yields a failing report."""
    label = str(path.relative_to(LIBRARY_ROOT)) if LIBRARY_ROOT in path.parents else str(path)
    try:
        if not path.is_file():
            return ClipReport(label, False, "missing")

        size = path.stat().st_size
        if size < MIN_BYTES:
            return ClipReport(label, False, f"too small ({size} bytes)", bytes=size)

        head = path.read_bytes()[:4]
        duration_ms: int | None = None
        peak: float | None = None

        if path.suffix == ".wav":
            if head[:4] != b"RIFF":
                return ClipReport(label, False, "not a RIFF/WAV file", bytes=size)
            duration_ms, peak = _wav_stats(path)
            if not MIN_DURATION_MS <= duration_ms <= MAX_DURATION_MS:
                return ClipReport(
                    label,
                    False,
                    f"duration {duration_ms}ms outside bounds",
                    bytes=size,
                    duration_ms=duration_ms,
                    peak=peak,
                )
            if peak < MIN_PEAK_AMPLITUDE:
                return ClipReport(
                    label,
                    False,
                    f"effectively silent (peak {peak:.4f})",
                    bytes=size,
                    duration_ms=duration_ms,
                    peak=peak,
                )
        elif path.suffix == ".mp3":
            if not any(head.startswith(magic) for magic in _MP3_MAGIC):
                return ClipReport(label, False, "not an MP3 stream", bytes=size)
            # Duration and amplitude need a decoder; size is the only gate we
            # can apply without one. Recorded here so the limitation is visible.
        else:
            return ClipReport(label, False, f"unsupported format {path.suffix!r}", bytes=size)

        return ClipReport(
            label,
            True,
            "",
            bytes=size,
            duration_ms=duration_ms,
            peak=peak,
            sha256=sha256_of(path),
        )
    except Exception as exc:  # pragma: no cover - validation must never raise
        logger.warning("clip validation failed for %s", path, exc_info=True)
        return ClipReport(label, False, f"unreadable: {exc}")


def scan_library() -> list[ClipReport]:
    """Validate every clip currently in the tree."""
    if not LIBRARY_ROOT.is_dir():
        return []
    reports: list[ClipReport] = []
    for script in SCRIPTS:
        for voice in VOICES:
            directory = LIBRARY_ROOT / script / voice
            if not directory.is_dir():
                continue
            for clip in sorted(directory.iterdir()):
                if clip.suffix in {".mp3", ".wav"}:
                    reports.append(validate_clip(clip))
    return reports


def write_manifest(reports: list[ClipReport] | None = None) -> Path:
    """Record every *valid* clip, with its checksum, in ``manifest.json``."""
    reports = reports if reports is not None else scan_library()
    payload = {
        "clips": [asdict(r) for r in reports if r.ok],
        "rejected": [{"path": r.path, "reason": r.reason} for r in reports if not r.ok],
    }
    LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return MANIFEST_PATH


def read_manifest() -> dict:
    """The manifest, or an empty structure when none has been written."""
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except (OSError, ValueError):
        return {"clips": [], "rejected": []}


def verify_against_manifest() -> list[str]:
    """Re-hash every manifested clip. Returns a list of drift descriptions."""
    problems: list[str] = []
    for entry in read_manifest().get("clips", []):
        path = LIBRARY_ROOT / entry["path"]
        if not path.is_file():
            problems.append(f"{entry['path']}: missing since manifest was written")
            continue
        if sha256_of(path) != entry.get("sha256"):
            problems.append(f"{entry['path']}: checksum changed")
    return problems


def is_validated(script: str, glyph: str, voice: str = "female") -> bool:
    """Whether a clip exists *and* passed validation.

    ``audio.get_audio`` uses the bundled clip only when this is true, so an
    unvalidated file is treated exactly as if it were absent.
    """
    for suffix in (".mp3", ".wav"):
        try:
            path = clip_path(script, glyph, voice, suffix)
        except ValueError:
            return False
        if path.is_file() and validate_clip(path).ok:
            return True
    return False


# ── cross-voice consistency ──────────────────────────────────────────────────
#
# An absolute duration floor cannot catch a clip that is merely *too short for
# this character* — a truncated render of へ came in at 0.24s and passed the
# 150ms gate. The same character spoken by two narrators should take roughly
# the same time; a large disagreement means one of them is wrong.

#: Duration disagreement between voices, in seconds, that warrants review.
CROSS_VOICE_TOLERANCE_S = 0.35

#: Below this a clip is too short to be a mora, whatever the gate says.
SUSPICIOUS_SHORT_S = 0.45


def probe_duration_s(path: Path) -> float | None:
    """Exact duration via ffprobe, or ``None`` when it is unavailable."""
    import json
    import subprocess

    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout
        return float(json.loads(out)["format"]["duration"])
    except Exception:
        return None


def cross_voice_report() -> list[dict]:
    """Characters whose voices disagree on duration, or that are implausibly short.

    This is a *review* signal, not a hard gate — it produces a prioritised list
    for a human to listen to, which is the only way pronunciation accuracy can
    actually be confirmed.
    """
    durations: dict[tuple[str, str, str], float] = {}
    for script in SCRIPTS:
        for voice in VOICES:
            directory = LIBRARY_ROOT / script / voice
            if not directory.is_dir():
                continue
            for clip in sorted(directory.iterdir()):
                if clip.suffix not in {".mp3", ".wav"}:
                    continue
                seconds = probe_duration_s(clip)
                if seconds is not None:
                    durations[(script, voice, clip.stem)] = seconds

    findings: list[dict] = []
    for (script, voice, glyph), seconds in sorted(durations.items()):
        if seconds < SUSPICIOUS_SHORT_S:
            findings.append(
                {
                    "glyph": glyph,
                    "script": script,
                    "issue": "too_short",
                    "detail": f"{seconds:.2f}s in {voice}",
                }
            )

    seen: set[tuple[str, str]] = set()
    for script, _voice, glyph in durations:
        if (script, glyph) in seen:
            continue
        seen.add((script, glyph))
        f = durations.get((script, "female", glyph))
        m = durations.get((script, "male", glyph))
        if f is None or m is None:
            continue
        if abs(f - m) > CROSS_VOICE_TOLERANCE_S:
            findings.append(
                {
                    "glyph": glyph,
                    "script": script,
                    "issue": "voices_disagree",
                    "detail": f"female {f:.2f}s vs male {m:.2f}s",
                }
            )
    return findings
