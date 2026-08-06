# Mockup Design Brief — Japanese Practice

Shared brief for all mockup variants. Each variant is a **self-contained static HTML
file** demonstrating one complete design direction. No build step, no external
requests, no CDN links — inline all CSS and JS.

## The product

A local desktop flash-card app (Quart + pywebview) for learning **Hiragana,
Katakana and Kanji**. It opens in its own native window and also works in a
browser.

## What every variant MUST show

### 1. Landing dashboard (the default view)
- Statistical performance across **every past exercise session** — not just a total
- A list of **exercise segments**, differentiated by:
  - **challenge type** (e.g. recognition, recall, timed, listening, mixed)
  - **scoring scheme** (e.g. accuracy, speed-weighted, streak, spaced-repetition)
  - **difficulty level** (at minimum: beginner → advanced, and Kanji graded separately)
- Entry points to start each exercise

### 2. Flash card
- **Front face: the character alone.** Nothing else. This is the default state.
- **Click flips the card** with a real animation.
- **Back face:** the sound written out (romaji + kana reading), plus a **speaker
  icon** that plays the pronunciation.
- The flip must be demonstrated working in the mockup (CSS 3D transform or equivalent).

### 3. Score / statistics tracking
- A score is recorded **each time** the user runs the app
- Show how per-session history is surfaced: trends over time, per-character-set
  accuracy, weak characters, streaks

## Design language (from `universal-themes`)

The reference UI kits share a consistent language — follow it:

- **Dark grounds:** near-black to charcoal (`#0d0d0f` – `#1c1c20`), never pure black
- **Layered gray panels** with subtle borders (`#26262b` – `#3a3a42`), soft depth,
  slight inner glow rather than heavy drop shadows
- **One high-chroma accent per theme** carrying all emphasis — amber/yellow
  (`#f5c518`), orange (`#ff8c3a`), or green (`#4ade80`). Accent is used sparingly
  and deliberately: active states, key metrics, progress fills.
- **Technical/HUD framing:** thin rules, small uppercase labels with letter-spacing,
  monospace for numerals, bracket and corner-tick motifs
- **Data-dense composition:** the reference dashboards pack many small charts and
  stat readouts into a tight grid rather than a few large cards
- Type: clean geometric sans for UI. Japanese glyphs need a font stack that
  actually resolves on Debian — use `"Noto Sans CJK JP", "Noto Sans JP", sans-serif`
  and set a generous size; the character is the hero.

## Hard constraints

- **Self-contained:** one `.html` file, everything inlined. It must render correctly
  opened directly from disk with no network.
- **No external fonts or images.** Use system font stacks and CSS/SVG for any icon,
  including the speaker icon.
- **Responsive** down to ~900px wide (the pywebview window will be resizable).
- **Realistic placeholder data** — plausible session history, accuracy figures and
  character sets. Real kana (あ, か, さ, ア, カ, サ) and real Kanji (水, 火, 山, 日)
  with correct readings. Do not invent incorrect readings.
- Keep it a **mockup**: no backend calls, no persistence. Interactions are faked.

## Deliverable

One file: `mockups/<NN>-<slug>.html`, with a `<title>` naming the direction.
Include a short comment block at the top of the file stating the direction's
thesis in 2–3 sentences.
