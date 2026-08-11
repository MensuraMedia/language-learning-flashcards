# Card dimensions

The rule every surface that shows Japanese has to follow, and the thresholds
each one currently uses.

Written because the same mistake was made **four times**: sizing a surface by
the *category* of thing on it rather than by the *content*. Each time it looked
fine on the content that existed when it was written, and broke as soon as
longer content arrived. This document exists so the fifth surface does not
repeat it.

- **Current as of** 2026-08-10 · 350 tests passing
- **Applies to** the study card, its answer options, the session recap tiles,
  the deck faces on a shelf, and the memory-game board tiles
- **Companion** [UI-FORMAT.md](UI-FORMAT.md) — type ranks, section headings,
  padding and the accent system. This document covers *measurement*; that one
  covers *format*.

---

## 1. The rule

> **Size by what is on the surface, not by which category it belongs to.**
> Grow *width* until the longest item fits on one line. Never shrink the type,
> and use one width for the whole session.

Five corollaries, each earned the hard way:

1. **A category is not a length.** "Kanji" tells you nothing about whether the
   answer is "sun" or "world/generation". "Phrase" does not distinguish 頭悪い
   from ゆっくり話してください.
2. **Extra text runs across, not down.** Widening fits more; heightening does
   not — it just leaves more of the face empty.
3. **The reading is the thing that must fit.** A glyph wrapping to two lines is
   ugly. A meaning wrapping to two lines makes an option hard to scan while the
   clock is running.
4. **Never shrink the type to avoid a wrap.** A phrase set small enough to fit
   is harder to read than the same phrase wrapped, and being read is the card's
   entire job. Widen instead.
5. **One width per session, not per card.** A face that changes width as you
   answer is distracting, and the eye has to reacquire the prompt each time.

### Why not just make everything big

Because the single-glyph card is 93% of the content — 1,545 of 1,658 — and its
5 : 7 playing-card portrait is the app's whole visual identity. Widening it to
suit 15 phrase cards would trade the look of the thing for an edge case.

---

## 2. Study card

`.deck3d`, sized once per session by `sizeCardsForSession()` in `study.js`.

A deck whose prompts are all one or two glyphs keeps the **5 : 7 playing-card
face at 336 × 470** — that is 93% of the content and the app's visual identity.

Anything longer gets a computed width, applied to every card in the session:

```js
const CARD_GLYPH_PX = 46;      // the size the type will not go below
const CARD_SIDE_PAD = 40;      // each side
const forGlyphs  = longestGlyph  * CARD_GLYPH_PX;
const forAnswer  = longestAnswer * CARD_GLYPH_PX * 0.42;   // Latin is narrower
const width  = min(700, max(340, ceil(max(forGlyphs, forAnswer))) + CARD_SIDE_PAD * 2);
const height = anyNote ? 430 : 372;
```

| Longest prompt in the session | Card width | Example |
|---|---:|---|
| ≤ 2 glyphs | 336 × 470 (5 : 7) | any kana or kanji deck |
| 3–6 | 420px | 頭悪い · 教えてください |
| 9 | 494px | レシートをください |
| 11 | 586px | ゆっくり話してください |

Prompt type is a **fixed 40px**, not a clamp: the width was chosen so it fits.

## 3. Answer options

`.choices`, sized once per session by `sizeOptionsForSession()` — the same rule
as the card, for the same reason.

```js
const OPTION_CHAR_PX = 8.4;        // a Latin character at the option's type size
const OPTION_SIDE_PAD = 44;
const width = min(300, max(96, ceil(longestAnswer * OPTION_CHAR_PX) + OPTION_SIDE_PAD));
```

| Longest answer in the session | Column | Example |
|---|---:|---|
| `kya` · `sun` | 96px, square tiles | any kana deck |
| `Wednesday` | 120px | words |
| `world/generation` | 178px | kanji |
| `please speak slowly` | 204px | phrases |
| `I'm fine, thanks / no need` | 262px | the convenience-store set |

Sizing these by *script* meant every kanji deck got the same column whether its
answers read `sun` or `world/generation`, and every phrase deck the same whether
they read `let's go` or `please speak slowly`.

Kanji options carry a second register — the reading of the character the option
stands for — so they get a taller minimum. That is display only; grading still
compares the option text.

---

## 4. Session recap tiles

`.recap-cards`, via `is-text` and a computed `--tile-w`.

The recap is the **one place a learner reads every card at once**, which makes
it the worst place for text not to fit — and it is easy to forget, because it
only appears after a session ends.

Same rule as the card: **one width for the whole grid**, computed from the
longest item, type left alone at 26px.

| Longest item | Tile width |
|---|---:|
| ≤ 2 glyphs | 84px square |
| otherwise | `min(360, max(140, max(glyphs × 26, answer × 12))) + 44` |

**The answer counts toward the width**, scaled by 0.46 because Latin characters
are narrower. Without that term the tiles fit 高い but not `expensive / tall`,
which is what the reported defect looked like.

Side padding is **22px** — text running to the tile edge reads as cramped even
when it technically fits.

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
  correction would be right for one width and wrong for every other. The
  top edge is the pivot, so it cannot move.

Verified at **0 px** on a kana card and a phrase card.

---

## 7. Adding content

When a new set arrives, check it against this list before shipping:

1. **Measure the longest prompt and the longest answer in the set.** The width
   is computed from them, so the only question is whether the result exceeds the
   700px cap — see below.
2. **Check the study card back**, not just the front. The back carries the most.
3. **Play a session to the recap.** It is the surface most often missed, because
   it only appears at the end.
4. **Check the deck face on the shelf.** Long titles wrap and make a rail ragged;
   phrase decks drop the script prefix for exactly this reason.
5. **If the set has notes**, confirm the note is not clipped — a session
   containing any note gets a 430px face instead of 372px.

### Headroom

The card width is computed, so there is no bucket to outgrow — it scales until
it hits the **700px cap**, which is reached at roughly **14 glyphs**. The longest
prompt in the content today is ゆっくり話してください at 11, giving 586px.

Past 14 glyphs the type would have to wrap, and that is the point at which a
second line becomes the right answer rather than a wider card.
