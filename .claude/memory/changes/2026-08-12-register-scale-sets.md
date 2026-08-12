# Change manifest — four register-scale sets on General Words

**Date:** 2026-08-12
**Trigger:** User approved the recommended sets and asked me to build them,
adding "keep an eye on the dimensional and format documents".

---

## 1. What shipped

Four review-mode sets, 40 cards, on the existing General Words shelf. All four
teach the same kind of thing — **how formal, how strong, how blunt** — which is
why they are review sets: every member is a correct translation of the headword,
so the only question a card can usefully ask is *which one belongs here*.

| Set | Cards | Scale |
|---|---:|---|
| Sorry — degrees of contrition | 10 | 悪い → ごめん → すいません → 失礼しました → 申し訳ございません |
| Thanks — degrees of gratitude | 10 | サンキュー → どうも → ありがとう → 恐れ入ります → お世話になりました |
| Very — degrees of intensity | 10 | ちょっと → わりと → けっこう → かなり → とても → すごく → めっちゃ → 超 → 非常に |
| Saying no without saying no | 10 | ちょっと… → 結構です → 遠慮しておきます → 難しいです → 無理 |

Highest-value individual cards: **結構です / いいです**, which can each mean yes
*or* no depending on context; **全然**, which means both "not at all" and
"totally"; and **ありがとうございます vs ございました**, present for ongoing and
past for finished.

---

## 2. Collision check ran *before* authoring

A glyph is unique per script, and an upsert would have silently moved an
existing card into the new category — the same class of fault that once shrank
the Top 200 deck. Checking first found four:

| Glyph | Already in | Resolution |
|---|---|---|
| すみません | Getting by | Sorry uses すいません (the spoken form) and names すみません in its note |
| ありがとうございます | Getting by | Thanks uses ありがとう, ありがとうございました and どうもありがとうございます |
| 大丈夫です | At the convenience store | Dropped — its existing gloss already *is* the refusal sense |
| なかなか | Not bad | Dropped from Very |

The file carries a comment saying which members are absent and why, so the gaps
read as deliberate rather than as oversights.

---

## 3. One card cut on content grounds

`すみません、ありがとう` was a teaching device, not an expression anyone says as a
unit. Replaced with **ごちそうさまでした**, which is real and high-frequency; the
apologetic-thanks lesson moved into the ありがとう note, where it belongs.

---

## 4. Dimensions, checked before shipping

| Set | Width | Driven by |
|---|---:|---|
| Very | 420px | meaning |
| Sorry · Saying no | 460px | meaning |
| **Thanks** | **600px** | **glyph** — どうもありがとうございます at 13 |

Thanks is now the widest deck in the app, inside the 700px / 15-glyph cap. At
the measured 40.3px per glyph that is 524px of text in a 600px face — the same
~38px clear each side as the 11-glyph ゆっくり話してください measured earlier.

Recorded in CARD-DIMENSIONS.md along with the crossover this exposed: **below
about 8 glyphs the meaning drives the width, above it the glyph does**, because
the gloss stops mattering once it wraps at 30ch. A set of long *expressions* is
therefore far more expensive than a set of long *glosses*.

No format changes were needed — the sets reuse the phrase card shape, and
UI-FORMAT.md's contract was already satisfied.

---

## 5. Files affected

```
src/japanese_practice/content/general.py     +4 sets, 40 cards (85 total)
src/japanese_practice/db.py                  4 difficulty keys, categories, labels
src/japanese_practice/analytics.py           DECK_META, shelf "general"
tests/test_content.py                        set counts, totals
tests/test_api.py                            catalogue count 37 → 41
docs/CARD-DIMENSIONS.md                      width table + crossover note
docs/FEATURES.md, docs/HANDOFF.md            totals, per-set table
changelog.md
```

**364 tests passing**, ruff and black clean. Confirmed working by the user.
