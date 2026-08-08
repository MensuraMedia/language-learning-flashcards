# Features & function reference

Everything the application does, and every module, endpoint and control that
does it. Current as of 2026-08-07 · 239 tests passing.

- [1. Study cards](#1-study-cards) · [2. Memory games](#2-memory-games) · [3. Dashboard](#3-dashboard--analytics)
- [4. Audio](#4-audio) · [5. Content](#5-content) · [6. Scoring](#6-scoring--scheduling)
- [7. HTTP API](#7-http-api) · [8. Modules](#8-module-reference) · [9. CLI](#9-command-line)
- [10. Configuration](#10-configuration) · [11. Not built](#11-deliberately-not-built)

---

## 1. Study cards

### The loop

A card shows **one glyph and nothing else**. Three options sit beside it. Picking
one scores automatically and flips the card, so a wrong answer still teaches.

| Feature | Detail |
|---|---|
| **Front face purity** | The glyph alone — no romaji, meaning or hint. Asserted by a test that parses the markup |
| **True 3D flip** | `rotateY(180deg)` with `backface-visibility`, 0.55 s |
| **Multiple choice** | 3 options, server-shuffled so the answer is never in a fixed slot |
| **Verdict hold** | Correct 1.9 s · wrong 2.9 s. A wrong answer is when the learner actually studies, so it gets longer |
| **Skip** | Scores −1 and records `skipped=1` — an honest "I don't know" |
| **Back / Next** | One split control. Next is greyed until you have gone back, then returns you forward **free** |
| **Voice toggle** | Female / male, persisted |
| **Session recap** | Every character covered, at option-card size, misses in red with romaji beneath |
| **Colour-coded metrics** | Score, accuracy and streak graded green / amber / red against what was achievable |

### Distractor quality

Distractors are not random. In priority order:

1. **Curated visual-confusion partners** — シ/ツ, ソ/ン, る/ろ, ぬ/め, き/さ, は/ほ
   (45 hand-authored pairs)
2. **Voicing siblings** — ぱ offers `ba` and `ha`, so the han-dakuon deck actually
   tests the は/ば/ぱ contrast it exists for
3. **Same kana group / JLPT level**
4. **Same script**

Without this a card can be won by elimination, which tests nothing.

### Keyboard

Every action is reachable without the mouse.

| Key | Action |
|---|---|
| `1` `2` `3` | Choose that option |
| `Space` `Enter` | Flip |
| `S` | Skip — "I don't know", −1 |
| `←` | Previous card |
| `→` | Return forward (free after going back; refused on an unanswered card) |
| `↑` `↓` | Volume |
| `M` | Mute |
| `P` `R` | Play pronunciation |
| `V` | Switch voice |
| `Esc` | End session |
| `?` `H` | Shortcut panel |

---

## 2. Memory games

Three unscored boards on one engine, at `/games`, **each dealt in one of the
three scripts** — nine games in all. **Seeded from your weakest characters by
default**: a generic memory game with kana on it trains spatial memory; a board
built from what you keep missing trains the failure.

| Mode | Loop | Trains |
|---|---|---|
| **Match Up** 対応 | All tiles face up; pair each glyph with what it means or sounds like | Reading → character for kana, Meaning → character for kanji — the direction no card tests |
| **Pelmanism** 神経衰弱 | The same board face down | Holding a glyph's shape in mind between turns |
| **Confusion Drill** 紛らわしい | Board stacked with curated look-alikes | Telling あ/お, シ/ツ, 像/象 apart |

**Why the script matters.** The same engine trains different things per script.
A kana board pairs a glyph with its sound; a kanji board pairs it with its
meaning, because that is what a kanji card is graded on. And the look-alikes a
learner confuses are disjoint sets — シ/ツ is a katakana problem, る/ろ a
hiragana one, 問/門 a kanji one. Each script's boards sit directly under that
script's decks on the dashboard.

Both halves of a confusion pair are always dealt onto the board together. A
look-alike without its partner is an ordinary memory tile; the discrimination
only happens when both shapes are in front of you.

- **Board shape**: columns in groups of three, count chosen to minimise the
  row/column difference. 6 pairs is a centred 3×4 block, never a long strip —
  position is what a memory game trains.
- **Selection state**: amber border, glyph, fill, lift, glow and corner dot.
- **Pair sizes**: 4, 6, 8 or 10.
- **Completion**: time, moves, and efficiency against the perfect move count.
- **Fallback**: a new learner has no weak set, so the deck fills in and the games
  work on day one.

### What they record, and what they do not

Mis-pairings **are** recorded — an unambiguous "I think this character reads as
that", better evidence than a multiple-choice guess.

They **do not** feed the drill queue or SM-2. As a board empties, elimination
makes a late match nearly free; counting that as knowledge would inflate mastery
the same way a chance floor does.

---

## 3. Dashboard & analytics

### Instrument row

Sessions run · Cards reviewed · Overall accuracy (with sparkline) · Best streak ·
Average response · Decks in play.

### Deck shelves

Every difficulty key as a physical deck: rung badge, three-glyph preview, an obi
band doubling as the mastery meter, and the challenge/scoring pairing it opens
with. Yoon decks preview two glyphs, because digraphs overrun the card.

Empty shelves are hidden rather than rendered as blank cards.

### Memory-training cards

Deliberately a different object from a deck: landscape, a miniature of the board
they deal (Pelmanism's is genuinely half-covered), what they train instead of
progress, an `unscored` tag, and a coloured edge per mode.

### Metrics

| Panel | What it computes |
|---|---|
| **Per-character miss-rate heatmap** | `missed / seen` per glyph, amber intensity, **click any cell to drill it** |
| **Weakest characters** | Recency-weighted — a miss yesterday outranks one 120 days ago. Skips weigh 1.25× |
| **Accuracy per session** | Trend, oldest first |
| **Accuracy by set** | Per deck |
| **Retention curve** | Accuracy bucketed by days since that character was last seen |
| **Time of day** | Accuracy by hour, as a dot plot |
| **Mastery by group** | Per kana group and JLPT level |
| **Leeches** | High lapses relative to reps — repeatedly relearned and re-forgotten |
| **First vs eventual** | Genuine recall against within-session pattern-matching |
| **Progress velocity** | Newly mastered per week |
| **Study calendar** | 90-day contribution grid |
| **Session history** | Date, deck, challenge, scoring, cards, accuracy, average, streak, score |

**Mastery** = `seen ≥ 3 AND miss_rate ≤ 0.15`. Deliberately conservative; three
exposures is the minimum at which a rate means anything.

**Every metric is derived at query time** from an append-only `attempts` table,
so a new metric applies retroactively to all existing history — no migration, no
backfill. Every one returns a sensible empty structure on a fresh install.

---

## 4. Audio

### Resolution chain — never raises

| # | Source | Offline | Cost |
|---|---|---|---|
| 1 | VOICEVOX, cached | ✅ | free |
| 2 | VOICEVOX, fresh | ✅ | free, ~0.45 s |
| 3 | Validated bundled clip | ✅ | free |
| 4 | ElevenLabs, cached | ✅ | free |
| 5 | ElevenLabs, fresh | ❌ | metered |
| 6 | espeak / pico | ✅ | free |
| 7 | Silent WAV stub | ✅ | free |

Any failure falls through. A missing engine costs 20 ms and logs nothing.

### VOICEVOX — the primary source

Japanese-native, local, free. It returns the full phonological analysis **before**
rendering — per-mora consonant, vowel, pitch, duration and accent position — and
every field is writable. Verified on minimal pairs: 箸 `accent=1` against 橋
`accent=2`; the geminate っ returns `pitch = 0.00`, a timed silent mora.

Voices: **No.7 アナウンス** (female) and **青山龍星** (male), chosen by audition on
measured per-character consistency.

### Bundled library

630 clips — 104 hiragana + 104 katakana + 107 kanji, in two voices. Every clip
validated before entering the library: format magic, size floor, 150–4000 ms
duration, and a **peak-amplitude gate that rejects silence**. A manifest records
SHA-256 per clip; `verify_against_manifest()` detects drift.

A **cross-voice consistency check** flags clips whose two voices disagree by more
than 0.35 s — it caught a truncated へ at 0.24 s that passed the absolute floor.

---

## 5. Content

| Set | Count | Groups |
|---|---:|---|
| Hiragana | **104** | 46 gojuon · 20 dakuon · 5 han-dakuon · 33 yoon |
| Katakana | **104** | same split |
| Kanji JLPT N5 | **113** | meaning, on'yomi (katakana), kun'yomi (hiragana), stroke count |
| Kanji JLPT N4 | **169** | meaning, on'yomi, kun'yomi, thematic category |
| Kanji JLPT N3 | **396** | same |
| Kanji JLPT N2 | **236** | same |
| Kanji JLPT N1 | **337** | same |
| Kanji by frequency | **500** | teaching order, ranked 1–500, slicing the Top 200 and Top 500 tiers |
| Confusion pairs | **84** | 21 hiragana · 24 katakana · 39 kanji |

**1,453 characters in total**, of which **1,245 are kanji**.

N4–N1 were extracted from the reference charts in the companion
[language-learning](https://github.com/MensuraMedia/language-learning)
repository — the project's authority for character data — rather than written
from memory. The charts give readings in wapuro romaji; conversion to kana is
mechanical and every one of the 789 distinct readings was verified by
converting back and comparing. Where a chart states a single reading it does
not say whether it is on' or kun', so the field is picked by a lexicon built
from the 664 explicit on/kun pairs; held out against the N1 pairs that rule
scored **94.6%**. Kanji cards are graded on the *meaning*, so a mislabelled
reading affects the reference rows on the card back and nothing scored.

One known source defect: the N1 chart gives 沌 the kun'yomi `yodmu`, which is
not a reading. It is dropped rather than guessed at.

Counts match the reference workbooks exactly. **58 tests** guard the data:
Hepburn traps (し=shi, ち=chi, つ=tsu, ふ=fu, じ=ji, を=wo, ん=n), forbidden
kunrei forms, Unicode block membership, reading conventions, no duplicates.

Difficulty keys: `hiragana:{gojuon,dakuon,handakuon,yoon,all}`, same for
katakana, and `kanji:N5`.

---

## 6. Scoring & scheduling

| Scheme | Award |
|---|---|
| `accuracy` | 10 flat |
| `speed` | `max(2, 20 − latency_ms // 250)` |
| `streak` | `10 × min(streak, 10)` |
| `srs` | `10 + 2 × min(reps, 5)`, advances SM-2 |

Wrong = 0. Skip = **−1** and resets the streak.

**SM-2**: first correct → 1 day, second → 6 days, thereafter `interval × ease`.
Wrong resets interval and reps, drops ease by 0.2 with a floor of 1.30.

---

## 7. HTTP API

All errors return `{"code", "message"}` with an appropriate status.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Dashboard |
| `GET` | `/study` | Study view |
| `GET` | `/games` | Memory games |
| `GET` | `/api/summary` | Every dashboard panel, one round trip |
| `GET` | `/api/segments` | Difficulty keys with live counts, plus challenge and scoring axes |
| `GET` | `/api/games` | Game catalogue with live board previews |
| `GET` | `/api/credits` | Attribution the active audio provider requires |
| `GET` | `/api/character/<id>` | Character detail plus recall history |
| `GET` | `/api/audio/<id>?voice=` | Pronunciation; always returns playable bytes |
| `POST` | `/api/session` | Start a session; `character_ids` overrides `difficulty` (the drill path) |
| `POST` | `/api/session/<id>/attempt` | Record an answer |
| `POST` | `/api/session/<id>/end` | Finalise |
| `POST` | `/api/game/board` | Deal a memory board |
| `POST` | `/api/game/mispair` | Record a wrong pairing |

---

## 8. Module reference

4,981 lines across 24 modules, zero import cycles. Full audit:
[STACK-VERIFICATION.md](STACK-VERIFICATION.md).

| Module | LOC | Responsibility |
|---|---:|---|
| `models` | 142 | Frozen dataclasses: `Character`, `CharacterSeed`, `Attempt`, `Session` |
| `config` | 153 | XDG-derived paths, `JP_*` env overrides |
| `db` | 347 | aiosqlite layer, schema, additive migrations, difficulty-key queries |
| `scoring` | 161 | Four schemes, SM-2 `next_review()` |
| `session` | 347 | Deck building, choice generation, attempt recording |
| `analytics` | 576 | 16 metric functions, deck shelves, session history |
| `games` | 214 | Board dealing for three modes, game catalogue |
| `audio` | 614 | Provider chain, caching, speech-text derivation |
| `audio_library` | 337 | Clip validation, manifest, cross-voice consistency |
| `tts_voicevox` | 263 | Local Japanese-native provider, accent extraction |
| `tts_elevenlabs` | 200 | Cloud fallback provider |
| `voicelab` | 412 | Audition / cost / build / verify / warm / speakers / accent |
| `routes.api` | 254 | JSON surface |
| `routes.views` | 25 | Three HTML views |
| `app` | 64 | Quart factory, DB lifecycle |
| `__main__` | 324 | CLI, pywebview shell, graceful fallback |
| `content/*` | 543 | Character data and loader |

---

## 9. Command line

```bash
python -m japanese_practice [--no-window] [--port N] [--host H] [--debug]
```

### Voice lab

```bash
python -m japanese_practice.voicelab cost       # estimate spend first
python -m japanese_practice.voicelab audition   # sample candidate voices
python -m japanese_practice.voicelab build      # render + validate a clip set
python -m japanese_practice.voicelab verify     # revalidate, rewrite manifest, review queue
python -m japanese_practice.voicelab warm       # pre-render locally via VOICEVOX
python -m japanese_practice.voicelab speakers   # list local VOICEVOX voices
python -m japanese_practice.voicelab accent 箸  # show the pitch contour
```

`build` is resumable and skips work already done — synthesis spend is
irreversible.

---

## 10. Configuration

Everything optional; all paths derived, none hard-coded.

| Variable | Default |
|---|---|
| `JP_DB_PATH` | `$XDG_DATA_HOME/japanese-practice/practice.db` |
| `JP_AUDIO_CACHE_DIR` | `…/japanese-practice/audio-cache` |
| `JP_HOST` · `JP_PORT` · `JP_DEBUG` | `127.0.0.1` · `8765` · off |
| `JP_VOICEVOX_URL` | `http://127.0.0.1:50021` |
| `JP_VOICEVOX_FEMALE` · `JP_VOICEVOX_MALE` | `30` (No.7 アナウンス) · `13` (青山龍星) |
| `JP_VOICEVOX_SPEED` | `0.85` |
| `ELEVENLABS_API_KEY` | none — falls back to `~/.config/japanese-practice/elevenlabs.key` |
| `JP_VOICE_FEMALE` · `JP_VOICE_MALE` | ElevenLabs voice ids |

---

## 11. Deliberately not built

Stated so the absences read as decisions, not oversights.

| Absent | Why |
|---|---|
| Joyo grades | The JLPT levels and the frequency tiers are both seeded; the Joyo school-grade axis is not, and no deck advertises it |
| Stroke counts beyond N5 | The reference charts do not carry them, so N4–N1 leave the field unset rather than filling it with guesses |
| Typed-recall mode | Planned. Until it exists, "mastery" means recognition at a 33% chance floor, not free recall |
| `recall`, `timed`, `listening`, `mixed` challenges | Stored and displayed but **not yet branched on** — they currently render as recognition |
| Accounts, sync, telemetry | Local-first by design |
| Negative marking | Belongs only in an opt-in exam mode; it depresses low-confidence learners |
| Character Runners | Evaluated and recommended against — highest build cost, lowest reading-per-minute |

Everything outstanding, with acceptance criteria: [ROADMAP.md](ROADMAP.md).
