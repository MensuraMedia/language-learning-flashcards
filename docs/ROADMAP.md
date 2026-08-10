# Roadmap & QA Register — Japanese Practice

Every outstanding item in one place: what is left, why it matters, what it
depends on, and **how to tell when it is genuinely done**.

- **Last updated:** 2026-08-10
- **Current state:** 341 tests passing · **1,658 cards across 33 decks** · 9 memory boards · 630 narration clips · installed as a desktop app · sound cues · server-side preferences
- **Companion docs:** [HANDOFF](HANDOFF.md) (session continuity) · [TESTING](TESTING.md) (what is covered) · [ARCHITECTURE](ARCHITECTURE.md) · [VOICE-LAB](VOICE-LAB.md) · [AUDIO](AUDIO.md)

## How to read this

| Symbol | Meaning |
|---|---|
| 🔴 | Blocked on a decision only the user can make |
| 🟠 | Known defect — shipped behaviour is wrong |
| 🟡 | Gap — behaviour is absent, not wrong |
| 🔵 | New feature |
| ⚪ | Tech debt / housekeeping |

**Effort** is rough: S ≈ under an hour · M ≈ half a day · L ≈ 1–3 days · XL ≈ a week+.

Every item carries **QA** — the observable condition that closes it. "Implemented"
is not "done"; the QA line is what a reviewer checks.

---

## 0. Decisions needed before their work can start 🔴

These are open because they change behaviour the user specified. They are not
oversights — they are waiting on a call.

| # | Decision | Current | Recommended | Why it matters |
|---|---|---|---|---|
| D1 | **Skip penalty** | `SKIP_PENALTY = -1` | `0`, relabel "Don't know" | With 3 options a guess is EV +3.33 vs −1 for a skip, so skipping is strictly dominated — the penalty taxes the one honest button while guessing pollutes the weakness data with lucky guesses recorded as knowledge |
| D2 | **Options per card** | `CHOICE_COUNT = 3` | `4` | Chance floor 33% → 25%; characters certified "mastered" by luck alone drop from 1/27 to 1/64 (≈3.9 → ≈1.6 per 104-character pass) |
| D3 | **Flip during scored play** | Free, unrecorded | Mark `assisted`, score 0, don't advance SRS | Flip reveals the answer, so flip → read → answer is the dominant strategy and yields a perfect score with zero knowledge |
| D4 | **Wrong-answer cost** | 0 points | Requeue the card, not negative marking | Makes a miss cost *work* rather than a demoralising negative number; negative marking belongs only in an opt-in Exam mode |
| D5 | **Character Runners** | Requested | **Recommend against** | Highest build cost of the named games, lowest Japanese-reading per minute; a platformer with kana on the gates |

> Full reasoning: the game-theory review summarised in §6. D1–D4 are cheap
> individually and interact — adopting one without the others leaves a loophole
> the others were closing.

---

## 1. Correctness & data integrity 🟠

Defects where shipped behaviour is measurably wrong. **Highest priority** — the
`attempts` table is the product; everything else is derived from it.

| ID | Item | Effort | Depends on | QA — done when |
|---|---|---|---|---|
| C1 | **`assisted` column + flip handling.** Add `attempts.assisted`, capture `state.flipped` at the *top* of `choose()` (the auto-flip on line ~148 makes a naive read always true), score 0, and **skip `next_review()` entirely** so an assisted answer never advances the SRS schedule | M | D3 | A flip-then-correct writes `assisted=1`, awards 0, leaves `review_state.reps`/`interval_days` unchanged, and appears in `weakest_characters` |
| C2 | **Requeue on miss/skip/assist.** Reinsert the card 3–5 positions later; session ends when every card is answered correctly unaided | M | D4 | A wrong answer causes the same glyph to reappear later in the same session; `first_attempt=0` on the repeat |
| C3 | **Server-side correctness.** `record_attempt` takes `correct` from the request body and the deck payload ships `answer` to the client. The server has no ground truth | M | — | Posting `{"correct": true}` for a wrong option is rejected or recomputed server-side |
| C4 | **Mastery is measured against recognition.** At a 33% floor, `miss_rate ≤ 0.15` corresponds to ~78% true recall. Rename the meter `recognised`, add a separate `recalled` count gated on typed recall | M | F1 | Deck faces show two meters; `mastered` is not claimed without a recall-mode success |
| C5 | **Latency-aware mastery.** A correct answer after 4 s is not mastery — ARCHITECTURE §5 says so and nothing acts on it. Count `correct AND latency > 4000ms` as 0.5 toward `weighted_miss` | S | — | A slow-correct character still surfaces in the drill queue |

---

## 2. Content gaps 🟡

| ID | Item | Effort | Depends on | QA — done when |
|---|---|---|---|---|
| ~~N1~~ | ~~**Kanji N4–N1**~~ | — | — | ✅ **Done 2026-08-08.** 1,138 characters extracted from the reference charts; counts asserted in `test_content.py` |
| ~~N2~~ | ~~**Kanji frequency rank**~~ | — | — | ✅ **Done 2026-08-08.** `frequency_rank` column + `kanji_frequency.py`; the volume shelf renders genuine 200/500 counts |
| **N3** | **Narration for 1,144 new characters.** 630 clips cover the original 315. The kanji expansion added 1,144 characters with no audio, so the speaker button on a kanji card falls through to live VOICEVOX synthesis every time — correct, but slower and unvalidated | **L** | — | `voicelab cost` reports 0 outstanding; `voicelab verify` reports 0 rejected across all 1,459 characters |
| **N3b** | **Which reading to narrate.** A kanji has several readings and the clip pipeline assumes one utterance per character. Needs a rule — likely primary on'yomi, matching what the option cards now show | S | N3 | The rule is stated in AUDIO.md and applied by `voicelab build` |
| **N6** | **Reading-field audit.** For the ~530 chart entries that gave a single reading, on'/kun' was assigned by a lexicon rule measured at 94.6% on held-out data. That implies roughly 30 mislabelled fields | M | — | A native or dictionary cross-check confirms each single-reading entry; disagreements corrected in the content module |
| **N7** | **Stroke counts for N4–N1.** The reference charts do not carry them, so 1,138 characters have `stroke_count = NULL`. Nothing renders it today, but a writing mode would need it | M | — | Every seeded kanji has a stroke count, sourced not guessed |
| N4 | **Vocabulary sets.** Days 曜日, Months 月, Numbers 数字, Time 時間 from the reference workbooks | L | — | Each appears as a themed deck with correct counts |
| N5 | **Thematic kanji categories.** Numbers & Counting, People & Family, Nature & Weather, Time & Calendar, Actions, Descriptions, Places — present in `characters.category`, unused by any deck | M | N1 | Category decks selectable from the shelf |

---

## 3. Study modes 🔵

The advertised-but-fictional problem first: `CHALLENGES` has five values, `sessions.challenge` stores them, `DECK_META` assigns them, `dashboard.js` prints them as tags on every deck face — and **`study.js` never branches on the value**. Four of the five modes do not exist.

| ID | Item | Effort | Depends on | QA — done when |
|---|---|---|---|---|
| M1 | **Recall (typed romaji).** Free recall, no options, no chance floor. This is what `challenge="recall"` was always meant to mean; ~40 lines to grade kana against `characters.romaji` | L | — | Selecting a `recall` deck shows an input, not options; accuracy is not floor-inflated |
| M2 | **Browse (unscored).** Self-paced flip-through: no options, no grade, no clock. Records exposure only, updates `review_state.last_seen`, excluded from the drill queue and SRS | M | C1 | A Browse session writes `mode='browse'` rows that do not appear in `weakest_characters` |
| M3 | **Rapid Fire.** 60 s, no reveal pause, no back-navigation, no flip. Reports throughput and median latency, **not** points | M | — | Session ends on the timer and reports cards/min; attempts DO feed the drill queue and SRS (unassisted, timed, same judgement) |
| M4 | **Card Matching.** 12 tiles face up, 6 glyphs + 6 readings; pair them. Trains the reverse mapping nothing else tests | L | — | Board clears; wrong pairings feed `confusion_pairs` but **not** `weakest_characters` (late-board elimination inflates it) |
| M5 | **Card Memory.** Same board face down | M | M4 | Shares M4's renderer; excluded from all analytics except weakly from confusion pairs |
| M6 | **Exam mode.** Opt-in proper scoring: +10 / −5 / 0, no flip, no requeue, results sealed until the end | M | D4 | Negative marking exists **only** here |
| M7 | **Listening mode.** Audio plays, no glyph — pick or type. The clip library and endpoint already exist and are used only on the card back | M | — | `challenge="listening"` plays before revealing anything |
| M8 | **Production mode.** Romaji/audio → pick or write the *glyph*. The reverse direction, which writing requires and no mode currently tests | L | M1 | — |

---

## 4. Character games 🔵

Ordered by learning value per unit of work, not by the order they were named.

| ID | Game | Effort | Feeds analytics | QA — done when |
|---|---|---|---|---|
| G1 | **Spot the Character.** Dense grid, find every instance of a target; ~40% of tiles are confusion-mates. Trains visual discrimination in a field — the closest mechanic to actual reading | L | `confusion_pairs` only | False positives are recorded as confusion data; grid seeding demonstrably uses `CONFUSION_PAIRS` |
| G2 | **Mirror Match.** Real glyph or forgery (mirrored, rotated, or one stroke altered). The canonical traps are *the same skeleton with a stroke difference* — シ/ツ is stroke angle, き/さ is one crossbar — so this attacks the discriminative feature no MCQ can reach | L | `confusion_pairs` + new *glyph fragility* metric | Forgery table covers all `CONFUSION_PAIRS` members; accepted-forgery rate is reported per character |
| G3 | **Gojuon Grid.** Rebuild the 5×10 syllabary from a tray. Teaches the system as a consonant × vowel product rather than a flat bag of 46 — and row vs column errors are cleanly typed consonant vs vowel confusions | L | `confusion_pairs` + `weakest_characters` at 0.5× | Placement errors are classified row/column; extending with dakuon rows makes は/ば/ぱ one column |
| G4 | **Character Shooters.** Kana descend; shoot the one matching the called reading. Spawn table seeded from `CONFUSION_PAIRS` | L | `confusion_pairs` only | Shooting a wrong glyph records a confusion; misses do not pollute the drill queue |
| G5 | **Character Runners** | XL | none | 🔴 **See D5 — recommended against.** If built, ship it honestly as decoration |

---

## 5. UI & UX 🟠🟡

| ID | Item | Sev | Effort | QA — done when |
|---|---|---|---|---|
| ~~U1~~ | ~~**Detached `.btn` in WebKit**~~ | — | — | ✅ **Done.** Root cause was a class collision: the deck's fanned-sheet `.ghost` (absolutely positioned, `::after` content 記) was capturing the End link. Renamed `.btn-ghost` |
| U2 | **Inline `style=` stopgaps.** 14 in `dashboard.html`, used for spacing while matching the mockup | ⚪ | S | Zero inline styles; spacing lives in `theme.css` |
| U3 | **Dashboard below the fold partly unverified.** Shelves, games rails, heatmap, streak and weak characters have now been captured with real data in the pywebview window. Retention, accuracy-by-set, leeches and session history still have not been confirmed together | 🟡 | S | A full-page capture shows every remaining panel rendering with real data |
| **U7** | **Large-set heatmap ergonomics.** The N3 grid is 396 cells in a scrolling box. It is honest — nothing is truncated — but it is not scannable | 🟡 | M | A grouping or paging affordance that still never hides characters silently |
| **U8** | **Kanji card back is dense.** Meaning, on'yomi, kun'yomi, both romaji lines and the speaker now share one face | 🟡 | S | The back reads cleanly at 1280×860 without crowding |
| U4 | **Deck mode picker.** `challenge`/`scoring` are baked per deck in `DECK_META` and rendered as authoritative tags. They should be *defaults* in a picker shown when a deck is opened | 🔵 | M | Any deck can be opened in any mode; the tag shows the default, not a constraint |
| U5 | **Virtual decks are unreachable.** `?characters=` drill works and is exercised by the heatmap, but "Review (due)" and "Drill (weak)" have no shelf entry | 🔵 | M | Both appear as decks and resolve their own character sets |
| U6 | **Deck unlock ladder.** `rung` labels (LV 1…LV 5) imply a progression nothing enforces | 🔵 | M | A rung unlocks at a stated threshold on the previous |

---

## 6. Audio & voice 🟡

| ID | Item | Effort | QA — done when |
|---|---|---|---|
| A1 | **🔴 Rotate the ElevenLabs API key.** It appeared in a chat transcript | S | Old key revoked; new key in `~/.config/japanese-practice/elevenlabs.key` (mode 600); `voicelab verify` still passes |
| A2 | **Audition the two voices by ear.** Matilda and Daniel were chosen on documented age labels and *measured pace*. Timbre and accent authenticity were **not** assessed — both are English-native voices through a multilingual model | S | A human confirms neither carries an audible English colour on Japanese, or replaces them via `voicelab build` |
| A3 | **Widen key scope to `voices_read`.** The current key is TTS-only, so `voicelab audition` cannot enumerate the account library and falls back to the public slate — which may exclude Japanese-native voices the account owns | S | `list_voices()` returns the account's voices |
| A4 | **Per-character reading review.** Kanji clips speak the primary kun'yomi. Some characters may be better served by on'yomi | M | A native speaker signs off on the kanji clip set |
| A6 | **🔴 Phonetic accuracy is unverified.** ElevenLabs claims the multilingual model handles Japanese pitch accent; the user reports it does not fully measure up. Nothing in this project has confirmed pronunciation by ear | M | A Japanese speaker listens to a sample and either signs off or lists the failures. See §6a |
| A7 | **Reference comparison harness.** Build a side-by-side player: our clip against a verified reference, per character, with a pass/fail toggle that writes back to the manifest | M | A reviewer can audit 104 kana in one sitting and the result is recorded |
| A8 | ~~Alternative sources~~ — **evaluated 2026-08-07, see [VOICEVOX-EVALUATION.md](VOICEVOX-EVALUATION.md)**. Verdict: adopt VOICEVOX as primary, keep ElevenLabs as fallback | — | Done |
| A9 | **Integrate VOICEVOX as a provider.** Add `tts_voicevox.py`; slot it into `get_audio()` above ElevenLabs; `voicelab --provider voicevox`. Engine discovery must be optional and silent | M | `voicelab build --provider voicevox` produces a validated library; with no engine running the app falls through without error |
| A10 | **🔴 Decide the clip-shipping model.** VOICEVOX terms are *silent* on redistributing generated audio, and this repo is public. Either generate on first run (recommended — 4.7 min locally, no key, no quota) or obtain written clarification | S | A decision recorded in `decisions.md` |
| A11 | **VOICEVOX attribution.** Credit is mandatory, e.g. `VOICEVOX:九州そら`, somewhere a user naturally finds it | S | Credit visible on an about/credits surface |
| A12 | **Pitch-accent teaching aid.** VOICEVOX returns per-mora pitch; the card could *show* the accent contour. No other provider makes this possible | M | A card displays the pitch pattern for its reading |
| A5 | **Pronunciation dictionary.** For any character the model reads wrongly, use ElevenLabs' `pronunciation_dictionary_locators` rather than an inline hack | M | Known-bad readings corrected without changing `speech_text_for()` |

### 6a. On verifying pronunciation

**I cannot hear.** No amount of analysis substitutes for a human — or a native
speaker — listening. What automation *can* do is narrow where they should listen.

**What has been done automatically**, and what it caught:

| Check | Result |
|---|---|
| Format, size, silence, checksum | 630/630 valid, zero rejected, no drift |
| Exact duration via `ffprobe` | Median 0.86 s kana / 1.07 s kanji — tightly clustered, no clip read as a whole word |
| Implausibly short (< 0.45 s) | **1 found** — `hiragana/female/へ` at 0.24 s, a truncated render |
| Cross-voice disagreement (> 0.35 s) | **1 found** — the same へ, 0.24 s against the male's 0.91 s |

The truncated へ **passed** the 150 ms absolute floor. Only comparing the two
voices against each other exposed it. That check is now permanent in
`audio_library.cross_voice_report()` and runs as part of `voicelab verify`.

**What this cannot tell you:** whether あ *sounds like* あ to a Japanese ear.
Duration and amplitude prove a clip is well-formed, not that it is correct.
Pitch accent, vowel quality, and the moraic ん are all invisible to these checks.

**On the YouTube reference.** Downloading audio from the linked channel to use
as a comparison corpus would breach YouTube's terms and the uploader's
copyright, so I have not done it — `yt-dlp` being installed does not make it
appropriate. The workable version is A7: a harness that plays our clip beside a
reference the reviewer opens themselves, with a pass/fail toggle. That keeps the
reference where it belongs and still produces a recorded audit.

---

## 7. Testing & QA infrastructure ⚪

Current coverage and its holes are documented in [TESTING §8](TESTING.md#8-what-is-not-covered).

| ID | Item | Effort | QA — done when |
|---|---|---|---|
| Q1 | **`pytest-cov` + a coverage floor.** 216 tests pass but coverage is unmeasured | S | CI fails below an agreed threshold |
| Q2 | **Frontend JS is untested.** No runner, and `node` is not installed on this machine. `dashboard.js` (791), `study.js` (593) and `games.js` (295) are **1,679 lines** of untested logic — three of the bugs found so far were in exactly that code, and this cycle added the pace scaling, the heatmap, the streak panel and the whole settings dialog to it | L | A JS test runner exercises `choose()`, `grade()`, `paceFactor()`, `renderChoices()`, `hmTint()` and the keymap |
| **Q7** | **Timing is unverified end to end.** The pace table is computed from constants and one hold was measured (355 ms at *relentless*); the screenshot-polling harness is too coarse for the rest | S | A harness measures each of the five holds within ±50 ms |
| **Q8** | **No test opens a real window.** Everything is exercised through the Quart test client. Every WebKit-only defect so far — the invisible `.view`, two class collisions, `localStorage` throwing — was invisible to it | L | A smoke test drives the pywebview window and asserts the card renders |
| Q3 | **CSS flip animation.** Verified visually once; nothing guards a regression | M | A visual-regression check on the front and back faces |
| Q4 | **Screenshot harness.** Firefox headless renders this app's card view blank even when the app is correct, and it cost real debugging time. The pywebview + `import -window` path works but is manual | M | A repeatable command captures dashboard and study views |
| Q5 | **Stale-process hazard.** Nine orphaned app instances accumulated during testing because `pkill -f`/`pgrep -f` match the calling shell. Filter on process *name* | S | A documented teardown that cannot kill its own shell |
| Q6 | **Seed-data realism.** `first_vs_eventual` reported a structural zero for a long time partly because seeded attempts never repeated a character | S | The seeder produces repeats, slow-corrects and skips |

---

## 7a. Profiles & data 🔵

Shipped 2026-08-08; these are the follow-ups it created.

| ID | Item | Effort | QA — done when |
|---|---|---|---|
| **X1** | **Merge on import.** `import_progress` already takes `replace=False` and is tested, but nothing in the UI offers it. Merging a second device's history is the reason the flag exists | S | The load dialog offers Replace or Merge, and merging does not duplicate sessions |
| ~~X6~~ | ~~**Preferences do not survive a restart**~~ | — | ✅ **Done 2026-08-08.** Moved server-side into the profile's database |
| ~~X2~~ | ~~**Per-profile preferences**~~ | — | ✅ **Done 2026-08-08.** Preferences live in the profile's own database file, so they are per-profile by construction. Covered by `test_preferences_are_per_profile` |
| **X3** | **Automatic backup before destructive actions.** Reset and replace-on-import both destroy history behind a `confirm()`. A silent snapshot first would make either recoverable | S | A timestamped copy is written before either action, and is documented |
| **X4** | **Profile rename.** Create and delete exist; rename does not, so a typo means recreating and re-importing | S | Renaming preserves the database and its history |
| **X7** | **Set-valued answers.** Alternate phrases, politeness registers and typed recall all need a card type that grades a *set* of correct answers. The engine has exactly one correct option per card | L | A card can accept any of several right answers, and the analytics still mean something |
| **X5** | **Export scope.** The export is whole-profile. Sharing one deck's history, or anonymising before sharing, is not possible | M | Export accepts a difficulty-key filter |

---

## 8. Packaging & distribution 🔵

| ID | Item | Effort | QA — done when |
|---|---|---|---|
| ~~P0~~ | ~~**Local desktop install**~~ | — | ✅ **Done 2026-08-08.** `tools/install-desktop.sh` — own venv under `~/.local/opt`, launcher on PATH, hicolor icons, validated `.desktop` entry. Verified by launching from both PATH and the menu, and by confirming zero mappings from the source tree |
| P1 | **`.deb` package** | M | Installs, launches from the desktop menu, icon appears |
| P2 | **AppImage** | M | Runs on a clean machine with no Python set up |
| P3 | **PyPI release** | S | `pip install japanese-practice` then `japanese-practice` works |
| P4 | **Windows / macOS** | L | pywebview backends verified on both |
| P5 | **First-run experience.** A fresh install has an empty dashboard and no guidance | M | First launch suggests a starting deck |
| ~~P6~~ | ~~**Data export**~~ | — | ✅ **Done 2026-08-08.** Save/load of a glyph-keyed JSON document, plus reset, from the Settings dialog |
| **P7** | **Profile-aware packaging.** A packaged build must place profile files under the platform data dir and survive upgrades | M | Installing over an existing version keeps every profile and its history |
| **P8** | **Export format v2.** v1 carries progress only. Sharing a *configuration* — chosen pace, voice, deck defaults — is the obvious next ask | S | v2 documented, and v1 files still load |
| **P9** | **PEP 639 licence metadata.** Modern setuptools deprecates `license = {file = ...}` in favour of an SPDX expression. Migrating needs `setuptools>=77`, which would break `pip install -e .` on this machine (59.6.0), so the build currently emits a deprecation notice that the install script hides | S | Metadata migrated and `pip install -e .` still works on the minimum supported setuptools |
| **P10** | **Installed app does not self-update.** Re-running the install script is the only upgrade path, and nothing tells a user a newer version exists | M | The app reports its version and where it was installed from |

---

## 9. Standards & housekeeping ⚪

| ID | Item | Effort | QA — done when |
|---|---|---|---|
| S1 | **Duplicate memory rule.** `.claude/rules/` holds both `memory-rules.md` and `universal-memory-rules.md`, byte-identical. Kept because the standards forbid removing universal rules — needs a ruling | S | One copy, or a documented reason for two |
| S2 | **Non-applicable example rules and agents.** `backend-example.md`, `infra-example.md`, `react-example.md`, `chrome-ext.md`, `stream-engineer.md` do not apply to this stack | S | Removed or justified |
| S3 | **Git credential helper is broken.** `~/.gitconfig` points at a missing `/usr/bin/gh`, so plain `git push` fails; pushes use an explicit auth header | S | `git push` works unaided |
| S4 | **Session logs.** `.claude/memory/sessions/` is empty despite the standard requiring a log per session | S | One log per working session |

---

## 10. Suggested order

Grouped so that each block leaves the app in a coherent state.

| Block | Contents | Rationale |
|---|---|---|
| **1. Close the measurement holes** | D1–D4 → C1, C2, C5 | The scored mode currently has a dominant strategy that yields a perfect score with zero knowledge. Every metric collected until this lands is of degraded quality, so features built on top inherit the flaw |
| **2. Make the meters honest** | C4, M1 | Mastery is claimed against a 33%-floor recognition test. Typed recall gives it something real to mean |
| **3. ~~Fill the content~~ → narrate it** | N3, N3b, N6 | ✅ The decks are filled — 1,459 characters across 17 decks. The gap moved: 1,144 of them have no recorded audio and fall through to live synthesis, and ~30 single-reading fields are statistically likely to be mislabelled |
| **4. Unscored practice** | M2, M3 | Browse ships *with* C1 so assisted-marking reads as "here is the right tool for looking things up" rather than a punishment |
| **5. The best game first** | G1, then G2/G3 | Spot the Character has the highest learning value per unit of work and is the best confusion-data instrument available |
| **6. Harden** | Q1, Q2, U3 | Frontend logic is where three of the four found bugs lived, and it has grown: `dashboard.js` is now 791 lines and `study.js` 593, all still untested. U1 is closed |
| **7. Ship it** | P1–P3, P7 | Packaging last — it is the only block that changes nothing about the app itself. P7 is new: an upgrade must not lose a learner's profiles |

---

## 11. Completed this cycle

Kept for QA reference — each of these has a regression test.

| Item | Evidence |
|---|---|
| Wired `CONFUSION_PAIRS` into distractor generation | 45 curated traps had been imported by tests and nothing else |
| Voicing-sibling distractors | ぱ now offers `ba`/`ha`; han-dakuon previously offered only `p-`, never testing は/ば/ぱ |
| Closed the free-skip loophole | `→` advanced an unanswered card with no record — it dominated the Skip button |
| Fixed `build_deck` shuffle no-op | Shuffle ran after concatenation; decks always dealt in id order |
| Fixed `first_attempt` hardcoded to 1 | `first_vs_eventual` could only ever report a zero gap |
| 630 narration clips, both voices | All validated, zero rejected, no checksum drift |
| Voice toggle | Live window served the 15,926-byte male clip after `V` |
| App icon, study symmetry, dashboard type scale | あ in amber on gray; squared options; larger chrome type |
| Withdrew unbacked Top 200/500 decks | They advertised the 107-character N5 set as the "Top 200" |

### Cycle of 2026-08-07 → 08

| Item | Evidence |
|---|---|
| **Pace slider** | 5 steps, 1.0× → 0.2× on the verdict hold, floored at 260 ms; persisted; `[`/`]` bound. Centring measured at 31 px above / 32 px below |
| **Kanji N4–N1 seeded** | 1,138 characters; 789/789 readings round-tripped; on/kun rule 94.6% on held-out N1; counts asserted in `test_content.py` |
| **N5 corrected** | 夕 田 外 青 赤 言 added — all six inside the Top 200, so the volume tiers could not have been complete without them |
| **Frequency tiers made real** | `frequency_rank` column via additive migration; Top 200 verified to be exactly the first 200 of Top 500 |
| **Shelves split by script** | Katakana had been pushed off the right edge of a shared rail, where it read as missing |
| **Per-script games** | 9 boards; engine, confusion pairs and copy all script-scoped |
| **Confusion pairs 45 → 84** | 39 kanji look-alikes added; every glyph asserted seeded |
| **Confusion boards deal both halves of a pair** | Previously drew glyphs individually, so a look-alike usually arrived without its partner and the drill was an ordinary memory game |
| **Miss-rate panel rebuilt** | Set selector, table view, 0–30% ceiling, unseen characters shown rather than hidden |
| **Streak & weak-character panels rebuilt** | `weekly_activity()` and `daily_streak()`; streaks count distinct dates, not sessions |
| **Time of day + mastery by group removed** | Removed end to end — query, payload, renderer, markup — not hidden with CSS |
| **Kanji accent** | Green from `mockups/03-arcade-ladder.html`; only accent tokens overridden |
| **Kanji reading reference** | New `kana.py`, 24 tests; romaji on card backs and on double-height options |
| **Profiles, save/load, reset** | File per profile; export keyed by glyph; reset requires explicit confirmation and reports what it removed |
| **Documented totals asserted** | They had already drifted once — six N5 characters were added after the figures were written |
