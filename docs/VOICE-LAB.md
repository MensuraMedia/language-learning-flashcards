# Voice Lab — creating, sampling and shipping pronunciation audio

How the application obtains natural Japanese pronunciation for every character,
and how to repeat the process for new voices, new characters or a new language.

The problem is decomposed **MECE** — seven layers, each with a single
responsibility, no overlap between them, and nothing outside them. A change in
one layer cannot require a change in another.

| # | Layer | Single responsibility | Module |
|---|---|---|---|
| 1 | [Credential](#1-credential-layer) | Prove identity to the provider | `tts_elevenlabs.api_key()` |
| 2 | [Selection](#2-selection-layer) | Decide *who* speaks | `voicelab audition` |
| 3 | [Derivation](#3-derivation-layer) | Decide *what* is said | `voicelab.speech_text_for()` |
| 4 | [Synthesis](#4-synthesis-layer) | Turn text into bytes | `tts_elevenlabs.synthesize()` |
| 5 | [Validation](#5-validation-layer) | Refuse bad audio | `audio_library.validate_clip()` |
| 6 | [Storage](#6-storage-layer) | Persist and prove integrity | `audio_library` + `manifest.json` |
| 7 | [Consumption](#7-consumption-layer) | Serve the right clip at runtime | `audio.get_audio()` |

---

## 1. Credential layer

**Responsibility:** supply an API key. Nothing else in this layer.

Resolution order is mutually exclusive — the first hit wins and the rest are not
consulted:

| Priority | Source | When to use |
|---|---|---|
| 1 | `ELEVENLABS_API_KEY` environment variable | CI, one-off runs, overriding the stored key |
| 2 | `~/.config/japanese-practice/elevenlabs.key` (mode `600`) | Desktop use — a windowed app launched from a menu has no shell to export a variable in |
| 3 | *(none)* | Backend disabled; the app falls through to local TTS |

```bash
install -m 600 /dev/null ~/.config/japanese-practice/elevenlabs.key
printf 'sk_...\n' > ~/.config/japanese-practice/elevenlabs.key
```

**Invariants.**
- The key file lives **outside the repository**, so it cannot be committed by any
  `git add` mistake. `.gitignore` is a safety net, not the mechanism.
- The key never passes through a shell command. The project's own
  `pre-tool-use-security.sh` hook blocks reading secret files, and it is correct
  to do so — the key is read inside the Python process.
- An account **password is never a credential** for this integration. The REST
  API authenticates with `xi-api-key`.

**Key permissions.** Scoped keys are the norm and most scopes are unnecessary
here:

| Scope | Needed? | Consequence if absent |
|---|---|---|
| `text_to_speech` | **Required** | Nothing works |
| `voices_read` | Optional | `voicelab audition` cannot enumerate the account library; the built-in candidate slate is used instead |
| `user_read` | Not needed | Quota cannot be queried; use `voicelab cost` to estimate instead |

---

## 2. Selection layer

**Responsibility:** decide which voices speak. Nothing about synthesis or storage.

### The criteria, in priority order

1. **Native or near-native Japanese.** An accented voice teaches wrong
   pronunciation, which is worse than no audio at all. Non-negotiable.
2. **Mature tone (30s).** Younger voices read with more prosodic variation, which
   is exactly what a learner should not pattern-match against.
3. **Unhurried pace.** A single mora needs room to be heard.
4. **Consistency across renders.** The same character must sound the same twice,
   or the learner keys on delivery rather than the glyph.
5. **Neutral standard accent** (標準語 / Tokyo).

### The audition

```bash
python -m japanese_practice.voicelab audition
python -m japanese_practice.voicelab audition --gender male   # narrow it
```

Every candidate reads one phrase, chosen to exercise what narrators most often
get wrong:

```
あいうえお。かきくけこ。しんぶん、きょう、がっこう。
```

| Fragment | Tests |
|---|---|
| `あいうえお` | the five pure vowels, evenly |
| `かきくけこ` | consistent consonant onset across the vowel row |
| `しんぶん` | the **moraic ん**, which must hold its own beat |
| `きょう` | a **yoon** contraction plus a long vowel |
| `がっこう` | the **geminate っ**, a silent beat English speakers drop |

Samples land in `~/.cache/japanese-practice/voice-audition/`. **Listen to them.**

### Measuring what you cannot hear

Where a human ear is unavailable, pace is still measurable. At a fixed 128 kbps
CBR, byte size is proportional to duration:

```
duration_s ≈ bytes × 8 ÷ 128000
```

The 2026-08-07 audition, same phrase and settings throughout:

| Voice | Gender | Bytes | ≈ Duration | Read |
|---|---|---:|---:|---|
| Brian | male | 54,378 | 3.40 s | rushed |
| Alice | female | 58,976 | 3.69 s | rushed |
| George | male | 84,889 | 5.31 s | brisk |
| Sarah | female | 87,815 | 5.49 s | brisk |
| **Daniel** | **male** | **93,248** | **5.83 s** | **measured — selected** |
| Lily | female | 91,577 | 5.72 s | measured |
| Callum | male | 91,577 | 5.72 s | measured |
| Liam | male | 104,951 | 6.56 s | slow; labelled *young* |
| **Matilda** | **female** | **110,385** | **6.90 s** | **deliberate — selected** |
| Charlotte | female | — | — | HTTP 402, unavailable on this tier |

### Selected

| Role | Voice | ID | Rationale |
|---|---|---|---|
| Female | **Matilda** | `XrExE9yKIg1WjnnlVkGX` | Middle-aged narration voice; the most deliberate pace in the slate |
| Male | **Daniel** | `onwK4e9ZLuTAKqWW03F9` | Middle-aged, authoritative, measured without dragging |

> **Stated limitation.** These were selected on documented age/style labels and
> on measured pace. **Timbre and accent authenticity were not assessed by ear.**
> Both are English-native voices rendered through a multilingual model. If they
> carry an audible English colour on Japanese, replace them — the audition
> samples are on disk and the override is one command.

Override without touching code:

```bash
export JP_VOICE_FEMALE="<voice_id>"
export JP_VOICE_MALE="<voice_id>"
```

---

## 3. Derivation layer

**Responsibility:** decide the text to speak. No knowledge of voices or files.

| Script | Spoken text | Why |
|---|---|---|
| Hiragana | the glyph itself (`あ`) | The model reads kana natively |
| Katakana | the glyph itself (`ア`) | Same |
| Kanji | primary **kun'yomi**, else primary **on'yomi** | A lone kanji has no single pronunciation; the kun'yomi is what a learner meets first |

Reading fields store alternatives separated by `/` with okurigana in
parentheses. Only the first alternative is spoken and brackets are stripped:
`ひと(つ)` → `ひとつ`.

`voicelab.speech_text_for()` and `audio.speech_text()` implement the same rule
deliberately, so a bundled clip and a live TTS render always say the same thing.

---

## 4. Synthesis layer

**Responsibility:** text in, audio bytes out.

| Parameter | Value | Reason |
|---|---|---|
| Model | `eleven_multilingual_v2` | The only model that handles Japanese pitch accent. Monolingual models mangle kana. |
| Format | `mp3_44100_128` | Matches the bundled-clip format; CBR makes duration derivable from size |
| `stability` | `0.75` | High = consistent. A character read twice must sound identical. |
| `similarity_boost` | `0.75` | Holds the voice's identity across short utterances |
| `style` | `0.0` | No dramatic interpretation. Zero character, maximum clarity. |
| `use_speaker_boost` | `true` | Clarity on short inputs |
| `speed` | `0.85` | Slightly slower than conversational — a mora needs room |

**No phonetic markup is required.** Per ElevenLabs, the multilingual model
detects and applies Japanese pronunciation from plain Japanese text; there is no
prompt to engineer. If a specific reading is ever wrong, the fix is their
**Pronunciation Dictionary** applied via `pronunciation_dictionary_locators`,
not an inline hack.

---

## 5. Validation layer

**Responsibility:** refuse bad audio. It knows nothing about where audio came
from — the same gates apply to an ElevenLabs render, an espeak render, or a
hand-recorded file.

| Gate | Rejects | Constant |
|---|---|---|
| File exists and ≥ 512 bytes | Zero-byte and header-only files | `MIN_BYTES` |
| RIFF / MP3 magic bytes | Wrong or corrupt format | `_MP3_MAGIC` |
| Duration 150–4000 ms | Truncated renders; a whole word read for one mora | `MIN/MAX_DURATION_MS` |
| Peak amplitude ≥ 0.01 | **Silence** | `MIN_PEAK_AMPLITUDE` |
| SHA-256 recorded | Silent corruption between runs | — |

**Silence is the gate that matters.** It is the worst failure mode: nothing
plays, and the learner concludes the character has no sound. This gate is what
caught the project's earlier false claim that espeak audio was working when no
TTS binary was installed at all — the 17,684-byte "audio" was a silent stub, and
size alone looked plausible.

> **Rule: never treat file size as evidence that audio contains sound.**

Duration is derived from the bytes actually present, not the WAV header —
streaming writers such as espeak-ng emit a placeholder length, which once
reported a duration of 48,695,681 ms.

**Validation happens before the clip enters the library.** `voicelab build`
writes to a hidden scratch file *with a real audio suffix*, validates, and only
then renames into place. A rejected render never occupies its final path.

---

## 6. Storage layer

**Responsibility:** where clips live and how integrity is proven.

```
static/audio/
├── manifest.json                     # sha256 + duration + peak per clip
├── hiragana/{female,male}/<glyph>.mp3
├── katakana/{female,male}/<glyph>.mp3
└── kanji/{female,male}/<glyph>.mp3
```

The tree mirrors selection order — **script → voice → glyph** — so a clip's
purpose is readable from its path and a missing set is visible in a directory
listing.

`manifest.json` records every *valid* clip with its checksum, duration and peak,
plus a `rejected` list with reasons. `verify_against_manifest()` re-hashes and
reports drift or deletion.

Scale for the current content set:

| Set | Characters | × 2 voices |
|---|---:|---:|
| Hiragana | 104 | 208 |
| Katakana | 104 | 208 |
| Kanji N5 | 107 | 214 |
| **Total** | **315** | **630 clips** |

≈1,050 API characters total — the utterances are one to four characters each.

---

## 7. Consumption layer

**Responsibility:** serve the right clip at runtime. It never synthesises.

`audio.get_audio(character, gender=...)` resolves in order and **never raises**:

| # | Source | Cost | Offline |
|---|---|---|---|
| 1 | Validated bundled clip | free | yes |
| 2 | Cached ElevenLabs render | free | yes |
| 3 | Fresh ElevenLabs render | API characters | no |
| 4 | Cached local TTS | free | yes |
| 5 | Fresh local TTS | free | yes |
| 6 | Silent WAV stub | free | yes |

Once the library is built, **step 1 always wins** — the application never calls
the API again, works with the network unplugged, and costs nothing to run.
Steps 2–5 exist for characters added after the last build.

---

## Operations

```bash
python -m japanese_practice.voicelab cost        # estimate BEFORE spending
python -m japanese_practice.voicelab audition    # sample candidates
python -m japanese_practice.voicelab build \
    --female-id XrExE9yKIg1WjnnlVkGX \
    --male-id   onwK4e9ZLuTAKqWW03F9
python -m japanese_practice.voicelab verify      # validate + rewrite manifest
```

| Property | Behaviour |
|---|---|
| **Resumable** | `build` skips any clip already present and valid, so an interrupted run continues where it stopped |
| **Bounded** | `--limit N` renders a trial batch first |
| **Fail-fast** | Five consecutive request failures abort the run rather than burning quota |
| **Rate-limited** | `REQUEST_SPACING_S = 0.35` keeps bursts under the API's limit |
| **Idempotent** | Re-running after a full build renders nothing and costs nothing |

### Failure modes

| Symptom | Cause | Action |
|---|---|---|
| `missing the permission voices_read` | Scoped key | Harmless — the candidate slate is used. Widen the scope to enumerate the account library. |
| HTTP 402 on one voice | Voice not available on the tier | Choose another; the rest of the run is unaffected |
| HTTP 429 | Rate limited | Raise `REQUEST_SPACING_S` and re-run; it resumes |
| `REJECTED: effectively silent` | Bad render | Re-run — the clip was never written |
| `REJECTED: duration … outside bounds` | Model read the glyph as a word | Check `speech_text_for()` for that character |

---

## Extending the toolset

| Goal | Change | Layers touched |
|---|---|---|
| Swap a voice | `JP_VOICE_*` env var, or `DEFAULT_VOICES` | 2 only |
| Add a third voice | Add to `CANDIDATES`; `build --voices female male child` | 2, 6 |
| Add characters (N4–N1) | Add the content module; re-run `build` | 3 only — it renders just the new ones |
| Change provider | Reimplement `tts_elevenlabs.synthesize()` | 4 only |
| Add a language | New content module + `clip_path()` script name | 3, 6 |
| Hand-recorded clips | Drop files into the tree and run `verify` | 5, 6 — the gates are provider-agnostic |

The MECE split is what makes this table short: swapping providers cannot break
validation, and adding characters cannot break voice selection.

---

## Related documents

| Document | Contents |
|---|---|
| [AUDIO.md](AUDIO.md) | Runtime resolution chain and voice criteria |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How audio fits the wider system |
| [TESTING.md](TESTING.md) | The 26 clip-library validation tests |
| [JAPANESE-CONTENT-MODEL.md](../mockups/_reference/JAPANESE-CONTENT-MODEL.md) | The character sets being voiced |
