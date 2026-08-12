# UI format specification

The formatting contract for every surface in the application: the dashboard,
the card shelves, section titles, the study table and the flash card itself.

**Why this document exists.** The same class of mistake has now been made five
times — sizing or spacing a surface locally, at the moment it was built, instead
of against a shared scale. Each fix looked right on the screen it was made for
and diverged from every other screen. The most recent example is worth stating
plainly, because it is the archetype:

> `.lbl` was used both for the label on a gauge and for the title of a section.
> When `#dashboard .lbl { font-size: 12px }` was added to lift the dashboard's
> chrome text, that ID-level rule silently captured every shelf heading on the
> page. The heading rule was correct, more recent, and lost anyway — because a
> rule that was never about headings out-specified it.

There is no way to prevent that with care alone. It is prevented by naming
things after what they *are*, and by deriving every size from a token rather
than a literal.

- **Current as of** 2026-08-10 · 350 tests passing
- **Source of truth** `static/css/theme.css` §5 (tokens) ·
  [`study.js`](../src/japanese_practice/static/js/study.js) (card sizing)
- **Companion** [CARD-DIMENSIONS.md](CARD-DIMENSIONS.md) — the content-driven
  sizing rule for cards, options and recap tiles, in depth

---

## 1. The three rules

Everything else in this document follows from these.

1. **Name a thing for what it is, not for how it looks.** `.sec-title` is a
   section title. `.lbl` is a label on a gauge. A name that describes a *role*
   cannot be captured by a rule written for a different role.
2. **Size from a token, never from a literal.** If a number appears in more than
   one rule it is a token. Changing a token must change every surface at once —
   that is the entire point.
3. **Size a surface by its content, not by its category.** "Kanji" is not a
   length. See [CARD-DIMENSIONS.md](CARD-DIMENSIONS.md) §1.

### The test for a new rule

> Could this rule be captured by a more specific rule written elsewhere for a
> different purpose?

If yes, the class is named wrong. Rename it; do not add specificity. Adding
`#dashboard .sec .lbl` to win a fight is how the drift started.

---

## 2. Type tokens

Declared once on `:root` in `theme.css` §5.

| Token | Value | Governs |
|---|---:|---|
| `--title-size` | 19px | Section titles — shelf headings, page sections, the study deck title |
| `--title-desc-size` | 13.5px | The description beside a section title |
| `--title-gap` | 14px | Title → description, on one line |
| `--title-inset` | 6px | Left inset, aligning a heading with the cards below it |
| `--title-space-above` | 38px | From the previous block to a heading |
| `--title-space-below` | 14px | From a heading to the rail it introduces |
| `--panel-title-size` | 15px | A heading one rank down, inside a panel or dialog |
| `--panel-desc-size` | 12.5px | Its description |

Under 720px, `--title-size` drops to 17px and `--title-desc-size` to 12.5px, and
the description wraps to its own line rather than being squeezed into a column
two words wide.

### Ranks

Three, and only three. A fourth rank is a sign that something is being
distinguished by size that should be distinguished some other way.

| Rank | Size | Used for | Example |
|---|---:|---|---|
| **Section** | 19px / 13.5px | The top-level divisions of a page | *Hiragana Shelf · gojuon → dakuon → …* |
| **Panel** | 15px / 12.5px | A heading inside a panel, dialog or settings group | *Audio · cues and pronunciation* |
| **Chrome** | 9.5–12px | Gauge labels, tags, counters, keys | `MASTERED`, `LV 1 · GOJUON` |

Chrome keeps its small letter-spaced uppercase form. That form is *for*
machine-ish detail, and it is exactly why it was wrong on a section heading: a
shelf title set in it read as a caption on a dial rather than as the name of the
thing below it.

---

## 3. Section headings

### Markup

```html
<section class="sec">
  <span class="sec-title">Hiragana Shelf</span>
  <span class="sec-desc">gojuon → dakuon → han-dakuon → yoon → 104 mixed</span>
</section>
```

`.sec-title` and `.sec-desc` are the **only** correct classes for a heading.
Never `.lbl` / `.lbl-sm` — those are gauge labels and are captured by the
dashboard's chrome scale.

### Geometry

| Property | Value | Reason |
|---|---|---|
| `display` | `flex`, `align-items: baseline` | Centring a 19px title against a 13.5px description leaves the description floating; baseline sits them on one line |
| `gap` | `var(--title-gap)` | |
| `margin` | `var(--title-space-above)` above, `var(--title-space-below)` below | A heading belongs to what is *below* it, so the space above is larger — 38 against 14 |
| `padding` | `0 var(--title-inset)` | Cards below carry their own border; without the inset the heading sits flush against their edge |

### Where a heading is nested

A heading inside a panel steps down to the panel rank automatically:

```css
.panel-h .sec-title, .set-h .sec-title, .hm-head .sec-title,
.streak-head .sec-title, .weak-head .sec-title { font-size: var(--panel-title-size); }
```

Adding a new panel container means adding it to that list — one place.

### Per-page rhythm

Only the *rhythm* may differ by page, never the type:

| Page | Override | Why |
|---|---|---|
| `#dashboard` | `margin: var(--title-space-above) 0 var(--title-space-below)` | Five shelves stacked, each followed by a games rail; the headings do the separating |
| `#decks` | `margin: 46px 0 0`, `.sec-major` 58px | A catalogue rather than a working surface — it breathes more |

---

## 4. The study table

```
┌─ .felt ─────────────────────────────────────────────┐
│ .felt-head                                          │
│   h1.deck-title       Please — てください        19px │
│   .felt-sub           PHRASE:REQUESTS · RECALL  9.5px │
│ ─────────────────────────────────────────────────── │
│                                                     │
│   .stage        .deck3d  │  .choices-col            │
│                          │    .choices              │
│                          │    .pace (pace + volume) │
└─────────────────────────────────────────────────────┘
```

| Element | Rank | Content |
|---|---|---|
| `.deck-title` | Section (19px) | The deck's name as the shelf shows it — `deck_title` from `POST /api/session` |
| `.felt-sub .lbl` | Chrome (9.5px) | The raw difficulty key and challenge |
| `.felt-sub .lbl-sm` | Chrome (9.5px) | The scoring scheme |

The deck title is deliberately the **same token** as a dashboard shelf heading:
the shelf heading and the table heading name the same object, and a learner
should recognise it as the same object.

`.felt-head` padding is `0 var(--title-inset) 14px` with a bottom rule, so the
title aligns with the section headings on the dashboard.

---

## 5. The flash card

Full treatment in [CARD-DIMENSIONS.md](CARD-DIMENSIONS.md). What follows is the
part that governs *format* rather than measurement.

### The back carries three registers, always in this order

| Register | Element | Type | Colour | Present when |
|---|---|---|---|---|
| Glyph | `.back-mini` | `clamp(64px, 8.5vw, 96px)` | `--ink` | Always |
| Sound | `.back-sound` | `clamp(36px, 5.6vw, 62px)` | `--amber` | Non-kanji with a reading |
| Meaning | `.back-meaning` | `clamp(17px, 2.0vw, 23px)` | `--ink` | Any card whose meaning differs from its reading |
| Readings | `.readings` | 19px rows | mixed | Kanji only — on/kun, each with romaji |
| Note | `.back-note` | 12px | `--ink-3` | Sets that carry context |

**Every card back shows the English.** It previously appeared on kanji alone, so
a phrase card revealed 見せてください / *misete kudasai* and never said it meant
"please show me" — the flip is the reveal, and withholding the translation made
the reveal incomplete for exactly the decks that need it most.

Kana are the deliberate exception: あ has a reading and no meaning, so the
meaning register is absent rather than empty, and the 5 : 7 playing-card face is
untouched.

The meaning is distinguished from the reading by **colour and weight, not
size**. It answers "what does this mean" — as important as "how does this sound"
— so shrinking it to imply subordination would be wrong.

### Card height is the sum of its registers

```js
CARD_BASE_PX     310   // frame, glyph, speaker foot
CARD_SOUND_PX     62   // the reading line
CARD_MEANING_PX   36   // per wrapped line of English
CARD_NOTE_PX      58   // the context note
CARD_READINGS_PX  96   // kanji on/kun rows
CARD_MEANING_CH   30   // the measure .back-meaning wraps at
```

A register that will not render contributes nothing. Calibrated so the two
previously known-good heights still come out exactly: 372 (`BASE + SOUND`) and
430 (`BASE + SOUND + NOTE`).

**`CARD_MEANING_CH` must match `.back-meaning { max-width: 30ch }`.** They are
the same measurement expressed in two languages; if they diverge the height is
computed for a wrap that does not happen.

### Padding

| Surface | Side padding | Reason |
|---|---:|---|
| Card face | 40px each side | Text running to the edge reads as cramped even when it fits |
| Answer option | 44px total | |
| Recap tile | 22px | |
| Section heading | 6px inset | Aligns with the card border below |

---

## 6. Colour: the kanji accent

The interface carries **one** accent, `--amber`. A kanji exercise swaps it for
green by overriding the variable — not by restyling components:

```css
.theme-kanji {
  --amber: #4ade80;
  --amber-soft: rgba(74, 222, 128, .12);
  --amber-line: rgba(74, 222, 128, .32);
  --amber-rgb: 74, 222, 128;
}
```

Anything using `var(--amber)` follows automatically. **Never write a green
literal**; a component that hard-codes the accent will not follow the theme and
will be the one thing on screen still amber.

### Where it is applied

| Surface | Applied to | Decided by |
|---|---|---|
| Dashboard shelf | `.sec.theme-kanji`, `.shelf-scroll.theme-kanji`, `.game-shelf.theme-kanji` | Static, in `dashboard.html` |
| All exercises | `.sec` / `.shelf-wrap` | `SHELVES[].kanji` in `decks.js` — a flag, not a title match, so a future kanji shelf cannot be missed |
| Study view | `body.theme-kanji` | `script` from `POST /api/session` |
| Games | `body.theme-kanji` | The selected script |
| Heatmap | `.hm-panel.theme-kanji` | The selected set |

**The accent belongs to the exercise, not the card.** It is applied once per
session from `session.deck_script()`, the single function that answers "is this
a kanji exercise?". Toggling per card made a mixed deck flicker between
palettes, and left a kanji *drill* un-themed because a drill's difficulty key is
`drill:custom` and contains no script. `deck_script()` takes the script from the
key where there is one and from the cards otherwise.

---

## 6a. Overlays: the session recap and its siblings

An overlay centres a panel in a viewport-sized parent. That shape has one
failure mode, and the recap hit it: the panel had no `max-height`, so it sized
to its content, and centring pushed the overflow off **both** ends — where
nothing scrolls. On a ten-card deck the last cards and, worse, the two buttons
that close the session were simply unreachable.

Four properties must hold **together**:

| # | Property | Rule |
|---|---|---|
| 1 | The overlay outranks all chrome | `z-index: var(--z-modal)` — above `--z-topbar` |
| 2 | The panel may never exceed the overlay | `max-height: 100%` (or `calc(100vh - 48px)` for fixed overlays) |
| 3 | The scroll area must be allowed to shrink | `flex: 1 1 auto; min-height: 0` |
| 4 | Leaving must never require scrolling | the actions are a **sibling** of the scroll area, not a child |

**Property 1 is not cosmetic.** The overlays were at z-index 6, 30 and 40
against the topbar's 60, so a panel tall enough to reach the top of the window
slid *under* the topbar — which sheared the first row off the session recap.
Scrolling could not recover it, because those pixels were not clipped, they were
**covered**. A modal the chrome can paint over is not a modal.

Raising the overlay is the right fix rather than padding it down: the panel then
gets the whole window, `max-height: 100%` means what it says, and the recap
already shows the score, streak and accuracy the topbar was contributing.

**`min-height: 0` is the other easy miss.** A flex item's default minimum size is its
content, so without it the scroll area refuses to shrink and overflows its
parent no matter what `overflow-y` says. `overflow-y: auto` on its own does
nothing here.

Property 3 is a design rule, not a layout one: a summary can be twenty cards
long, and pinning the actions means the way out is always one click away rather
than one scroll-to-the-bottom away.

### Width buys rows back

The recap panel is `min(980px, 100%)`, not the 400px it started at. Both tile
grids are `auto-fill`, so **width converts directly into columns**: a ten-card
review deck was ten rows deep at 400px and is five rows in two columns at 980px,
which fits without scrolling at all. The four session metrics use `auto-fit`
and collapse onto one row at that width, buying back the vertical space the
wider panel is meant to spend on cards.

Scrolling is the fallback, not the normal case. Measured: **10 cards fits, 14
scrolls** — and when it scrolls the actions stay pinned, so nothing is ever out
of reach.

### Which overlays this applies to

| Overlay | Bound |
|---|---|
| `.recap-card` — session recap | `max-height: 100%`, scrolling body, pinned actions |
| `.settings-card` | `max-height: 88vh`, sticky header |
| `.help-card` — shortcuts | `max-height: calc(100vh - 48px)`, sticky header |
| `.game-done-card` — cleared board | `max-height: calc(100vh - 48px)` |

`tests/test_ui_format.py` asserts all four are bounded, and asserts the recap's
three properties individually — the nesting one by **parsing** the template
rather than counting tags in a string, which is how a check like that quietly
stops meaning anything.

This is a property of the panel, not of any deck, so it holds for **every**
session: 10 cards or 20, text tiles or glyph tiles, any window size.

---

## 7. Adding a surface

1. **Heading?** Use `.sec-title` / `.sec-desc`. Do not use `.lbl`.
2. **Inside a panel?** Add the container to the panel-rank selector list in §3.
3. **New size?** Add a token, or reuse one. A literal that appears twice is a
   token that has not been named yet.
4. **Kanji-specific?** Set `.theme-kanji` on the container; never a green
   literal.
5. **Shows Japanese?** Follow [CARD-DIMENSIONS.md](CARD-DIMENSIONS.md) §7 —
   measure the longest prompt and answer, and play a session through to the
   recap.
6. **Check the three ranks read as three ranks.** If a new heading competes with
   the section above it, it is at the wrong rank — not the wrong size.
7. **An overlay?** Bound it to the window and give it a scrolling body — see
   §6a. Put any action that closes it outside the scroll area.

---

## 8. Known remaining inconsistencies

Recorded rather than hidden, because an undocumented exception becomes the next
precedent.

| Surface | State | Note |
|---|---|---|
| `.recap` title ("Session complete") | Still `.lbl` | A recap panel title; wants the panel rank, but sits inside an overlay with its own centred layout. Convert when the recap is next touched |
| `.game-done` title ("Board cleared") | Still `.lbl` | Same shape as above |
| Deck faces and game tiles | Sized by category, not content | Acceptable only because a shelf shows a fixed set — see [CARD-DIMENSIONS.md](CARD-DIMENSIONS.md) §5. **If either grows, move them to the measured rule** |
| `#dashboard` chrome scale | 20 rules stepping up chrome text | Legitimate — the generated system was tuned for a dense 1440px mock. It no longer touches headings, which is what made it dangerous |
