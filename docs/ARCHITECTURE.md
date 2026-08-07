# System Architecture — Japanese Practice

How the application works, why it is built this way, and what that buys you in
supportability, applicability and universality.

> **Status:** describes the v0.1 architecture as specified in
> [BUILD-SPEC.md](BUILD-SPEC.md). Implementation status is tracked in the
> [README roadmap](../README.md#roadmap).

---

## 1. What the system is, in one paragraph

A local-first study application. A Quart (ASGI) server runs on `127.0.0.1`,
serves a small server-rendered web UI, and persists every answer to a SQLite
file in the user's home directory. A pywebview window hosts that UI using the
operating system's own WebKit runtime, so the application looks and behaves like
a native desktop program while remaining, underneath, an ordinary web
application. Nothing leaves the machine.

```
┌──────────────────────────────────────────────────────────┐
│  pywebview window  (system WebKit — no bundled browser)   │
│  ┌────────────────────────────────────────────────────┐   │
│  │  dashboard.html / study.html                       │   │
│  │  vanilla ES modules · inline SVG charts · theme.css│   │
│  └───────────────────┬────────────────────────────────┘   │
└──────────────────────┼────────────────────────────────────┘
                       │  HTTP  127.0.0.1:8731
┌──────────────────────┴────────────────────────────────────┐
│  Quart (ASGI)                                              │
│  routes/views.py ── HTML     routes/api.py ── JSON         │
│         │                          │                       │
│    session.py ── scoring.py   analytics.py    audio.py     │
│         └──────────┬───────────────┘              │        │
│                   db.py (aiosqlite)          espeak-ng /   │
│                    │                          pico2wave    │
└────────────────────┼───────────────────────────────────────┘
                     │
         ~/.local/share/japanese-practice/practice.db
```

## 2. Technology choices and why

| Layer | Choice | Why this and not the alternative |
|---|---|---|
| Desktop shell | **pywebview** | Uses the OS WebKit/WebView2 already present. An Electron build would ship a ~150MB browser and a Node runtime for a UI that is a few hundred KB. A native GTK/Qt UI would mean rewriting the interface per platform and abandoning browser compatibility. |
| Server | **Quart** | Flask's API with native `async`. Audio synthesis shells out to a subprocess and analytics runs multi-table SQL — both would block a WSGI worker. Flask-compatible means the ecosystem and idioms transfer directly. |
| Persistence | **SQLite** via `aiosqlite` | Single-user local app. Zero configuration, zero daemon, one file the user can copy or back up. The analytics are genuinely relational — miss rates, confusion pairs and retention curves are joins and aggregates, which is exactly what SQL is for. |
| Frontend | **Server-rendered templates + vanilla ES modules** | No bundler, no `node_modules`, no build step. The source that ships is the source that runs. This is what makes the same UI open unchanged in a browser, which is the brief's cross-platform requirement satisfied by construction rather than by porting effort. |
| Charts | **Inline SVG built in JS** | A charting library would be the single largest dependency in the project and the only one requiring a CDN or bundle step. The charts needed here — line, bar, heatmap grid, calendar — are tens of lines of SVG each. |
| Audio | **Bundled clips + TTS fallback** | The kana set is small and fixed, so real recordings are practical and give correct native pronunciation. Kanji vocabulary is open-ended, where bundling every reading is not practical — TTS covers the tail. |

**The unifying principle:** the application is a web app that happens to be
delivered in a native window. Every choice above follows from refusing to
duplicate work across the desktop and browser cases.

## 3. Request lifecycle

**Startup.** `__main__.py` parses arguments, builds the `Config`, and calls
`create_app()`. A `before_serving` hook opens the SQLite connection, enables WAL
and foreign keys, executes `schema.sql` (idempotent `CREATE TABLE IF NOT
EXISTS`), and seeds character content. The server starts on a background loop;
pywebview then opens a window pointed at it. With `--no-window`, the server runs
in the foreground and prints its URL.

**A study session.**

1. `POST /api/session` with `{challenge, scoring, difficulty}`
2. `session.build_deck()` selects cards for that difficulty key. Under `srs`
   scoring it prioritises due cards from `review_state`, then unseen cards, then
   the weakest by miss rate
3. A `sessions` row is created; the deck is returned to the client
4. The client shows one glyph, alone. The user flips, self-marks, and each answer
   `POST`s to `/api/session/<id>/attempt`
5. The server writes an `attempts` row, computes the awarded score via
   `scoring.score_attempt()`, and — under `srs` — advances `review_state` through
   `scoring.next_review()`
6. `POST /api/session/<id>/end` finalises totals

**The dashboard.** `GET /api/summary` calls `analytics.dashboard_summary()`,
which runs every metric query and returns one payload. The client renders it
into SVG. One round trip, no waterfall.

## 4. Data model

Four tables, described fully in [BUILD-SPEC.md](BUILD-SPEC.md#3-database-schema-schemasql).

- **`characters`** — the content. Seeded from `content/`, keyed by glyph.
  Carries `kana_group` and `jlpt_level`, which are what the difficulty ladder
  actually selects on.
- **`sessions`** — one row per study run. This is what satisfies "a score is
  recorded each time the user runs the application."
- **`attempts`** — one row per answer. The atom of the whole analytics layer.
  `latency_ms` enables hesitation analysis; `given_answer` enables confusion
  detection; `first_attempt` separates recall from eventual recognition.
- **`review_state`** — SM-2 scheduling state per character.

**Why `attempts` is append-only:** every metric is derived, never stored. Miss
rates, retention curves and confusion pairs are computed from raw attempts at
query time. Adding a new metric later requires no migration and no backfill — the
history is already there. This is the single most important structural decision
in the schema.

## 5. The analytics engine

This is the part that makes the application worth using over paper cards. Paper
does not know what you keep getting wrong.

| Metric | What it computes | What it tells the learner |
|---|---|---|
| **Per-character miss rate** | `missed / seen` per glyph, worst first | The headline weakness view — exactly which characters are failing |
| **Confusion pairs** | Mines `given_answer` against the correct glyph | *What* a character is being mistaken for. シ/ツ and ソ/ン are the classic traps; knowing the pair is far more actionable than knowing the character is hard |
| **Weakest characters** | Recency-weighted miss rate | A drill queue. Missing something yesterday matters more than missing it a month ago |
| **Retention curve** | Accuracy bucketed by days since that character was last seen | Where personal forgetting sets in — the empirical basis for review intervals |
| **Latency distribution** | Histogram of response times | The gap between *knowing* and *recalling*. A correct answer after 4 seconds is not mastery |
| **Time-of-day performance** | Accuracy by hour | When study actually works for this person |
| **Streak calendar** | Attempts and accuracy per day, 90 days | Consistency, which predicts retention more than session length |
| **Mastery by group** | Per `kana_group` and per JLPT level | Progress against the real structure of the writing system |
| **Leeches** | High `lapses` relative to `reps` | Characters repeatedly learned and re-forgotten — these need a different strategy, not more repetition |
| **First vs eventual accuracy** | First-attempt accuracy against overall | Whether the learner genuinely recalls or is pattern-matching within a session |
| **Progress velocity** | Newly-mastered characters per week | Trajectory, and whether it is flattening |
| **Accuracy by session** | Per-session trend | The top-level story over time |

Mastery threshold: `seen >= 3 AND miss_rate <= 0.15`. Deliberately conservative —
three exposures is the minimum at which a rate means anything.

**Empty-database behaviour is a hard requirement.** Every function returns a
sensible empty structure on a fresh install. No division by zero, no crash, no
`None` leaking into the UI.

## 6. Audio pipeline

Three-stage resolution, each falling through to the next:

1. **Bundled clip** — `static/audio/<script>/<glyph>.mp3`
2. **Cached synthesis** — `<cache_dir>/<sha1(text, backend)>.wav`
3. **Fresh synthesis** — `espeak-ng` → `pico2wave` → silent-WAV stub

The stub matters: on a machine with no TTS installed, the speaker button still
returns valid audio and the UI does not error. **`get_audio()` never raises.**
Audio is a nice-to-have; it must never be able to break a study session.

Subprocess work goes through `asyncio.create_subprocess_exec`, never a blocking
call, because synthesis takes long enough to stall other requests.

## 7. Supportability

**Failure modes are designed to degrade, not stop.**

| Failure | Behaviour |
|---|---|
| pywebview missing or no WebKit | Warns, falls back to server-only mode; the UI is reachable in a browser |
| No TTS backend installed | Silent-WAV stub; everything else works |
| No bundled audio clips | TTS path; everything else works |
| Empty database | Dashboard renders a first-run empty state |
| Corrupt database | SQLite file is a single artifact — delete it and the app reseeds from scratch |

**Diagnosis.** All state is in one SQLite file at
`~/.local/share/japanese-practice/practice.db`, inspectable with any SQLite
client. There is no hidden state, no cache to invalidate, no server-side
session. `--no-window --debug` runs the whole stack in a terminal with tracebacks
and reload.

**The dependency surface is deliberately tiny** — Quart, aiosqlite, pywebview.
No transitive JavaScript tree, no bundler, no lockfile drift. The most common
class of "it broke and nobody changed anything" simply cannot occur here.

**Data portability.** Copy the `.db` file to move or back up a full study
history. No export tooling required.

## 8. Applicability

**Who it fits:** a self-directed learner drilling the writing system, who wants
their history to stay on their own machine and wants to know precisely where
they are weak.

**Where it fits less well:** it drills characters. It does not teach grammar, and
it is not a full course. It is single-user by design — multi-profile support is
on the roadmap, not in v0.1. It has no sync; that is a deliberate consequence of
local-first, not an oversight.

**Deployment contexts it supports today:**
- Desktop application (pywebview window)
- Local browser (`--no-window`, open the URL)
- Headless/server (`--no-window --host 0.0.0.0` on a trusted network — note there
  is no authentication, so do not expose it beyond that)

## 9. Universality

Four distinct senses, all of which the brief asked for:

**Cross-platform.** The Python stack is platform-neutral. pywebview abstracts
GTK/WebKit on Linux, WebView2 on Windows and WKWebView on macOS. The only
platform-specific pieces are the optional TTS binaries, and those are behind a
fallback chain.

**Cross-browser.** Because the UI is plain HTML/CSS/ES modules with no build
step and no framework, it runs in any modern engine. There is no transpilation
target to get wrong. The desktop window and a browser tab load the identical
assets.

**Script-agnostic.** The `characters` table stores a glyph plus optional
readings and grouping metadata. Nothing in the schema, the scoring, the session
engine or the analytics is specific to Japanese — `script`, `kana_group` and
`jlpt_level` are just strings. Adding Korean Hangul or Chinese Hanzi means adding
a content module and difficulty keys; the entire engine is reused unchanged. This
is why the analytics were built over a generic `attempts` table rather than
kana-specific columns.

**Accessibility and input universality.** Full keyboard operation is a
first-class requirement, not a retrofit — `Space` flip, `J` correct, `F` wrong,
`Esc` end. Focus-visible states are in the stylesheet. Charts are SVG, so they
scale without resampling.

## 10. Extending the system

**Add a character set:** write a module in `content/`, add its seeds to
`loader.py`, add difficulty keys. Nothing else changes.

**Add a challenge type:** extend the allowed values in `session.py` and add the
client-side interaction. Scoring and analytics are unaffected.

**Add a scoring scheme:** add a branch to `scoring.score_attempt()`. Sessions
record the scheme name, so history stays interpretable.

**Add an analytics metric:** write one async function in `analytics.py` and one
render function in `dashboard.js`. Because `attempts` is append-only and
complete, new metrics apply retroactively to all existing history.

**Replace the TTS backend:** implement `_synthesize()`. Nothing else touches it.

## 11. Related documents

| Document | Contents |
|---|---|
| [BUILD-SPEC.md](BUILD-SPEC.md) | Binding implementation contract — paths, signatures, schema |
| [PROJECT-CONTEXT.md](PROJECT-CONTEXT.md) | Original brief and confirmed decisions |
| [../mockups/DESIGN-BRIEF.md](../mockups/DESIGN-BRIEF.md) | What each design direction had to demonstrate |
| [../mockups/_reference/JAPANESE-CONTENT-MODEL.md](../mockups/_reference/JAPANESE-CONTENT-MODEL.md) | Authoritative character data |
| [../CLAUDE.md](../CLAUDE.md) | Build commands and conventions |
