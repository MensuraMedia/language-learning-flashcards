# Interface sound

The chime that plays when you get something right, and the preference system it
forced into existence.

Distinct from [AUDIO.md](AUDIO.md), which covers *pronunciation* — the Japanese
being taught. This document is about sound as feedback on an action. The two are
gated by the same master switch and are otherwise unrelated.

- **Current as of** 2026-08-08 · 311 tests passing
- **Source**: [`static/js/sound.js`](../src/japanese_practice/static/js/sound.js) ·
  [`static/js/prefs.js`](../src/japanese_practice/static/js/prefs.js) ·
  [`tools/make_cues.py`](../tools/make_cues.py)
- **Assets**: [`static/audio/sounds/`](../src/japanese_practice/static/audio/sounds/)

---

## 1. What it does

| Where | Trigger |
|---|---|
| Study view | A card answered correctly — not a skip, not a wrong answer |
| Memory games | A pair matched correctly, in any of the three scripts |
| Settings | Choosing a cue previews it; **Test sound** fires it on demand; turning the master switch on confirms itself |

A correct answer on a card and a matched pair are the same event to a learner,
so they get the same feedback. Nothing sounds on a wrong answer: a cue for
failure would fire constantly early on, when a learner is least in need of
being told off.

**The cue is fired before the attempt is posted to the server**, not after. It is
feedback on the click; waiting for the round trip put it audibly late.

---

## 2. The cue set

Seven options, chosen in **Settings → Audio**. Each is a different *character* of
positive rather than a different pitch of the same sound — this fires several
times a minute, so the one that does not grate after two hundred repeats is a
real choice.

| Cue | Character | Duration | Centroid |
|---|---|---:|---:|
| **Ding** | The supplied sound — soft and low | 0.320 s | 625 Hz |
| **Chime** | Two notes rising a perfect fifth | 0.320 s | 2256 Hz |
| **Bell** | A single struck bell, inharmonic partials | 0.320 s | 2661 Hz |
| **Marimba** | Warm and wooden, fast decay | 0.260 s | 1116 Hz |
| **Arpeggio** | Three rising notes, a major triad | 0.320 s | 2270 Hz |
| **Sparkle** | Two bright high pings | 0.300 s | 2292 Hz |
| **Blip** | One soft sine — the least intrusive | 0.130 s | 1779 Hz |

`Ding` is derived from the supplied MP3. The other six are synthesised by
`tools/make_cues.py`, which builds each from sine partials with per-partial
decay envelopes — giving a struck quality, where upper partials die first,
rather than an additive drone.

### The asset contract

Every cue meets the same four constraints, each asserted per-cue by the suite.

| Property | Value | Why |
|---|---|---|
| **Format** | mono 44.1 kHz 16-bit WAV | Decoded once into memory; MP3's encoder delay left ~14 ms of lag even after trimming silence out |
| **Onset** | < 20 ms | Leading silence *is* latency between the click and the sound. The supplied MP3 had **64 ms** of it |
| **Duration** | ≤ 380 ms | The study view advances 380 ms after a correct answer at its fastest pace. Anything longer rings over the next card |
| **Loudness** | −14 dBFS RMS, ±0 dB across the set | Peak is not loudness. Matching RMS is what lets one volume control govern cues and speech together — see §4 |
| **Peak** | 0.35–0.99, capped at −1 dBFS | A sanity floor and a clipping ceiling only. Deliberately *not* a target |

```bash
python tools/make_cues.py       # regenerate all six synthesised cues
```

---

## 3. Why Web Audio, not `HTMLAudioElement`

The first implementation used `new Audio(url).play()`. That is the API for media
playback — a track you start, scrub and stop — and for a short cue it fails in
three specific ways:

| Problem | Consequence |
|---|---|
| `play()` returns a promise the autoplay policy can **reject**, and rejection is the normal state until the page has been interacted with | Swallowing that rejection makes a blocked cue indistinguishable from a working one. This is what hid the fault |
| `currentTime = 0` restarts are not sample accurate and **cancel the cue already sounding** | Two quick correct answers give one blip |
| Every play crosses the media pipeline | Latency varies with whatever else the engine is doing |

The Web Audio API is what the platform provides for interface sound:

```
fetch → decodeAudioData → AudioBuffer          (once, per cue)
              ↓
      BufferSourceNode → GainNode → destination (per play)
```

Decoded once into memory; each cue is a fresh source node started immediately.
Sub-millisecond, overlapping safely, with an explicit level.

### Autoplay unlocking

The one obligation Web Audio adds. An `AudioContext` created before any user
gesture starts `suspended`, and every cue from it is silent until something
resumes it.

- Unlocked on the **first** `pointerdown`, `keydown` or `touchstart`, by a
  listener that removes itself afterwards.
- Re-resumed on **every** cue, because the engine suspends the context again
  whenever the window loses focus.

### Decode timing

A cue that has not finished decoding used to return silently, which is why five
of the seven made no sound the first time they were clicked. `playCorrect` now
decodes and then plays, bounded at **400 ms** — past that the answer has moved
on, and dropping the cue beats sounding it over the next card.

---

## 4. Level

**Loud in the file, attenuated in code. Never the reverse.**

The first version kept the source's −8.2 dBFS peak and multiplied it by an 0.55
app gain:

```
   0.391  cue peak
 × 0.55   app gain
 × 0.51   system volume
 = 0.110  →  about -19 dBFS at the speakers
```

Which is inaudible over anything, and was the entire reason the cue "did not
work". The fix was to normalise the assets loud and attenuate in code.

### Peak is not loudness

Normalising them loud was right; normalising them to a **peak** was not. Every
cue went to −0.4 dBFS peak, which sounds like it should match a pronunciation
clip at −8.3 dBFS peak reasonably closely. It did not — the cue was **+10.1 dB
louder to the ear**, and one volume control governing both felt broken, because
turning it down to suit the cue made the speech inaudible.

The reason is crest factor. Speech is mostly quiet: consonants, gaps and decays
sit far below the one vowel peak that sets the file's maximum. A short bright
tone spends nearly all of its length near its own peak. Two files with identical
peaks therefore carry very different *average* energy, and average energy is
what the ear integrates.

| | Peak | RMS over the audible part |
|---|---:|---:|
| Cue, peak-normalised | −0.4 dBFS | −11.6 dBFS |
| Pronunciation clip | −8.3 dBFS | −19.7 dBFS |

So the cues are now **loudness**-normalised: RMS measured over the audible part
of the file — samples above 5% of peak, which excludes the long decay tails that
would otherwise make a ringing bell read as quieter than a short blip that is
actually just as loud. All seven land at −14 dBFS RMS with **0.0 dB** of spread
between them, where peak normalisation had left them 1.7 dB apart.

`CUE_GAIN = 0.507` then closes the remaining 5.9 dB to the narration median:

```
  -14.0 dBFS   cue asset, RMS
 ×  0.507      CUE_GAIN
 =  -19.9 dBFS at volume 1.0
```

Measured against 60 clips sampled from the library: speech median **−19.7 dBFS**,
10th–90th percentile −21.9 to −17.3. The cue sits **0.2 dB** below that median —
comfortably inside the spread of the narration against itself, which is the
tightest match that means anything.

Both paths then scale linearly from the same `jp.volume` value — `gain.value` on
the Web Audio node, `.volume` on the `HTMLAudioElement` — so they track together
across the whole range of the slider rather than only at one setting.

> **Do not re-tighten the peak assertion into a peak target.** That is the exact
> change that caused this, and the test carries a comment saying so.

Three preferences compose to the final level:

| Preference | Set in | Effect |
|---|---|---|
| `jp.sound` | Settings → Audio → Sound | Master. Off silences cues **and** pronunciation, everywhere |
| `jp.muted` | Study view, `M` | Quick mute for the current sitting |
| `jp.volume` | Study view, `↑` / `↓` | Level |

A cue is heard only when the master is on and nothing is muted, so `M` still
silences a session and Settings still wins over `M`.

---

## 5. Preferences, and why they live on the server

This is the part that took three attempts, and the reasoning matters more than
the result.

### What went wrong, in order

| Attempt | Approach | Failure |
|---|---|---|
| 1 | `localStorage` directly | The desktop webview **accepts writes and drops them**. `setSoundEnabled(false)` wrote nothing; the next read returned the old value; the switch repainted itself back **on** and audio kept playing. A toggle that does not toggle is worse than an absent one |
| 2 | Authority in memory, `localStorage` as a mirror | Fixed the toggle *within a page*. But `/study` is a **full page navigation** — a fresh JS context with an empty cache — so a cue chosen on the dashboard never reached the study view. Pace, voice and volume had been failing the same way all along, unnoticed, because none of them visibly contradicts itself the way a toggle does |
| 3 | **Server-side, per profile** | Works. Survives navigation *and* restarting the application |

### How it works now

Preferences are rows in a `preferences` table. Because **each profile is already
its own database file**, the table is per-profile without needing a profile
column — which closed the separate "per-profile preferences" roadmap item for
free.

| Aspect | Detail |
|---|---|
| Endpoint | `GET` / `PUT` / `POST /api/preferences` |
| Why `POST` | `navigator.sendBeacon`, used to flush on `pagehide`, cannot issue a `PUT` |
| Keys | Closed set: `jp.sound`, `jp.cue`, `jp.volume`, `jp.muted`, `jp.voice`, `jp.pace`. Unknown keys are **rejected**, not ignored |
| Limits | Values capped at 64 characters. An open key-value store reachable from the page is a way to fill someone's database |
| Reads | Synchronous, from a cache primed at start-up |
| Writes | Applied to the cache immediately — a control always reflects what you just did — then flushed on a 250 ms debounce, so dragging a slider is one request |
| Load order | The study view adopts pace, voice, volume and cue **before dealing its first card**, rather than at module load when nothing has arrived |

---

## 6. Diagnostics

A cue that cannot be heard should be able to say why, rather than leaving the
user to guess between *off*, *blocked* and *broken*.

**Settings → Audio → Test sound** fires the cue and reports the outcome: sound
is off · no Web Audio support · the last error · played · still loading · the
context state.

From the webview console, `window.jpSound` exposes:

| Field | Meaning |
|---|---|
| `soundStatus.supported` | Web Audio is available |
| `soundStatus.contextState` | `running`, `suspended` or `none` |
| `soundStatus.decoded` | At least one cue has decoded |
| `soundStatus.cue` | The cue id currently selected |
| `soundStatus.plays` | Cues emitted this session |
| `soundStatus.lastError` | Most recent failure, or `null` |
| `soundStatus.storage` | Whether preferences reached the server |

---

## 7. How this was verified

Every claim here was checked by **recording the machine's own audio output**,
not by reading the code. That method is worth keeping, because every fault in
this feature was invisible from the source.

```bash
SINK=$(pactl get-default-sink)
parecord --device="${SINK}.monitor" --rate=44100 --channels=1 --format=s16le out.wav
# ... drive the app ...
# then measure bursts: onset, duration, peak, spectral centroid
```

| Question | Evidence |
|---|---|
| Does it sound at all? | Bursts of 0.32 s at −1.4 dBFS on correct answers |
| Is it level with the speech? | Cue and narration measured the same way: −19.9 vs −19.7 dBFS RMS at volume 1.0, a 0.2 dB gap. Previously +10.1 dB |
| Does the master switch work? | Six recorded steps: on → sound, off → silence for both the picker and Test sound, back on → sound. Six for six |
| **Does the selected cue actually apply?** | Selected *marimba*, navigated into a session, answered: recorded 0.23 s at 1070 Hz. Marimba is 0.26 s / 1116 Hz; ding is 0.32 s / 625 Hz. The fingerprint identifies it |

Duration and spectral centroid together identify which cue played, which is what
made the last question answerable at all.

---

## 8. Adding a cue

1. Add a builder to `CUES` in `tools/make_cues.py` and run it.
2. Add an entry to the `CUES` array in `static/js/sound.js` — `id`, `label`,
   `hint`. The id must match the filename, `cue-<id>.wav`.
3. Add the id to `CUE_IDS` in `tests/test_audio_library.py` and to the
   parametrised list in `tests/test_api.py`.

The suite then enforces the §2 contract on it, and asserts the set stays varied
— seven near-identical sounds would not be a choice worth presenting.

---

## 9. Known limits

| Limit | Detail |
|---|---|
| No cue for wrong answers | Deliberate. See §1 |
| No per-cue volume | The set is level-matched; the study view's volume applies to all of them |
| Cue is not previewed in the games view | The picker lives only in Settings, on the dashboard |
| Frontend is untested by a runner | `sound.js` and `prefs.js` are verified by recording output and by the asset tests, not by unit tests — `node` is not installed here (roadmap Q2) |
