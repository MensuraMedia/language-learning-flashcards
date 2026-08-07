# Design Direction Comparison — Japanese Practice Flash-Card App

Five self-contained mockups, one per design direction, evaluated against
`DESIGN-BRIEF.md` and `_reference/JAPANESE-CONTENT-MODEL.md`.

**Date:** 2026-08-06 · **Files:** `/home/user/projects/japanese_practice/mockups/`

---

## 1. How to view

All five are single-file static HTML with everything inlined. No server, no build
step, no network. Open them directly from disk:

```bash
# Open one direction in the default browser
xdg-open /home/user/projects/japanese_practice/mockups/04-data-studio.html

# Open all five at once (each in its own tab)
xdg-open /home/user/projects/japanese_practice/mockups/01-hud-command-deck.html
xdg-open /home/user/projects/japanese_practice/mockups/02-zen-focus.html
xdg-open /home/user/projects/japanese_practice/mockups/03-arcade-ladder.html
xdg-open /home/user/projects/japanese_practice/mockups/04-data-studio.html
xdg-open /home/user/projects/japanese_practice/mockups/05-tactile-deck.html

# Or explicitly, with a file:// URL
firefox 'file:///home/user/projects/japanese_practice/mockups/04-data-studio.html'
chromium 'file:///home/user/projects/japanese_practice/mockups/04-data-studio.html'
```

To preview one inside the eventual desktop shell — pywebview loads a local path
directly, so a throwaway harness is enough:

```bash
/home/user/projects/japanese_practice/.venv/bin/python - <<'PY'
import webview
webview.create_window(
    "Mockup", "/home/user/projects/japanese_practice/mockups/04-data-studio.html",
    width=1440, height=980, resizable=True)
webview.start()
PY
```

**Resize the window while viewing.** The brief requires the layout to hold down to
~900px, and three of the five have defects that only appear between roughly 900px
and 1200px. Drag the window narrow before you judge any of them.

**Note on rendering mode:** `01`, `03` and `04` have **no `<!DOCTYPE html>`** —
they open with a comment block, then `<meta charset>`. Browsers render these in
**quirks mode**, which changes box-model and percentage-height behaviour. `02` and
`05` declare a doctype correctly. This is a one-line fix in each, but it means the
three affected files are not currently being rendered the way their CSS assumes.
Judge them knowing that; do not read layout wobble as a design failure.

---

## 2. Comparison matrix

| | 01 HUD Command Deck | 02 Zen Focus | 03 Arcade Ladder | 04 Data Studio | 05 Tactile Deck |
|---|:---:|:---:|:---:|:---:|:---:|
| **Front face = character alone** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Flip animation works** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Speaker icon present** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Dashboard: per-session stats** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Segments: challenge × scoring × difficulty** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Readings correct (no fabrication)** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Terminology & counts correct** | ❌ 6 errors | ✅ | ✅ | ⚠️ 1 conflation | ⚠️ 2 errors |
| **Self-contained (no network)** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Valid doctype** | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Debian-safe font stack** | ✅ | ⚠️ Inter/JetBrains first | ✅ | ✅ | ⚠️ mono on CJK readings |
| **Responsive to 900px** | ⚠️ clip 900–1150px | ✅ | ✅ | ⚠️ type ~5.8px in rails | ✅ |
| **Brief: data-dense composition** | ✅ strongest | ❌ deliberately opposite | ✅ | ✅ | ✅ |
| **Blocking defects** | 4 | 2 | 2 | 5 | 3 |
| **Minor defects** | 8 | 12 | 11 | 10 | 9 |
| **Score** | **8.5** | **8.5** | **8.5** | **9.0** | **8.5** |

Legend: ✅ met · ⚠️ met with qualification · ❌ not met.
"Blocking" is defined in §4.

---

## 3. The five directions

### 01 — HUD Command Deck (`01-hud-command-deck.html`, 1,608 lines)

**Commits to:** study as instrumentation. The whole app is framed as a telemetry
console — a `topbar` with `Operator KANA-01`, `Session S-0147` and a live `Uptime`
clock, a 12-column grid of `.panel.tk` modules each stamped with a fake module ID
(`MOD/GAUGE-01`, `MOD/TREND-02`, `MOD/LOG-07`), and a corner-tick motif implemented
as a pure-CSS eight-gradient background rather than pseudo-elements. Six KPI tiles
run across the top (lifetime accuracy 81.4% with an inline microbar, sessions
logged, total reps, streak, mean latency, D7 retention), then a character-set gauge
bank, a dual-scale session telemetry chart, a segments table, a difficulty ladder,
a 28-day heat map and a full 11-column session log.

**Does well:** this is the densest and most brief-faithful composition of the five,
and its segments module is the best in the set. The `.segtable` renders challenge
type, scoring scheme and difficulty as **three separate columns** across three
switchable tracks (kana ladder / JLPT / volume), with an `Arm ▸` button per row and
a companion "Scoring schemes" panel that spells out the actual formulas
(`accuracy × (target / response ms)`, `SM-2 interval · ease 1.30 – 2.50`). The
difficulty ladder below it states its own unlock rule — "a rung unlocks at 90% on
the previous" — which is the only place in any of the five that explains *why*
segments are ordered. The card view keeps the instrument frame (a `.reticle`
crosshair over the card, a "Segment spec" panel, an SRS queue readout), and the
speaker is a hand-built inline SVG with `stopPropagation()` so it never flips the
card. The arithmetic that matters is real: last-16 reps sum to exactly the 1,067
the KPI claims.

**Falls short:** it has the worst Japanese-accuracy record of the five — six
distinct terminology and count errors, including labelling the 1,372-card
"Complete" tier as 常用漢字 while the same file separately lists Joyo as 1,521, and
using 学/生/中/上 as N4 exemplars when its own N5 deck contains 学 and 生. A
`132 / 530` gauge has a denominator that corresponds to nothing in the content
model. Several of its most prominent numbers are also internally false: the heat
map contains a zero-activity day inside a window it labels a 34-day streak, and the
"Mean latency 1.91s" KPI is just the newest session's figure under a lifetime
label. Because the direction's entire claim is *these are instruments, trust the
readouts*, wrong readouts damage it more than they would damage any other
direction here.

**Suits:** a user who wants the app to feel like a cockpit and reads numbers for
pleasure. It is the right choice if density and the segment/ladder model are the
priority and you are prepared to do a full data-correctness pass.

---

### 02 — Zen Focus (`02-zen-focus.html`, 1,030 lines)

**Commits to:** radical restraint, and it does not blink. The dashboard is a single
narrow column of five numbered sections — `01 Standing`, `02 Trend`, `03 Sessions`,
`04 Practice`, `05 Needs attention` — separated by generous silence, opening with a
full-width statement headline ("Twelve days unbroken. / *One character at a time.*")
over a `一文字ずつ` subtitle. Standing is three enormous figures with quiet captions.
The card view strips almost everything: a deck name, the glyph at `clamp()`-scaled
size with corner ticks, a `Got it` / judge row, a position counter and a hint line
of `<kbd>` keys.

**Does well:** it is the cleanest file in the set — the only one with **zero
Japanese accuracy errors and correct terminology throughout**, and every reading,
count and level name checks out against the content model. It has the best flash
card of the five as a *card*: `perspective:2200px`, a genuinely large glyph, no
competing chrome, and a speaker whose cone/wave/ripple animation and "Playing…"
state feel like a deliberate moment rather than an icon. Its interactive trend
chart with hover scrub is elegant, and the six-row session table with
`+ 35 earlier sessions` is honest about being a preview. Small details are right:
6 August 2026 really is a Thursday, and 6 shown + 35 earlier = the 41 lifetime
sessions it claims.

**Falls short:** it directly contradicts a stated brief requirement — "pack many
small charts and stat readouts into a tight grid rather than a few large cards."
That is the thesis, not an oversight, but it is a requirement traded away and you
should decide consciously whether you want it back. Beyond that, its numbers drift:
"Mean 79%" is asserted over a last-12 window whose actual mean is 74.2%, the
"Twelve days unbroken" headline is contradicted by its own session list (no
sessions on 3 or 5 Aug), and "Hiragana 91%" cannot be reconciled with its own
sub-segment figures (weighted, they give 84.4%). The progress bar uses
`pos/deck.length`, so it never reaches 100% and snaps back to 0% on wrap. Its font
stacks lead with Inter and JetBrains Mono, neither of which exists on Debian, so
the intended type never actually renders.

**Suits:** a user who studies in the evening and wants the app to lower their heart
rate. It is the wrong choice as a whole-app direction if the dashboard's job is to
tell you things — but its card view is the best card view here and should survive
regardless of which direction wins.

---

### 03 — Arcade Ladder (`03-arcade-ladder.html`, 1,551 lines)

**Commits to:** progression as the organising idea. A three-column dashboard —
left rail with a rank badge (`四 / 4 DAN`), an XP bar (`12,480 / 16,000`), a 28-day
streak grid, per-set accuracy bars and "Bonus stages"; a centre column that is
nothing but the ladder itself under a `Climb the *ladder*.` headline with
kana/JLPT/volume track tabs; a right rail with score-per-session bars, a session log
and weakest characters. The run view is a proper arcade HUD: a stage badge, card
counter, lives pips, a run score with a `+N` floater, a combo meter with multiplier,
and a 20-cell run strip under a stated clear condition — "Clear target **85%** to
unlock the next rung."

**Does well:** it is the only direction where the difficulty ladder is the primary
navigation rather than a table, and it is the only one that answers *what do I do
next* without the user having to decide. Every rung tile carries all three brief
axes as visible tags — `.tag.chal`, `.tag.score`, and a Diff n/5 five-pip meter —
so the ladder doubles as the segments list. Japanese content is **clean: every kana
pair, every one of the 20 N5 kanji triples, and every count matches the reference**,
and the header comment's `46+20+5+33 = 104` breakdown reconciles exactly. The
"Cleared 6/17" figure matches the real rung inventory. Session history is real, not
aggregate: 14 dated sessions render as an interactive bar chart with per-bar
tooltips *and* as a scrollable log with PB / CLEAR / UNDER-85% verdicts.

**Falls short:** the game layer is a costume over a single generic drill. `judge()`
decrements `lives` to zero and nothing ever checks it — the run continues past zero
lives, so the arcade thesis is unfalsifiable in the mockup. Challenge type is
label-only: Recognition, Recall, Timed and Mixed all run identical mechanics, there
is no timer on the Timed stages, and no listening challenge exists at all despite a
working speaker. Deck routing contradicts the rung you clicked — pressing Replay on
kana stage 04 HAN-DAKUON opens a HUD labelled stage 03 — and stage 03 is labelled
`DAKUON 濁音` while its deck contains ぱ, a han-dakuon character. Three of its four
headline chart figures are wrong (Avg 6,842 vs an actual 6,173; Trend 7d +18.2% vs
+9.4%; a 12-day streak claim over a grid showing 16 unbroken days).

**Suits:** a user who needs external motivation to open the app daily, and who
would rather be told which set to drill than choose. It is the strongest answer to
"how do I keep coming back" and the weakest answer to "what am I actually good at."

---

### 04 — Data Studio (`04-data-studio.html`, 1,446 lines)

**Commits to:** the landing page *is* an analytics surface, and the flash card is
launched out of the data rather than the data being a report on the card. A
persistent `filterbar` (Range × Track) sits under the topbar. Below it: a hero
weighted-accuracy figure with a sparkline plus four stat tiles; a full accuracy-by-
session line chart with a 5-session moving average and an accessible table twin; a
retention curve annotated with the 90% scheduler threshold; a per-character miss-rate
heatmap with a set selector and a distribution histogram beside it; a time-of-day dot
plot; weakest-characters and session-log tables side by side; and a 12-column
segments table at the bottom. The card view is a three-column studio — a left rail
of live telemetry (accuracy, answered, streak, avg response, score, answer strip,
scoring scheme), the card, and a right rail of per-character analytics (attempts,
miss-rate rank, next interval, ease factor, recall history, confusables).

**Does well:** it is the only direction that actually satisfies the brief's hardest
requirement — "statistical performance across every past exercise session, not just
a total" — as a *premise* rather than a panel. Twenty-four individually dated
sessions drive four separate views of the same data. Its chart craft is the best
here and is reasoned, not decorative: time-of-day is a dot plot specifically because
a clipped axis under bars would lie, the miss-rate histogram uses bars because counts
start at zero, and the ordered colour ramp is applied only where the categories *are*
the value bins. The thesis genuinely lands: click any heatmap cell, any Drill button,
or "Drill all 8 →" and it builds a targeted queue, sets a breadcrumb naming the panel
it came from, and keeps the analytics rails alive beside the card. The flip has the
nicest detail in the set — `showCard()` defers the face-content swap by 330ms so the
content change happens mid-rotation and is never seen. The segments table carries all
three axes as separate columns with 1–5 difficulty pips and the model's own ladder
names. Readings are perfect: all 104 kana entries and all 20 N5 kanji are verbatim.

**Falls short:** two defects strike at the thesis rather than the surface. The
time-of-day chart's data is **fabricated independently of the session array and
contradicts it** — it claims the 09–12 bucket has n=9 at 91.4% where the sessions
give n=13 at 83.9%. And the filterbar overclaims: `renderRetention()`,
`renderTOD()`, `renderHeatmap()` and `renderWeak()` take no rows argument and ignore
both Range and Track entirely, so setting Range=14D silently leaves four of six
panels showing all-time figures with no indication they are unscoped. In an
analytics-first direction, a chart that disagrees with its own source and a filter
that lies about its scope are the two worst possible bugs. Separately, `hostW()`
clamps to a 300px minimum, which breaks the file's own stated "1 SVG unit = 1 CSS
pixel" invariant — inside the 246px rails the sparkline SVG is authored at 300 and
scaled to 0.73, rendering 8px labels at ~5.8px. The speaker button is
keyboard-inoperable: the card's keydown handler catches bubbled Space/Enter from the
button and `preventDefault()`s it, so keyboard users flip the card instead of playing
the sound.

**Suits:** a user who wants to know *which characters are failing and when*, and who
will act on that. It is the direction with the most product in it — everything else
here is a menu with statistics attached, and this is a diagnostic tool that also
deals cards.

---

### 05 — Tactile Deck (`05-tactile-deck.html`, 1,722 lines)

**Commits to:** the physical card metaphor, executed literally. Decks have real
thickness — stacked `.sheet` layers, a `.contact` shadow, a `.cut` edge — and sit on
three shelves (`Kana Shelf 仮名`, `Kanji Shelf — Proficiency 漢字·級`, `Kanji Shelf —
Volume & Theme 頻度·分野`), each a horizontally scrollable rail with `.plank`
underneath and left/right nudge buttons. Every deck wears a paper *obi* band that
doubles as its progress meter. The card stage is a `.deck3d` → `.tilt` → `.lift` →
`.card3d` chain: the deck tilts under the cursor, the card lifts off the stack on an
arc, turns in 3D, and deals back. A `.recap` overlay — "Session recorded" with
accuracy, score, best streak and avg response — closes each run.

**Does well:** the metaphor is not a veneer, it is carried through every element,
and it is the only direction that makes the brief's "a score is recorded each time
the user runs the app" a *visible moment* rather than a row appended to a table.
The 3D construction is the most careful here: `perspective:1700px`, `preserve-3d`
maintained through four nested transforms, a deliberate opacity cross-swap at 300ms
as a belt-and-braces fallback, and an `.instant` class that suppresses the transition
when the next card is dealt so the deal-in never inherits the flip's easing. It is the
only direction where **the scoring scheme actually changes behaviour**: the grade bar
becomes Again/Hard/Good/Easy under SRS, a speed multiplier under speed-weighted, and
a streak multiplier under streak. Its 11-column session-history table is the most
complete of the five, and its per-run "Table log" and "Answer trail" pips give the
card view a genuine record. Readings and counts are otherwise verbatim from the model.

**Falls short:** the katakana shelf is broken at the content level — the Dakuon,
Yoon and Full-104 katakana decks all point at `k_gojuon`, so starting "Katakana ·
Dakuon + Han-dakuon" deals ア/a and カ/ka. Unvoiced kana are presented as dakuon.
One cover glyph is `ゃ`, a standalone small-ya that is not a character of the
104-set at all (yoon are two-character digraphs). And `.wcard .r` renders kanji
readings — `セイ / い(きる)` — in `var(--mono)`, a stack with **no CJK member**, with
`white-space:nowrap; text-overflow:ellipsis` in a 96px cell: this is precisely the
fallback failure the brief names, and it truncates the readings on top of it. Its
streak data is the least defensible of the five (a "Current streak 14" claim over a
`DAILY` array showing 19 unbroken days, above a session list with 2–3 day gaps
throughout that cannot support 14). There is dead code that produces a visible bug:
`S.deck.kind==='kana'?item[1]:item[1]` has identical branches, so the Table log's
"reading" column shows the English meaning on kanji runs.

**Suits:** a user who misses paper flash cards and for whom the ritual is part of
the practice. It is the most charming file here and the one whose animation budget
is most at risk against the CLAUDE.md constraint of 60fps flips and sub-100ms
perceived latency — four nested 3D transform layers plus cursor-tracked tilt is a
lot to ask of a pywebview WebKit surface.

---

## 4. Outstanding defects

**BLOCKING** = violates a hard brief constraint (self-contained, front-face-only,
working flip, speaker, per-session stats, three-axis segments, responsive to 900px,
Debian-safe fonts, correct data) **or** contains a Japanese accuracy / content-model
error. **MINOR** = everything else, including internal data inconsistency that is
invisible unless you check the arithmetic.

### 01 — HUD Command Deck

**BLOCKING**
- **Japanese terminology:** the V-ALL segment and volume ladder RUNG 3 label the
  1,372-card "Complete" tier as 常用漢字, while the same file lists JOYO ALL as 1,521
  (line 945). One term, two counts. (lines 987, 1015)
- **Japanese content:** the J-N4 segment uses 学 生 中 上 as N4 exemplars; the content
  model lists all four as N5, and the file's own N5 deck contains 学 and 生
  (lines 973, 1101–1105).
- **Japanese reading:** the WEAK entry for 生 reads `sei / iki` (line 1022). The
  reference kun'yomi is い(きる)/う(まれる) → `i(kiru)/u(mareru)`; `iki` is a truncated
  stem that appears nowhere in the model. Every other weak-cell pair is exact.
- **Japanese counts:** kana ladder RUNG 5 "FULL 104 MIX" is glossed
  ひらがな・カタカナ (line 1003). A combined hiragana + katakana mix is 208 — as the
  file's own KANA COMPOSITE gauge (185/208) states. Separately, the gauge
  "KANJI JLPT 132 / 530" has a denominator matching no JLPT sum in the reference
  (N5+N4+N3 = 675; N5–N1 = 1305; N5+N4 = 281) (line 950).
- **No `<!DOCTYPE html>`** — file opens with a comment then `<meta charset>`
  (lines 1–10), so it renders in quirks mode; `html,body{height:100%}` and other
  percentage/inline-block layout assume standards mode.
- **Responsive:** `.tablescroll` only gains `overflow-x` below 900px (line 544) while
  `body` sets `overflow-x:hidden` (line 50), so between ~900px and ~1150px the
  11-column nowrap session-log table is **clipped rather than scrollable**.

**MINOR**
- Space-key flip is dead. `#card3d`'s own keydown handler calls `setFlip()` (lines
  1579–1581) without `stopPropagation()`, and the document handler fires again on the
  same event (line 1590). Once the card has been clicked (`tabindex=0` gives it
  focus), Space flips twice = no visible change — contradicting the on-screen
  `<kbd>Space</kbd>` hint (line 852). *Highest-priority minor: click-flip still works,
  so the hard requirement holds, but a documented control is inert.*
- `Arm ▸` collapses every non-kana track to one deck:
  `const deck = track==="kana" ? … : "n5"` (line 1329). Arming J-N4, J-N3, V-200,
  V-500 or any thematic segment loads the N5 deck while the toast names the segment
  you clicked.
- "Drill weak set" (lines 1574–1576) loads the full katakana deck, not the 12 flagged
  characters, while the toast asserts "12 weak characters."
- Mean-latency KPI shows 1.91s (line 614) — exactly the newest session's 1910ms
  (line 933), not a mean. The 16-session mean is ~2.5s. The "▲ 0.14s faster" delta is
  likewise last-vs-previous under a lifetime label.
- 28-day heat map contradicts its own streak: the load array has a 0 at index 7
  (line 1360) while the panel reads "34 consecutive days" (line 736) and the KPI says
  34 (line 609).
- Weekly rollup (lines 754–757) does not reconcile with SESSIONS. W-1 · 07-27 shows
  331 reps where 07-27..08-01 totals 325; W-3 and W-2 claim 4 sessions each where only
  3 dated sessions fall in either window.
- `buildReps()` bar geometry overflows its viewBox: the last bar spans to x≈808 in an
  800-wide viewBox (clipped), and the first spans back to x≈18, overlapping the
  `100`/`0` axis labels at x=32 (lines 1296–1299).
- `SESSIONS.seg` uses "KANA / …" to mean hiragana while also using "KATAKANA / …"
  (lines 918–933); kana is the superset of both, so the log's segment column is
  ambiguous about which syllabary was drilled.
- JOYO COMPLETE done 129 (lines 945/951) is lower than the JLPT done total of 132
  (79+42+11), though all N5–N3 kanji are Joyo.

### 02 — Zen Focus

**BLOCKING**
- **Content model:** the third tier card conflates two distinct reference numbers —
  the volume ladder ends at "Complete (1,372)" but the card shows **1,521** (the Joyo
  figure) under a Top 200 / Top 500 volume triptych (lines 728–732).
- **Brief requirement traded away:** directly contradicts "Data-dense composition:
  pack many small charts and stat readouts into a tight grid rather than a few large
  cards." Deliberate to the thesis — but it is a stated requirement, and adopting this
  direction means formally waiving it.

**MINOR**
- Font stacks lead with `"Inter"` and `"JetBrains Mono"` (lines 32–33), which do not
  exist on Debian. They fall back silently, so the intended type never renders. The
  brief calls for system stacks. One-line fix.
- Katakana segment advertises "104 / complete set" but its deck is `KATA_GOJUON`
  (46 items) — starting it shows "01 / 46" (lines 712–714).
- Dakuon segment claims 25 cards, deck has 7. Yoon claims 33, deck has 6. The *counts*
  are correct per the model; the decks do not back them (lines 664–665, 708–711).
- All five JLPT segments N5→N1 share the identical 20-character `KANJI_VERIFIED` pool,
  so the N1 deck presents 日/月/火 as advanced kanji (lines 716–725). The header
  comment admits this. *Same limitation as 03, 04 and 05 — the reference supplies only
  20 kanji.*
- Trend section states "Mean 79%" over "last 12 sessions"; the TREND array's 12 values
  average 74.2%. 79% is the lifetime mean from Standing, mislabelled inside a last-12
  context (lines 487, 507, 742–755).
- Per-set "Hiragana 91%" is inconsistent with its own sub-segments (gojuon 92, dakuon
  88, yoon 71 → weighted 84.4%) (lines 707–711, 735).
- "Twelve days unbroken" contradicts the session list, which has gaps — 6, 4, 2, 1 Aug,
  31, 29 Jul, with nothing on 3 or 5 Aug (lines 458, 757–764).
- Session rows record 60 cards for "Katakana — full set" and 40 for "Kanji — JLPT N5",
  matching neither the segment counts (104, 107) nor the decks (lines 760–761).
- Progress bar uses `pos/deck.length`, so it never reaches 100% and snaps to 0% when
  the deck wraps at the last card (lines 959, 976).
- Both tier-card entries and all three volume tiers hard-wire `data-start="n5"`, so
  Top 200 / Top 500 / Joyo all launch the same N5 deck (line 830).
- Kanji segment Japanese subtitles 日常の基礎 / 動作・描写 / 抽象概念 / 報道・文学 /
  学術・文語 are invented editorial labels, not present in the content model
  (lines 716–725). They are descriptions rather than readings, so nothing is
  falsified — but they are outside the sanctioned vocabulary.
- Back-face DOM stays in the accessibility tree while the front shows;
  `backface-visibility` hides it visually only, so a screen reader reads the romaji and
  meaning before the flip (lines 319–329, 620–623). *Present in all five directions.*

### 03 — Arcade Ladder

**BLOCKING**
- **Japanese terminology:** stage 03 is labelled `DAKUON 濁音` with the note "Voiced
  marks — が ざ だ ば", but its `daku` deck includes ぱ `pa`, a **han-dakuon**
  character. The ladder's own next rung is han-dakuon.
- **No `<!DOCTYPE html>`** — quirks mode, same as 01 and 04.

**MINOR**
- Deck routing contradicts the rung clicked. Kana stage 04 HAN-DAKUON maps to deck
  `daku` (stageNo "03"), so Replay on stage 04 opens a HUD labelled stage 03. Same for
  kanji stage 02 (JLPT N4, marked *current*) and volume stage 01 TOP 200, both of which
  map to deck `kanji` whose stageNo/stage are "01"/"JLPT N5 漢字"
  (lines 1029–1031, 1060–1062, 1086–1088 vs DECKS at 1178–1184).
- Lives are decorative: `judge()` decrements `lives` to 0 (line 1502) but nothing ever
  reads it — the run continues past zero lives with no game-over state, which is the
  one mechanic the arcade thesis most needs.
- Challenge type is label-only. `runStageMode` changes text per deck but mechanics are
  identical for Recognition / Recall / Timed / Mixed — no timer on Timed stages, no
  recall input, and **no listening challenge type exists at all** despite a working
  speaker (the brief lists listening as an example type).
- Streak grid contradicts its own label: `lv` (line 1336) has its last zero at index
  11, giving 16 consecutive active days, while the panel header and HUD both claim a
  12-day live streak (lines 813–814, 754–761).
- Streak grid marks Aug 06 (`today`, level 3 = active) but SESSIONS ends 08-05 with no
  Aug 06 run — a session-free day shown as practised.
- Chart footer "Avg 6,842" (line 882) does not match SESSIONS: the 14 session scores
  average 6,173. (Best 10,940 is correct.)
- "Trend 7d +18.2%" (line 884) is unsupported — last 7 sessions average 6,449 vs prior
  7 at 5,897 = +9.4%.
- "Best combo ×14" on the dashboard and HUD (lines 764–765, 807) uses multiplier
  notation for what is a hit-streak *length*, while the in-run `mult` caps at ×5
  (line 1435). Two different quantities share the same ×N glyph.
- Deck sizes are far below the counts the ladder advertises (DAKU 7 vs "40
  characters"; YOON 6 vs 33; KANJI 20 vs N5's 107). `resetRun()` pads a 20-card run by
  concatenating reshuffles, so a yoon run repeats each of 6 cards 3–4 times.
- `showCard()` removes `.flipped` and rewrites `#back` innerHTML in the same tick
  180ms after judging, so the next card's back content swaps in mid-flip-back rather
  than after the animation settles.
- The speaker `<button>` sits inside `.card`, which itself carries `role="button"` and
  `tabindex="0"` — nested interactive controls, and the speaker is unreachable from
  the card's own Space/Enter flip handler.

### 04 — Data Studio

**BLOCKING**
- **Fabricated chart data contradicting its own source.** `TOD` (line 727) claims
  06–09 n=3, 09–12 n=9, 12–15 n=2, 18–21 n=4, 21–24 n=4; recomputing from the `hour`
  field of the 24 sessions gives 0, 13, 3, 2, 3, 3. Bucket accuracies are wrong too
  (09–12 stated 91.4% vs 83.9% actual; 21–24 stated 79.1% vs 74.8%). Only the n total
  happens to line up. In an analytics-first direction this is disqualifying for the
  panel.
- **The filterbar lies about its scope.** The comment at line 112 and the panel
  framing say the row "scopes everything below it", but `renderRetention()`,
  `renderTOD()`, `renderHeatmap()` and `renderWeak()` take no rows argument
  (line 1226) and ignore both RANGE and TRACK; `renderSegments()` honours TRACK only.
  Setting Range=14D leaves four of six panels showing all-time figures with no
  indication they are unscoped.
- **Content model:** "Volume · Joyo Complete" is given size **1,521** / "Grade 1–6 +
  Secondary" (line 822) — the model's *Joyo* row. The volume track's third tier is
  "Complete (1,372)". Two ladders conflated into one row. (Same error class as 02's
  tier card and 01's V-ALL.)
- **Responsive / legibility:** `hostW()` clamps to a 300px minimum (line 851), breaking
  the "1 SVG unit == 1 CSS pixel" invariant the comment at line 842 claims. In the
  246px rails the `cd-spark` host measures ~218px, so the SVG is authored at 300 and
  scaled to 0.73 — the 8px OLDEST / "n/12 RECALLED" labels render at **~5.8px**, and
  it is worse at the 216px breakpoint.
- **No `<!DOCTYPE html>`** — quirks mode.

**MINOR**
- Speaker is keyboard-inoperable. `el('card').addEventListener('keydown', …)`
  (line 1354) fires on bubbled keydowns from descendants and calls `preventDefault()`
  for Space and Enter. With focus on the `.spk` button inside the back face,
  Space/Enter flips the card instead of playing, and the `preventDefault` suppresses
  the button's own activation. Mouse works; keyboard does not. *Highest-priority
  minor.*
- Segment→deck mapping is wrong for 8 of 15 segments. Kanji N4/N3/N2/N1 and all three
  Volume tiers point at `deck:'kanji-n5'` (lines 816–822); "Katakana · Dakuon + Yoon"
  points at `kata-gojuon` (line 812). Launching "Kanji · JLPT N1 Literary" puts that
  name in the deckbar and crumb while dealing 日/月/火 — and the header disclaimer
  ("demo decks seeded from the verified sample set") does not reach the card view where
  the contradiction is visible.
- Heatmap set-selector labels read HIRAGANA / KATAKANA / KANJI N5 while `hm-note`
  asserts "46 characters" and "20 characters"; the model gives 104 / 104 / 107. The
  selector should read "HIRAGANA · GOJUON" or the note "46 of 104", as the segments
  table correctly does.
- Charts re-rendered while their table twin is showing measure a `display:none` host.
  Changing a filter with the trend Table toggle on makes `renderTrend()` read
  `clientWidth` 0 and fall back to W=760 (line 935); toggling back shows a 760-unit
  viewBox stretched to the panel width — exactly the type-scaling artefact the file's
  own comment warns against. `toggleTable()` never re-renders after switching back.
- Answer-strip panel is labelled "last 24" but `renderLive()` does `strip.slice(0,24)`
  (line 1377) — the *first* 24 slots of the deck. With the 20-card demo decks the two
  coincide, so the bug is latent.
- `grade()` wraps `di` back to 0 at the end of the deck (line 1368) while still
  incrementing `answered`, so the Live readout can display "21 / 20" and `strip[di]`
  silently overwrites the earlier result for that slot.
- Session-log deck naming contradicts the segments table: sessions 12/15/23 use
  "Kana · Full Mixed 104" with 104 cards, while the segment "Kana · Full Mixed" is
  declared 208 / "both syllabaries" (line 813).
- The median-response tile prints "stable across scope" whenever `msDelta <= 0`
  (line 905), so a genuine slowdown is reported as stability rather than a negative
  delta.
- Back-face content is in the DOM and exposed to assistive tech when unflipped; no
  `aria-hidden` toggle in `flip()`. Nested focusable buttons inside a `role="button"`
  card is also an ARIA anti-pattern.
- `hero-acc` renders "0.0%" rather than an em-dash when a scope yields zero sessions
  (`renderStats`, line 883) — unreachable with the current fixture, but the neighbouring
  tiles do handle the empty state.

### 05 — Tactile Deck

**BLOCKING**
- **Japanese content:** deck `kd` ("Katakana · Dakuon + Han-dakuon", lines 1119–1121)
  has `pool:'k_gojuon'` — starting it deals ア/a and カ/ka, presenting **unvoiced kana
  as dakuon/han-dakuon**. Same defect on `ky` ("Katakana · Yoon", `pool:'k_gojuon'`)
  and `ka` ("Katakana · Full mixed 全104", `k_all` = gojuon only, 46 items).
- **Japanese content:** deck `ha` cover glyphs `['ぬ','ふ','ゃ']` (line 1114) — `ゃ` is a
  standalone small-ya, not a character of the 104-set. Yoon are two-character digraphs
  (きゃ).
- **Font stack:** `.wcard .r` (line 361) renders kanji readings (`セイ / い(きる)`,
  `ジョウ / うえ`) in `var(--mono)` — a stack with **no CJK member** and no `.jp` class,
  which is precisely the fallback the brief warns against — and with
  `white-space:nowrap; text-overflow:ellipsis` in a 96px-min grid cell, so the readings
  truncate as well.

**MINOR**
- Every kanji deck (N5, N4, N3, N2, N1, Joyo, Top 200/500/Complete and all four themes)
  shares `pool:'kanji'` = KANJI_N5, so the N1 and Joyo decks deal the same 20 N5 kanji.
  Labelling is correct; the dealt content contradicts it. *Same limitation as 02, 03,
  04.*
- Cover glyphs outside the reference's verified list: ぴ/ぷ (`hh`), シュ/チョ (`ky`),
  時 (`th3`). No readings are attached, so nothing is fabricated — but they are outside
  the sanctioned sample set.
- Han-dakuon deck (`hh`) draws from a 1-item pool (ぱ only), so a 24-card run shows ぱ
  24 times; Hiragana Dakuon draws 24 cards from 6. Reference-limited, but it makes those
  difficulty rungs undemonstrable.
- Stat tile "Decks in play 22 · 8 kana · 14 kanji" (line 1243) contradicts DECKS:
  there are 9 kana decks (hg, hd, hh, hy, ha, kg, kd, ky, ka) and 13 kanji. The total is
  right; the split is wrong.
- Streak data is internally inconsistent three ways: `DAILY` (line 1220) has its last
  zero at index 8 (a 19-day run), the header/stat/panel all claim "Current streak 14"
  with "Best 23", and the 12 listed sessions (2026-07-14 → 08-05, gaps of 2–3 days
  throughout) cannot support a 14-day streak at all.
- Dead and misleading code: `d.rung.replace(/ · /,' · ')` (line 1485) is a no-op; in
  `grade()`, `S.deck.kind==='kana'?item[1]:item[1]` (line 1621) has identical branches,
  so the Table-log "reading" column shows the **English meaning** on kanji runs.
- Trend tooltip maps points to sessions via `SESSIONS[i-2]` (line 1364) — an
  undocumented magic offset created by prepending two synthetic accuracies (72, 77) to
  reach the advertised "last 14 runs". Those two points show "Mixed warm-up" and have no
  session row, so the chart's 14 and the table's 12 never reconcile.
- Stat tile labels 6,842 cards / 47 sessions as "avg 146 / day" (lines 1239–1240) —
  6842/47 = 146 is per **session**, not per day. The Streak panel repeats the number
  under "Cards / day".
- `.face.back` is hidden by opacity + `backface-visibility` but never
  `pointer-events:none`; the `#speaker` button inside it calls `stopPropagation()`, so
  on any engine where the reversed face still hit-tests, a click on that region of the
  front face is swallowed instead of flipping.
- Back-face answer DOM is populated by `renderCard()` while the card is still
  front-side-up and hidden visually only, so it remains in the accessibility tree.
- `.back-mini` reprints the kana above the romaji, so for yoon cards the only
  differentiation from a gojuon card is a 38px mini-glyph — dakuon and yoon backs read
  identically.

### Cross-cutting (all five)

- **Back-face content is in the accessibility tree before the flip** in every
  direction. `backface-visibility` is a visual property only. The fix is the same
  everywhere: toggle `aria-hidden` on the two faces inside the flip handler. This is
  the one defect that appears in all five files and should be fixed in the shared
  component rather than per-direction.
- **The kanji pool is 20 characters.** Every direction fakes N4–N1, Joyo and the
  volume tiers from the same N5 sample. That is a limitation of
  `JAPANESE-CONTENT-MODEL.md`, not of the mockups — but it means no mockup can
  currently demonstrate a real difficulty gradient on the kanji track, and the seed
  data work is a prerequisite for the real app regardless of direction.

---

## 5. Recommendation

**Take 04 — Data Studio forward.**

It is the only direction whose thesis *is* the brief's hardest requirement. The brief
asks for "statistical performance across every past exercise session — not just a
total" and for a data-dense grid; the other four treat that as a panel to satisfy,
and 04 treats it as the reason the app exists. Concretely, it is also the only one
where the flash card has somewhere to come *from*: click a cell in the miss-rate
heatmap, or "Drill all 8 →" on the weakest-characters table, and it builds a targeted
queue and sets a breadcrumb naming the panel that produced it. That is a real product
loop — *see what's failing → drill exactly that → watch it move* — and none of the
other four have one. Its chart craft is genuinely reasoned rather than decorated (the
time-of-day dot plot exists specifically because bars under a clipped axis would lie),
its readings are perfect, and it has the most transferable code.

Its two blocking defects are damning *for a mockup that claims analytical honesty* but
they are both small fixes, not structural ones: derive `TOD` from `SESSIONS` instead of
hand-writing it, and thread the filtered rows through `renderRetention`,
`renderTOD`, `renderHeatmap` and `renderWeak` (or, cheaper and equally honest, badge
those four panels "all-time" and remove them from the filter's implied scope). Both are
an afternoon.

**What to graft from the runners-up:**

1. **From 02 — Zen Focus: the card stage itself.** This is the most important graft.
   04's card is boxed between two analytics rails, which is right for a diagnostic
   session but wrong for the moment of recall — the character should be the only thing
   in the room. Take 02's `.card-scene` treatment (near-full-bleed glyph, corner ticks,
   everything else gone) and make it a **focus toggle** in 04's card view: rails
   collapse, glyph scales up, and they slide back after you grade. 02 also has the
   better speaker moment — the cone/wave/ripple animation with the "Playing…" state
   beats 04's icon-plus-label swap. Take that wholesale.

2. **From 01 — HUD Command Deck: the segments module and the ladder's unlock rule.**
   01's `.segtable` is the best expression of the three-axis requirement in the set,
   and its "Scoring schemes" panel — which prints the actual formulas
   (`accuracy × (target / response ms)`, `SM-2 interval · ease 1.30 – 2.50`) — makes
   the schemes legible instead of decorative. 04's segments table already has the three
   columns; add 01's formula panel beside it. More importantly, steal 01's stated
   progression rule, *"a rung unlocks at 90% on the previous"*, which gives the
   difficulty ladder a reason to be ordered. 04 lists tiers; 01 explains them.

3. **From 03 — Arcade Ladder: the clear condition and the run strip.** 03's
   *"Clear target 85% to unlock the next rung"* under a 20-cell run strip turns a drill
   into something with a pass/fail edge. 04's answer strip is nearly the same component
   already — give it a target line. Take the session-log verdict badges too
   (PB / CLEAR / UNDER-85%): they make 04's dense log scannable at a glance, which is
   its weakest quality. **Do not** take the rank/dan/XP layer — it fights 04's
   analytical register and 03 does not implement it truthfully anyway.

4. **From 05 — Tactile Deck: the end-of-run recap and the scheme-driven grade bar.**
   05's `.recap` overlay ("Session recorded" with accuracy, score, best streak, avg
   response) is the only place in any of the five that makes the brief's "a score is
   recorded each time the user runs the app" a visible event. 04 needs this — a run that
   ends by silently appending a row to a table undersells the whole direction. Also take
   05's approach of letting the **scoring scheme actually change the grade bar** (SRS →
   Again/Hard/Good/Easy; speed-weighted → a speed multiplier; streak → a streak
   multiplier). 04 already has an SRS grade bar; 05 shows how to make the other schemes
   more than labels. **Do not** take the four-layer 3D deck physics — CLAUDE.md requires
   60fps flips and sub-100ms perceived latency in a pywebview WebKit surface, and
   `deck3d → tilt → lift → card3d` plus cursor-tracked tilt is the riskiest thing in any
   of these files.

**What to drop entirely:** 03's lives/dan/XP gamification (unimplemented and off-register),
02's whole-app vertical rhythm (it waives a stated brief requirement), and 01's fake
module IDs (`MOD/GAUGE-01`) — they are atmosphere in a direction that should earn trust
through accuracy instead.

**Before any of this:** fix the shared `aria-hidden` flip defect once, in the component,
and add `<!DOCTYPE html>` to 04. Then do a single arithmetic pass deriving every
displayed figure from the session array rather than hand-writing headline numbers — that
one discipline would have prevented roughly two-thirds of the MINOR defects across all
five files, and it is the difference between an analytics direction that is trustworthy
and one that merely looks it.

---

## 6. Open questions for the user

These are decisions the mockups surface that the mockups cannot settle.

1. **Do you want the dashboard to be dense or calm?** This is the real fork, and 02
   exists to force it. The brief says dense; 02 argues, persuasively, that a study app
   you open every evening should not greet you with 14 panels. You can have a dense
   default with a calm focus mode, but you cannot have both as the landing view. Which
   one do you see first when the window opens?

2. **Is the app trying to motivate you, or inform you?** 03 assumes you need a reason
   to come back and gives you streaks, ranks and unlock gates. 04 assumes you will come
   back anyway and spends its surface telling you what is failing. These lead to
   genuinely different products. If the honest answer is "I need to be nagged into
   practising", 03's ladder should be the spine and 04's analytics the second tab.

3. **Should difficulty tiers gate each other?** 01 and 03 both assert unlock rules
   (90% / 85% on the previous rung); 02, 04 and 05 let you start anything. Gating gives
   the ladder meaning and gives scores stakes; it also means the app can tell you no.
   Do you want that?

4. **What is the kanji content plan?** Every direction fakes N4 through N1 from the same
   20 N5 characters because that is all the reference supplies. Real N5 alone is 107
   characters, and Joyo is 1,521. Are you sourcing the full set, restricting v1 to
   kana + N5, or shipping a partial kanji track with honest labelling? Nothing else can
   be finalised until this is answered — it determines whether the difficulty ladder is
   a real feature or a roadmap.

5. **Volume tiers or JLPT levels — or both?** The content model offers three parallel
   kanji ladders (JLPT N5→N1, Joyo Grade 1→Secondary, and Top 200→500→Complete). Every
   mockup shows two or three of them side by side, and every mockup conflates the Joyo
   1,521 figure with the volume track's Complete 1,372 at least once. That is not five
   independent mistakes; it is a sign that three parallel ladders is one too many for
   the UI to keep straight. Pick the primary one.

6. **How much motion is acceptable in pywebview?** 05's card physics are the most
   charming thing in these five files and also the most likely to drop frames on a
   WebKit surface inside a resizable native window. Do you want to spend the animation
   budget on the flip, or hold it in reserve for responsiveness? This needs a test on
   the actual target machine before it is decided on taste.

7. **Is the speaker real, or aspirational?** All five draw an inline-SVG speaker and
   fake the playback. CLAUDE.md specifies bundled clips first with a TTS fallback. For
   104 kana that is tractable; for kanji with multiple on'yomi and kun'yomi readings
   per character it is a content project of its own. Does the speaker play the
   character, or the specific reading you are being tested on — and what happens on
   kanji cards with two on'yomi?

8. **Does the app record a run that you abandon halfway?** The brief says a score is
   recorded each time the app is run. 05 is the only mockup that shows the recording
   moment, and it shows it at the *end* of a completed run. If you quit at card 9 of
   24, is that a session?
