# Change manifest — General Words shelf and self-graded review mode

**Date:** 2026-08-11
**Trigger:** User asked for a "General Words" shelf: all the words for *maybe*,
one context sentence per card, **no multiple choice**; then a *not bad* set
(warukunai, kekkou ii, sokosoko); then a *seriously* set (honto ni, majide, uso
desho); then a *question words* set **with** multiple choice and a sample
sentence.

---

## 1. What shipped

A new shelf between Words and Phrase Sets, with four sets and **45 cards**.

| Set | Cards | Mode | Ordering principle |
|---|---:|---|---|
| Maybe — degrees of certainty | 10 | review | Confidence, high to low: たぶん → かもしれない → さあ |
| Not bad — faint praise | 10 | review | Warmth, high to low: なかなか → まあまあ → まし |
| Seriously — surprise and disbelief | 11 | review | Register, neutral to slang: 本当に → マジで → ガチで |
| Question words | 14 | multiple choice | The interrogatives |

Each set is *ordered*, not alphabetical, because the ordering is the lesson:
these are scales, and seeing them in sequence is what makes the difference
legible.

Every card carries an example sentence in **Japanese with an English gloss**. A
test asserts each note actually contains Japanese — a note that only restates the
meaning in English is precisely what these cards exist to avoid.

---

## 2. Review mode — the new interaction

"No multiple choice" is not a display flag; the app had no such mode.

### Why it is necessary rather than cosmetic

Multiple choice cannot test a near-synonym set. Given たぶん against "probably /
might / possibly / who knows", a learner is not being asked whether they know
たぶん — they are being asked which English gloss the author happened to type,
and elimination often wins without knowing any of the four. The distinction
these sets teach is one of **degree**, and degree does not survive being turned
into a four-way choice.

### How it works

| Piece | Decision |
|---|---|
| `session.CHALLENGES` | Gains `review`; `deals_choices()` is the single place that answers "does this challenge present options?" |
| API | **Omits** the options entirely rather than hiding them client-side — the answer would otherwise sit in the payload for a mode whose whole premise is self-honesty. `deals_choices` is returned so the view need not infer intent from an empty array, which is indistinguishable from a deck that failed to build any |
| Study view | Two buttons, *Got it* / *Missed it*, keys `1` and `2` |
| Gating | Both stay **disabled until the card is flipped**. Grading before seeing the answer is a coin toss, and it would put noise into the SRS schedule these sets are graded on |
| Recording | A self-graded attempt goes through the same `record_attempt` path, so SRS, streaks and the weak-character heatmap all work unchanged |

**Two outcomes, not one.** A self-graded deck with only a "next" button never
records a miss — it teaches nothing and feeds nothing to the analytics.

---

## 3. Two defects found by looking at it

Both were caught in the running app, not by the suite.

1. **"Missed it" wrapped onto two lines.** `sizeOptionsForSession()` measures
   the longest answer to size the column; with no choices it measured 1 and
   collapsed to the 96px floor. Review mode now sizes for the labels that are
   actually there (`SELF_GRADE_W = 176`).
2. **A bare "why" read as the default answer.** どうして, なんで and なぜ all
   gloss as "why", and with one of them unqualified a learner could pick it by
   elimination. All three now carry their register — `why (everyday)`,
   `why (casual)`, `why (formal)`.

A third apparent defect was **not** one: the card looked like it auto-flipped on
load. A clean capture with the pointer parked away from the window showed the
front face and disabled buttons, as intended. The flip was a stray click of mine.

---

## 4. Shelf reuses the phrase script

`script="phrase"` rather than a new script. These are short expressions, graded
on meaning, needing the wide card and a note — all of which the phrase machinery
already provides. A new script would have touched the clip path, `MEANING_SCRIPTS`,
the heatmap and the seed uniqueness constraint for no gain. The shelf comes from
`DECK_META`, which is keyed by difficulty rather than script, so a separate shelf
costs nothing.

Consequence: the documented phrase total rises from 93 to 138. The assertion
carries a comment saying why, so it is not later read as a phrase-set regression.

---

## 5. Files affected

```
src/japanese_practice/content/general.py          new — 45 cards, 4 sets
src/japanese_practice/content/loader.py           registered
src/japanese_practice/db.py                       4 difficulty keys, categories, labels
src/japanese_practice/analytics.py                DECK_META — shelf "general"
src/japanese_practice/session.py                  review challenge, deals_choices()
src/japanese_practice/routes/api.py               omit options, return deals_choices
src/japanese_practice/static/js/study.js          self-grade UI, keys, column width
src/japanese_practice/static/js/dashboard.js      render the shelf, wide deck face
src/japanese_practice/static/js/decks.js          shelf in the catalogue
src/japanese_practice/static/css/theme.css        .self-grade, .sg-hint
src/japanese_practice/templates/dashboard.html    shelf markup
tests/test_content.py                             completeness, notes carry Japanese
tests/test_api.py                                 review ships nothing, MC intact, attempts record
docs/FEATURES.md, changelog.md, .claude/memory/decisions.md
```

**362 tests passing**, ruff and black clean.

---

## 6. Verification

API: all four decks checked through `/api/session` — the three review decks
return `deals_choices: false` with zero options; Question words returns three.
The catalogue advertises `challenge=review` for the first three, which is what
the shelf button passes.

Visual, in a real browser window pointed at the deck URL:

- Front face shows the glyph alone, buttons disabled, "Flip the card, then grade
  yourself"
- After `Space`: 本当に / *hontou ni* / "really, truly" plus the sentence
  「本当にありがとう」, buttons live, "How did you do?"
- Question words deals three English options against なぜ

**Harness note.** Driving the pywebview window by synthetic clicks is
unreliable — the shelf rails swallow wheel events and keyboard focus often is
not in the document. Pointing a real browser window at the study URL gives
direct control of the deck under test and was far faster. Firefox *headless*
`--screenshot` remains unusable here: it captures before paint and cannot
resolve the `system-ui` font stack, so every page renders as a flat background.
