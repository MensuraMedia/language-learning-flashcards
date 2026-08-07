# HANDOFF — Japanese Practice

**Living document. Update it at the end of every working session.**
It is the single place a new session (human or agent) reads to know where the
project stands, what is real, what is assumed, and what to do next.

- **Last updated:** 2026-08-06 23:05 UTC-4
- **Updated by:** session `30934411` (Claude Opus 5)
- **Project root:** `/home/user/projects/japanese_practice`
- **Remote:** https://github.com/MensuraMedia/language-learning-flashcards (public)
- **Current state:** application runs end to end; 155 tests passing; UI polish outstanding

---

## 0. Maintenance contract

This file is governed by the universal standards' change-tracking rules. Whoever
works on this project **must**:

1. Update §1 (status), §5 (what works / what doesn't) and §8 (next actions) before
   ending a session.
2. Append to `changelog.md` **as changes are made**, not afterwards.
3. Record architectural decisions in `.claude/memory/decisions.md` with rationale.
4. Write a session log to `.claude/memory/sessions/YYYY-MM-DD_HHmm_summary.md`.
5. Use **absolute dates** (YYYY-MM-DD). Never "yesterday" or "last week".
6. **Verify before claiming.** If this document says something works, it means
   someone ran it. Do not mark anything verified that you have not executed.

---

## 1. Where the project stands

| Phase | Status |
|---|---|
| Standards adoption | ✅ Complete |
| Japanese content model | ✅ Complete and verified |
| Design mockups (5 directions) | ✅ Complete, direction chosen |
| Application skeleton | ✅ Runs end to end |
| Analytics engine | ✅ All 13 metrics compute from real data |
| Desktop window (pywebview) | ✅ Opens and renders |
| UI layout polish | ✅ Dashboard rebuilt to the approved mockup (deck shelves, instrument row, history) |
| Audio (local TTS) | ✅ **Working end to end.** espeak-ng + `ja` voice; API returns audible WAV (peaks 0.385–0.786); renders cached |
| Audio (ElevenLabs) | ⚠️ Integrated, never called against the live API |
| Clip library + validation | ✅ `audio_library.py`, manifest + checksums |
| Keyboard controls | ✅ **All verified with xdotool** |
| Tests | ✅ **181 passing**, lint + format clean — see [TESTING.md](TESTING.md) |
| Packaging / distribution | ❌ Not started |

**Chosen design direction:** `mockups/05-tactile-deck.html`, with the analytics
surface grafted from `mockups/04-data-studio.html`. Decided by the user on
2026-08-06. Note the automated synthesis in `mockups/COMPARISON.md` recommended
04 instead; the user's combination was chosen deliberately and supersedes it.

---

## 2. How to run it

```bash
cd /home/user/projects/japanese_practice

# The venv MUST be created with --system-site-packages, or pywebview cannot
# find PyGObject (gi) and silently falls back to server-only mode.
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e .

# Desktop window
.venv/bin/python -m japanese_practice

# Browser / headless
.venv/bin/python -m japanese_practice --no-window --port 8731
```

Override the database location with `JP_DB_PATH`. Default is
`~/.local/share/japanese-practice/practice.db`.

---

## 3. Verified working (executed, not assumed)

All of the following were run on 2026-08-06 and produced the stated result.

**Content data** — exact counts against the authoritative reference:
- Hiragana 104 (46 gojuon + 20 dakuon + 5 handakuon + 33 yoon)
- Katakana 104 (same split)
- Kanji N5 107
- No duplicate glyphs; all glyphs inside their correct Unicode ranges
- Hepburn romanisation correct on the classic traps (し=shi, ち=chi, つ=tsu,
  ふ=fu, じ=ji, を=wo, ん=n, しゃ=sha, じゅ=ju, ちょ=cho)

**API** — every endpoint exercised with curl:
- `GET /` → 200
- `GET /api/segments` → 13 segments with live counts
- `POST /api/session` → session created, deck returned
- `POST /api/session/<id>/attempt` → scores and streaks update correctly
- `POST /api/session/<id>/end` → totals finalised
- `GET /api/character/<id>` → character + recall history
- `GET /api/audio/<id>` → 200 with a playable WAV.
  **CORRECTION (2026-08-06 22:00):** an earlier note in this file claimed this
  was "real espeak synthesis". It was not. 17,684 bytes is *exactly* the silent
  stub (0.4s x 22050Hz x 2 bytes + 44-byte header) — the size was inferred from,
  not verified against, the content, and **no TTS binary was installed at all**.
  `espeak-ng` has since been installed and real synthesis is now verified by
  amplitude (peak 0.571, 772ms for あ). Never infer audio validity from file size.
- Bad input → `{"code","message"}` with HTTP 400

**Analytics** — computed over 545 seeded attempts across 28 sessions / 20 days.
Every metric returned real values. The confusion-pair detector independently
surfaced the genuine learner traps: る/ろ, ぬ/め, き/さ, わ/ね, は/ほ.

**Desktop window** — pywebview opened `Japanese Practice — 日本語練習`, loaded
the dashboard, and pulled 21 KB of analytics from the API. Japanese glyphs render
correctly (Noto Sans CJK JP present system-wide).

---

## 4. Three bugs found and fixed (do not reintroduce)

1. **Circular import.** `app.py` imported `routes.api`, which imported `get_db`
   back from `app`. Fixed by defining `get_db()` inside `routes/api.py` using
   `current_app`. **Do not** move `get_db` back into `app.py`.

2. **`.view` hidden by default.** `theme.css` inherits the mockup's view-switcher
   contract: `.view { display:none }` / `.view.on { display:block }`. Templates
   **must** carry `class="view on"` or the entire page body is invisible with no
   error. This cost real debugging time — the page looked blank while the API was
   returning 200s.

3. **CJK text in `--mono`.** The mockup set kanji readings in `var(--mono)`, a
   stack with no CJK member, which renders tofu. Fixed in `.back-sound`.
   **Rule: `--mono` is for numerals only. All Japanese text uses `--jp`.**

---

## 5. What works / what does not

### Works
- **Test suite: 155 passing in ~1s**, `ruff` and `black` clean
- Full session lifecycle: start → answer → score → end, persisted to SQLite
- All 13 analytics metrics, computed at query time from `attempts`
- Per-character miss-rate heatmap, amber-intensity encoded, click-to-drill
- Deck shelf with live segment counts
- Real TTS audio with graceful degradation
- pywebview desktop window and `--no-window` browser mode
- Post-edit lint hook (black + ruff on Python edits)

### Does not work / not done
- **Reverse-face glyph enlarged 2026-08-06** — `.back-mini` went from a flat
  38px muted thumbnail to `clamp(64px, 8.5vw, 96px)` in full ink. Verified on
  both a kana back (あ) and the worst-case kanji back (三 with meaning, on'yomi
  and kun'yomi) — no overflow in either.
- **UI layout is functional but unpolished.** `theme.css` (2159 lines) was
  generated against the mockup's exact DOM; the templates approximate it. Several
  panels below the fold are unverified visually. Inline `style=` attributes were
  used as spacing stopgaps in `dashboard.html` — these should move into CSS.
- ~~`study.html` unverified~~ — **FULLY VERIFIED 2026-08-06** with `xdotool`
  installed. Every keyboard control exercised against the live pywebview window:
  Space flips, ←/→ navigate, ↑/↓ change volume (readout confirmed at 90%),
  M mutes, P plays, H opens the shortcut panel, J/F grade (score 30, streak
  reset on a wrong answer confirmed), Esc ends and shows the recap.
- ~~No tests~~ — **155 tests passing** as of 2026-08-06 (scoring 35, content 58,
  analytics 41, API 21). Full breakdown and coverage gaps in
  [TESTING.md](TESTING.md). Not covered: frontend JS, keyboard controls, the CSS
  flip animation, and the live ElevenLabs call.
- **`first_vs_eventual` reads 0% against the demo data** — the seeded history
  sets `first_attempt=1` on every row, so there is nothing to contrast. The
  metric itself is correct and is now proven by
  `test_first_vs_eventual_separates_recall_from_recognition`, which asserts
  first 0.5 / eventual 0.75 / gap 0.25. Real usage will populate it.
- **Kanji beyond N5 is not seeded.** `content/kanji_n5.py` only. The dashboard
  shelf code fully supports N4–N1 and the Top 200/500 volume tiers — `DECK_META`
  defines all of them — but with no characters seeded those shelves are hidden
  rather than rendered as empty cards. This is the single largest visible gap
  against the mockup, and it is a **content** gap, not a UI one.
- **`.claude/rules/` contains a duplicate** — `memory-rules.md` and
  `universal-memory-rules.md` are byte-identical. Kept both because the standards
  forbid removing universal rules; worth a decision.
- **Unused example rules and agents** were deployed (`backend-example.md`,
  `infra-example.md`, `react-example.md`, `chrome-ext.md`, `stream-engineer.md`)
  and do not apply to this stack.

---

## 6. Environment gotchas

| Gotcha | Detail |
|---|---|
| **venv must use `--system-site-packages`** | Otherwise pywebview cannot import `gi` and silently degrades to server-only |
| **`gh` CLI is not installed** | `~/.gitconfig` points its credential helper at a missing `/usr/bin/gh`, so plain `git push` fails |
| **Git auth works via header** | See below. Token lives in `~/.config/gh/hosts.yml` |
| **`pkill -f japanese_practice` kills the calling shell** | The pattern matches the shell's own command line. Use a narrower pattern |
| **Firefox headless screenshots are unreliable here** | It restores previous session tabs, times out, and renders app pages BLANK even when the app is correct. It cost significant debugging time chasing a non-bug. **Always verify UI in the real pywebview window** + ImageMagick `import -window <id>` |
| **No `xdotool`, no `xvfb-run`** | `wmctrl` and `import` are available |

**Git push (the only method that works on this machine):**

```bash
TOK=$(grep -m1 'oauth_token:' ~/.config/gh/hosts.yml | awk '{print $2}')
AUTH=$(printf 'x-access-token:%s' "$TOK" | base64 -w0)
git -c http.extraheader="Authorization: Basic $AUTH" push origin main
```

Never write the token into a file, the remote URL, or a commit.

---

## 7. Repository policy

**`language-learning-flashcards` is PUBLIC.** These are excluded via `.gitignore`
and must stay excluded:

- `docs/REPO-ACCESS.md` — documents where credentials live
- `universal-instruction-set-main/` and its `.zip` — contents of a **private** repo
- `.venv/`, `*.db`, `__pycache__/`

Before any push, confirm:
```bash
git status --short | grep -E 'REPO-ACCESS|universal-instruction-set-main' && echo LEAK || echo clean
```

Commit identity is `MensuraMedia <MensuraMedia@users.noreply.github.com>` —
chosen deliberately to keep the real address out of public history.

---

## 8. Next actions, in order

1. **Fix the detached `.btn` rendering.** The topbar "End" link and the help
   panel's "Close" button render centred in their container rather than inline,
   in WebKit. `.topbar-right .btn, .panel-h .btn { flex: 0 0 auto }` did not
   resolve it and asset cache-busting ruled out staleness. Cosmetic, not
   functional. Reproduce in the pywebview window, not Firefox.
2. **Finish the dashboard layout** — check every panel below the fold renders
   (trend, retention, latency, time-of-day, leeches, mastery, calendar). Move the
   inline `style=` stopgaps into `theme.css`.
3. **Add `pytest-cov`** and set a coverage floor; the suite exists but coverage
   is unmeasured.
4. **Seed Kanji N4–N1** so those difficulty keys stop returning empty decks.
5. **Bundle real kana audio clips** to replace TTS for the fixed 104-character sets.
6. **Decide the `.claude/rules/` duplicate** and whether to drop the non-applicable
   example rules and agents.
7. **Package** — `.deb` / AppImage, per the README roadmap.

---

## 9. Document map

| Document | Purpose |
|---|---|
| `README.md` | Public-facing: what the app is, features, roadmap |
| `docs/HANDOFF.md` | **This file** — session-to-session continuity |
| `docs/ARCHITECTURE.md` | How the system works; stack rationale; supportability, applicability, universality |
| `docs/BUILD-SPEC.md` | Binding implementation contract — paths, signatures, schema |
| `docs/AUDIO.md` | Audio resolution chain, ElevenLabs setup, voice-selection criteria |
| `docs/TESTING.md` | Test suite structure, what each layer proves, coverage gaps |
| `docs/PROJECT-CONTEXT.md` | Original brief, requirements decomposition, confirmed decisions |
| `docs/REPO-ACCESS.md` | **Local only, never pushed** — credential paths and working git commands |
| `mockups/COMPARISON.md` | Evaluation of the five design directions |
| `mockups/_reference/JAPANESE-CONTENT-MODEL.md` | Authoritative character data — binding |
| `changelog.md` | Append-only change log |
| `.claude/memory/decisions.md` | Architectural decisions with rationale |
