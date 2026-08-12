# Change manifest — the session recap could not be scrolled or left

**Date:** 2026-08-12
**Trigger:** User reported the session completion window cut off at the bottom,
asked for it to scroll, then for the capability to be universal across all
sessions, then for the panel to be wider so more fits before scrolling is needed.

---

## 1. The defect

`.recap-card` had no `max-height`, so it sized to its content, and `.recap`
centres its child. A panel taller than the overlay therefore overflowed **both**
ends — in a direction nothing scrolls. On a ten-card deck the last cards and,
worse, *Practice again* and *Back to dashboard* were unreachable. The session
could not be closed from the summary at all.

A `.recap-scroll` wrapper already existed and did nothing, because
`.recap-card > * { flex: 0 0 auto }` forbade it from shrinking.

## 2. Four properties, and they only work together

**Stacking came last and mattered most.** After the scroll fix the panel still
looked sheared at the top, and the cause was not layout: the modal overlays sat
at z-index 6, 30 and 40 against the topbar's 60, so a full-height panel slid
*under* the chrome. Scrolling could not recover those pixels because they were
not overflowing — they were painted over. `--z-topbar` and `--z-modal` tokens
now exist and every overlay uses them. Settings had escaped notice only because
`.settings-card`'s 88vh kept it small; it shares the same overlay and was
equally at risk.

| # | Property | Rule |
|---|---|---|
| 1 | The overlay outranks all chrome | `z-index: var(--z-modal)` |
| 2 | The panel may not exceed the overlay | `max-height: 100%` |
| 3 | The scroll area must be allowed to shrink | `flex: 1 1 auto; min-height: 0` |
| 4 | Leaving must not require scrolling | actions are a **sibling** of the scroll area |

**`min-height: 0` is the non-obvious one.** A flex item's default minimum size is
its content, so without it the area refuses to shrink and overflows regardless
of `overflow-y`. Setting `overflow-y: auto` alone — which is what most attempts
at this bug do — changes nothing.

Property 3 is a design decision rather than a layout one: a recap can be twenty
cards long, so the way out is pinned rather than sitting at the end of the list.

## 3. Universal, not per-deck

These are properties of the panel, so they hold for every session regardless of
deck, card count, tile type or window size. The other full-screen overlays share
the same failure shape — a centred child in a viewport-sized parent — so they
carry the same guard:

| Overlay | Bound |
|---|---|
| `.recap-card` | `max-height: 100%`, scrolling body, pinned actions |
| `.help-card` | `max-height: calc(100vh - 48px)`, sticky header |
| `.game-done-card` | `max-height: calc(100vh - 48px)` |
| `.settings-card` | already had `max-height: 88vh` |

`.recap-act` is reused by the games overlay, so the pinned-footer styling is
scoped to `.recap-card > .recap-act` — the games action row keeps its plain form.

## 4. Width buys rows back

Widened **400px → 980px**. Both tile grids are `auto-fill`, so width converts
directly into columns, and the four metrics use `auto-fit` and collapse onto one
row — which returns the vertical space the wider panel is meant to spend on
cards.

Measured in the running app:

| Session | Result |
|---|---|
| 10 cards (Sorry, text tiles) | 2 columns × 5 rows — **fits, no scrolling** |
| 14 cards (Question words) | scrolls, actions still pinned |
| 20 cards (Kanji N1, glyph tiles) | scrolls, actions still pinned |

Scrolling is now the fallback rather than the normal case, which is what was
asked for.

## 5. Tests

`tests/test_ui_format.py` asserts each of the three properties separately, and
that all four overlays are bounded. The nesting check **parses** the template
rather than counting tags in a string — the first version counted `<div>`s and
was already wrong, which is precisely how a check like that quietly stops
meaning anything.

## 6. Files affected

```
src/japanese_practice/templates/study.html    actions moved out of .recap-scroll
src/japanese_practice/static/css/theme.css    overlay bounds, width, pinned footer
tests/test_ui_format.py                       3 properties + all overlays bounded
docs/UI-FORMAT.md                             §6a — the overlay contract
docs/CARD-DIMENSIONS.md                       recap grid sits in a 980px panel
changelog.md
```

**367 tests passing**, ruff and black clean.
