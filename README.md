# Japanese Practice — Flash Card Desktop Application

**日本語練習** · A local desktop application for learning Hiragana, Katakana and Kanji through interactive flash cards, with per-session scoring and long-term performance analytics.

Built by [Mensura Media](https://github.com/MensuraMedia) · Companion to the
[language-learning](https://github.com/MensuraMedia/language-learning) worksheet collection.

---

## What This Is

A **native desktop application** — its own window, not a browser tab — that turns
the printable flash-card sets from the `language-learning` workbooks into an
interactive, self-scoring study tool.

The core interaction is deliberately simple:

1. A card appears showing **one character and nothing else**
2. You recall the sound, then **click to flip**
3. The reverse shows the written reading and a **speaker icon** that plays the pronunciation
4. You mark it right or wrong, and the app records it

Everything else in the application — the dashboard, the challenge segments, the
analytics — exists to make that loop productive over months of study.

## Why It Exists

Printed flash cards do not know what you keep getting wrong. This application
tracks every card you have ever seen, surfaces the characters that are actually
failing, and lets you drill precisely those. It runs entirely on your machine —
no account, no network, no telemetry.

---

## Core Features

### Flash Cards
- **Character-only front face.** No hints, no romaji, no meaning — the recall test is honest.
- **True 3D flip animation** on click, not a fade or a swap.
- **Audio pronunciation** via a speaker control on the reverse face.
- **Hybrid audio:** bundled native-speaker clips for the fixed kana set, text-to-speech fallback for the open-ended Kanji vocabulary.
- Reverse face shows romaji for kana; English meaning plus **on'yomi** and **kun'yomi** for Kanji.

### Exercise Segments
Sessions are differentiated along three independent axes, so the same character
set can be drilled many ways:

| Axis | Options |
|---|---|
| **Challenge type** | Recognition · Recall · Timed · Listening · Mixed |
| **Scoring scheme** | Accuracy · Speed-weighted · Streak · Spaced repetition |
| **Difficulty** | Kana groups and JLPT/Joyo levels — see below |

### Difficulty Ladder
Levels follow the authentic structure of the writing system rather than an
arbitrary easy/medium/hard scale:

- **Kana track** — gojuon → dakuon → han-dakuon → yoon → full mixed set
- **Kanji track (JLPT)** — N5 → N4 → N3 → N2 → N1
- **Kanji track (Joyo)** — Grade 1 → Grade 6 → Secondary
- **Kanji volume tiers** — Top 200 → Top 500 → Complete

### Scoring & Analytics
- A score is recorded **every time** the application is run
- Landing dashboard shows performance across **every past session**, not just totals
- Accuracy trend over time, per-character-set breakdown, weak-character
  identification, streak tracking, and time-of-day performance

---

## Content Model

Character data follows the
[language-learning](https://github.com/MensuraMedia/language-learning) reference
sets exactly — no invented readings, no approximated counts.

| Set | Characters |
|---|---:|
| Hiragana ひらがな | 104 |
| Katakana カタカナ | 104 |
| Kanji — JLPT N5 | 107 |
| Kanji — JLPT N4 | 174 |
| Kanji — JLPT N3 | 394 |
| Kanji — JLPT N2 | 248 |
| Kanji — JLPT N1 | 382 |
| Kanji — Joyo complete | 1,521 |

Thematic groupings available as exercise segments: Numbers & Counting · People &
Family · Nature & Weather · Time & Calendar · Actions · Descriptions · Places.

Vocabulary topic sets: Days 曜日 · Months 月 · Numbers 数字 · Time 時間.

---

## Technology

| Layer | Choice | Rationale |
|---|---|---|
| Desktop shell | **pywebview** | Native window using the system WebKit runtime — no bundled browser, no Node dependency |
| Server | **Quart** (ASGI) | Async Flask-compatible API; non-blocking audio and database work |
| Language | **Python 3.10+** | |
| Persistence | **SQLite** via `aiosqlite` | Single-user local app; zero configuration |
| Frontend | Server-rendered templates + vanilla JS/CSS | No bundler, no framework lock-in — the same UI opens unchanged in any browser |
| Audio | Bundled clips + TTS fallback | Correct native pronunciation where it matters, coverage everywhere else |

**Design principle:** the application is a web app that happens to be delivered in
a native window. That keeps it cross-platform and browser-compatible by
construction rather than by effort.

---

## Design Language

Dark, technical, single-accent. Near-black grounds with layered gray panels, one
high-chroma accent carrying all emphasis, thin rules and small letter-spaced
labels, monospace numerals, and data-dense composition.

The Japanese glyph is always the visual hero — set large, with generous space,
in `Noto Sans CJK JP`.

Five complete design directions were prototyped as interactive mockups before any
application code was written. See [`mockups/`](mockups/) and
[`mockups/COMPARISON.md`](mockups/COMPARISON.md).

---

## Getting Started

> **Status: pre-implementation.** Design mockups are complete; the application
> itself is not yet built. The commands below describe the intended interface.

### Requirements
- Debian/Ubuntu Linux (other platforms planned — see Roadmap)
- Python 3.10 or newer
- `fonts-noto-cjk` for Japanese glyph rendering
- WebKit runtime (`gir1.2-webkit2-4.0` or equivalent) for the pywebview shell

### Install
```bash
git clone https://github.com/MensuraMedia/language-learning-flashcards.git
cd language-learning-flashcards
python3 -m venv .venv
.venv/bin/pip install -e .
```

### Run
```bash
# Native desktop window
.venv/bin/python -m japanese_practice

# Browser mode / headless
.venv/bin/python -m japanese_practice --no-window
```

### Develop
```bash
.venv/bin/python -m pytest                  # tests
.venv/bin/python -m ruff check .            # lint
.venv/bin/python -m black .                 # format
```

---

## Roadmap

### Phase 1 — Foundation ✅
- [x] Project scaffolding and standards adoption
- [x] Japanese content model locked to authoritative reference sets
- [x] Five interactive design directions prototyped
- [ ] Design direction selected

### Phase 2 — Core Application
- [ ] Quart application skeleton with pywebview shell
- [ ] SQLite schema: characters, sessions, attempts, scores
- [ ] Character data seeded for Hiragana and Katakana (104 each)
- [ ] Flash card component with 3D flip
- [ ] Single exercise loop end to end

### Phase 3 — Audio
- [ ] Audio playback layer with caching
- [ ] Bundled kana pronunciation clips
- [ ] TTS fallback engine and abstraction
- [ ] Listening-mode challenge type

### Phase 4 — Exercises & Scoring
- [ ] All five challenge types
- [ ] All four scoring schemes
- [ ] Full difficulty ladder across kana and Kanji
- [ ] Kanji sets: N5 through N1, Joyo grades

### Phase 5 — Analytics
- [ ] Per-session history dashboard
- [ ] Accuracy trend and retention curves
- [ ] Weak-character heatmap
- [ ] Streak and consistency tracking

### Phase 6 — Polish & Distribution
- [ ] Keyboard-only operation
- [ ] Accessibility pass
- [ ] Packaging: `.deb`, AppImage, PyPI
- [ ] Windows and macOS builds

---

## Future Features

Under consideration, not committed:

- **Spaced repetition (SRS)** — a proper SM-2 or FSRS scheduler so review timing adapts to individual retention
- **Stroke order animation** — animated stroke-by-stroke writing on the card reverse
- **Handwriting input** — draw the character and have it graded, closing the recall loop
- **Vocabulary and sentence mode** — extend beyond single characters into the themed sentence tables from the workbook collection
- **Custom decks** — user-defined character subsets and import/export
- **Progress export** — CSV/JSON dump of full study history
- **Multi-profile support** — several learners sharing one installation
- **Print bridge** — generate a printable worksheet from your weakest characters, closing the loop back to the original workbooks
- **Additional languages** — the architecture is script-agnostic; Korean Hangul and Chinese Hanzi are natural extensions

---

## Expectations & Scope

**What this application is:**
- A focused, offline, single-user study tool
- Honest about recall: no hints on the front face, no partial credit
- Backed by authentic reference data, not approximations

**What it is not:**
- Not a full Japanese course — it drills characters, it does not teach grammar
- Not a cloud service — there is no account, no sync, no server
- Not a spaced-repetition system on day one (see Future Features)

**Performance targets:**
- Card interactions under 100ms perceived latency
- Flip animation at 60fps
- Cold start under 2 seconds

**Data ownership:** all study history stays in a local SQLite file. Nothing is
transmitted anywhere.

---

## Project Documentation

| Document | Contents |
|---|---|
| [`docs/PROJECT-CONTEXT.md`](docs/PROJECT-CONTEXT.md) | Original brief, requirements decomposition, confirmed decisions |
| [`mockups/DESIGN-BRIEF.md`](mockups/DESIGN-BRIEF.md) | What every design direction had to demonstrate |
| [`mockups/COMPARISON.md`](mockups/COMPARISON.md) | Evaluation of the five directions and recommendation |
| [`mockups/_reference/JAPANESE-CONTENT-MODEL.md`](mockups/_reference/JAPANESE-CONTENT-MODEL.md) | Authoritative character sets, counts, terminology |
| [`CLAUDE.md`](CLAUDE.md) | Build commands and conventions |
| [`changelog.md`](changelog.md) | Append-only local change log |

---

## Related Projects

- **[language-learning](https://github.com/MensuraMedia/language-learning)** — the printable worksheet, reference chart and flash card collection this application is built from

## License

Free to use and distribute. Created by **Mensura Media** (メンスラ・メディア).
