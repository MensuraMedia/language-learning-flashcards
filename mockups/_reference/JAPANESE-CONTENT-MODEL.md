# Japanese Content Model — Authoritative Reference

Source: `MensuraMedia/language-learning` @ `main` (public), `japanese/` subtree.
This defines the real character sets, level structure and terminology the app must
use. **Do not invent alternative groupings or counts.**

## Character sets and true counts

| Set | Count | Composition |
|---|---:|---|
| Hiragana ひらがな | **104** | 46 core gojuon + dakuon + han-dakuon + yoon combinations |
| Katakana カタカナ | **104** | same structure as hiragana |
| Kanji — JLPT N5 | **107** | numbers, time, directions, people, nature |
| Kanji — JLPT N4 | **174** | everyday actions, descriptions, concepts |
| Kanji — JLPT N3 | **394** | abstract concepts, emotions, formal vocabulary |
| Kanji — JLPT N2 | **248** | news, literature, professional contexts |
| Kanji — JLPT N1 | **382** | rare/specialised, academic and literary |
| Kanji — Joyo complete | **1,521** | Grade 1–6 plus Secondary |

Kanji study tiers used by the reference flash cards: **Top 200**, **Top 500**,
**Complete (1,372)**.

## Correct terminology (use these names in the UI)

- **gojuon** (五十音) — the base 46-character grid
- **dakuon** — voiced marks (が ざ だ ば / ガ ザ ダ バ)
- **han-dakuon** — half-voiced (ぱ ぴ ぷ ぺ ぽ / パ ピ プ ペ ポ)
- **yoon** — contracted combinations (きゃ きゅ きょ / キャ キュ キョ)
- **romaji** — Latin transliteration
- **JLPT N5–N1** — proficiency levels, N5 easiest → N1 hardest
- **Joyo** (常用漢字) — the official general-use kanji list, graded by school year

## Difficulty ladder this maps onto

This is the natural, source-backed progression for the "different levels of
difficulty" requirement — use it rather than a generic easy/medium/hard scale:

**Kana track:** gojuon → dakuon → han-dakuon → yoon → full 104 mixed
**Kanji track:** N5 → N4 → N3 → N2 → N1, or Joyo Grade 1 → 6 → Secondary
**Kanji volume track:** Top 200 → Top 500 → Complete

## Thematic categories (from the Top 200 kanji wall chart)

Usable directly as exercise segments:
Numbers & Counting · People & Family · Nature & Weather · Time & Calendar ·
Actions · Descriptions · Places

## Vocabulary topic sets

Days of the week 曜日 · Months 月 · Numbers 数字 · Time 時間

## Verified sample characters for mockups

Use only these known-correct pairings. Do not fabricate readings.

**Hiragana (gojuon):**
あ a · い i · う u · え e · お o · か ka · き ki · く ku · け ke · こ ko ·
さ sa · し shi · す su · せ se · そ so · た ta · ち chi · つ tsu · て te · と to ·
な na · に ni · ぬ nu · ね ne · の no · は ha · ひ hi · ふ fu · へ he · ほ ho ·
ま ma · み mi · む mu · め me · も mo · や ya · ゆ yu · よ yo ·
ら ra · り ri · る ru · れ re · ろ ro · わ wa · を wo · ん n

**Hiragana dakuon/han-dakuon:** が ga · ぎ gi · ざ za · じ ji · だ da · ば ba · ぱ pa
**Hiragana yoon:** きゃ kya · きゅ kyu · きょ kyo · しゃ sha · しゅ shu · しょ sho

**Katakana (gojuon):**
ア a · イ i · ウ u · エ e · オ o · カ ka · キ ki · ク ku · ケ ke · コ ko ·
サ sa · シ shi · ス su · セ se · ソ so · タ ta · チ chi · ツ tsu · テ te · ト to ·
ナ na · ニ ni · ヌ nu · ネ ne · ノ no · ハ ha · ヒ hi · フ fu · ヘ he · ホ ho ·
マ ma · ミ mi · ム mu · メ me · モ mo · ヤ ya · ユ yu · ヨ yo ·
ラ ra · リ ri · ル ru · レ re · ロ ro · ワ wa · ヲ wo · ン n

**Kanji (N5) — character · meaning · on'yomi · kun'yomi:**
- 日 · day, sun · ニチ/ジツ · ひ/か
- 月 · month, moon · ゲツ/ガツ · つき
- 火 · fire · カ · ひ
- 水 · water · スイ · みず
- 木 · tree, wood · モク/ボク · き
- 金 · gold, money · キン/コン · かね
- 土 · earth, soil · ド/ト · つち
- 山 · mountain · サン · やま
- 川 · river · セン · かわ
- 人 · person · ジン/ニン · ひと
- 大 · big · ダイ/タイ · おお(きい)
- 小 · small · ショウ · ちい(さい)
- 中 · middle, inside · チュウ · なか
- 上 · up, above · ジョウ · うえ
- 下 · down, below · カ/ゲ · した
- 一 · one · イチ · ひと(つ)
- 二 · two · ニ · ふた(つ)
- 三 · three · サン · みっ(つ)
- 学 · study, learning · ガク · まな(ぶ)
- 生 · life, birth · セイ/ショウ · い(きる)/う(まれる)

## Rules for the flash-card back face

- Kana cards: show **romaji** as the written sound, plus the kana itself
- Kanji cards: show **English meaning**, **on'yomi** (katakana convention) and
  **kun'yomi** (hiragana convention) — the reference charts list meaning + reading
- Never show the reading on the front face; the front is the character alone
