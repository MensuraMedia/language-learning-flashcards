# Japanese Practice — Flash Card Desktop Application

**日本語練習** · A local desktop application for learning Hiragana, Katakana and
Kanji: multiple-choice flash cards, memory-training boards, native Japanese
pronunciation, and analytics that show precisely which characters are failing.

Built by [Mensura Media](https://github.com/MensuraMedia) · Companion to the
[language-learning](https://github.com/MensuraMedia/language-learning) worksheet
collection.

> **Licence: personal use only.** Commercial use, modification and
> redistribution require prior written consent — see [LICENSE](LICENSE).

---

## What it is

A **native desktop application** — its own window, not a browser tab — that runs
entirely on your machine. No account, no network, no telemetry.

The study loop:

1. A card shows **one character and nothing else**
2. Three options appear beside it — one correct, two drawn from characters that
   are genuinely confusable with it
3. Choosing scores automatically and flips the card, so a wrong answer still
   teaches
4. Every answer is recorded, and the dashboard shows what you keep missing

Printed flash cards do not know what you keep getting wrong. This does.

---

## Features

Full reference: **[docs/FEATURES.md](docs/FEATURES.md)**

| Area | Summary |
|---|---|
| **Study** | 3-option multiple choice, true 3D flip, skip, back/next navigation, adjustable pace, full keyboard control |
| **Memory games** | Match Up, Pelmanism, Confusion Drill — in all three scripts, unscored boards dealt from your weakest characters |
| **Audio** | 630 bundled clips in two voices, plus local Japanese-native VOICEVOX synthesis with editable pitch accent |
| **Analytics** | Per-character miss-rate heatmap, weakest-character drill queue, retention curve, mastery by group, leeches, streak calendar, session history |
| **Content** | Hiragana 104 · Katakana 104 · Kanji 1,245 across JLPT N5–N1 plus Top 200/500 by frequency — extracted from the reference workbooks |
| **Scoring** | Four schemes: accuracy, speed, streak, SM-2 spaced repetition |

---

## Status

Working and in daily use. **248 tests passing.**

| Component | State |
|---|---|
| Study cards, scoring, analytics | ✅ Complete |
| Memory games | ✅ Complete |
| Audio — bundled + VOICEVOX | ✅ Complete |
| Desktop window + browser mode | ✅ Complete |
| Kanji N4–N1 + frequency tiers | ✅ Complete — 1,245 characters, 17 decks |
| Typed-recall mode | ❌ Planned |
| Packaging (`.deb`, AppImage) | ❌ Planned |

Everything outstanding is tracked with acceptance criteria in
**[docs/ROADMAP.md](docs/ROADMAP.md)**.

---

## Getting started

### Requirements

- Linux, macOS or Windows · **Python 3.10+**
- A CJK font (`fonts-noto-cjk` on Debian/Ubuntu) for glyph rendering
- A WebKit runtime for the desktop window (`gir1.2-webkit2-4.0` on Debian/Ubuntu).
  Without it the app runs in browser mode instead — it does not fail.

### Install

```bash
git clone https://github.com/MensuraMedia/language-learning-flashcards.git
cd language-learning-flashcards

# --system-site-packages is required on Linux, or pywebview cannot find
# PyGObject and silently falls back to browser mode.
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e ".[dev]"
```

### Run

```bash
.venv/bin/python -m japanese_practice              # desktop window
.venv/bin/python -m japanese_practice --no-window  # browser mode
```

### Develop

```bash
.venv/bin/python -m pytest                  # 239 tests, ~3s
.venv/bin/python -m ruff check src/ tests/
.venv/bin/python -m black src/ tests/
```

### Optional — better pronunciation

The app ships 630 clips and works offline without any setup. For Japanese-native
synthesis with correct pitch accent, run a local
[VOICEVOX engine](https://github.com/VOICEVOX/voicevox_engine); the app detects
it automatically and falls through silently when it is absent. See
[docs/VOICEVOX-EVALUATION.md](docs/VOICEVOX-EVALUATION.md).

---

## Technology

Three runtime dependencies. **33 packages** in the entire closure, no build step,
no `node_modules`.

| Layer | Choice | Why not the alternative |
|---|---|---|
| Desktop shell | **pywebview** | Uses the OS WebView already present. Electron would ship a ~150 MB browser and a Node runtime for a UI of a few hundred KB. |
| Server | **Quart** (ASGI) | Flask's API with native `async`. Audio shells out to a subprocess and analytics runs multi-table SQL — both would block a WSGI worker. |
| Persistence | **SQLite** via `aiosqlite` | Single-user, local. Zero configuration, one file to back up. The analytics are genuinely relational. |
| Frontend | Server-rendered templates + vanilla ES modules | No bundler, no framework. The source that ships is the source that runs — which is what makes the same UI open unchanged in a browser. |
| Charts | Inline SVG built in JS | A charting library would be the largest dependency in the project and the only one needing a CDN or bundle step. |

Verified, not asserted — see
**[docs/STACK-VERIFICATION.md](docs/STACK-VERIFICATION.md)**: zero import cycles,
zero hard-coded platform paths, zero external network references in the shipped
frontend.

---

## Documentation

| Document | Contents |
|---|---|
| [FEATURES.md](docs/FEATURES.md) | Complete feature and function reference |
| [STACK-VERIFICATION.md](docs/STACK-VERIFICATION.md) | Stack, modularity and universality audit |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the system works; supportability |
| [ROADMAP.md](docs/ROADMAP.md) | Everything outstanding, with QA criteria |
| [TESTING.md](docs/TESTING.md) | Test suite structure and coverage gaps |
| [AUDIO.md](docs/AUDIO.md) · [VOICE-LAB.md](docs/VOICE-LAB.md) · [VOICEVOX-EVALUATION.md](docs/VOICEVOX-EVALUATION.md) | The audio pipeline end to end |
| [HANDOFF.md](docs/HANDOFF.md) | Session-to-session continuity |
| [BUILD-SPEC.md](docs/BUILD-SPEC.md) | Implementation contract |

---

## Attribution

Pronunciation audio generated with **VOICEVOX** — the application displays the
required speaker credit, and it must not be removed. Bundled clips were
synthesised with ElevenLabs. Character data derives from the MensuraMedia
`language-learning` reference set.

## Licence

**Personal use only.** Copyright © 2026 Mensura Media (メンスラ・メディア).
All rights reserved.

You may download, run and study this software for your own private learning.
**Commercial use, modification, redistribution and derivative works require
prior express written consent.** See [LICENSE](LICENSE) for the full terms,
including Section 7 on third-party materials that carry their own conditions.

This is a source-available, non-commercial licence. It is **not** an OSI
open-source licence.
