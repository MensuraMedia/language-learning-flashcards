# Features & function reference

Everything the application does, and every module, endpoint and control that
does it. Current as of **2026-08-08** · **289 tests passing** · **1,459
characters seeded**.

- [1. Study cards](#1-study-cards) · [2. Memory games](#2-memory-games) · [3. Dashboard](#3-dashboard--analytics)
- [4. Audio](#4-audio) · [5. Content](#5-content) · [6. Scoring](#6-scoring--scheduling)
- [7. HTTP API](#7-http-api) · [8. Modules](#8-module-reference) · [9. CLI](#9-command-line)
- [10. Configuration](#10-configuration) · [10a. Profiles & data](#10a-profiles-and-your-data) · [11. Not built](#11-deliberately-not-built)

Every figure in this document was measured against the working tree, not
recalled. Where something is unverified or known-weak it says so.

---

## 0. At a glance

| Dimension | Count | Notes |
|---|---:|---|
| Cards seeded | **1,613** | 104 hiragana · 104 katakana · 1,251 kanji · 106 words · 48 phrases |
| Study decks | **28** | 5 hiragana · 5 katakana · 5 JLPT · 2 volume · 6 word sets · 5 phrase sets |
| Memory boards | **9** | 3 modes × 3 scripts |
| Confusion pairs | **84** | 21 hiragana · 24 katakana · 39 kanji |
| Scoring schemes | **4** | accuracy · speed · streak · SRS |
| Dashboard analytics | **13** | see §3 |
| HTTP endpoints | **27** | 4 views + 23 API |
| Python modules | **32** | 7,473 lines, zero import cycles |
| Bundled audio clips | **630** | plus local VOICEVOX synthesis |
| Tests | **289** | ~5 s, 10 files |
| Runtime dependencies | **3** | 33 packages in the whole closure |

---

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
| **Verdict hold** | Correct 1.9 s · wrong 2.9 s at the default pace. A wrong answer is when the learner actually studies, so it gets longer |
| **Pace slider** | Five steps scaling the hold 1.0× → 0.2×, so a known deck moves at the learner's speed rather than beginner timing. See below |
| **Skip** | Scores −1 and records `skipped=1` — an honest "I don't know" |
| **Back / Next** | One split control. Next is greyed until you have gone back, then returns you forward **free** |
| **Voice toggle** | Female / male, persisted |
| **Session recap** | Every character covered, at option-card size, misses in red with romaji beneath |
| **Colour-coded metrics** | Score, accuracy and streak graded green / amber / red against what was achievable |
| **Kanji reading reference** | Card backs and options carry romaji — see [Kanji cards](#kanji-cards) |
| **Per-script accent** | Kanji surfaces use a green accent, kana amber, so the script is never in doubt |

### Pace

The default holds suit someone meeting a character for the first time. A learner
who already knows the deck wants it to move, and being held at beginner timing
for 20 cards is the difference between a drill and a chore. The control sits
directly under the options, persists as `jp.pace`, and steps with `[` and `]`.

| Step | Name | Factor | Correct hold | Wrong hold |
|---:|---|---:|---:|---:|
| 1 | relaxed | 1.00× | 1,900 ms | 2,900 ms |
| 2 | steady | 0.70× | 1,330 ms | 2,030 ms |
| 3 | brisk | 0.50× | 950 ms | 1,450 ms |
| 4 | fast | 0.35× | 665 ms | 1,015 ms |
| 5 | relentless | 0.20× | 380 ms | 580 ms |

Holds are floored at **260 ms**: below that the verdict colour is not
perceptible, and the whole point of the hold is that a wrong answer can be read.
Skip keeps its own brisk constant (250 ms) and does not scale — there is no
verdict to read.

> **Verification note.** The step table above is computed from the constants in
> `study.js`. One end-to-end timing was measured in the running window (355 ms
> at *relentless*, against a computed 380 ms); the slower holds were not
> measured, because the screenshot-polling harness available here is too coarse
> to time them reliably.

### Kanji cards

A kanji card is graded on its **meaning**, so its options are English. That
leaves a learner who cannot yet read kana fluently with readings they cannot
use — the opposite of a reference. Three things address it:

| Feature | Detail |
|---|---|
| **Romaji under each reading** | The card back shows on'yomi and kun'yomi in kana with the Hepburn transliteration beneath (ジ → `ji`, あざ → `aza`) |
| **Readings on the options** | Each option carries the reading of the character it stands for, so three English phrases become three characters you could say |
| **Double-height options** | "world/generation" does not fit the square that suits `kya`. The kanji column widens and the tiles stop being square |

Transliteration is done by `kana.py` in wapuro romaji — long vowels written out
(シュウ → `shuu`) rather than macronned, matching the reference charts and
round-tripping back to the same kana. Option readings are **display only**;
grading still compares the option text against the answer.

### Distractor quality

Distractors are not random. In priority order:

1. **Curated visual-confusion partners** — シ/ツ, ソ/ン, る/ろ, ぬ/め, き/さ, は/ほ,
   人/入, 大/犬, 問/門 (84 hand-authored pairs across all three scripts)
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
| `[` `]` | Pace — slower / faster |
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

### The nine boards

| Script | Match Up pairs on | Confusion drill stacks |
|---|---|---|
| **Hiragana** | reading | あ/お · ぬ/め · る/ろ · き/さ · は/ほ (21 pairs) |
| **Katakana** | reading | シ/ツ · ソ/ン · ク/ワ · ル/レ (24 pairs) |
| **Kanji** | meaning | 人/入 · 大/犬 · 問/門 · 像/象 · 績/積 (39 pairs) |

### Controls and behaviour

- **Script picker**: switch alphabet without leaving the view; the mode
  descriptions rewrite themselves to match.
- **Board shape**: columns in groups of three, count chosen to minimise the
  row/column difference. 6 pairs is a centred 3×4 block, never a long strip —
  position is what a memory game trains.
- **Selection state**: amber border, glyph, fill, lift, glow and corner dot.
- **Pair sizes**: 4, 6, 8 or 10.
- **Completion**: time, moves, and efficiency against the perfect move count.
- **Fallback**: a new learner has no weak set, so the deck fills in and the games
  work on day one.
- **Deep links**: `/games?mode=confusion&script=kanji`, which is what the
  dashboard rails open.

### What they record, and what they do not

Mis-pairings **are** recorded — an unambiguous "I think this character reads as
that", better evidence than a multiple-choice guess.

They **do not** feed the drill queue or SM-2. As a board empties, elimination
makes a late match nearly free; counting that as knowledge would inflate mastery
the same way a chance floor does.

---

## 3. Dashboard & analytics

The dashboard is the landing page and the diagnostic surface. It is assembled
from **one** round trip to `/api/summary`, plus two lazy calls for the games
catalogue and the heatmap.

### 3.1 Instrument row

Sessions run · Cards reviewed · Overall accuracy (with sparkline) · Best streak ·
Average response · Decks in play.

### 3.2 Shelves — organised by script

Each script gets its **own shelf**, and each shelf is immediately followed by its
own games rail, so the drill and the game for what you are working on sit
together.

| Shelf | Decks | Contents |
|---|---:|---|
| **Hiragana** | 5 | gojuon 46 · dakuon 20 · han-dakuon 5 · yoon 33 · all 104 |
| **Katakana** | 5 | the same five rungs in the loanword script |
| **Kanji — Proficiency** | 5 | JLPT N5 113 · N4 169 · N3 396 · N2 236 · N1 337 |
| **Kanji — Volume** | 2 | Top 200 · Top 500 by teaching frequency |

Previously hiragana and katakana shared one horizontally-scrolling rail, which
pushed katakana off the right edge where it read as missing. Empty shelves are
hidden rather than rendered as blank cards.

A deck card carries: rung badge, three-glyph preview, an obi band doubling as
the mastery meter, and the challenge/scoring pairing it opens with. Yoon decks
preview two glyphs, because digraphs overrun the card.

**Kanji shelves and their games use a green accent**; kana keeps amber. Kana and
kanji are different undertakings — one is a closed set of 104 sounds you finish,
the other 1,251 characters you chip at for years — and with the two now stacked
one above the other, the accent is what tells you which you are looking at. Only
the accent tokens change; surfaces, ink and card stock are shared, so this is a
change of signal colour rather than a second theme to maintain.

### 3.2a The More… card, and the catalogue

Every shelf ends with a **More…** deck. It is deliberately a deck rather than a
link: it sits in the same rail and reads as "there are more of these", which is
what it means. A five-deck rail also leaves room for a sixth on a wide screen,
and the catalogue is otherwise unreachable — the app has no menu.

It opens `/decks`, which lists **every exercise in one place**: the 23 that work,
grouped by shelf, and the eight that are designed but not built.

Listing the second group is the point. A catalogue showing only what works tells
a learner nothing about where the app is going, and hiding unbuilt work invites
the same question every few weeks. Each entry carries a status —
`experimental` (designed, no implementation) or `planned` (also waiting on
content that must be sourced rather than invented) — and, critically, **what is
blocking it**. That is what stops the list becoming a wish list that implies
work is imminent.

| In development | Status | Blocked on |
|---|---|---|
| Phrases · Expressions · Adjectives | planned | A sourced list; the reference worksheets do not cover them |
| **Alternate phrases** | experimental | Needs a card type that grades a *set* of right answers. Thanks is ありがとう *and* どうも *and* 感謝します; sorry is すみません *and* ごめん *and* 失礼します. The engine has exactly one correct option per card |
| Politeness registers | planned | The same one-to-many problem — 食べる / 食べます / いただきます |
| Reactions (相槌) | planned | A sourced list; the worksheets do not cover conversation |
| Verbs | planned | Conjugation is a generator, not a card list — it needs its own exercise type |
| Word combinations | experimental | Derivable from the seeded kanji, but the pairings need checking |
| Counters | experimental | A closed set and safe to author; not yet written |
| Typed recall | experimental | Roadmap M1 — scoring is ready, the input mode is not |
| Listening | experimental | Roadmap M7 — the clip library and endpoint already exist |

### 3.3 Memory-training rails

Deliberately a different object from a deck: landscape, a miniature of the board
they deal (Pelmanism's is genuinely half-covered), what they train instead of
progress, an `unscored` tag, and a coloured edge per mode.

### 3.4 Per-character miss rate

The headline diagnostic, rebuilt as a map of a **set** rather than of your
attempt log.

| Control | Behaviour |
|---|---|
| **Set selector** | Hiragana · Katakana · Kanji N5 · N4 · N3 · N2 · N1 · Top 200 |
| **Table toggle** | The same data as a ranked work list: character, reading, seen, missed, miss rate |
| **Cell click** | Starts a drill session on that character alone |
| **Footer** | `N characters · set mean X% · weakest 字` |

Two decisions worth stating:

- **Characters you have never seen are shown**, dashed and empty. A grid built
  from the `attempts` table alone silently hides everything untouched, which is
  precisely the most actionable thing the panel could tell you.
- **The colour ramp tops out at 30% miss rate**, not 100%. Above 30% a character
  is simply failing; below it is where the differences a learner can act on
  live, and a 0–100% ramp flattens all of them into the same dim wash.

Set mean is accuracy over *attempts*, not the mean of per-character rates — ten
tries at one character should not weigh the same as one try at ten.

### 3.5 Streak

| Element | Detail |
|---|---|
| **Hero figure** | Longest consecutive-day run on record, with the current run beside it |
| **28-day strip** | One cell per day in four load bands |
| **Weekly table** | Last four weeks: sessions · reps · mean accuracy, labelled W-0 … W-3 |

Streaks count **distinct dates**, not sessions: two sessions in one evening is
one day of the habit. The current run survives today being empty — it breaks
only once a whole day has been missed, or it would read zero every morning.

Four load bands rather than a continuous ramp, because the question the strip
answers is "did I study, and roughly how hard", which four bands answer and a
256-step gradient does not.

### 3.6 Weak characters

A ranked grid: glyph, reading, error rate, and a bar of that rate so the column
reads as ranked before you take in any numbers. Clicking a card drills it;
**Drill weak set** opens the whole set as one session.

Ranking is recency-weighted — a miss yesterday outranks one 120 days ago — and
skips weigh 1.25×, because guessing wrong still shows a partial trace whereas
passing means no recall at all.

### 3.7 The remaining panels

| Panel | What it computes |
|---|---|
| **Accuracy per session** | Trend, oldest first |
| **Accuracy by set** | Per deck |
| **Retention curve** | Accuracy bucketed by days since that character was last seen |
| **Leeches** | High lapses relative to reps — repeatedly relearned and re-forgotten |
| **First vs eventual** | Genuine recall against within-session pattern-matching |
| **Progress velocity** | Newly mastered per week |
| **Session history** | Date, deck, challenge, scoring, cards, accuracy, average, streak, score |

**Mastery** = `seen ≥ 3 AND miss_rate ≤ 0.15`. Deliberately conservative; three
exposures is the minimum at which a rate means anything.

**Every metric is derived at query time** from an append-only `attempts` table,
so a new metric applies retroactively to all existing history — no migration, no
backfill. Every one returns a sensible empty structure on a fresh install.

### 3.8 Removed, and why

| Panel | Reason |
|---|---|
| **Response latency** | Removed on request. Latency conflates thinking with reading speed and with being interrupted |
| **Confused with** | Removed on request. The confusion drill acts on the same signal without asking the learner to interpret a matrix |
| **Time of day** | Removed on request — no action followed from it |
| **Mastery by group** | Removed on request; the shelves already carry per-deck mastery |

All four are gone end to end — query, endpoint payload, renderer and markup —
rather than hidden with CSS.

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
| Words · days | **7** | extracted from the reference worksheets |
| Words · months | **12** | same |
| Words · numbers | **36** | same |
| Words · time | **16** | same |
| Words · demonstratives | **20** | こそあど, authored — a closed 4 × 5 grid |
| Words · particles | **15** | authored — the closed set a beginner meets first |
| Confusion pairs | **84** | 21 hiragana · 24 katakana · 39 kanji |

**1,565 cards in total**: 1,459 characters, of which 1,251 are kanji, plus 106
whole words.

### Words

The first decks whose prompt is a **word** rather than a glyph. The engine
needed no change — a word sits in `glyph` exactly as a character does, is graded
on `meaning` the way kanji already were, and carries its reading in `romaji`.
What changed is presentation: 月曜日 and "Wednesday" need more room than あ and
"a", so word cards and their options are wider.

Days, months, numbers and time were **extracted** from the reference worksheets.
Demonstratives and particles were **authored**, because the worksheets do not
cover them and both are closed, rigidly structured systems that every N5 course
teaches identically — unlike open vocabulary, where writing entries from memory
would produce confident, plausible, unverifiable data.

**Distractors come from the same set.** Offering "March" against a 月曜日 card
can be solved by category rather than by knowing the word.

### Phrase sets

Each set is chosen because **one structure generates all of it**. Learn that
〜ましょう turns a verb into "let's" and 行きましょう, 食べましょう and 飲みましょう
arrive together — a different kind of learning from memorising ten unrelated
sentences, and what makes these worth cards.

| Set | Pattern | Reach |
|---|---|---|
| **Saying you like it** | Adjectives and nouns that stand alone — no grammar attached | Reacting well is most of early conversation |
| **At the convenience store** | A complete transaction, ordered as it happens | Ask for a bag, say how you are paying, ask the price — a real errand, start to finish |
| **Let's — ましょう** | Polite stem + ましょう. 行きます → 行きましょう | One rule turns every verb you know into an invitation |
| **Please — てください** | te-form + ください. 待って → 待ってください | The same rule turns any verb into a polite request |
| **Getting by** | A stock, not a pattern | The highest-reach set here: these work in any situation |

**Politeness is consistent inside a set.** Mixing 行こう with 食べましょう would
teach register as noise rather than as a choice, so the volitional set is
uniformly polite and the casual forms belong to a future set of their own.

**On accuracy.** These are authored, not extracted — the reference worksheets
cover vocabulary, not conversation. That is defensible only because each set is
either rule-governed (〜ましょう and 〜てください are mechanical) or a small stock
every beginner course teaches identically. Open-ended phrase vocabulary is
deliberately still absent, and stays on the catalogue as unbuilt.

Phrase deck titles drop the script prefix: the shelf is already called Phrase
Sets, so "At the convenience store" says what the deck is without wrapping the
card onto two lines.

### One glyph, two meanings

は is a hiragana character *and* the topic particle. 一 is a kanji *and* the
number one. They are different learning objects with different answers, so
`characters` is unique on **`(glyph, script)`**, not on `glyph` alone.

That was not the original design. Seeding the word sets against a glyph-unique
table silently *overwrote* 41 characters — the Top 200 kanji deck quietly shrank
to 175 — because an upsert keyed on glyph treated the particle は and the
character は as the same row. Fixed by rebuilding the table with the wider
constraint; ids are copied verbatim, so existing attempt history keeps pointing
at the same characters.

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

### N5 correction

The original N5 module and the reference chart differed by six characters each
way. **夕 田 外 青 赤 言** were on the chart but missing from the transcription,
and all six are inside the Top 200 by frequency, so without them the volume
tiers could not be complete. They were added by hand in the curated N5 style,
with stroke counts and okurigana notation. The six the module has that the chart
does not (鳥 帰 犬 早 字 魚) were left where they are — they are legitimate
characters, and moving them would change which deck an existing learner's
history sits under for no gain.

### The volume tiers

`kanji:top200` and `kanji:top500` slice a **`frequency_rank` column**, populated
from `content/kanji_frequency.py` — the 500-glyph order taken from the printed
Top 200/500 flash-card decks in the same reference repository, so screen and
paper agree. The Top 200 set was verified to be exactly the first 200 entries of
the Top 500.

This is a **teaching** order, not a corpus frequency count: it front-loads
numbers, days and the characters a beginner meets first. It deliberately crosses
JLPT levels — that is the point of the tier.

Before this the keys resolved to "the first N kanji by id", which after seeding
N5 first would have advertised a mostly-N5 set as the Top 200. Labelling that
"Top 200" would have been false, so the ranking column was added rather than the
label kept.

### Difficulty keys — all 17

| Script | Keys |
|---|---|
| Hiragana | `hiragana:{gojuon,dakuon,handakuon,yoon,all}` |
| Katakana | `katakana:{gojuon,dakuon,handakuon,yoon,all}` |
| Kanji · JLPT | `kanji:{N5,N4,N3,N2,N1}` |
| Kanji · volume | `kanji:{top200,top500}` |

Every one now resolves to characters; a key with none is omitted from
`/api/segments` rather than offered as an empty deck.

### Data guarantees

**59 tests** guard the content: Hepburn traps (し=shi, ち=chi, つ=tsu, ふ=fu,
じ=ji, を=wo, ん=n), forbidden kunrei forms, Unicode block membership, reading
conventions, no duplicate glyphs, every confusion-pair glyph seeded, and the
totals quoted in this document and the README asserted against the seed set —
those drifted once already when the six N5 characters were added.

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

**23 endpoints** — 3 views and 20 JSON. All errors return `{"code", "message"}`
with an appropriate status.

### Views

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Dashboard |
| `GET` | `/study` | Study view. `?difficulty=`, `?challenge=`, `?scoring=`, `?characters=` |
| `GET` | `/games` | Memory games. `?mode=`, `?script=` |

### Study & content

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/summary` | Every dashboard panel, one round trip |
| `GET` | `/api/segments` | The 17 difficulty keys with live counts, plus challenge and scoring axes |
| `GET` | `/api/heatmap?difficulty=` | One set's characters with miss rates, **including unseen ones** |
| `GET` | `/api/character/<id>` | Character detail plus recall history |
| `GET` | `/api/audio/<id>?voice=` | Pronunciation; always returns playable bytes |
| `GET` | `/api/credits` | Attribution the active audio provider requires |
| `POST` | `/api/session` | Start a session; `character_ids` overrides `difficulty` (the drill path) |
| `POST` | `/api/session/<id>/attempt` | Record an answer |
| `POST` | `/api/session/<id>/end` | Finalise |

### Games

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/games` | Catalogue of all 9 boards with live previews |
| `POST` | `/api/game/board` | Deal a board — `mode`, `script`, `pairs`, `character_ids` |
| `POST` | `/api/game/mispair` | Record a wrong pairing |

### Profiles & data

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/profiles` | Every profile, active one flagged |
| `POST` | `/api/profiles` | Create and switch to a profile |
| `POST` | `/api/profiles/activate` | Switch, reopening the database |
| `DELETE` | `/api/profiles/<slug>` | Delete a profile and its database |
| `GET` | `/api/data/summary` | What a reset would remove |
| `GET` | `/api/data/export` | Progress as a portable document |
| `POST` | `/api/data/import` | Load an export back |
| `POST` | `/api/data/reset` | Wipe progress — requires `{"confirm": true}` |

---

## 8. Module reference

**7,473 lines across 32 Python modules, zero import cycles.** Full audit:
[STACK-VERIFICATION.md](STACK-VERIFICATION.md).

### Layering

```
leaves        models · config · scoring · audio_library · tts_* · kana
                  · confusions · kanji_frequency
    ↓
core          db · profiles
    ↓
domain        analytics · session · games · audio · userdata
    ↓
composition   routes.api · app · __main__
```

### Backend

| Module | LOC | Responsibility |
|---|---:|---|
| `models` | 142 | Frozen dataclasses: `Character`, `CharacterSeed`, `Attempt`, `Session` |
| `config` | 153 | XDG-derived paths, `JP_*` env overrides |
| `db` | 365 | aiosqlite layer, schema, additive migrations, difficulty-key queries |
| `scoring` | 161 | Four schemes, SM-2 `next_review()` |
| `session` | 385 | Deck building, choice generation, option readings, attempt recording |
| `analytics` | 664 | 15 metric functions, character grid, deck shelves, session history |
| `games` | 301 | Script-scoped board dealing for three modes, per-script catalogue |
| `kana` | 196 | Kana → Hepburn romaji, for the kanji reading reference |
| `profiles` | 226 | One database file per learner; create, activate, delete |
| `userdata` | 217 | Export, import and reset of progress |
| `audio` | 614 | Provider chain, caching, speech-text derivation |
| `audio_library` | 337 | Clip validation, manifest, cross-voice consistency |
| `tts_voicevox` | 263 | Local Japanese-native provider, accent extraction |
| `tts_elevenlabs` | 200 | Cloud fallback provider |
| `voicelab` | 412 | Audition / cost / build / verify / warm / speakers / accent |
| `routes.api` | 382 | JSON surface, 20 endpoints |
| `routes.views` | 25 | Three HTML views |
| `app` | 84 | Quart factory, profile-aware DB lifecycle |
| `__main__` | 324 | CLI, pywebview shell, graceful fallback |

### Content

| Module | LOC | Contents |
|---|---:|---|
| `content.hiragana` | 119 | 104 characters |
| `content.katakana` | 119 | 104 characters |
| `content.kanji_n5` | 172 | 113 · hand-curated, with stroke counts and okurigana notation |
| `content.kanji_n4` | 220 | 169 · extracted from the reference chart |
| `content.kanji_n3` | 447 | 396 · extracted |
| `content.kanji_n2` | 287 | 236 · extracted |
| `content.kanji_n1` | 388 | 337 · extracted |
| `content.kanji_frequency` | 36 | 500 glyphs in teaching order |
| `content.confusions` | 105 | 84 visual-confusion pairs |
| `content.loader` | 113 | Idempotent upsert by glyph, frequency ranking |

### Frontend

No bundler, no framework, no build step.

| Asset | Lines |
|---|---:|
| `static/css/theme.css` | 3,185 |
| `static/js/dashboard.js` | 791 |
| `static/js/study.js` | 593 |
| `static/js/games.js` | 295 |
| `templates/*.html` | 461 |

---

### Correct-answer cues

A short sound plays when a study card is answered correctly and when a memory
board pairs a match — the same event to a learner, so the same feedback.

| Aspect | Detail |
|---|---|
| **Choice of seven** | Ding · Chime · Bell · Marimba · Arpeggio · Sparkle · Blip, picked in Settings → Audio. Choosing one plays it |
| **API** | Web Audio, not `HTMLAudioElement`. Decoded once into an `AudioBuffer`; each cue is a fresh `BufferSourceNode` through a `GainNode` — sub-millisecond, overlapping safely, with an explicit level |
| **Autoplay** | The `AudioContext` is unlocked on the first pointer/key/touch event and re-resumed per cue, since the engine suspends it when the window loses focus |
| **Timing** | Fired *before* the attempt is posted. The cue is feedback on the click; waiting on the round trip put it audibly late |
| **Level** | Assets peak-normalised to ≈ −0.4 dBFS and attenuated in code. Measured at the speakers: −1.4 dBFS |
| **Master switch** | Settings → Audio → Sound. Off silences cues *and* pronunciation everywhere. Composes with the study view's `M` mute and volume |
| **Diagnostics** | `window.jpSound.soundStatus` reports support, context state, decode state, play count, last error and storage availability. **Test sound** in Settings reports which of those is the problem |

Full reference — the cue set, the Web Audio graph, autoplay unlocking, levels,
how it was verified and how to add a cue: **[INTERFACE-SOUND.md](INTERFACE-SOUND.md)**.
Asset contract: [`static/audio/sounds/README.md`](../src/japanese_practice/static/audio/sounds/README.md).

### Preferences

Pace, voice, volume, master mute and the chosen cue are stored **on the server**,
in the active profile's own database file.

That is not the obvious choice for interface settings, and it was arrived at by
elimination. The desktop webview accepts `localStorage` writes and silently
drops them, which first made the audio toggle look inert. Moving the authority
into memory fixed the toggle *within a page* — but `/study` is a full page
navigation, so the study view started with an empty cache and fell back to
defaults. A cue chosen on the dashboard never applied. Pace, voice and volume
had been failing the same way, unnoticed, because nothing visibly contradicted
itself the way a toggle does.

Because each profile is already a separate database file, the `preferences`
table is per-profile without a profile column, and settings now survive both
navigation and restarting the application.

| Aspect | Detail |
|---|---|
| Endpoint | `GET` / `PUT` / `POST /api/preferences`. `POST` exists because `navigator.sendBeacon`, used to flush on `pagehide`, cannot `PUT` |
| Keys | A closed set — `jp.sound`, `jp.cue`, `jp.volume`, `jp.muted`, `jp.voice`, `jp.pace`. Unknown keys are rejected rather than ignored |
| Limits | Values capped at 64 characters. An open key-value store reachable from the page is a way to fill someone's database |
| Reads | Synchronous, against a cache primed at start-up |
| Writes | Applied immediately, flushed on a 250 ms debounce, so dragging a slider is one request |

### Regenerating the screenshots

`tools/demo_data.py` writes a fabricated study history — repeats, a stable set
of problem characters, skips, slow-corrects and a run of consecutive days — so
every analytics panel has something to render. It is deterministic, so
regenerating the README screenshots does not silently change every number in
them.

```bash
python tools/demo_data.py --db /tmp/demo.db
JP_DB_PATH=/tmp/demo.db python -m japanese_practice
```

Point it at a throwaway database, never at your own.

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

## 10a. Profiles and your data

Reached from **Settings** in the dashboard top bar.

### Profiles

Each profile is a **separate database file**, not a column on a shared one.
Every analytics query in this project reads `attempts` directly; a `profile_id`
would mean threading a filter through all of them, and one forgotten `WHERE`
would quietly mix two learners' histories — a failure that looks like bad data
rather than a bug. A file cannot be half-filtered.

| Action | Effect |
|---|---|
| Create | Registers the profile and switches to it. Its database is created on first use |
| Use | Reopens the connection on that profile, then reloads the page |
| Delete | Removes the profile and its database, including the WAL sidecars |

The default profile keeps using the existing `db_path`, so an install that
predates profiles becomes "Default" with its history intact and nothing to
migrate. The default profile and the active one cannot be deleted.

### Save and load

**Save progress** writes a JSON document containing every session, attempt and
review state. **Every row is keyed by the character's glyph, never its id** —
ids are an artefact of seed order, and seed order has already changed once in
this project's life, so an export taken before the kanji expansion would point
at different characters after it. A glyph *is* the character.

Loading replaces the active profile's progress. Glyphs this build does not have
are skipped and counted rather than aborting the restore, so an export from a
future version still returns everything it can. The file is refused outright if
its `format` or `version` is not one this build reads.

The `characters` table is content, not progress: it is reseeded from the bundled
modules on every start and is never exported, which is what keeps the file small.

### Reset

Clears `sessions`, `attempts` and `review_state` for the active profile and
leaves the seeded characters alone. It requires explicit confirmation at the API
as well as in the UI — an unconfirmed request changes nothing — and reports what
it removed, because a destructive action that says nothing is indistinguishable
from one that failed.

---

## 11. Deliberately not built

Stated so the absences read as decisions, not oversights.

| Absent | Why |
|---|---|
| Joyo grades | The JLPT levels and the frequency tiers are both seeded; the Joyo school-grade axis is not, and no deck advertises it |
| Stroke counts beyond N5 | The reference charts do not carry them, so N4–N1 leave the field unset rather than filling it with guesses |
| Typed-recall mode | Planned. Until it exists, "mastery" means recognition at a 33% chance floor, not free recall |
| `recall`, `timed`, `listening`, `mixed` challenges | Stored and displayed but **not yet branched on** — they currently render as recognition |
| Accounts, sync, telemetry | Local-first by design. Profiles are local files; sharing progress means sharing a file you exported deliberately |
| Negative marking | Belongs only in an opt-in exam mode; it depresses low-confidence learners |
| Character Runners | Evaluated and recommended against — highest build cost, lowest reading-per-minute |

Everything outstanding, with acceptance criteria: [ROADMAP.md](ROADMAP.md).
What changed and why, cycle by cycle: [RELEASE-NOTES.md](RELEASE-NOTES.md).
