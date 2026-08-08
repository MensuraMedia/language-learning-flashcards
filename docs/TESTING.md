# Testing — Japanese Practice

How the suite is built, what each layer proves, and why it is shaped this way.

- **Last run:** 2026-08-06 · **193 passed, 0 failed** · 1.49s
- **Lint:** `ruff` clean · `black` clean (25 files)

---

## 1. Running it

```bash
cd /home/user/projects/japanese_practice

.venv/bin/python -m pytest                  # whole suite
.venv/bin/python -m pytest -q               # quiet
.venv/bin/python -m pytest tests/test_analytics.py -v
.venv/bin/python -m pytest -k "confusion"   # by name
.venv/bin/python -m pytest --durations=10   # slowest tests
```

Lint and formatting, both enforced by the `PostToolUse` hook in
[`.claude/settings.json`](../.claude/settings.json) on every Python edit:

```bash
.venv/bin/python -m ruff check src/ tests/
.venv/bin/python -m black --check src/ tests/
```

Configuration lives in [`pyproject.toml`](../pyproject.toml): `asyncio_mode = "auto"`,
so `async def` tests need no per-test decorator.

---

## 2. The suite at a glance

| File | Tests | Lines | Layer | What it proves |
|---|---:|---:|---|---|
| [`tests/conftest.py`](../tests/conftest.py) | — | 104 | fixtures | Isolation: every test gets a throwaway DB and data dir |
| [`tests/test_scoring.py`](../tests/test_scoring.py) | **35** | 186 | pure functions | Four scoring schemes and SM-2 scheduling are exactly right |
| [`tests/test_content.py`](../tests/test_content.py) | **59** | 259 | data | No Japanese character teaches something false; documented totals match the seed set |
| [`tests/test_analytics.py`](../tests/test_analytics.py) | **37** | 520 | SQL | Every metric computes correctly, and survives an empty DB |
| [`tests/test_api.py`](../tests/test_api.py) | **47** | 648 | HTTP | The whole stack works end to end — choices, skip scoring, per-script boards, volume tiers, kanji option readings |
| [`tests/test_audio_library.py`](../tests/test_audio_library.py) | **20** | 224 | assets | No silent, truncated or corrupt clip reaches a learner |
| [`tests/test_userdata.py`](../tests/test_userdata.py) | **16** | 184 | profiles & data | One learner's history never appears in another's; an export round-trips; a reset cannot fire unconfirmed |
| [`tests/test_kana.py`](../tests/test_kana.py) | **3** | 61 | transliteration | Every seeded reading converts to romaji with no kana left behind |
| [`tests/test_profiles.py`](../tests/test_profiles.py) | **2** | 26 | pure functions | A profile name always yields a usable filename |
| [`tests/test_voicelab.py`](../tests/test_voicelab.py) | **14** | 129 | tooling | The voice pipeline's commands behave |
| [`tests/test_voicevox.py`](../tests/test_voicevox.py) | **14** | 139 | provider | Local synthesis and pitch accent, and the absent-engine path |

**290 tests, ~5 seconds.** The parametrised cases mean the count exceeds the
number of `def test_` functions.
| **Total** | **193** | **1,643** | | |

The distribution is deliberate. **Content has the most tests despite being the
simplest code**, because it carries the highest consequence — see §4.

---

## 3. Isolation strategy

Every test runs against a fresh SQLite file under pytest's `tmp_path`. Nothing
in the suite can read or write the real database at
`~/.local/share/japanese-practice/practice.db`.

| Fixture | Provides | Used by |
|---|---|---|
| `config` | `Config` pointed entirely at `tmp_path` | everything |
| `db` | Connected, schema applied, **no content** | analytics empty-state tests |
| `seeded_db` | 6 hand-written characters across 3 scripts | analytics behaviour tests |
| `iso` | Deterministic ISO-8601 timestamps N days ago | anything time-dependent |
| `app` | Quart app wired to the temp DB | API tests |

**Why `seeded_db` is hand-written rather than the real content modules:** with 6
known characters a test can assert `seen == 4, missed == 3, miss_rate == 0.75`.
Against the full 315-character set the same test could only assert "returns
something", which proves nothing. Six characters is enough to cover three
scripts, two kana groups, and a kanji with both readings.

The API fixture uses Quart's `test_app()` context so **`before_serving` actually
runs** — the tests exercise the real startup path that opens the database,
applies `schema.sql` and seeds content, rather than a hand-assembled substitute.

---

## 4. Layer 1 — content integrity (58 tests)

This is the highest-stakes suite in the project, and the reason it is the
largest. A wrong reading here **crashes nothing**. It silently teaches a learner
something false, and they carry the error for months.

Everything is asserted against
[`mockups/_reference/JAPANESE-CONTENT-MODEL.md`](../mockups/_reference/JAPANESE-CONTENT-MODEL.md),
derived from the [MensuraMedia/language-learning](https://github.com/MensuraMedia/language-learning)
workbooks.

| Check | Guards against |
|---|---|
| Exact set sizes (104 / 104 / 107) | Silent truncation of a character set |
| Kana group split (46 / 20 / 5 / 33) | A character filed under the wrong group, breaking difficulty selection |
| Unicode block membership | A katakana glyph sitting in the hiragana list |
| No duplicate glyphs | Copy-paste during data entry |
| No glyph in two scripts | The same mistake, across files |
| Hepburn traps (し=shi, ち=chi, つ=tsu, ふ=fu, じ=ji, を=wo, ん=n) | The single most common romanisation error |
| Forbidden kunrei forms (si/ti/tu/hu/zi/sya…) | A different romanisation system leaking in |
| Yoon are two-character digraphs | きゃ recorded as a single character |
| Kana carry no kanji fields | Schema confusion between scripts |
| On'yomi in katakana, kun'yomi in hiragana | The reading convention inverted |
| Spot-check 水/山/人 against the reference | Wholesale data drift |
| Stroke counts within 1–30 | Typos in numeric fields |
| Confusion pairs reference real glyphs | Dangling references |
| Classic pairs シ/ツ and ソ/ン present | The canonical traps being missed |

**Result: all 58 pass.** The content modules are clean as written — no data
corrections were needed.

---

## 5. Layer 2 — scoring and scheduling (35 tests)

Pure functions, no I/O, so every case asserts an **exact** value rather than a
range or a property.

| Scheme | Rule | Tested at |
|---|---|---|
| `accuracy` | Flat `BASE_AWARD` | Fastest and slowest answers score identically |
| `speed` | `SPEED_MAX - latency // 250`, floored | 0ms, 250ms, 1s, 2.5s, 100s, negative |
| `streak` | `10 × min(streak, 10)` | 1, 5, 10, 99 — cap verified against the constant |
| `srs` | `10 + 2 × min(reps, 5)` | 0, 1, 5, 50 — plus the `reps`-absent fallback |
| *all four* | Wrong answer scores 0 | Parametrised across every scheme |

SM-2 scheduling, both paths:

| Path | Expected | Why it matters |
|---|---|---|
| 1st correct | interval → 1 day | Ladder entry point |
| 2nd correct | interval → 6 days | Fixed second step |
| 3rd+ correct | `interval × ease` | Compounding verified across two reviews (6 → 15 → 37.5) |
| Correct | ease unchanged | A right answer must never move ease |
| Wrong | interval → 0, reps → 0, ease − 0.2 | Lapse resets progress |
| Repeated wrong | ease floors at **1.30** | Prevents a card becoming unschedulable |
| Lapse then correct | restarts at 1 day, **not** 30 | The subtlest rule in the module |
| Negative inputs | clamped, not propagated | Defensive against bad client data |

---

## 6. Layer 3 — analytics (41 tests)

Real SQL against real rows. The metrics are the product's reason to exist, so
each is asserted against a history whose answer is known by construction.

### Empty-database contract

**Nine tests** assert a fresh install returns sensible empty structures rather
than crashing or dividing by zero. This is a hard requirement: the first thing
a new user sees is a dashboard with no data behind it.

| Function | Empty behaviour |
|---|---|
| 8 list metrics (parametrised) | `[]` |
| `retention_curve` | All 7 buckets present, `samples: 0` — the axis must not collapse |
| `time_of_day_performance` | All 24 hours present |
| `latency_distribution` | All 5 buckets present |
| `first_vs_eventual` | Zeros, no `ZeroDivisionError` |
| `dashboard_summary` | All 13 keys present |

### Behavioural assertions

| Metric | Asserted |
|---|---|
| **Per-character miss rate** | 3 of 4 wrong → exactly `0.75`; sorted worst-first; unseen characters excluded; `script=` filter works |
| **Confusion pairs** | Counts what a glyph is mistaken *for*; ignores correct answers and null answers; **resolves a romaji answer (`"tsu"`) back to its glyph (つ)** |
| **Accuracy by session** | Computed per session, ordered oldest-first, empty sessions skipped, `limit` honoured |
| **Latency** | 100/600/1500/3000/9000ms land in five distinct buckets; untimed attempts ignored |
| **Time of day** | Two attempts at 09:00 → `accuracy 0.5` at hour 9 |
| **Weakest characters** | Perfect characters excluded; **a miss today outranks an identical miss 120 days ago** |
| **Streak calendar** | Grouped by day; the 90-day window excludes older attempts |
| **Mastery** | Requires *both* `seen ≥ 3` **and** `miss_rate ≤ 0.15` — all three failure modes tested separately; untouched groups still report `0/N` |
| **Leeches** | Surfaces 6 lapses, excludes 1 lapse (below threshold) |
| **First vs eventual** | first `0.5`, eventual `0.75`, gap `0.25` |
| **Retention curve** | Reviews 7 days then 1 day apart land in the 7d and 1d buckets |
| **Totals** | Aggregate across sessions and attempts |

The recency-weighting test is the one worth keeping: it is the difference
between a drill queue that reflects *what is failing now* and one that
resurfaces characters the learner fixed months ago.

---

## 7. Layer 4 — HTTP surface (21 tests)

Real requests through Quart's test client.

| Group | Tests |
|---|---|
| **Views** | Dashboard renders; study view carries the full `.deck3d > .tilt > .lift > .card3d` scaffold |
| **Front-face purity** | The `.face front` markup contains **no** reading, meaning or speaker element — parsed out of the HTML and asserted |
| **`.view on` regression** | Asserts the class is present, because without it the entire page is invisible while the API returns 200s |
| **Segments** | Live counts (46 / 104 / 104 / 107); all three axes exposed; unseeded difficulties omitted |
| **Session lifecycle** | Create → attempt → attempt → end, asserting the exact score/streak/total payload at each step |
| **Streak reset** | A wrong answer sets streak to 0 |
| **Scoring scheme** | `streak` scheme with streak 4 awards exactly 50 |
| **Drill path** | `character_ids` overrides `difficulty`; deck matches exactly; recorded as `drill:custom` |
| **Analytics feedback** | An attempt posted through the API appears in `/api/summary` miss rate *and* confusion pairs |
| **Character detail** | Returns the character plus its recall history |
| **Audio** | Always 200 with playable bytes; WAV responses start with `RIFF` |
| **Errors** | Unknown difficulty / challenge / scheme → 400; missing `character_id` → 400; unknown session → 400; unknown character → 404; **all errors share the `{code, message}` shape** |

Three of these are **regression tests for bugs found during development** — the
front-face purity check, the `.view on` check, and the study-view scaffold
check. Each corresponds to a defect documented in
[`HANDOFF.md` §4](HANDOFF.md#4-bugs-found-and-fixed-do-not-reintroduce).

---

## 8. What is *not* covered

Stated plainly, because an unqualified "155 passing" would overstate it.

| Gap | Why | Mitigation |
|---|---|---|
| **Frontend JavaScript** | No JS test runner; no `node` on this machine | Rendering verified manually in the pywebview window |
| ~~Keyboard controls~~ | — | **Verified 2026-08-06** with `xdotool` against the live window: every key in the map exercised |
| **The 3D flip animation** | CSS transform, not assertable from Python | Verified visually — front and back faces both captured |
| **ElevenLabs API** | No API key available | Fallback path verified; the live call has **never run** |
| **pywebview window lifecycle** | Needs a display server | Verified manually on `DISPLAY=:0` |
| **Concurrency / locking** | Single-user local app | Deferred |
| **Coverage measurement** | `pytest-cov` not installed | Add it and set a floor |

---

## 9. Design principles used

1. **Assert exact values, not shapes.** `miss_rate == 0.75`, not
   `isinstance(miss_rate, float)`. A test that cannot fail is not a test.
2. **Build fixtures small enough to reason about.** Six characters, not 315.
3. **Test the empty case for everything.** A fresh install is the state every
   user starts in, and the one most easily forgotten.
4. **Parametrise the shared rules.** "Wrong answers score zero" is one test
   across four schemes, not four near-identical tests.
5. **Turn every fixed bug into a test.** Three of the API tests exist only
   because those bugs happened once.
6. **Exercise the real startup path.** `test_app()` runs `before_serving`, so
   the seeding and schema code is covered rather than bypassed.
7. **Name the consequence, not the mechanism.**
   `test_weakest_characters_weights_recent_misses_higher` says why it matters;
   `test_weakest_2` would not.

---

## 10. Related documents

| Document | Purpose |
|---|---|
| [`HANDOFF.md`](HANDOFF.md) | Session-to-session continuity; verified-vs-unverified status |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | How the system works; stack rationale |
| [`BUILD-SPEC.md`](BUILD-SPEC.md) | Binding implementation contract the tests assert against |
| [`AUDIO.md`](AUDIO.md) | Audio chain and ElevenLabs configuration |
| [`JAPANESE-CONTENT-MODEL.md`](../mockups/_reference/JAPANESE-CONTENT-MODEL.md) | Authoritative character data — the content suite's source of truth |
