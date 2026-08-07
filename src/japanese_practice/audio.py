"""Pronunciation audio: bundled clips first, TTS second, silence as a floor.

BUILD-SPEC section 9. :func:`get_audio` resolves, in order:

1. a bundled clip at ``static/audio/<script>/<glyph>.mp3``
2. a cached TTS render at ``<config.audio_cache_dir>/<sha1>.wav``
3. a freshly generated TTS render, which is then cached

The synthesis backend is pluggable behind :func:`_synthesize`, which tries
``espeak-ng`` (with the Japanese voice when the installation provides one),
then ``pico2wave``, then falls back to a valid short silent WAV. Nothing in
this module ever raises to the caller: a failed lookup, a missing backend, a
hung subprocess or an unreadable cache all degrade to the silent stub so that
playback in the browser never errors.

All filesystem and subprocess work is dispatched off the event loop —
``asyncio.to_thread`` for file IO, ``asyncio.create_subprocess_exec`` for the
synthesisers.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import os
import re
import shutil
import struct
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import tts_elevenlabs
from .config import Config
from .db import SCRIPTS
from .models import Character

__all__ = [
    "MIME_MPEG",
    "MIME_WAV",
    "Backend",
    "BUNDLED_AUDIO_DIR",
    "configure",
    "detect_backends",
    "get_audio",
    "reset_backend_cache",
    "silent_wav",
    "speech_text",
]

logger = logging.getLogger(__name__)

MIME_MPEG = "audio/mpeg"
MIME_WAV = "audio/wav"

#: Directory holding hand-recorded clips shipped with the package.
BUNDLED_AUDIO_DIR = Path(__file__).with_name("static") / "audio"

#: Bundled clip extensions, in preference order, mapped to their mimetype.
_BUNDLED_FORMATS: tuple[tuple[str, str], ...] = ((".mp3", MIME_MPEG), (".wav", MIME_WAV))

#: Backend identifiers. These take part in the cache key, so they are stable.
ESPEAK_NG = "espeak-ng"
ESPEAK = "espeak"
PICO2WAVE = "pico2wave"
SILENCE = "silence"

_ESPEAK_CANDIDATES: tuple[str, ...] = (ESPEAK_NG, ESPEAK)
_ESPEAK_JAPANESE_VOICE = "ja"
_ESPEAK_WORDS_PER_MINUTE = 130
_PICO_LANGUAGE = "en-US"

#: Hard ceiling on any one subprocess, in seconds. A hung TTS binary must not
#: hold a request open.
_PROCESS_TIMEOUT = 10.0

#: Silent stub geometry: 16-bit mono PCM.
_SILENT_SECONDS = 0.4
_SILENT_SAMPLE_RATE = 22050

_KANA_SCRIPTS = frozenset({"hiragana", "katakana"})
_VALID_SCRIPTS = frozenset(SCRIPTS)

# Readings are stored as "よっ(つ)/よん" or "ニチ/ジツ": alternatives separated by
# a slash, okurigana in parentheses. The first alternative is the primary one and
# the parentheses are dropped, so "ひと(つ)" is spoken as "ひとつ".
_READING_SEPARATORS = re.compile(r"[/／・、,;]")
_READING_BRACKETS = re.compile(r"[()（）\[\]【】]")
_READING_TRIM = "-‐–—.·・ \t"

#: Characters that must never reach a bundled-clip filename.
_UNSAFE_GLYPH_CHARS = frozenset({"/", "\\", "\0", os.sep, os.altsep or "/"})

_config: Config | None = None
_backends: tuple[Backend, ...] | None = None
_backend_lock = asyncio.Lock()


@dataclass(frozen=True, slots=True)
class Backend:
    """A resolved synthesis backend.

    ``name`` is the stable identifier that takes part in the cache key,
    ``executable`` the absolute path found on ``PATH`` (``None`` for the silent
    stub) and ``voice`` the voice/language argument to hand the binary, when the
    installation supports one.
    """

    name: str
    executable: str | None = None
    voice: str | None = None

    @property
    def available(self) -> bool:
        """True when this backend can actually produce audio from a binary."""
        return self.name != SILENCE and self.executable is not None


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------


def configure(config: Config | None) -> None:
    """Install the :class:`Config` used to locate the audio cache.

    Passing ``None`` clears the override; the next call resolves the
    configuration from the environment again.
    """
    global _config
    _config = config


def _active_config() -> Config:
    """Return the configured :class:`Config`, resolving from env on first use."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


# --------------------------------------------------------------------------
# What to say
# --------------------------------------------------------------------------


def speech_text(character: Character) -> str:
    """Return the text a synthesiser should pronounce for ``character``.

    Kana are spoken as the glyph itself. Kanji are spoken as their primary
    kun'yomi when one exists, otherwise their primary on'yomi; a kanji carrying
    neither reading falls back to the glyph.
    """
    if character.script in _KANA_SCRIPTS:
        return character.glyph
    for raw in (character.kunyomi, character.onyomi):
        reading = _primary_reading(raw)
        if reading:
            return reading
    return character.glyph


def _primary_reading(raw: str | None) -> str:
    """Extract the first alternative from a reading field, without okurigana marks."""
    if not raw:
        return ""
    first = _READING_SEPARATORS.split(raw, maxsplit=1)[0]
    return _READING_BRACKETS.sub("", first).strip(_READING_TRIM)


# --------------------------------------------------------------------------
# Backend detection (performed once, then cached)
# --------------------------------------------------------------------------


async def detect_backends() -> tuple[Backend, ...]:
    """Return the usable backends in preference order, ending with the stub.

    The probe — a ``PATH`` lookup plus a voice-list query for espeak — runs at
    most once per process; every later call returns the memoised tuple.
    """
    global _backends
    if _backends is not None:
        return _backends
    async with _backend_lock:
        if _backends is None:
            _backends = await _probe_backends()
        return _backends


def reset_backend_cache() -> None:
    """Forget the detected backends so the next call probes the system again."""
    global _backends
    _backends = None


async def _probe_backends() -> tuple[Backend, ...]:
    """Probe the system for synthesis binaries. Never raises."""
    found: list[Backend] = []
    try:
        for name in _ESPEAK_CANDIDATES:
            executable = await asyncio.to_thread(shutil.which, name)
            if executable:
                voice = await _espeak_japanese_voice(executable)
                found.append(Backend(name=name, executable=executable, voice=voice))
                break
        pico = await asyncio.to_thread(shutil.which, PICO2WAVE)
        if pico:
            found.append(Backend(name=PICO2WAVE, executable=pico, voice=_PICO_LANGUAGE))
    except Exception:  # pragma: no cover - defensive: probing must never fail
        logger.exception("TTS backend probe failed; falling back to silence")
    found.append(Backend(name=SILENCE))
    logger.debug("TTS backends detected: %s", [b.name for b in found])
    return tuple(found)


async def _espeak_japanese_voice(executable: str) -> str | None:
    """Return ``"ja"`` when this espeak build ships a Japanese voice, else ``None``."""
    code, stdout, _ = await _run([executable, f"--voices={_ESPEAK_JAPANESE_VOICE}"])
    if code != 0:
        return None
    if _lists_japanese_voice(stdout.decode("utf-8", "replace")):
        return _ESPEAK_JAPANESE_VOICE
    return None


def _lists_japanese_voice(listing: str) -> bool:
    """True when an ``espeak --voices`` listing contains a Japanese entry."""
    for line in listing.splitlines():
        fields = line.split()
        if not fields or fields[0].lower() in {"pty", "priority"}:
            continue
        for field in fields:
            token = field.lower()
            if token == _ESPEAK_JAPANESE_VOICE or token.startswith("ja-"):
                return True
            if token == "japanese":
                return True
    return False


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------


async def get_audio(
    character: Character,
    *,
    config: Config | None = None,
    gender: str = "female",
) -> tuple[bytes, str]:
    """Return ``(audio_bytes, mimetype)`` for ``character``.

    Resolution order is bundled clip, ElevenLabs (when an API key is
    configured), cached local TTS render, freshly generated local TTS render.
    The result is always playable: on any failure — no backend, a dead
    subprocess, an unwritable cache, an API outage — a short silent WAV is
    returned instead of an exception.
    """
    try:
        bundled = await _load_bundled(character)
        if bundled is not None:
            return bundled

        cfg = config if config is not None else _active_config()
        text = speech_text(character)

        # ElevenLabs, when configured. Cached by (text, voice) so a given
        # character in a given voice is only ever paid for once.
        if tts_elevenlabs.is_configured():
            voice = tts_elevenlabs.voice_for(gender)  # type: ignore[arg-type]
            eleven_key = f"eleven:{voice.voice_id}"
            cached_mp3 = await _read_bytes(
                cfg.audio_cache_dir / f"{_cache_key(text, eleven_key)}.mp3"
            )
            if cached_mp3:
                return cached_mp3, tts_elevenlabs.MIME_MPEG
            rendered = await tts_elevenlabs.synthesize(text, gender=gender)  # type: ignore[arg-type]
            if rendered is not None:
                data, mimetype = rendered
                await _store_cached_bytes(cfg, f"{_cache_key(text, eleven_key)}.mp3", data)
                return data, mimetype
            # fall through to the local chain

        backends = await detect_backends()

        cached = await _load_cached(cfg, text, backends)
        if cached is not None:
            return cached, MIME_WAV

        data, used = await _synthesize_with(text, backends)
        if used.available:
            await _store_cached(cfg, text, used.name, data)
        return data, MIME_WAV
    except Exception:  # pragma: no cover - the contract is "never raise"
        logger.exception("audio lookup failed for %r", getattr(character, "glyph", "?"))
        return silent_wav(), MIME_WAV


# --------------------------------------------------------------------------
# Bundled clips
# --------------------------------------------------------------------------


async def _load_bundled(character: Character) -> tuple[bytes, str] | None:
    """Load a hand-recorded clip for ``character``, or ``None`` if there is none."""
    if character.script not in _VALID_SCRIPTS:
        return None
    glyph = character.glyph
    if not glyph or ".." in glyph or _UNSAFE_GLYPH_CHARS & set(glyph):
        logger.warning("refusing bundled-clip lookup for unsafe glyph %r", glyph)
        return None
    directory = BUNDLED_AUDIO_DIR / character.script
    for suffix, mimetype in _BUNDLED_FORMATS:
        data = await _read_bytes(directory / f"{glyph}{suffix}")
        if data:
            return data, mimetype
    return None


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------


def _cache_key(text: str, backend: str) -> str:
    """SHA-1 of the ``(text, backend)`` pair — the cached render's filename stem."""
    digest = hashlib.sha1()
    digest.update(text.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(backend.encode("utf-8"))
    return digest.hexdigest()


def _cache_path(config: Config, text: str, backend: str) -> Path:
    """Absolute path of the cached render for ``(text, backend)``."""
    return config.audio_cache_dir / f"{_cache_key(text, backend)}.wav"


async def _load_cached(config: Config, text: str, backends: Sequence[Backend]) -> bytes | None:
    """Return a previously generated render, trying backends in preference order."""
    for backend in backends:
        if not backend.available:
            continue
        data = await _read_bytes(_cache_path(config, text, backend.name))
        if data and _looks_like_wav(data):
            return data
    return None


async def _store_cached(config: Config, text: str, backend: str, data: bytes) -> None:
    """Write ``data`` into the cache atomically. Failures are logged, not raised."""
    if not data or not _looks_like_wav(data):
        return
    path = _cache_path(config, text, backend)
    try:
        await asyncio.to_thread(_write_atomic, path, data)
    except OSError:
        logger.warning("could not cache audio at %s", path, exc_info=True)


def _write_atomic(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` via a temporary file in the same directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


# --------------------------------------------------------------------------
# Synthesis
# --------------------------------------------------------------------------


async def _synthesize(text: str) -> bytes:
    """Render ``text`` to WAV bytes, degrading to the silent stub on failure.

    This is the pluggable seam named by the build spec: swap this body to change
    engines. It never raises and always returns a playable WAV.
    """
    data, _ = await _synthesize_with(text, await detect_backends())
    return data


async def _synthesize_with(text: str, backends: Sequence[Backend]) -> tuple[bytes, Backend]:
    """Try each backend in turn; return the audio and the backend that produced it."""
    stub = Backend(name=SILENCE)
    spoken = text.strip()
    if not spoken:
        return silent_wav(), stub
    for backend in backends:
        if not backend.available:
            continue
        try:
            if backend.name in _ESPEAK_CANDIDATES:
                data = await _synthesize_espeak(backend, spoken)
            elif backend.name == PICO2WAVE:
                data = await _synthesize_pico(backend, spoken)
            else:  # pragma: no cover - unknown backend names never get queued
                data = None
        except Exception:
            logger.warning("%s synthesis failed", backend.name, exc_info=True)
            data = None
        if data:
            return data, backend
    return silent_wav(), stub


async def _synthesize_espeak(backend: Backend, text: str) -> bytes | None:
    """Synthesise with espeak(-ng), writing WAV to stdout. ``None`` on failure."""
    assert backend.executable is not None
    command = [
        backend.executable,
        "--stdout",
        "-s",
        str(_ESPEAK_WORDS_PER_MINUTE),
    ]
    if backend.voice:
        command += ["-v", backend.voice]
    async with _text_file(text) as source:
        command += ["-f", str(source)]
        code, stdout, stderr = await _run(command)
    if code == 0 and _looks_like_wav(stdout):
        return stdout
    logger.debug("%s exited %s (%s)", backend.name, code, stderr.decode("utf-8", "replace")[:200])
    return None


async def _synthesize_pico(backend: Backend, text: str) -> bytes | None:
    """Synthesise with pico2wave, which can only write to a file. ``None`` on failure."""
    assert backend.executable is not None
    async with _scratch_dir() as scratch:
        target = scratch / "speech.wav"
        command = [
            backend.executable,
            "-l",
            backend.voice or _PICO_LANGUAGE,
            "-w",
            str(target),
            text,
        ]
        code, _, stderr = await _run(command)
        data = await _read_bytes(target)
    if code == 0 and data and _looks_like_wav(data):
        return data
    logger.debug("%s exited %s (%s)", backend.name, code, stderr.decode("utf-8", "replace")[:200])
    return None


# --------------------------------------------------------------------------
# Silent stub
# --------------------------------------------------------------------------


def silent_wav() -> bytes:
    """Return a valid, short, silent 16-bit mono WAV.

    This is the floor of the resolution chain: it is always playable, so the
    frontend's ``<audio>`` element never raises a decode error.
    """
    return _silent_wav_bytes(_SILENT_SECONDS, _SILENT_SAMPLE_RATE)


@lru_cache(maxsize=4)
def _silent_wav_bytes(seconds: float, sample_rate: int) -> bytes:
    """Build (and memoise) the RIFF/PCM byte string for a silent clip."""
    frames = max(1, int(seconds * sample_rate))
    channels = 1
    bits_per_sample = 16
    block_align = channels * bits_per_sample // 8
    byte_rate = sample_rate * block_align
    payload = b"\x00" * (frames * block_align)
    fmt_chunk = b"fmt " + struct.pack(
        "<IHHIIHH",
        16,
        1,  # PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
    )
    data_chunk = b"data" + struct.pack("<I", len(payload)) + payload
    body = b"WAVE" + fmt_chunk + data_chunk
    return b"RIFF" + struct.pack("<I", len(body)) + body


def _looks_like_wav(data: bytes) -> bool:
    """Cheap sanity check that ``data`` is a RIFF/WAVE stream with a payload."""
    return len(data) > 44 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"


# --------------------------------------------------------------------------
# Off-loop primitives
# --------------------------------------------------------------------------


async def _run(command: Sequence[str]) -> tuple[int, bytes, bytes]:
    """Run ``command`` off the event loop, returning ``(code, stdout, stderr)``.

    A missing binary, a crash or a timeout all surface as a non-zero code rather
    than an exception; a timed-out child is killed and reaped.
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except (OSError, ValueError) as exc:
        logger.debug("could not start %s: %s", command[0], exc)
        return -1, b"", str(exc).encode("utf-8", "replace")

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=_PROCESS_TIMEOUT)
    except asyncio.TimeoutError:
        with contextlib.suppress(ProcessLookupError, OSError):
            process.kill()
        with contextlib.suppress(Exception):
            await process.wait()
        logger.warning("%s timed out after %.0fs", command[0], _PROCESS_TIMEOUT)
        return -1, b"", b"timed out"

    code = process.returncode if process.returncode is not None else -1
    return code, stdout, stderr


async def _read_bytes(path: Path) -> bytes | None:
    """Read a file off the event loop; ``None`` when it is missing or unreadable."""
    try:
        return await asyncio.to_thread(path.read_bytes)
    except (OSError, ValueError):
        return None


@contextlib.asynccontextmanager
async def _scratch_dir():
    """Yield a private temporary directory, removed off the loop on exit."""
    path = await asyncio.to_thread(tempfile.mkdtemp, prefix="japanese-practice-tts-")
    try:
        yield Path(path)
    finally:
        await asyncio.to_thread(shutil.rmtree, path, ignore_errors=True)


@contextlib.asynccontextmanager
async def _text_file(text: str):
    """Yield the path of a UTF-8 file holding ``text``, cleaned up on exit.

    Handing the synthesiser a file rather than an argv word keeps text that
    happens to start with ``-`` from being read as an option.
    """
    async with _scratch_dir() as scratch:
        source = scratch / "utterance.txt"
        await asyncio.to_thread(source.write_text, text, encoding="utf-8")
        yield source


async def _store_cached_bytes(config: Config, filename: str, data: bytes) -> None:
    """Write ``data`` into the audio cache under ``filename``, ignoring failures.

    Caching is an optimisation, never a requirement — an unwritable cache
    directory must not break playback.
    """
    try:
        config.audio_cache_dir.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread((config.audio_cache_dir / filename).write_bytes, data)
    except OSError:
        logger.warning("could not cache %s", filename, exc_info=True)
