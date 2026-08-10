# Release notes

What changed, why, and what it cost. Newest first. Every figure here was
measured against the working tree rather than recalled; where something is
unverified it says so.

For what the application *does*, see [FEATURES.md](FEATURES.md). For what is
still outstanding, see [ROADMAP.md](ROADMAP.md).

---

## 2026-08-08 — Content, organisation and ownership

The largest cycle so far. Three commits: `fe74ff9`, `bf3a4a5`, `354b011`.

### Headline numbers

| Measure | Before | After | Change |
|---|---:|---:|---|
| Characters seeded | 315 | **1,459** | +1,144 |
| Kanji | 107 | **1,251** | +1,144 |
| Study decks | 11 offered | **17** | +6 |
| Memory boards | 3 | **9** | +6 |
| Confusion pairs | 45 | **84** | +39 |
| HTTP endpoints | 14 | **23** | +9 |
| Python modules | 24 | **32** | +8 |
| Python lines | 4,981 | **7,473** | +2,492 |
| Frontend JS lines | 1,259 | **1,679** | +420 |
| Tests | 239 | **290** | +51 |

---

### 1. Study pace

**What.** A five-step slider under the answer options scaling how long a verdict
stays on screen before the next card.

**Why.** The default holds (1.9 s correct, 2.9 s wrong) suit someone meeting a
character for the first time. A learner who already knows the deck was being held
at beginner timing for twenty cards, which is the difference between a drill and
a chore.

| Step | Name | Factor | Correct | Wrong |
|---:|---|---:|---:|---:|
| 1 | relaxed | 1.00× | 1,900 ms | 2,900 ms |
| 2 | steady | 0.70× | 1,330 ms | 2,030 ms |
| 3 | brisk | 0.50× | 950 ms | 1,450 ms |
| 4 | fast | 0.35× | 665 ms | 1,015 ms |
| 5 | relentless | 0.20× | 380 ms | 580 ms |

**Decisions.** Holds floor at **260 ms** — below that the verdict colour is not
perceptible, and the entire purpose of the hold is that a wrong answer can be
read. Skip keeps its own 250 ms constant and does not scale, because there is no
verdict to read. Persisted as `jp.pace`; `[` and `]` step it.

**Also.** The keymap recital under the control row was removed — the shortcuts
panel already covers it — leaving a centred `? shortcuts` link. The slider was
centred by measurement: 31 px above, 32 px below, at 1280×860.

> **Not fully verified.** The step table is computed from the constants in
> `study.js`. One end-to-end hold was measured in the running window — 355 ms at
> *relentless* against a computed 380 ms. The slower holds were not measured;
> the screenshot-polling harness available here is too coarse to time them.

---

### 2. Kanji content: 107 → 1,251

**What.** JLPT N4, N3, N2 and N1 seeded — 1,138 new characters.

**Source.** Extracted from the reference charts in the companion
[language-learning](https://github.com/MensuraMedia/language-learning)
repository, which is this project's authority for character data. **Not written
from memory.** Reciting 1,138 kanji with readings would have produced confident,
plausible, unverifiable data — the worst possible outcome for a learning tool.

**Extraction pipeline.**

| Stage | Method | Result |
|---|---|---|
| 1. Text | `pdftotext -layout` on four reference charts | Column-aligned grids preserved |
| 2. Parse | Column-aware parser matching each token to the glyph whose centre it sits under | N4 174/174 · N3 397 · N2 248/248 · N1 376 |
| 3. Merge | Reference grid supplies readings + full meanings; themed pages supply categories | Meanings no longer truncated to column width |
| 4. Romaji → kana | Mechanical conversion, wapuro convention | **789/789 readings round-tripped** back to identical romaji |
| 5. Dedup | Each glyph assigned to the easiest level that lists it | 1,138 after removing cross-level overlap |

**The on/kun problem.** Charts write readings as `kei/ani` — on'yomi then
kun'yomi. But **530 entries give only one reading and do not say which kind it
is** (the N2 chart gives one for every character). Guessing silently was not
acceptable, so the field is chosen by a lexicon built from the **664 explicit
on/kun pairs** across all five levels, with a Sino-Japanese shape rule as
fallback.

That rule was **held out against the N1 pairs and scored 94.6%** (onyomi 98.6%,
kunyomi 90.5%). On ~530 single-reading entries that implies roughly 30
mislabelled fields. This is logged as roadmap item **N6**. It matters less than
it sounds: **kanji cards are graded on the meaning**, so a mislabelled reading is
a card-back annotation, never a scoring error.

**Known source defect.** The N1 chart gives 沌 the kun'yomi `yodmu`, which is not
a reading (almost certainly a typo for `yodomu`). It is dropped rather than
guessed at.

**N5 correction.** The existing N5 module and the reference chart differed by six
characters each way. **夕 田 外 青 赤 言** were on the chart but missing from the
transcription, and all six are inside the Top 200 by frequency — without them the
volume tiers could not be complete. Added by hand in the curated N5 style with
stroke counts and okurigana notation. The six the module has that the chart does
not (鳥 帰 犬 早 字 魚) were left alone: they are legitimate characters, and moving
them would change which deck an existing learner's history sits under for no
gain.

**Not carried over.** The charts have no stroke counts, so 1,138 characters leave
that field `NULL` rather than filling it with guesses (roadmap N7).

---

### 3. Kanji volume tiers made real

**What.** `kanji:top200` and `kanji:top500` now slice a real ranking.

**Why.** They previously resolved to "the first N kanji by id". With seeding
running N5 → N1, that would have advertised a mostly-N5 set as the Top 200 —
a false label, and one the content expansion would have created rather than
fixed.

**How.** A new `frequency_rank` column (additive migration, following the
existing `skipped` precedent) populated from `content/kanji_frequency.py` — 500
glyphs in the order used by the printed Top 200/500 flash-card decks in the same
reference repository, so screen and paper agree. The Top 200 set was verified to
be exactly the first 200 entries of the Top 500.

This is a **teaching** order, not a corpus frequency count: it front-loads
numbers, days and the characters a beginner meets first, and deliberately crosses
JLPT levels. That is the point of the tier.

`_segment_clause` was fixed at the same time — the volume decks had been counting
progress across all 1,251 kanji rather than their own 200 or 500.

---

### 4. Dashboard reorganised

#### Shelves split by script

| Before | After |
|---|---|
| One "Kana Shelf" with 10 decks in a horizontally-scrolling rail | **Hiragana**, **Katakana**, **Kanji — Proficiency** and **Kanji — Volume**, each with its own rail |

Katakana had been pushed off the right edge of the shared rail, where it read as
missing rather than present. Each shelf is now followed immediately by its own
games rail, so the drill and the game for what you are working on sit together.

Shelf headings gained top margin, a gap below, and a small horizontal inset —
with five shelves stacked they were doing all the work of separating one section
from the next with almost no room to do it.

#### Per-character miss rate, rebuilt

| Feature | Detail |
|---|---|
| Set selector | Hiragana · Katakana · Kanji N5 · N4 · N3 · N2 · N1 · Top 200 |
| Table view | The same data as a ranked work list |
| Unseen characters | **Shown**, dashed and empty, rather than omitted |
| Colour ceiling | 30% miss rate, not 100% |
| Footer | `N characters · set mean X% · weakest 字` |

Two decisions worth restating. A grid built from the `attempts` table alone
silently hides every character you have never touched — which is the most
actionable thing the panel could tell you. And a 0–100% colour ramp flattens
every difference a learner can act on into the same dim wash; above 30% a
character is simply failing.

Backed by a new `analytics.character_grid()` and `GET /api/heatmap`.

#### Streak and Weak characters

Rebuilt as instrument modules matching the supplied mockup: a hero figure, a
28-day activity strip in four load bands, a four-week table of sessions · reps ·
mean accuracy, and a ranked grid of weak characters with an error-rate bar.

New `analytics.weekly_activity()` and `analytics.daily_streak()`. Streaks count
**distinct dates, not sessions** — two sessions in one evening is one day of the
habit — and the current run survives today being empty, or it would read zero
every morning.

#### Removed

| Panel | Reason |
|---|---|
| Time of day | Requested. No action followed from it |
| Mastery by group | Requested. The shelves already carry per-deck mastery |

Both removed **end to end** — query, endpoint payload, renderer, markup and
tests — rather than hidden with CSS.

#### Kanji accent

Kanji surfaces take the green accent from `mockups/03-arcade-ladder.html`; kana
keeps amber. Kana and kanji are different undertakings — one is a closed set of
104 sounds you finish, the other 1,251 characters you chip at for years — and
with the two now stacked one above the other, the accent is what tells you which
you are looking at.

Only the four accent tokens are overridden. Surfaces, ink and card stock are
shared, so this is a change of signal colour rather than a second theme to
maintain. Run-time tints were switched from a hardcoded `rgba(240,180,41,…)` to
`rgba(var(--amber-rgb),…)` so the heatmap and activity strip follow the scope
automatically.

---

### 5. Games: 3 boards → 9

**What.** Each of the three modes is now dealt in each of the three scripts.

**Why.** The same engine trains different things per script. A kana board pairs a
glyph with its sound; a kanji board pairs it with its **meaning**, because that
is what a kanji card is graded on. And the look-alikes a learner confuses are
disjoint sets — シ/ツ is a katakana problem, る/ろ a hiragana one, 問/門 a kanji
one.

| Script | Match Up pairs on | Confusion drill stacks |
|---|---|---|
| Hiragana | reading | あ/お · ぬ/め · る/ろ (21 pairs) |
| Katakana | reading | シ/ツ · ソ/ン · ク/ワ (24 pairs) |
| Kanji | meaning | 人/入 · 大/犬 · 問/門 (39 pairs) |

**Confusion pairs 45 → 84.** 39 kanji look-alikes added. Five proposed pairs were
dropped because one half was not seeded; a test now asserts every confusion-pair
glyph exists.

**A real bug fixed.** `_confusable_ids` drew confusable glyphs **one at a time**
from a shuffled flat list, so a look-alike usually arrived on the board without
its partner — making the Confusion Drill an ordinary memory game with unusual
characters on it. Its own docstring claimed otherwise. Pairs are now dealt
together, and a test asserts every glyph on a confusion board has its partner
present.

The games view gained a script picker; the mode descriptions rewrite themselves
to match.

---

### 6. Kanji reading reference

**Problem.** A kanji card is graded on its meaning, so its options are English.
That left a learner who cannot yet read kana fluently with readings they could
not use — the opposite of a reference.

| Change | Detail |
|---|---|
| New `kana.py` | Kana → Hepburn romaji, 196 lines, 24 tests |
| Card back | On'yomi and kun'yomi shown in kana with romaji beneath (ジ → `ji`) |
| Options | Each carries the reading of the character it stands for |
| Option height | Doubled to 116 px; "world/generation" does not fit the square that suits `kya` |
| Option text | 15.5 px meaning, 13 px reading |

Transliteration uses the wapuro convention — long vowels written out (シュウ →
`shuu`) rather than macronned — matching the reference charts and round-tripping
to identical kana. Structure survives: `/` still separates alternatives and
okurigana stay in their parentheses (よっ(つ) → `yot(tsu)`, which required the
geminate lookahead to see past the bracket).

Option readings are **display only**. Grading still compares the option text
against the answer, so this could not affect a score.

---

### 7. Settings: profiles, save/load, reset

Reached from a **Settings** button in the dashboard top bar.

#### Profiles

Each profile is a **separate database file**, not a column on a shared one.

Every analytics query in this project reads `attempts` directly. A `profile_id`
would mean threading a filter through all of them, and one forgotten `WHERE`
would quietly mix two learners' histories — a failure that looks like bad data
rather than a bug. A file cannot be half-filtered. It also makes the two
operations users actually ask for trivial and safe: exporting is copying a file,
and deleting a profile leaves no rows behind pointing at it.

The cost is that switching reopens the connection, which is why `activate()` is
the only way to do it. The default profile keeps using the existing `db_path`, so
an install predating this becomes "Default" with its history intact and nothing
to migrate.

#### Save and load

**Every row is keyed by the character's glyph, never its id.** Ids are an
artefact of seed order — and seed order changed in this very cycle, so an export
taken before the kanji expansion would have pointed at different characters
after it. A glyph *is* the character.

| Behaviour | Detail |
|---|---|
| Contents | Every session, attempt and review state |
| Excluded | The `characters` table — content, not progress; reseeded on every start |
| Unknown glyphs | Skipped and counted, so an export from a future version still restores what it can |
| Rejected | Any file whose `format` or `version` this build does not read |
| Merge | `replace=False` is implemented and tested, but not yet exposed in the UI (roadmap X1) |

#### Reset

Clears `sessions`, `attempts` and `review_state`; leaves the seeded characters
alone. Requires explicit confirmation **at the API as well as in the UI** — an
unconfirmed request changes nothing — and reports what it removed, because a
destructive action that says nothing is indistinguishable from one that failed.

#### New endpoints

| Method | Path |
|---|---|
| `GET` / `POST` | `/api/profiles` |
| `POST` | `/api/profiles/activate` |
| `DELETE` | `/api/profiles/<slug>` |
| `GET` | `/api/data/summary` · `/api/data/export` |
| `POST` | `/api/data/import` · `/api/data/reset` |

---

### 8. Corrections made during this cycle

| Issue | Resolution |
|---|---|
| Documented totals drifted | The README and docs said 1,453/1,245 — correct when written, stale after six N5 characters were added. Corrected to 1,459/1,251 and **asserted by a test**, because they had now drifted once |
| `_segment_clause` ignored volume limits | Volume decks were reporting progress across all 1,251 kanji |
| Confusion boards dealt orphaned glyphs | See §5 |
| A vacuous assertion | A test contained `assert … or True`. Replaced with a real check that the Top 200 is not the naive id slice |
| Create-profile response reported `active: false` | It predated the switch it triggered; now re-read after activation |
| `sqlite_sequence` cleanup | Would have raised — the schema uses no `AUTOINCREMENT`, so the table does not exist |
| "1 attempts" | Pluralisation helper, in a confirmation dialog where the user is deciding whether to trust the thing |

### Known-unfixed, carried to the roadmap

| Item | Roadmap |
|---|---|
| **ElevenLabs API key still unrotated** — exposed in a session transcript | — |
| 1,144 new kanji have no recorded audio; they synthesise live | N3 |
| ~30 single-reading on/kun fields statistically likely mislabelled | N6 |
| 1,138 kanji have no stroke count | N7 |
| Frontend JS untested — now 1,679 lines | Q2 |
| Pace timing not measured end to end | Q7 |
| No test opens a real window | Q8 |
| Preferences are per-browser, not per-profile | X2 |

---

## 2026-08-08 → 08-10 — Sound, ownership, and content beyond characters

Eighteen commits. The cycle divides into four unrelated pieces of work: making
the application ownable (licence, install, backup), giving it a voice (the sound
cue and the preference layer it forced into existence), extending it past single
characters (words, phrases, context), and fixing what that extension broke.

### Headline numbers

| Measure | Start of cycle | Now | Change |
|---|---:|---:|---|
| Cards seeded | 1,459 | **1,658** | +199 |
| — of which words | 0 | **106** | new |
| — of which phrases | 0 | **93** | new |
| Study decks | 17 | **33** | +16 |
| Shelves | 4 | **6** | +2 |
| HTTP endpoints | 23 | **27** | +4 |
| Python modules | 32 | **36** | +4 |
| Python lines | 7,473 | **8,635** | +1,162 |
| Frontend JS lines | 1,679 | **2,378** | +699 |
| Tests | 290 | **341** | +51 |

---

### 1. Ownership: licence, install, backup

**Attribution licence.** `LICENSE` §5 now requires anyone building a flash-card,
spaced-repetition, character-drill or other language-learning application
derived from this project to credit Mensura Media, somewhere an ordinary user of
their app can find it. It covers ports, transpilation and model-assisted
rewrites explicitly, because rewriting in another language is the obvious way to
argue the obligation away.

Two clauses were written deliberately and matter more than the rest:

* **§5.4** — attribution grants no rights. Without it the natural reading is
  "credit them and do as I like"; a derivative still needs consent under §4.
* **§5.5** — the limits, stated plainly. The obligation binds a licensee, not
  someone who built a flash-card app independently. No claim is made over spaced
  repetition, multiple-choice drilling, the kana or kanji themselves, or the
  JLPT levels. Nothing restricts discussing, reviewing or teaching about the
  project.

The mechanism is a **condition on the permission in §2** — contract, not
copyright. That is real, and it is how source-available licences generally do
this, but copyright does not protect ideas or methods and §5.5 says so rather
than bluffing. A `NOTICE` file carries the verbatim text and ships in the
distribution.

**Desktop install.** `tools/install-desktop.sh` builds a wheel and installs it
**non-editable** into its own virtualenv under `~/.local/opt`, links a launcher
onto `PATH`, installs five icon sizes and writes a validated `.desktop` entry.
Non-editable deliberately: an editable install breaks the moment the checkout
moves, which is not what "installed" should mean. Verified by checking
`/proc/<pid>/maps` on the running app — **zero mappings from the project tree**.

`tools/uninstall-desktop.sh` **keeps study history by default**; deleting it
requires `--purge` and typing `DELETE`. Removing an application should not throw
away the practice done with it.

**Backup retaken** as `20260808-0015`, and verified by *restoring* it rather
than inspecting it: cloned to a scratch directory and ran the suite from the
restored tree. The previous set's userdata tarball was **121 bytes** — an empty
directory, because no database existed when it was taken.

### 2. Sound

Took four commits and three wrong turns, all of which are worth recording
because none of the faults were visible from the source.

**It was inaudible.** The cue kept its source peak of −8.2 dBFS and was then
multiplied by an 0.55 app gain; at 51% system volume it arrived at roughly
**−19 dBFS**. Loud asset, quiet code is the correct arrangement and this was the
reverse. Assets are now peak-normalised to −0.4 dBFS. Measured at the speaker
monitor: **−1.4 dBFS**.

**It was on the wrong API.** `new Audio().play()` is for media playback. For a
short cue it fails three ways: the autoplay policy rejects the returned promise
until the page has been interacted with — and swallowing that rejection makes a
blocked cue indistinguishable from a working one, which is what hid the fault;
`currentTime = 0` restarts are not sample-accurate and cancel the cue already
sounding; and every play crosses the media pipeline, adding variable latency.
Rebuilt on the **Web Audio API**: decoded once into an `AudioBuffer`, each cue a
fresh `BufferSourceNode` through a `GainNode`, with the context unlocked on the
first gesture and re-resumed per cue.

**The asset was wrong for the job.** The supplied MP3 had **64 ms of leading
silence** — pure click-to-sound latency — and ran 1.056 s, still ringing when the
next card arrived at the fastest pace. Trimmed to 0.320 s with a 2 ms onset, and
moved to WAV because MP3's encoder delay left 14 ms even after trimming.

**Seven cues** now ship, six synthesised by `tools/make_cues.py`, all to one
contract: mono 44.1 kHz WAV, onset < 20 ms, ≤ 380 ms, peak ≈ −0.4 dBFS. Each is
a different *character* of positive rather than a different pitch of one sound.

### 3. Preferences moved to the server

The audio toggle appeared inert. Three attempts:

| Attempt | Approach | Failure |
|---|---|---|
| 1 | `localStorage` directly | This webview **accepts writes and drops them**. The write vanished, the next read returned the old value, the switch repainted itself back on, audio kept playing |
| 2 | Authority in memory, storage as a mirror | Fixed the toggle *within a page*. But `/study` is a **full page navigation** — a fresh JS context with an empty cache — so a cue chosen on the dashboard never applied. Pace, voice and volume had been failing identically, unnoticed, because none of them visibly contradicts itself the way a toggle does |
| 3 | **Server-side, per profile** | Works. Survives navigation *and* restarting the application |

Preferences are rows in a `preferences` table. Because each profile is already
its own database file, they are **per-profile without a profile column** —
closing two roadmap items rather than working around them. The key set is closed
and values are length-capped: an open key-value store reachable from the page is
a way to fill someone's database.

### 4. Content beyond single characters

**Words** — 106 across six sets. Days, months, numbers and time were *extracted*
from the reference worksheets. Demonstratives (こそあど) and particles were
*authored*, because both are closed, rigidly structured systems every N5 course
teaches identically.

**Phrases** — 93 across ten sets, on their own shelf. Five are built on a shared
pattern: 〜ましょう and 〜てください are mechanical, so learning the shape delivers
the whole set. The convenience-store set is ordered the way the transaction
actually happens.

**Context** — five of those sets exist because the English gloss alone misleads,
so a new `note` column carries a line of usage context, shown beneath the reading
on the card back:

| Set | Why the gloss is not enough |
|---|---|
| Praising someone | さすが assumes a track record; to a beginner it sounds sarcastic |
| Encouraging someone | 頑張れ is the shouted form — fine from a friend, rough from a stranger |
| Describing things | One word covers two English ones: きれい is beautiful *and* clean |
| Rough language | ばか is mild in Osaka and sharp in Tokyo; 死ね is not banter in any register |
| Personality — がり | 強がり is **not** "a strong person" — it is someone putting on a brave face |

Rough language is included for **recognition, not production**. These appear
constantly in manga and television whether or not a course admits it, and
knowing that 死ね is said to wound is safety information. A test asserts every
card in these five sets has a note of real length.

**One supplied example was corrected rather than encoded.** "I'm a fan — *tsugi
no wa*" is wrong; 次のは means "the next one". It ships as ファンです.

**The catalogue.** Every shelf now ends with a **More…** deck opening `/decks`,
which lists all 33 working decks plus eleven designed-but-unbuilt exercises,
each carrying a status and **what is blocking it**. That last part is what stops
it becoming a wish list implying work is imminent.

### 5. What extending the content broke

**A data-model error.** `characters` was unique on `glyph` alone, so seeding
words *overwrote* 41 characters — the particle は replaced the hiragana は, the
number 一 replaced the kanji 一 — and the Top 200 kanji deck quietly shrank to
175. Caught by a test asserting that count. Uniqueness is now `(glyph, script)`;
the migration rebuilds the table preserving ids, so existing attempt history
still points at the same characters.

**Cards sized by script.** `.deck3d` is a 5:7 playing-card portrait — right for
a glyph that fills the face, wrong for text. Combined with a script-driven
width, every phrase card came out at 520 × 728, so 頭悪い sat in the middle of a
mostly empty card. The face now picks one of four sizes from its **content**;
1,545 of 1,658 cards fall in the unchanged single-glyph bucket.

**Card and options drifting apart.** The stage centred its two columns, so
whichever was taller pushed the other's top out of line — and which is taller
now varies. A kana card sat 23 px above the options, a phrase card 27 px below:
the same bug in opposite directions. `.deck3d` also rotated about its centre,
which moves the top edge by an amount proportional to card height. It now pivots
on its top edge, which cannot move. Measured at **0 px** at every size.

### Corrections made during this cycle

| Issue | Resolution |
|---|---|
| `NameError` stopped the app booting | `db.py` used `log` with no logger. It failed loudly at startup, which is the right way to fail |
| A placeholder shipped into content | A Cyrillic string where 新しい belonged, caught before commit |
| A stale `build/` shipped a deleted file | setuptools reuses it; the installer now clears it first |
| Deck titles wrapped | Phrase decks dropped the redundant "Phrases ·" prefix |
| Catalogue headings were fine print | `.lbl` is 9.5px — right beside a shelf, wrong as a page title |
| Recap button sat flush against the grid | 22 px separation |

### Known-unfixed, carried forward

| Item | Roadmap |
|---|---|
| **ElevenLabs API key still unrotated** — exposed in a session transcript | — |
| 1,144 kanji have no recorded audio; they synthesise live | N3 |
| ~30 single-reading on/kun fields statistically likely mislabelled | N6 |
| Frontend JS untested — now 2,378 lines across six files | Q2 |
| No test opens a real window | Q8 |
| Open-ended phrase vocabulary still unsourced | catalogue |

---

## Earlier cycles

Condensed; see `changelog.md` for the full append-only log.

| Date | Summary |
|---|---|
| **2026-08-07** | Personal-use licence; `docs/FEATURES.md` and `docs/STACK-VERIFICATION.md`; corrected a repo that declared MIT against the owner's intent |
| **2026-08-07** | Memory games (Match Up, Pelmanism, Confusion Drill); game cards on the dashboard; squared vertical boards; selection feedback |
| **2026-08-07** | Session recap with misses in red; split Back/Next control; colour-coded recap metrics; removed response-latency and confused-with panels |
| **2026-08-06** | VOICEVOX integrated as the primary provider; No.7 announcer set as the female default; pitch accent exposed per mora |
| **2026-08-06** | 630 ElevenLabs clips built and validated; `voicelab` toolset; cross-voice consistency checking caught a truncated へ clip |
| **2026-08-06** | Application built end to end from the chosen mockup; keyboard control; test suite; documentation set |
