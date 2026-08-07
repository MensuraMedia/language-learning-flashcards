# Build Specification — Japanese Practice v0.1

Binding contract for all implementation work. Every module implements exactly
these names, paths and signatures. Do not invent alternatives; if something is
underspecified, follow the nearest existing convention rather than redesigning.

Design direction: **05 Tactile Deck** (`mockups/05-tactile-deck.html`)
Analytics grafted from: **04 Data Studio** (`mockups/04-data-studio.html`)

---

## 1. Package layout

```
pyproject.toml
src/japanese_practice/
├── __init__.py            # __version__ = "0.1.0"
├── __main__.py            # CLI entry: pywebview shell, --no-window, --port
├── app.py                 # create_app() -> Quart
├── config.py              # Config dataclass, paths, env overrides
├── db.py                  # aiosqlite access layer
├── schema.sql             # DDL, executed on first run
├── models.py              # frozen dataclasses
├── scoring.py             # scoring schemes
├── session.py             # exercise session engine
├── analytics.py           # all learner-performance metrics
├── audio.py               # bundled clips + TTS fallback
├── content/
│   ├── __init__.py
│   ├── hiragana.py        # HIRAGANA: list[CharacterSeed]
│   ├── katakana.py        # KATAKANA: list[CharacterSeed]
│   ├── kanji_n5.py        # KANJI_N5: list[CharacterSeed]
│   ├── confusions.py      # CONFUSION_PAIRS: list[tuple[str, str]]
│   └── loader.py          # seed_content(db)
├── routes/
│   ├── __init__.py
│   ├── views.py           # HTML pages
│   └── api.py             # JSON API, blueprint prefix /api
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   └── study.html
└── static/
    ├── css/theme.css      # design tokens + components
    ├── js/dashboard.js
    ├── js/study.js
    └── audio/             # bundled clips (may be empty at first)
tests/
```

## 2. Design tokens (verbatim from mockup 05)

```css
--bg:#0d0d0f; --bg-deep:#09090b;
--panel:#16161a; --panel-2:#1c1c21; --panel-3:#23232a;
--line:#26262b; --line-2:#33333c; --line-3:#45454f;
--ink:#e8e8ee; --ink-2:#9a9aa6; --ink-3:#66666f; --ink-4:#4a4a53;
--amber:#f0b429; --amber-soft:rgba(240,180,41,.14); --amber-line:rgba(240,180,41,.34);
--card-hi:#262630; --card-lo:#15151a; --felt:#101014;
--ui: ui-sans-serif, system-ui, "Inter", "Segoe UI", Roboto, sans-serif;
--mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
--jp: "Noto Sans CJK JP", "Noto Sans JP", sans-serif;
--r-sm:6px; --ease:cubic-bezier(.2,.75,.25,1);
```

Amber is reserved for progress, live values and the flip. Never use it as a
general-purpose text or border colour.

## 3. Database schema (`schema.sql`)

SQLite, WAL mode, foreign keys on.

```sql
CREATE TABLE IF NOT EXISTS characters (
  id            INTEGER PRIMARY KEY,
  glyph         TEXT NOT NULL UNIQUE,
  script        TEXT NOT NULL,      -- 'hiragana' | 'katakana' | 'kanji'
  romaji        TEXT,               -- kana only
  meaning       TEXT,               -- kanji only
  onyomi        TEXT,               -- kanji only, katakana convention
  kunyomi       TEXT,               -- kanji only, hiragana convention
  kana_group    TEXT,               -- 'gojuon'|'dakuon'|'handakuon'|'yoon'
  jlpt_level    TEXT,               -- 'N5'..'N1'
  category      TEXT,               -- thematic grouping
  stroke_count  INTEGER
);

CREATE TABLE IF NOT EXISTS sessions (
  id            INTEGER PRIMARY KEY,
  started_at    TEXT NOT NULL,      -- ISO 8601 UTC
  ended_at      TEXT,
  challenge     TEXT NOT NULL,      -- recognition|recall|timed|listening|mixed
  scoring       TEXT NOT NULL,      -- accuracy|speed|streak|srs
  difficulty    TEXT NOT NULL,      -- level key, e.g. 'hiragana:gojuon'
  score         INTEGER DEFAULT 0,
  total         INTEGER DEFAULT 0,
  correct       INTEGER DEFAULT 0,
  max_streak    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS attempts (
  id            INTEGER PRIMARY KEY,
  session_id    INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  character_id  INTEGER NOT NULL REFERENCES characters(id),
  answered_at   TEXT NOT NULL,
  correct       INTEGER NOT NULL,   -- 0|1
  latency_ms    INTEGER,
  first_attempt INTEGER NOT NULL DEFAULT 1,
  given_answer  TEXT                -- for confusion analysis
);

CREATE TABLE IF NOT EXISTS review_state (
  character_id  INTEGER PRIMARY KEY REFERENCES characters(id),
  ease          REAL NOT NULL DEFAULT 2.5,
  interval_days REAL NOT NULL DEFAULT 0,
  due_at        TEXT,
  lapses        INTEGER NOT NULL DEFAULT 0,
  reps          INTEGER NOT NULL DEFAULT 0,
  last_seen     TEXT
);

CREATE INDEX IF NOT EXISTS idx_attempts_char    ON attempts(character_id);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at);
```

## 4. Models (`models.py`) — frozen dataclasses

```python
CharacterSeed(glyph, script, romaji=None, meaning=None, onyomi=None,
              kunyomi=None, kana_group=None, jlpt_level=None,
              category=None, stroke_count=None)
Character(id, glyph, script, romaji, meaning, onyomi, kunyomi,
          kana_group, jlpt_level, category, stroke_count)
Attempt(id, session_id, character_id, answered_at, correct, latency_ms,
        first_attempt, given_answer)
Session(id, started_at, ended_at, challenge, scoring, difficulty,
        score, total, correct, max_streak)
```

## 5. Difficulty keys

Format `script:group`. These are the only valid values:

```
hiragana:gojuon  hiragana:dakuon  hiragana:handakuon  hiragana:yoon  hiragana:all
katakana:gojuon  katakana:dakuon  katakana:handakuon  katakana:yoon  katakana:all
kanji:N5  kanji:N4  kanji:N3  kanji:N2  kanji:N1
kanji:top200  kanji:top500
```

## 6. `scoring.py`

```python
def score_attempt(scheme: str, *, correct: bool, latency_ms: int|None,
                  streak: int) -> int
```
- `accuracy` — 10 correct, 0 wrong
- `speed` — correct: `max(2, 20 - latency_ms // 250)`; wrong: 0
- `streak` — correct: `10 * min(streak, 10)`; wrong: 0
- `srs` — correct: `10 + 2 * reps_bonus`; wrong: 0, and schedule updated

```python
def next_review(ease: float, interval_days: float, reps: int,
                correct: bool) -> tuple[float, float, int]
```
SM-2 style. Wrong → interval 0, ease `max(1.3, ease - 0.2)`, reps 0.
Right → reps 1: 1 day; reps 2: 6 days; else `interval * ease`.

## 7. `analytics.py` — the learner-weakness apparatus

Every function is `async` and takes the db handle first. All return
JSON-serialisable structures.

```python
async def accuracy_by_session(db, limit=30) -> list[dict]
    # [{session_id, started_at, accuracy, total, challenge, difficulty}]

async def per_character_miss_rate(db, script=None) -> list[dict]
    # [{glyph, character_id, seen, missed, miss_rate, last_seen}] desc by miss_rate
    # miss_rate = missed / seen; only characters with seen >= 1

async def confusion_pairs(db, limit=20) -> list[dict]
    # [{glyph, mistaken_for, count}] derived from attempts.given_answer

async def retention_curve(db) -> list[dict]
    # [{days_since_last, accuracy, samples}] bucketed 0,1,2,3,7,14,30+

async def time_of_day_performance(db) -> list[dict]
    # [{hour, accuracy, attempts}] 0..23

async def weakest_characters(db, limit=12) -> list[dict]
    # miss_rate weighted by recency; actionable drill queue

async def latency_distribution(db, script=None) -> list[dict]
    # [{bucket_ms, count}] — hesitation signal, buckets 0-500,500-1k,1-2k,2-4k,4k+

async def streak_calendar(db, days=90) -> list[dict]
    # [{date, attempts, accuracy}] — consistency heat calendar

async def mastery_by_group(db) -> list[dict]
    # [{script, group, total, mastered, accuracy}]
    # mastered = seen >= 3 and miss_rate <= 0.15

async def leeches(db, limit=10) -> list[dict]
    # [{glyph, lapses, reps, miss_rate}] — repeatedly failed despite review

async def first_vs_eventual(db) -> dict
    # {first_attempt_accuracy, eventual_accuracy, gap}

async def progress_velocity(db, weeks=8) -> list[dict]
    # [{week_start, newly_mastered, cumulative}]

async def dashboard_summary(db) -> dict
    # aggregates everything above into one payload for the dashboard
```

## 8. API (`routes/api.py`, prefix `/api`)

```
GET  /api/summary                     -> dashboard_summary payload
GET  /api/segments                    -> available exercise segments
POST /api/session                     -> {challenge, scoring, difficulty} -> {session_id, cards[]}
POST /api/session/<id>/attempt        -> {character_id, correct, latency_ms, given_answer} -> {score, streak}
POST /api/session/<id>/end            -> final session record
GET  /api/character/<id>              -> character detail + its recall history
GET  /api/audio/<character_id>        -> audio bytes (bundled or TTS), audio/mpeg or audio/wav
```

All errors: `{"code": <str>, "message": <str>}` with an appropriate status.

## 9. `audio.py`

```python
async def get_audio(character: Character) -> tuple[bytes, str]
```
Resolution order:
1. Bundled clip at `static/audio/<script>/<glyph>.mp3`
2. Cached TTS at `<cache_dir>/<sha1>.wav`
3. Generate via TTS, cache, return

TTS backend is pluggable behind `_synthesize(text: str) -> bytes`. Try, in
order: `espeak-ng`, `pico2wave`, then a silent-wav stub so the app never breaks.
Never raise to the caller — return the stub on total failure.

## 10. Frontend

- `dashboard.html` — deck shelf (tactile-deck metaphor) + the analytics panels
- `study.html` — the card with true 3D flip, keyboard operable
- Flip: `transform: rotateY(180deg)` with `backface-visibility: hidden`,
  `transition: transform .55s var(--ease)`
- **Front face renders the glyph and nothing else.** No romaji, no meaning, no hint.
- Back face: reading + inline-SVG speaker button
- Keyboard: `Space` flip · `J` correct · `F` wrong · `Esc` end session
- No framework, no bundler, no external requests. Vanilla ES modules only.

## 10a. Corrections carried from the mockup review

Two findings from the design critique that MUST be applied to the build:

1. **Never render Japanese text in `--mono`.** Mockup 05 set kanji readings
   (`セイ / い(きる)`) in `var(--mono)`, a stack with no CJK member — the glyphs
   fall back unpredictably and can render as tofu. `--mono` is for **numerals
   only**. Every Japanese character, including all readings, uses `--jp`.

2. **The drill loop is a required feature, not a nice-to-have.** The analytics
   must be actionable: clicking a cell in the per-character miss-rate heatmap, or
   a row in the weakest-characters table, starts a session built from exactly
   those characters. This is what makes the dashboard a diagnostic tool rather
   than a report.

   API support: `POST /api/session` accepts an optional `character_ids: list[int]`
   which, when present, overrides `difficulty` and builds the deck from exactly
   those characters. The session records `difficulty` as `drill:custom`.
   The study view shows a breadcrumb naming the panel the drill came from.

## 11. Quality bar

- All Quart handlers `async def`; never block the loop
- Type hints on every public function
- `black` formatting, `ruff` clean
- Tests for `scoring.py`, `analytics.py` and the API happy paths
- The app must start and serve a working dashboard with seeded data
