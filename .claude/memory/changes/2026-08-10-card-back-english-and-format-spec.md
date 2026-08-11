# Change manifest — English on the card back, kanji green, and one format spec

**Date:** 2026-08-10
**Trigger:** User asked for the English translation on the card flip-side, all
kanji exercises in green, larger shelf descriptions, a padding/margin audit, a
deck title above each exercise, and a technical document to stop the drift.

---

## 1. English on the card back

`render()` populated the meaning for `script === "kanji"` and explicitly cleared
it for everything else, so a phrase card showed 見せてください / *misete kudasai*
and never said it meant "please show me".

Every back now carries the same three registers in the same order — **glyph,
sound, meaning** — with only the *source* differing by script:

| Script | Glyph | Sound | Meaning | Readings |
|---|---|---|---|---|
| Kana | ✅ | romaji | — (kana have none) | — |
| Vocab / phrase | ✅ | romaji | ✅ **new** | — |
| Kanji | ✅ | — | ✅ | on/kun + romaji |

The meaning is distinguished by colour and weight, **not size** — it answers a
question as important as the reading does.

### Height had to follow

A fixed `372 / 430` clipped the new line on the phrase sets, where the meaning is
the longest text on the card. Height is now the sum of the registers that will
actually render:

```
CARD_BASE_PX 310 + SOUND 62 + MEANING 36×lines + READINGS 96 + NOTE 58
```

Calibrated so the two known-good heights reproduce exactly (372 = BASE+SOUND,
430 = BASE+SOUND+NOTE). `CARD_MEANING_CH` (30) must match
`.back-meaning { max-width: 30ch }`.

---

## 2. Deck title above each exercise

`POST /api/session` now returns `deck_title` (via `db.difficulty_label`) and
`script`. The study table is headed by the deck's name at the **same token** as a
dashboard shelf heading — the shelf and the table name the same object. The raw
key and mode drop to a chrome-rank sub-line.

Previously the only heading was `phrase:requests · recall` in letter-spaced
uppercase: the deck you chose went unnamed the moment you started studying it.

---

## 3. Kanji green, decided once

`theme-kanji` was toggled **per card** inside `render()`. Two consequences: a
mixed deck flickered between palettes, and a kanji *drill* was never themed,
because the drill path's key is `drill:custom` and carries no script.

`session.deck_script(difficulty, cards)` is now the single answer to "is this a
kanji exercise?" — script from the key where there is one, from the cards
otherwise. Applied once per session.

Also applied to the All-exercises page, via an explicit `kanji: true` flag on the
shelf definition rather than a string match on the title, so a future kanji shelf
cannot be missed.

---

## 4. The heading bug — root cause, not a patch

The reported symptom was "descriptions next to shelf titles are too small". The
cause was structural.

`.lbl` was used for **two unrelated roles**: the label on a gauge (`MASTERED`,
`streak`) and the title of a section (*Hiragana Shelf*). When
`#dashboard .lbl { font-size: 12px }` was added to lift the dashboard's chrome
text, that ID-level rule captured every shelf heading on the page. A heading rule
written afterwards, correctly, at `.sec .lbl`, **lost on specificity to a rule
that was never about headings.**

Fixed by naming the role: `.sec-title` / `.sec-desc`. No gauge rule can match
them. 20 titles and 15 descriptions converted across dashboard, decks, games,
study and the settings dialog; `decks.js` generates the new classes.

| | Before | After |
|---|---:|---:|
| Shelf title (dashboard) | 12px, uppercase, letter-spaced | 19px, sentence case |
| Shelf description | 11px, dim | 13.5px |
| `/decks` title | 17px | 19px — now the *same* rule |
| Panel / settings heading | 12px | 15px |

Three ranks now exist and only three: section (19/13.5), panel (15/12.5), chrome
(9.5–12). Per-view overrides may change rhythm, never type.

---

## 5. Padding and margin audit

| Token | Value | Governs |
|---|---:|---|
| `--title-inset` | 6px | Left inset, aligning a heading with the cards below |
| `--title-space-above` | 38px | Previous block → heading |
| `--title-space-below` | 14px | Heading → its rail |
| `--title-gap` | 14px | Title → description |

A heading belongs to what is below it, so the space above is larger than the
space below (38 vs 14). `#decks` keeps a looser rhythm (46/58px) because it is a
catalogue; its *type* now comes from the shared tokens.

---

## 6. docs/UI-FORMAT.md

The document requested. Covers: the three rules and the test for a new rule; the
token table; the three ranks; section heading markup and geometry; the study
table anatomy; the card back's registers and the height arithmetic; padding per
surface; the accent system and where it is applied; a checklist for adding a
surface; and **the known remaining inconsistencies**, listed rather than hidden
so an undocumented exception does not become the next precedent.

---

## 7. Files affected

```
src/japanese_practice/routes/api.py                 deck_title + script
src/japanese_practice/session.py                    deck_script()
src/japanese_practice/static/js/study.js            meaning on every back, height
                                                    arithmetic, session-level accent
src/japanese_practice/static/js/decks.js            kanji flag, .sec-title/.sec-desc
src/japanese_practice/static/css/theme.css          §5 rewritten: tokens, ranks,
                                                    .sec-title/.sec-desc, .felt-head,
                                                    .back-meaning; per-view overrides folded in
src/japanese_practice/templates/{dashboard,study,games,decks}.html
tests/test_api.py                                   3 contract tests
docs/UI-FORMAT.md                                   new
docs/CARD-DIMENSIONS.md                             cross-linked
README.md, changelog.md, .claude/memory/decisions.md
```

**350 tests passing**, ruff and black clean.

---

## 8. Verification note

Visual checks were made against the real pywebview window (`import -window`),
which is the only renderer that reproduces the app faithfully here:

- Firefox headless `--screenshot` captures before paint and cannot resolve the
  `system-ui` font stack — every page linking `theme.css` screenshots as a flat
  background with no text. It is not usable for this project's CSS.
- **An installed copy of the app was left running from an earlier session and
  its window kept being captured instead of the dev instance.** Roughly an hour
  went into "the CSS is not applying" before that was spotted. *Kill every
  instance and confirm exactly one window before trusting a screenshot* —
  X reuses window IDs, so matching on a new ID is not sufficient.

Confirmed visually: shelf titles and descriptions at the new scale; kanji shelf
and its deck rungs green; deck title above the exercise; card back showing
ああ / *aa* / "like that (over there)"; kana cards unchanged on the 5 : 7 face;
settings dialog headings at panel rank.

Not yet confirmed visually: the kanji **study view** in green. The API contract
that drives it (`script: "kanji"`, including for drills) is asserted by test,
and `.theme-kanji` is proven to recolour the interface on the dashboard, so the
two halves are each verified — but the combination has not been seen on screen.
