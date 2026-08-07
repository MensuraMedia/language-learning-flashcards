# VOICEVOX evaluation — a Japanese-native alternative to ElevenLabs

**Verdict: adopt VOICEVOX as the primary source, keep ElevenLabs as a fallback.**

Evaluated 2026-08-07 by running engine 0.25.2 locally and measuring it against
the 630 ElevenLabs clips already shipped. Every claim below is something that
was executed, not quoted from documentation.

---

## 1. Why this was worth evaluating

The user reported that ElevenLabs' Japanese "does not measure up to full
phonetic accuracy." That is a perceptual judgement I cannot make — **I cannot
hear.** But it is testable in a different way: a system that genuinely models
Japanese phonology will *expose* that model, and one that applies a multilingual
network to Japanese text will not.

That reframes the question from "which sounds better" (unanswerable here) to
"which one can be inspected and corrected" (answerable, and arguably more
important for a teaching tool).

---

## 2. The decisive difference: phonology is data, not a black box

`POST /audio_query` returns the full phonological analysis before any audio is
rendered. `きょう`:

```
accent position: 1
  キョ   consonant=ky  vowel=o  pitch=5.84  vowel_length=0.119
  オ     consonant=—   vowel=o  pitch=5.63  vowel_length=0.164
```

Every one of those fields is **writable**. You can correct the accent, lengthen a
single mora, or flatten the pitch — then synthesise.

ElevenLabs offers none of this. You send text, you get audio. If a reading is
wrong there is nothing to inspect and nothing to fix short of a pronunciation
dictionary entry.

### It gets the hard cases right — verified

| Test | Expected | VOICEVOX returned | ✓ |
|---|---|---|---|
| 箸 *chopsticks* | accent 1 (HL) | `accent=1` · ハ 5.71 → シ 5.52 (falling) | ✅ |
| 橋 *bridge* | accent 2 (LH) | `accent=2` · ハ 5.47 → シ 5.58 (rising) | ✅ |
| 雨 *rain* | accent 1 | `accent=1` · ア 5.61 → メ 5.50 | ✅ |
| 飴 *candy* | accent 2 | `accent=2` · ア 5.40 → メ 5.44 | ✅ |
| 新聞 | 4 moras, ン is its own beat | `シンブン`, ン carries pitch 5.90 | ✅ |
| 学校 | geminate っ is a silent beat | `ガッコオ`, **ッ pitch = 0.00** | ✅ |
| おばさん *aunt* | 4 moras | `オバサン` accent 4 | ✅ |
| おばあさん *grandmother* | 5 moras, different accent | `オバアサン` accent 2 | ✅ |

**箸/橋 and 雨/飴 are minimal pairs where pitch accent is the only difference in
speech.** Getting both right, in opposite directions, is not something a
multilingual model does by accident. The geminate returning `pitch = 0.00` is
the detail that settles it — the engine models っ as a timed silent mora, which
is precisely the beat English speakers drop.

---

## 3. Measured comparison

Same 14 characters, VOICEVOX 九州そら at `speedScale 0.85` against the shipped clips:

| Source | Median | Spread (max−min) |
|---|---:|---:|
| **VOICEVOX** 九州そら | 0.52 s | **0.33 s** |
| ElevenLabs Matilda (female) | 0.78 s | 0.37 s |
| ElevenLabs Daniel (male) | 0.91 s | 0.44 s |

Tighter spread means more consistent delivery across characters — which is what
a learner should be keying on, rather than variation in the narrator's mood.

> **Caveat, stated plainly.** Duration spread is a proxy for consistency, not a
> measure of naturalness. It says nothing about whether either sounds *right* to
> a Japanese ear. That still requires a human.

---

## 4. Operational comparison

| | VOICEVOX | ElevenLabs |
|---|---|---|
| Language model | **Japanese-native** | Multilingual applied to Japanese |
| Pitch accent | **Exposed and editable per mora** | Opaque |
| Mora decomposition | **Yes** — consonant/vowel/length | No |
| Cost | **Free, unlimited** | Metered characters |
| Network | **None — fully local** | Required |
| API key | **None** | Required, scoped, rotatable |
| Rebuild 630 clips | **4.7 min** on 8 cores | ~4 min + quota |
| Per-clip latency | 0.45 s | ~1 s + network |
| Disk | 2.1 GB engine | 0 |
| Memory | 536 MB resident | 0 |
| Voices | 43 speakers, many styles | Large library |
| Licence | LGPL v3 or commercial | Commercial SaaS |

**The cost/quota asymmetry changes the architecture.** With ElevenLabs the clips
*must* be bundled, because no user will have a key. With VOICEVOX they *can* be
generated on the user's own machine — which, as §6 explains, also sidesteps a
licensing question.

---

## 5. Voice candidates

43 speakers. Most are character voices with an energetic anime delivery,
unsuitable for instruction. These are the exceptions:

| Speaker | Style | ID | Why |
|---|---|---:|---|
| **九州そら** | ノーマル | 16 | 「気品のある大人な声」 — dignified adult female. **Recommended female.** |
| **青山龍星** | ノーマル | 13 | 「重厚で低音な声」 — deep, weighty male. **Recommended male.** |
| **No.7** | アナウンス | 30 | An **announcer** style — purpose-built for clear delivery |
| **No.7** | 読み聞かせ | 31 | A **read-aloud** style, built for narration |
| 玄野武宏 | ノーマル | 11 | Clear younger male; brighter than 青山龍星 |
| もち子さん | ノーマル | 20 | 「明瞭で穏やかな声」 — clear and calm |
| 冥鳴ひまり | ノーマル | 14 | Neutral female |

**No.7's アナウンス and 読み聞かせ styles deserve a listen before anything else.**
They are the only two voices in either provider explicitly designed for the job
this application needs.

---

## 6. Licensing — the one genuine complication

| Question | Answer |
|---|---|
| Commercial use of generated audio | **Permitted** |
| Attribution | **Required** — e.g. `VOICEVOX:九州そら`, shown somewhere a user would naturally find it |
| Engine redistribution | **Prohibited** |
| **Redistributing generated audio files** | **Not addressed.** The terms are silent |

That last row matters, because this repository is **public and currently ships
630 audio files**. The voice-library terms are written for end-user
applications and do not contemplate bundling pre-generated clips in a
repository. Silence is not permission.

**Two clean options:**

1. **Generate on first run** *(recommended)*. Ship no VOICEVOX audio. On first
   launch, if a local engine is reachable, build the library on the user's
   machine — 4.7 minutes, no network, no key, no quota. Nothing is
   redistributed, so the question never arises.
2. **Ship the clips** — only after written clarification from the voice owner.

Option 1 is also better architecture: it makes the app's audio independent of
any vendor account, and it is only possible *because* VOICEVOX is free and local.

Attribution is required either way, and belongs on an about/credits surface.

---

## 7. Recommended architecture

Extend the existing chain rather than replacing it. `audio.get_audio()` already
resolves bundled → ElevenLabs → local TTS → silence; VOICEVOX slots in as a
provider and the validation, manifest and storage layers are untouched — which
is exactly what the MECE split in [VOICE-LAB](VOICE-LAB.md) was for.

```
1. Validated bundled clip            (free, offline)
2. VOICEVOX, if an engine is reachable   ← new primary source
3. ElevenLabs, if a key is configured    ← fallback
4. Local espeak / pico                   (floor)
5. Silent stub                           (never errors)
```

`voicelab` gains `--provider voicevox|elevenlabs`, so the same audition → cost →
build → verify workflow drives both.

**Engine discovery must be optional.** Probe `127.0.0.1:50021/version` with a
short timeout; if nothing answers, fall through silently. A user without the
engine must see no error — the app already has three working fallbacks beneath
it.

---

## 8. What this evaluation did *not* establish

- **Whether VOICEVOX sounds better.** It has verifiably correct phonology and
  tighter consistency. Whether 九州そら sounds *natural* to a Japanese ear is a
  human judgement, still outstanding as roadmap item **A2/A6**.
- **Whether the character voices suit the tone.** Both recommended speakers are
  described as mature, but VOICEVOX voices come from a character-voice tradition
  with a different register to Western TTS narration.
- **Windows/macOS behaviour.** Only the Linux CPU x64 build was run.

---

## 9. Reproducing this

```bash
# engine, ~1.8 GB download, 2.1 GB extracted
curl -L -o engine.7z.001 \
  https://github.com/VOICEVOX/voicevox_engine/releases/download/0.25.2/voicevox_engine-linux-cpu-x64-0.25.2.7z.001
7z x engine.7z.001
./linux-cpu-x64/run --host 127.0.0.1 --port 50021

curl http://127.0.0.1:50021/version
curl http://127.0.0.1:50021/speakers | python3 -m json.tool | head -40

# inspect the phonology before rendering anything
curl -X POST "http://127.0.0.1:50021/audio_query?text=%E7%AE%B8&speaker=16" | python3 -m json.tool
```

Installed for this evaluation at `/home/user/opt/voicevox/linux-cpu-x64`.

---

## 10. Related

| Document | Contents |
|---|---|
| [AUDIO.md](AUDIO.md) | Current runtime resolution chain |
| [VOICE-LAB.md](VOICE-LAB.md) | The MECE pipeline this plugs into |
| [ROADMAP.md](ROADMAP.md) | Items A6–A8 — phonetic verification and alternatives |
