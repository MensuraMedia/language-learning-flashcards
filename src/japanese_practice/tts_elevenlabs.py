"""ElevenLabs text-to-speech backend.

Optional. When ``ELEVENLABS_API_KEY`` is present in the environment this becomes
the preferred voice for card pronunciation, ahead of the local espeak/pico
backends. When the key is absent — or the API errors, rate-limits or times out —
the caller falls through to the local chain exactly as before.

**Credentials are read from the environment only.** Never hard-code a key, never
commit one, and never put an account password anywhere near this module: the
ElevenLabs REST API authenticates with a scoped, revocable API key, which is the
only credential this code accepts.

    export ELEVENLABS_API_KEY="sk_..."
    export JP_VOICE_FEMALE="<voice_id>"   # optional override
    export JP_VOICE_MALE="<voice_id>"     # optional override

Voice selection is deliberately configurable rather than hard-coded, because
voice IDs are account-specific: the ids below are the well-known shared-library
voices and should be replaced with whichever voices the account actually curates
for Japanese language learning.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

API_ROOT = "https://api.elevenlabs.io/v1"

# eleven_multilingual_v2 is the model that actually handles Japanese well.
# The monolingual/English models mangle kana readings.
DEFAULT_MODEL = "eleven_multilingual_v2"

# MP3 keeps bundled-clip parity with static/audio/<script>/<glyph>.mp3.
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"

MIME_MPEG = "audio/mpeg"

REQUEST_TIMEOUT = 20.0

Gender = Literal["female", "male"]


@dataclass(frozen=True)
class VoiceProfile:
    """A configured narrator voice."""

    voice_id: str
    label: str
    gender: Gender


# Placeholder defaults. These are shared-library voice ids, NOT verified against
# the project's ElevenLabs account and NOT verified as natural Japanese
# narrators. Confirm and replace them — see `list_voices()` below, and the
# selection criteria in docs/AUDIO.md.
DEFAULT_VOICES: dict[Gender, VoiceProfile] = {
    "female": VoiceProfile("EXAVITQu4vr4xnSDxMaL", "Sarah (placeholder)", "female"),
    "male": VoiceProfile("TX3LPaxmHKxFdv7VOQHJ", "Liam (placeholder)", "male"),
}

# Language-learning delivery: minimal expressiveness, maximum consistency. A
# character read twice must sound the same both times, or the learner starts
# matching prosody instead of the glyph.
VOICE_SETTINGS = {
    "stability": 0.75,  # high = consistent, low = expressive
    "similarity_boost": 0.75,
    "style": 0.0,  # no dramatic interpretation
    "use_speaker_boost": True,
    "speed": 0.85,  # slightly slower than conversational
}


def api_key() -> str | None:
    """The API key from the environment, or ``None`` when unconfigured."""
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    return key or None


def is_configured() -> bool:
    """Whether this backend can be used at all."""
    return api_key() is not None


def voice_for(gender: Gender) -> VoiceProfile:
    """The configured voice for ``gender``, honouring environment overrides."""
    env_key = "JP_VOICE_FEMALE" if gender == "female" else "JP_VOICE_MALE"
    override = os.environ.get(env_key, "").strip()
    base = DEFAULT_VOICES[gender]
    if override:
        return VoiceProfile(override, f"{gender} (configured)", gender)
    return base


def _request(url: str, *, method: str = "GET", body: bytes | None = None) -> bytes:
    """Blocking HTTP call. Always invoked via ``asyncio.to_thread``."""
    key = api_key()
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    headers = {"xi-api-key": key, "accept": "*/*"}
    if body is not None:
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return resp.read()


async def list_voices() -> list[dict]:
    """Every voice available to the account.

    Use this to pick real voice ids rather than trusting the placeholders above:

        python -c "import asyncio,json;from japanese_practice import tts_elevenlabs as t;\\
                   print(json.dumps(asyncio.run(t.list_voices()), ensure_ascii=False, indent=2))"
    """
    if not is_configured():
        return []
    try:
        raw = await asyncio.to_thread(_request, f"{API_ROOT}/voices")
        payload = json.loads(raw.decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, RuntimeError):
        logger.warning("could not list ElevenLabs voices", exc_info=True)
        return []
    return [
        {
            "voice_id": v.get("voice_id"),
            "name": v.get("name"),
            "labels": v.get("labels", {}),
            "preview_url": v.get("preview_url"),
        }
        for v in payload.get("voices", [])
    ]


async def synthesize(
    text: str,
    *,
    gender: Gender = "female",
    model: str | None = None,
) -> tuple[bytes, str] | None:
    """Render ``text`` via ElevenLabs.

    Returns ``(audio_bytes, mimetype)``, or ``None`` on any failure so the
    caller can fall through to a local backend. This function never raises.
    """
    spoken = text.strip()
    if not spoken or not is_configured():
        return None

    voice = voice_for(gender)
    url = f"{API_ROOT}/text-to-speech/{voice.voice_id}" f"?output_format={DEFAULT_OUTPUT_FORMAT}"
    body = json.dumps(
        {
            "text": spoken,
            "model_id": model or DEFAULT_MODEL,
            "voice_settings": VOICE_SETTINGS,
        }
    ).encode("utf-8")

    try:
        audio = await asyncio.to_thread(_request, url, method="POST", body=body)
    except urllib.error.HTTPError as exc:
        # 401 = bad key, 429 = rate limited, 422 = bad voice id. All are
        # recoverable by falling through; none should break a study session.
        logger.warning("ElevenLabs HTTP %s for voice %s", exc.code, voice.voice_id)
        return None
    except (urllib.error.URLError, OSError, RuntimeError):
        logger.warning("ElevenLabs request failed", exc_info=True)
        return None

    if not audio:
        return None
    return audio, MIME_MPEG
