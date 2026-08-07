# Audio & Voice — Japanese Practice

How pronunciation audio is produced, how the ElevenLabs integration is
configured, and what makes a voice suitable for language learning.

---

> **Provider direction (2026-08-07):** VOICEVOX has been evaluated and is
> recommended as the primary source — it is Japanese-native, free, local, and
> exposes editable per-mora pitch accent. See
> [VOICEVOX-EVALUATION.md](VOICEVOX-EVALUATION.md). The chain below describes
> what ships today.

## 1. Resolution chain

`audio.get_audio(character, gender=...)` resolves in this order and **never
raises**:

| # | Source | Format | Notes |
|---|---|---|---|
| 1 | **VOICEVOX**, cached | wav | Japanese-native, local, free. Cached per `(text, speaker_id)` |
| 2 | **VOICEVOX**, fresh | wav | ~0.45 s; result cached. Requires a reachable engine |
| 3 | **Validated** bundled clip — `static/audio/<script>/<voice>/<glyph>.mp3` | mp3/wav | ElevenLabs renders shipped with the app. Works with no engine and no key |
| 4 | **ElevenLabs**, cached | mp3 | Only when `ELEVENLABS_API_KEY` is set |
| 5 | **ElevenLabs**, fresh | mp3 | Result written to cache |
| 6 | Local TTS cache / fresh | wav | `espeak-ng` / `pico2wave` |
| 7 | Silent WAV stub | wav | Floor. Playback never errors |

VOICEVOX sits **above** the bundled clips deliberately: the shipped clips are
ElevenLabs renders, and a reachable engine produces better Japanese. Users
without an engine are unaffected — the probe is 1.5 s, memoised, and its failure
silent. Measured: a request with the engine pointed at a dead port returns the
bundled clip in **20 ms** with zero errors logged.

Any failure at any step falls through to the next. An expired key, a rate
limit, a network outage or a missing binary all degrade silently — **audio must
never be able to break a study session.**

---

## 2. Credentials

**The API key is read from the environment only.** It is never stored in the
repo, never committed, and never written to a config file.

```bash
export ELEVENLABS_API_KEY="sk_..."
```

Generate it in the ElevenLabs dashboard under **Settings → API Keys**. Scope it
to text-to-speech only if the account plan supports scoping, and rotate it if it
is ever pasted anywhere shared.

> An account **password** is never a valid credential for this integration. The
> REST API authenticates with the `xi-api-key` header. If you find yourself
> needing to log into the web UI to make the app work, something is wrong with
> the configuration, not with the key.

Check whether the backend is live:

```python
from japanese_practice import tts_elevenlabs
tts_elevenlabs.is_configured()   # False when no key is set
```

---

## 3. Voice selection

The brief calls for **one male and one female voice, both in a 30s age tone**,
with a natural delivery suited to language learning.

### Configure

```bash
export JP_VOICE_FEMALE="<voice_id>"
export JP_VOICE_MALE="<voice_id>"
```

### Find real voice IDs

Voice IDs are account-specific. The defaults in `tts_elevenlabs.py` are
**placeholders from the shared library and are not verified** — neither against
this account nor as natural Japanese narrators. Replace them:

```bash
ELEVENLABS_API_KEY=sk_... .venv/bin/python -c \
"import asyncio,json;from japanese_practice import tts_elevenlabs as t;\
print(json.dumps(asyncio.run(t.list_voices()), ensure_ascii=False, indent=2))"
```

### Selection criteria

Pick voices that are:

- **Native or near-native Japanese.** An English-accented voice teaches wrong
  pronunciation, which is worse than no audio at all. This is the single
  non-negotiable criterion.
- **Aged 30s in tone** — settled and neutral. Younger voices tend to read with
  more prosodic variation, which is exactly what a learner should not be
  pattern-matching against.
- **Neutral standard accent** (標準語 / Tokyo). Regional accents are a later
  feature, not a default.
- **Even and unhurried.** A single mora needs clarity, not expression.
- **Consistent across renders** — the same character must sound the same every
  time.

Record the chosen IDs and the reason for each in
`.claude/memory/decisions.md` once selected.

---

## 4. Model and delivery settings

```python
DEFAULT_MODEL = "eleven_multilingual_v2"
```

`eleven_multilingual_v2` is the model that handles Japanese properly. The
monolingual/English models mangle kana readings — do not use them.

```python
VOICE_SETTINGS = {
    "stability": 0.75,        # high = consistent; low = expressive
    "similarity_boost": 0.75,
    "style": 0.0,             # no dramatic interpretation
    "use_speaker_boost": True,
    "speed": 0.85,            # slightly slower than conversational
}
```

The reasoning is deliberate and worth preserving: **language learning wants
consistency, not personality.** High stability and zero style mean a character
read twice sounds identical both times, so the learner keys on the glyph rather
than on prosody. The reduced speed gives a single mora room to be heard.

---

## 5. What gets spoken

From `audio.speech_text()`:

- **Kana** — the glyph itself (`あ` → "あ")
- **Kanji** — the primary **kun'yomi** if present, otherwise the primary
  **on'yomi**; the glyph as a last resort

Reading fields store alternatives separated by `/` with okurigana in
parentheses. Only the first alternative is spoken and the brackets are dropped:
`ひと(つ)` → "ひとつ".

---

## 6. Caching and cost

Renders are cached under `config.audio_cache_dir`
(`~/.local/share/japanese-practice/audio-cache/` by default), keyed by SHA-1 of
`(text, voice_id)`. **A given character in a given voice is synthesised once,
ever.** With 104 + 104 + 107 characters, a full two-voice build is roughly 630
API calls total — after which the app runs indefinitely without touching the
network.

To pre-warm the cache rather than paying per first-use, iterate the character
table and call `get_audio` for each glyph in each voice. Better still, promote
the results to **bundled clips** under `static/audio/<script>/<glyph>.mp3`,
which removes the API dependency entirely for the fixed kana sets.

Clearing the cache is safe — it simply re-synthesises.

---

## 7. Current status

| Item | Status |
|---|---|
| Resolution chain implemented | ✅ |
| ElevenLabs module (`tts_elevenlabs.py`) | ✅ Written, imports clean |
| Wired into `get_audio` ahead of local TTS | ✅ |
| Caching per `(text, voice)` | ✅ |
| Graceful degradation without a key | ✅ **Verified** — falls through to local TTS |
| Local clip library + validation | ✅ `audio_library.py`; 26 tests |
| espeak-ng installed | ✅ 2026-08-06; Japanese voice `ja` present |
| **End-to-end audio through `/api/audio`** | ✅ **Verified 2026-08-06** — audible WAV, peaks 0.385–0.786, cached to disk |
| **Called against the live API** | ✅ **2026-08-07** — 630 clips rendered and validated |
| Real voice IDs chosen | ✅ Matilda (female) / Daniel (male) — see [VOICE-LAB.md](VOICE-LAB.md) |
| `gender` exposed on `/api/audio/<id>` | ✅ `?voice=female\|male` |
| Bundled clips | ✅ **630** — every character in both voices, validated, manifested |

### Correction — 2026-08-06

An earlier revision of this document and of `HANDOFF.md` stated that
`/api/audio` returned "real espeak synthesis". **It did not.** No TTS binary was
installed; every response was the 0.4s silent stub, whose 17,684-byte size was
mistaken for evidence of real audio. The clip validator built for this section
is what caught it, by measuring amplitude rather than trusting size.

`espeak-ng` 1.50 is now installed with the Japanese voice `ja`, and synthesis is
verified by amplitude: あ renders at 772ms with peak 0.571.

**Rule: never treat file size as evidence that audio contains sound.**

---

## 8. The local clip library

Every clip the app ships is stored locally and validated before use. Nothing is
fetched from a third party at runtime.

```
static/audio/
├── manifest.json                     # sha256 + duration + peak per clip
├── hiragana/{female,male}/<glyph>.{mp3,wav}
├── katakana/{female,male}/<glyph>.{mp3,wav}
└── kanji/{female,male}/<glyph>.{mp3,wav}
```

The tree mirrors how audio is selected — **script → voice → glyph** — so a
clip's purpose is readable from its path and a missing set shows up in a plain
directory listing.

### Validation gates

`audio_library.validate_clip()` rejects a clip for any of these, and
`is_validated()` treats a rejected file as **absent** so it can never reach a
learner:

| Gate | Rejects |
|---|---|
| Exists and ≥ 512 bytes | Zero-byte and header-only files |
| RIFF / MP3 magic bytes | Wrong or corrupt format |
| Duration 150–4000 ms | Truncated renders; a whole word read instead of a mora |
| Peak amplitude ≥ 0.01 | **Silence** — the worst failure, since nothing plays and the learner assumes the character has no sound |
| SHA-256 recorded | Silent corruption between runs |

Duration is derived from the bytes actually present, not the WAV header:
streaming writers such as espeak-ng emit a placeholder length, and trusting it
reported durations of 48,695,681 ms.

### Commands

```python
from japanese_practice import audio_library as lib

lib.scan_library()             # validate every clip in the tree
lib.write_manifest()           # record the valid ones with checksums
lib.verify_against_manifest()  # detect drift or deletion since then
lib.is_validated("hiragana", "あ", "female")
```

---

## 9. Next steps

**Next steps:** provide a key, run `list_voices()`, choose a male and a female
Japanese voice per §3, set `JP_VOICE_MALE` / `JP_VOICE_FEMALE`, then add a
`?voice=male|female` query parameter to `/api/audio/<id>` and a voice toggle in
the study view.
