# Change manifest — cue loudness matching, and the silence gate that never ran

**Date:** 2026-08-10
**Trigger:** User asked whether the default ding's base level is level with the
volume control and the speaker volume, and to reduce it if not.

---

## 1. Cue loudness (the reported issue)

**Confirmed, and measured before changing anything.** The ding was **+10.1 dB
louder** than the pronunciation clips at the same volume setting.

### Root cause

The cues were **peak**-normalised to −0.4 dBFS. Peak is not loudness. Speech has
a far higher crest factor — mostly quiet, with one vowel peak setting the
maximum — while a short bright tone sits near its own peak throughout. Equal
peaks, very unequal perceived level.

Peak normalisation was itself a fix for the *previous* fault (assets too quiet,
inaudible at the speakers). It corrected the direction and overshot the amount.

| | Peak | RMS (audible part) |
|---|---:|---:|
| Cue, as shipped | −0.4 dBFS | −11.6 dBFS |
| Pronunciation clip | −8.3 dBFS | −19.7 dBFS |

### Fix

- `tools/make_cues.py` — `normalise()` now targets **RMS over samples above 5%
  of peak**, with a −1 dBFS peak ceiling. The 5% floor matters: including decay
  tails would make a ringing bell read as quieter than an equally loud blip.
- All seven cues regenerated. `cue-ding.wav` re-derived from
  `_source/ding-original.mp3` through the same path, dropping the hardcoded
  `volume=2.43` peak-matching constant.
- `sound.js` — `CUE_GAIN` 0.9 → **0.507**, closing the 5.9 dB to the narration
  median.

### Result

| | Before | After |
|---|---:|---:|
| Spread across the seven cues | 1.7 dB | **0.0 dB** |
| Cue vs speech at volume 1.0 | +10.1 dB | **−0.2 dB** |

Speech reference: 60 clips sampled from the library, median −19.7 dBFS RMS,
10th–90th percentile −21.9 to −17.3. The cue now sits inside the spread of the
narration against itself. Both paths scale linearly from the same `jp.volume`,
so they track together across the slider's whole range, not just at one setting.

---

## 2. The silence gate had never run (found while measuring)

Measuring all 630 clips to establish the speech reference surfaced
`hiragana/female/あ.mp3` at **peak 0.0009** — inaudible, and listed in the
manifest as *validated*.

### Root cause

`validate_clip()` applied its duration and amplitude gates to **WAV only**. The
MP3 branch checked magic bytes and stopped, with a comment acknowledging that
measuring needed a decoder. **The entire shipped library is MP3.** So the
silence gate — the stated purpose of `audio_library.py` — had never run against
a single clip the app ships.

A second, compounding fault: `audio._load_bundled()`'s docstring claimed it
loaded a "validated" clip, but it only checked the file existed. Nothing on the
serving path ever consulted validation.

### Why present-but-silent is worse than missing

A missing clip falls through the resolution chain to VOICEVOX or ElevenLabs and
the learner hears the character. A silent clip that *exists* stops the chain
dead and plays nothing. This is the one gate that must not be skipped — and it
was skipped for the first character of the first deck a beginner opens.

### Fix

| File | Change |
|---|---|
| `audio_library.py` | `_mp3_stats()` decodes via ffmpeg; MP3s now take the same duration and amplitude gates as WAV. Absent ffmpeg it degrades to the old sniff and records `peak=None`, so *unmeasured* is never mistaken for *measured* |
| `audio.py` | `_load_bundled()` consults the manifest's rejected list and skips those entries, making the docstring true. **Fail-open** — an unreadable manifest serves clips unfiltered rather than muting the whole library |
| `static/audio/hiragana/female/あ.mp3` | Re-rendered, peak 0.0009 → **0.4864** |
| `manifest.json` | Rebuilt with real measurement: 630 accepted, 0 rejected |

### Why the clip was bad

Not corruption. ElevenLabs renders a bare single vowel as near-silence roughly
one time in three — reproduced directly: attempts measured 0.6592, 0.0281,
0.6217. The build simply got an unlucky draw, and unmeasured validation had no
way to notice. `voicelab` re-renders on a failed report, so with the gate live
this class of fault now self-corrects.

`is_validated()` is **not** on the request path (voicelab and tests only), so
decoding adds no per-request cost.

---

## 3. Tests

| Test | Guards |
|---|---|
| `test_cues_are_loudness_matched_to_each_other` | All seven within 1.0 dB RMS and near −14 dBFS |
| `test_mp3_clips_are_decoded_not_merely_sniffed` | A silent MP3 is rejected |
| `test_the_shipped_library_has_no_silent_clips` | Runs against the real library, where the bug lived |
| `test_every_cue_is_audible_prompt_and_short` | Peak band widened to 0.35–0.99 and **commented not to re-tighten into a peak target** — that is precisely what caused this |
| `test_outstanding_skips_clips_that_already_validate` | Its MP3 stub was ID3 + 4 KB of zeroes, which passed only because of this same hole. Now generates genuine audio, skipping without ffmpeg rather than asserting against a fake |

**347 passing**, ruff and black clean.

---

## 4. Files affected

```
tools/make_cues.py
src/japanese_practice/static/js/sound.js
src/japanese_practice/audio_library.py
src/japanese_practice/audio.py
src/japanese_practice/static/audio/sounds/cue-*.wav        (all 7)
src/japanese_practice/static/audio/hiragana/female/あ.mp3
src/japanese_practice/static/audio/manifest.json
src/japanese_practice/static/audio/sounds/README.md
tests/test_audio_library.py
tests/test_voicelab.py
docs/INTERFACE-SOUND.md
docs/AUDIO.md
docs/FEATURES.md
changelog.md
```

---

## 5. Lesson

Both faults are the same mistake in different clothing: **trusting a proxy for
the property that actually matters.** File size proxied for "is this audio"
(caught long ago). Magic bytes proxied for "is this audible". Peak amplitude
proxied for "how loud is this". Each proxy correlates with the real property
often enough to look fine, and fails exactly where it counts.

The project already had the rule — *never judge an audio file by its size* — but
applied it only to the WAV path. **Measure the thing you care about, on the
format you actually ship.**
