"""VOICEVOX text-to-speech backend — the primary source of pronunciation audio.

VOICEVOX is a Japanese-native engine that runs locally over HTTP. It is
preferred over :mod:`tts_elevenlabs` for reasons that were measured rather than
assumed (see ``docs/VOICEVOX-EVALUATION.md``):

* **It models Japanese phonology and exposes that model.** ``/audio_query``
  returns per-mora consonant, vowel, pitch and duration plus an accent position,
  and every field is writable. A multilingual model gives you text in, audio
  out, with nothing to inspect or correct.
* **Verified on the hard cases.** 箸 ``accent=1`` against 橋 ``accent=2`` — a
  minimal pair where pitch accent is the only difference in speech — and the
  geminate っ returned with ``pitch = 0.00``, a timed silent mora, which is
  exactly the beat English speakers drop.
* **Free, unlimited and offline.** No key, no quota, no network.

Configuration, all optional::

    JP_VOICEVOX_URL     default http://127.0.0.1:50021
    JP_VOICEVOX_FEMALE  default 30  (No.7 アナウンス)
    JP_VOICEVOX_MALE    default 13  (青山龍星 ノーマル)
    JP_VOICEVOX_SPEED   default 0.85

**Availability is optional and failure is silent.** A user without an engine
running must see no error — the caller has bundled clips, ElevenLabs and local
espeak beneath this, and finally a silent stub. Nothing here ever raises.

Attribution: VOICEVOX requires visible credit for generated audio, naming the
speaker — e.g. ``VOICEVOX:No.7（アナウンス）``. See :data:`ATTRIBUTION`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://127.0.0.1:50021"

#: Probe timeout. Short on purpose — an absent engine must not stall a card.
PROBE_TIMEOUT = 1.5

#: Synthesis is CPU-bound locally; ~0.45 s per mora-length clip on 8 cores.
REQUEST_TIMEOUT = 30.0

MIME_WAV = "audio/wav"

Gender = Literal["female", "male"]


@dataclass(frozen=True)
class Speaker:
    """A configured narrator."""

    style_id: int
    name: str
    gender: Gender


#: Chosen from 43 speakers by audition (2026-08-07), on measured per-character
#: consistency — the spread of clip durations across single glyphs. Tight spread
#: means the learner keys on the glyph rather than on how long the audio ran.
#:
#:   青山龍星        0.06 s spread   <- 2.5x tighter than anything else
#:   No.7 アナウンス  0.15 s
#:   No.7 ノーマル    0.16 s
#:   九州そら        0.19 s
#:   No.7 読み聞かせ  0.21 s   (storytelling varies pace for expression)
#:
#: Female confirmed acceptable by listening; male retained on the measurement.
DEFAULT_SPEAKERS: dict[Gender, Speaker] = {
    # No.7 アナウンス — an announcer style, purpose-built for clear delivery.
    # Chosen over 九州そら on measured per-character consistency (0.15 s spread
    # against 0.19 s) and a brisker read.
    "female": Speaker(30, "No.7（アナウンス）", "female"),
    # 青山龍星 — 0.06 s spread across single characters, 2.5x tighter than any
    # other candidate. Every card takes the same time, so the learner keys on
    # the glyph rather than on how long the audio ran.
    "male": Speaker(13, "青山龍星", "male"),
}

#: Slightly slower than conversational — a single mora needs room to be heard.
DEFAULT_SPEED = 0.85

#: Required credit for VOICEVOX-generated audio. Must appear somewhere a user
#: would naturally find it.
ATTRIBUTION = "VOICEVOX"

_available: bool | None = None
_probe_lock = asyncio.Lock()


def engine_url() -> str:
    """Base URL of the local engine."""
    return os.environ.get("JP_VOICEVOX_URL", DEFAULT_URL).rstrip("/")


def speaker_for(gender: Gender) -> Speaker:
    """The configured speaker for ``gender``, honouring environment overrides."""
    env_key = "JP_VOICEVOX_FEMALE" if gender == "female" else "JP_VOICEVOX_MALE"
    base = DEFAULT_SPEAKERS.get(gender, DEFAULT_SPEAKERS["female"])
    raw = os.environ.get(env_key, "").strip()
    if raw.isdigit():
        return Speaker(int(raw), f"{gender} (configured)", base.gender)
    return base


def speed() -> float:
    try:
        return float(os.environ.get("JP_VOICEVOX_SPEED", DEFAULT_SPEED))
    except ValueError:
        return DEFAULT_SPEED


def credit(gender: Gender = "female") -> str:
    """The attribution string for audio produced by this backend."""
    return f"{ATTRIBUTION}:{speaker_for(gender).name}"


def _get(path: str, timeout: float) -> bytes:
    with urllib.request.urlopen(f"{engine_url()}{path}", timeout=timeout) as resp:
        return resp.read()


def _post(path: str, body: bytes | None, timeout: float) -> bytes:
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(f"{engine_url()}{path}", data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


async def is_available(refresh: bool = False) -> bool:
    """Whether a local engine is reachable. Probed once, then memoised.

    Never raises and never blocks for long: a missing engine is the normal case
    for a user who has not installed one.
    """
    global _available
    if _available is not None and not refresh:
        return _available
    async with _probe_lock:
        if _available is not None and not refresh:
            return _available
        try:
            raw = await asyncio.to_thread(_get, "/version", PROBE_TIMEOUT)
            _available = bool(raw)
            logger.info("VOICEVOX engine %s at %s", raw.decode().strip(), engine_url())
        except Exception:
            _available = False
            logger.debug("no VOICEVOX engine at %s", engine_url())
        return _available


def reset_availability() -> None:
    """Forget the probe result so the next call re-checks."""
    global _available
    _available = None


async def speakers() -> list[dict[str, Any]]:
    """Every speaker and style the engine offers. Empty when unavailable."""
    if not await is_available():
        return []
    try:
        raw = await asyncio.to_thread(_get, "/speakers", REQUEST_TIMEOUT)
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        logger.warning("could not list VOICEVOX speakers", exc_info=True)
        return []
    return [
        {
            "name": s.get("name"),
            "styles": [{"name": st.get("name"), "id": st.get("id")} for st in s.get("styles", [])],
        }
        for s in payload
    ]


async def audio_query(text: str, gender: Gender = "female") -> dict[str, Any] | None:
    """The engine's phonological analysis of ``text``, before any audio exists.

    Contains ``accent_phrases`` with per-mora ``consonant``/``vowel``/``pitch``/
    ``vowel_length`` and an ``accent`` position. This is what makes a pitch-accent
    teaching aid possible, and what no cloud provider exposes.
    """
    if not await is_available():
        return None
    speaker = speaker_for(gender)
    path = f"/audio_query?text={urllib.parse.quote(text)}&speaker={speaker.style_id}"
    try:
        raw = await asyncio.to_thread(_post, path, None, REQUEST_TIMEOUT)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        logger.warning("VOICEVOX audio_query failed for %r", text, exc_info=True)
        return None


async def accent_pattern(text: str, gender: Gender = "female") -> list[dict[str, Any]]:
    """Per-mora pitch for ``text``, flattened for display.

    ``[{mora, pitch, is_accent, vowel_length}]``. Empty when unavailable.
    """
    query = await audio_query(text, gender)
    if not query:
        return []
    out: list[dict[str, Any]] = []
    for phrase in query.get("accent_phrases", []):
        accent = phrase.get("accent")
        for index, mora in enumerate(phrase.get("moras", []), start=1):
            out.append(
                {
                    "mora": mora.get("text"),
                    "pitch": mora.get("pitch", 0.0),
                    "vowel_length": mora.get("vowel_length", 0.0),
                    "is_accent": index == accent,
                }
            )
    return out


async def synthesize(
    text: str,
    *,
    gender: Gender = "female",
    speed_scale: float | None = None,
) -> tuple[bytes, str] | None:
    """Render ``text`` locally. ``(wav_bytes, mimetype)``, or ``None`` on failure.

    Never raises — the caller falls through to the next provider.
    """
    spoken = text.strip()
    if not spoken or not await is_available():
        return None

    query = await audio_query(spoken, gender)
    if not query:
        return None
    query["speedScale"] = speed_scale if speed_scale is not None else speed()

    speaker = speaker_for(gender)
    try:
        audio = await asyncio.to_thread(
            _post,
            f"/synthesis?speaker={speaker.style_id}",
            json.dumps(query).encode("utf-8"),
            REQUEST_TIMEOUT,
        )
    except urllib.error.HTTPError as exc:
        logger.warning("VOICEVOX HTTP %s for speaker %s", exc.code, speaker.style_id)
        return None
    except Exception:
        logger.warning("VOICEVOX synthesis failed", exc_info=True)
        return None

    return (audio, MIME_WAV) if audio else None
