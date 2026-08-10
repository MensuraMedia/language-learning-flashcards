# Card dimensions

The rule every surface that shows Japanese has to follow, and the thresholds
each one currently uses.

Written because the same mistake was made **four times**: sizing a surface by
the *category* of thing on it rather than by the *content*. Each time it looked
fine on the content that existed when it was written, and broke as soon as
longer content arrived. This document exists so the fifth surface does not
repeat it.

- **Current as of** 2026-08-10 · 341 tests passing
- **Applies to** the study card, its answer options, the session recap tiles,
  the deck faces on a shelf, and the memory-game board tiles

---

## 1. The rule

> **Size by what is on the surface, not by which category it belongs to.**
> Grow only when the content requires it, and grow *width first*.

Three corollaries, each earned the hard way:

1. **A category is not a length.** "Kanji" tells you nothing about whether the
   answer is "sun" or "world/generation". "Phrase" does not distinguish 頭悪い
   from ゆっくり話してください.
2. **Extra text runs across, not down.** Each step up should widen *and* shorten.
   A taller card holds no more text; it just leaves more of itself empty.
3. **The reading is the thing that must fit.** A glyph wrapping to two lines is
   ugly. A meaning wrapping to two lines makes an option hard to scan while the
   clock is running.

### Why not just make everything big

Because the single-glyph card is 93% of the content — 1,545 of 1,658 — and its
5 : 7 playing-card portrait is the app's whole visual identity. Widening it to
suit 15 phrase cards would trade the look of the thing for an edge case.

---

## 2. Study card

`.deck3d`, sized from `document.body.dataset.cardSize`, set in `study.js`.

The face must hold, on the back: the prompt, its reading, the meaning, and —
where the set has one — the usage note.

| Bucket | Face | Prompt font | Applies when | Cards |
|---|---|---|---|---:|
| `sm` | 336 × 470 (5 : 7) | clamp 42–120px | ≤ 2 glyphs, no note | 1,545 |
| `md` | 350 × 378 (1 : 1.08) | clamp 30–46px | 3–7 glyphs, **or any card with a note** | 94 |
| `lg` | 410 × 385 (1 : 0.94) | clamp 24–38px | 8–9 glyphs, or 5+ with a note | 15 |
| `xl` | 460 × 405 (1 : 0.88) | clamp 20–31px | 10+ glyphs | 4 |

```js
const glyphLength = [...card.glyph].length;   // code points, not UTF-16 units
const hasNote = Boolean(card.note);
let cardSize = "sm";
if (glyphLength > 9) cardSize = "xl";
else if (glyphLength > 7 || (hasNote && glyphLength > 4)) cardSize = "lg";
else if (glyphLength > 2 || hasNote) cardSize = "md";
```

**A note counts as length.** It adds two or three lines to the back, so any card
carrying one starts at `md` regardless of how short its prompt is.

---

## 3. Answer options

`.choices`, via `wide` / `wider` classes.

| Class | Column width | Tile | Applies to |
|---|---|---|---|
| *(none)* | clamp 84–104px | square | kana — the answer is `kya` |
| `wide` | clamp 150–196px | ≥ 116px, not square | kanji — the answer is `world/generation`, plus a reading line |
| `wider` | clamp 190–250px | ≥ 74px (84 for phrases) | words and phrases — `please speak slowly` |

Kanji options carry a second register: the reading of the character the option
stands for. That is display only — grading still compares the option text.

---

## 4. Session recap tiles

`.recap-cards`, via `is-wide` / `is-wider` / `is-widest`.

The recap is the **one place a learner reads every card at once**, which makes
it the worst place for text not to fit — and it is easy to forget, because it
only appears after a session ends.

Sized from the widest thing in *that session*, not from a per-card rule: a grid
of mixed widths reads worse than a grid sized for its longest member.

| Class | Column min | Glyph | Applies when |
|---|---|---|---|
| *(none)* | 84px, square | 30px | widest ≤ 2 |
| `is-wide` | 122px | 26px | 3–5 |
| `is-wider` | 158px | 23px | 6–8 |
| `is-widest` | 206px | 21px | 9+ |

```js
const widest = seen.reduce((n, i) => {
  const o = state.outcomes.get(i);
  return Math.max(n, [...(o.glyph || "")].length,
                  Math.ceil((o.answer || "").length / 2.4));
}, 1);
```

**The answer counts toward the width**, divided by 2.4 to bring Latin characters
onto roughly the same scale as Japanese ones. Without that term the tiles fit
高い but not `expensive / tall`, which is what the reported defect looked like.

Above the square bucket the tiles drop `aspect-ratio` for a `min-height`, so a
tile grows downward only if it must.

---

## 5. Deck faces and game tiles

| Surface | Rule |
|---|---|
| Deck face | `.deck-wide` for the words shelf (clamp 200–264px), `.deck-phrase` for phrases (clamp 230–300px) |
| Game tile | `.tile-reading` steps down at 6 and 10 characters (`is-long`, `is-verylong`), wrapping rather than overflowing |

These two are still keyed to a *category* rather than measured content, which is
acceptable only because a shelf shows a fixed set and a board shows at most 24
tiles. **If either grows, they should move to the measured rule above.**

---

## 6. Alignment

The top edge of the card and the top edge of the first option sit on the same
line, at every size.

Two things make that hold, and both are necessary:

- `.stage` uses `align-items: flex-start`. It centred them, so whichever column
  was taller pushed the other's top out of line — and which is taller varies,
  since the card is sized by its content and the options by their answers. A
  kana card sat 23 px above the options; a phrase card 27 px below. The same bug
  in opposite directions.
- `.deck3d` uses `transform-origin: 50% 0%`. Rotating about the centre moves the
  top edge down by an amount **proportional to the card's height**, so any fixed
  correction would be right for one bucket and wrong for the other three. The
  top edge is the pivot, so it cannot move.

Verified at **0 px** on a kana card and a phrase card.

---

## 7. Adding content

When a new set arrives, check it against this list before shipping:

1. **Measure the longest prompt and the longest answer in the set.** If either
   exceeds the top bucket's comfortable capacity, add a bucket — do not stretch
   the last one.
2. **Check the study card back**, not just the front. The back carries the most.
3. **Play a session to the recap.** It is the surface most often missed, because
   it only appears at the end.
4. **Check the deck face on the shelf.** Long titles wrap and make a rail ragged;
   phrase decks drop the script prefix for exactly this reason.
5. **If the set has notes**, confirm the note is not clipped at the smallest
   bucket that can carry one (`md`).

### Comfortable capacity, measured

At a 1920-wide window, roughly, before wrapping:

| Bucket | Glyphs on one line | Answer characters |
|---|---:|---:|
| `sm` | 2 | — |
| `md` | 7 | 24 |
| `lg` | 10 | 30 |
| `xl` | 14 | 34 |

The longest prompt in the content today is ゆっくり話してください at 11 glyphs,
which sits in `xl` and wraps to two lines in the recap only. That is the current
headroom: **one more bucket would be needed at roughly 15 glyphs.**
