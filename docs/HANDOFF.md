# HANDOFF — Japanese Practice

**Living document. Update it at the end of every working session.**
It is the single place a new session (human or agent) reads to know where the
project stands, what is real, what is assumed, and what to do next.

- **Last updated:** 2026-08-08 03:30 UTC-4
- **Updated by:** session `30934411` (Claude Opus 5)
- **Project root:** `/home/user/projects/japanese_practice`
- **Remote:** https://github.com/MensuraMedia/language-learning-flashcards (public)
- **Current state:** application runs end to end; **290 tests passing**; 1,459 characters across 17 decks; profiles, save/load and reset shipped; README carries 13 real screenshots
- **Head:** `4661b01` — pushed

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
| Analytics engine | ✅ 13 metrics compute from real data (time-of-day and mastery-by-group removed on request) |
| Desktop window (pywebview) | ✅ Opens and renders |
| UI layout polish | ✅ Dashboard rebuilt to the approved mockup (deck shelves, instrument row, history) |
| Audio (local TTS) | ✅ **Working end to end.** espeak-ng + `ja` voice; API returns audible WAV (peaks 0.385–0.786); renders cached |
| Audio (ElevenLabs) | ✅ **630 clips built** — Matilda/Daniel, validated, shipped offline |
| Clip library + validation | ✅ `audio_library.py`, manifest + checksums |
| Keyboard controls | ✅ **All verified with xdotool** |
| Tests | ✅ **290 passing**, lint + format clean — see [TESTING.md](TESTING.md) |
| Kanji content N4–N1 | ✅ **1,138 characters** extracted from the reference charts |
| Kanji frequency tiers | ✅ Top 200 / Top 500 backed by a real `frequency_rank` |
| Per-script shelves & games | ✅ 17 decks, 9 memory boards |
| Profiles, save/load, reset | ✅ Settings dialog, file per profile, glyph-keyed export |
| Kanji audio | ❌ **1,144 of 1,459 characters have no recorded clip** — they fall through to live VOICEVOX synthesis (roadmap N3) |
| Frontend JS tests | ❌ 1,679 lines untested; no runner, `node` not installed (roadmap Q2) |
| Licence & attribution | ✅ Personal-use licence with §5 attribution for derived language-learning apps; `NOTICE` ships in the distribution |
| Screenshots | ✅ 13 in `docs/screenshots/`, regenerable via `tools/demo_data.py` |
| Local desktop install | ✅ **Installed on this machine 2026-08-08.** `tools/install-desktop.sh` — own venv at `~/.local/opt`, launcher on PATH, icon + menu entry. Verified from PATH and from the menu |
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

### As an installed application

It is installed on this machine. Launch from the application menu, or:

```bash
japanese-practice                      # ~/.local/bin -> ~/.local/opt/japanese-practice
./tools/install-desktop.sh             # reinstall / upgrade from this tree
./tools/uninstall-desktop.sh           # remove it, keeping study history
```

The installed copy is a **non-editable wheel in its own venv**, so it does not
read this tree at runtime — verified: `/proc/<pid>/maps` shows zero mappings
from `projects/japanese_practice`. Edits here do not reach the installed app
until the install script is re-run.

---

## 3. Verified working (executed, not assumed)

Nothing in this section is inferred. Each line is something a command produced.

### Verified 2026-08-08 (this session)

**Suite** — `290 passed in ~5s`; `ruff check src/ tests/ tools/` and
`black --check` both clean.

**Content** — asserted by `test_documented_totals_match_the_seed_set`, not just
counted once:
- Hiragana 104 · Katakana 104
- Kanji N5 113 · N4 169 · N3 396 · N2 236 · N1 337 — **1,251 kanji, 1,459 total**
- Frequency list 500; Top 200 verified to be exactly its first 200
- 789/789 extracted readings round-tripped romaji → kana → romaji identically
- 84 confusion pairs, every glyph confirmed seeded

**API** — served from a cold start on a fresh database:
`/api/segments` (**17** decks) · `/api/games` · `/api/profiles` ·
`/api/data/summary` · `/api/heatmap?difficulty=kanji:top200` — all 200.

**Kanji option readings** — spot-checked against the cards dealt:
父 `fu` · 本 `hon` · 足 `soku` · 飲 `in` · 食 `shoku` · 四 `shi` · 魚 `gyo` ·
田 `den` · 言 `gen`. All correct on'yomi.

**Confusion boards deal both halves of a pair** — hiragana も/ま に/こ あ/め ·
katakana ス/ヌ ツ/シ チ/テ · kanji 像/象 百/白 木/休.

**Profiles isolate history** — default profile 1 attempt → create "Kenji" → 0
attempts → switch back → 1 attempt. Also covered by
`test_profiles_keep_separate_histories`.

**Export is glyph-keyed** — an attempt row exports as
`{"glyph": "ひ", "session_id": 1, "correct": 1, …}` with no `character_id`.

**Packaging** — `importlib.metadata` reports `License-File: LICENSE, NOTICE`.

**Desktop window** — captured 13 screenshots from the live pywebview window:
dashboard, kanji shelf, both card types front and back, session recap, memory
board, heatmap, streak, weak characters, performance, settings.

### Verified earlier, still true

- Hepburn traps correct: し=shi, ち=chi, つ=tsu, ふ=fu, じ=ji, を=wo, ん=n,
  しゃ=sha, じゅ=ju, ちょ=cho
- No duplicate glyphs; all glyphs inside their correct Unicode ranges
- Full session lifecycle: start → answer → score → end, persisted
- `GET /api/audio/<id>` returns a playable WAV.
  **CORRECTION (2026-08-06 22:00):** an earlier note here claimed this was "real
  espeak synthesis". It was not. 17,684 bytes is *exactly* the silent stub
  (0.4s × 22050Hz × 2 bytes + 44-byte header) — the size was inferred from,
  rather than verified against, the content, and **no TTS binary was installed
  at all**. `espeak-ng` has since been installed and real synthesis is verified
  by amplitude (peak 0.571, 772 ms for あ). **Never infer audio validity from
  file size.**
- Every keyboard control exercised against the live window with `xdotool`

### Measured, but not fully

- **Pace timing.** The five-step table in FEATURES is *computed* from the
  constants in `study.js`. Exactly one hold was measured end to end — 355 ms at
  *relentless*, against a computed 380 ms. The other four were not: the
  screenshot-polling harness available here costs ~250 ms per sample, which is
  too coarse. Roadmap **Q7**.

---

## 4. Bugs found and fixed (do not reintroduce)

1. **Circular import.** `app.py` imported `routes.api`, which imported `get_db`
   back from `app`. Fixed by defining `get_db()` inside `routes/api.py` using
   `current_app`. **Do not** move `get_db` back into `app.py`.

2. **`.view` hidden by default.** `theme.css` inherits the mockup's view-switcher
   contract: `.view { display:none }` / `.view.on { display:block }`. Templates
   **must** carry `class="view on"` or the entire page body is invisible with no
   error. This cost real debugging time — the page looked blank while the API was
   returning 200s.

3. **Class-name collision with the design system.** A pass control classed
   `skip` silently inherited `.skip`, the accessibility skip-to-content link
   (`position:absolute; top:-40px`), and was yanked out of the button row.
   **Check `theme.css` for an existing rule before naming a new class.** Now
   `.btn-skip`.

4. **CJK text in `--mono`.** The mockup set kanji readings in `var(--mono)`, a
   stack with no CJK member, which renders tofu. Fixed in `.back-sound`.
   **Rule: `--mono` is for numerals only. All Japanese text uses `--jp`.**

5. **A third class collision.** `class="btn ghost"` inherited `.ghost`, the
   deck's fanned-sheet class (`position:absolute; inset:0`, `::after` content
   記), and the button was pulled out of its row. Renamed `.btn-ghost`.
   **That is three collisions now** (`.skip`, `.ghost`, and `.view` behaving as
   a switcher). Grep `theme.css` before naming any class.

6. **`.btn` carries `flex: 1`.** It is set for the study foot's three-across
   row, so a `.btn` dropped into any other flex container stretches to fill it.
   Seen on `Drill weak set` and the settings buttons. Add `flex: 0 0 auto` in
   new containers.

7. **Statement nested inside a handler it was meant to precede.** The
   "reflect a deep-linked mode in the picker" line sat *inside* the mode
   picker's own click listener, so it only ran on a click. Arriving from a
   dashboard game card dealt the correct board while the picker still
   highlighted Match Up — a mismatch that looked like a routing bug and was an
   indentation bug.

8. **Content sized for kana does not fit kanji.** Twice: study options
   ("world/generation" in a square built for `kya`) and game tiles
   ("interval, between" running off the edge). **Whenever a surface shows a
   reading, check it with a kanji meaning, not a two-letter romaji.**

9. **`sqlite_sequence` does not exist here.** The schema uses no `AUTOINCREMENT`,
   so a reset that tried to clear it would have raised. Plain rowids restart on
   their own once a table is empty.

10. **Documented counts drift.** The docs said 1,453 characters / 1,245 kanji —
    true when written, wrong the moment six characters were added to N5. Now
    asserted by `test_documented_totals_match_the_seed_set`. **Do not quote a
    count in prose without a test behind it.**

---

## 5. What works / what does not

### Works

**Study**
- Multiple-choice answering — three options, server-shuffled, drawn from
  confusion partners → voicing siblings → same group → same script, so a card
  cannot be won by elimination. Selection auto-scores; no self-grading buttons.
- Skip scores −1 and stores `attempts.skipped = 1`, which feeds the weakness
  views (a skip weighs 1.25× a wrong guess in `weighted_miss`: a pass means no
  recall at all, where a wrong guess still shows a partial trace).
- Back / Next split control; Next is live only after going back.
- **Pace slider** — 5 steps, 1.0× → 0.2× on the verdict hold, floored at 260 ms.
- **Kanji reading reference** — romaji on the card back and on every option.
- Session recap: every character seen, misses in red with romaji beneath.
- Full keyboard control, verified with `xdotool` against the live window.

**Content** — 1,459 characters, 17 decks, all keys resolving. See §3.

**Games** — 9 boards (3 modes × 3 scripts), script picker, confusion boards
dealing both halves of a pair.

**Dashboard** — per-script shelves each with their own games rail; the
miss-rate map with set selector, table view and unseen characters shown; streak;
weak characters; accuracy trend, accuracy by deck, retention curve, leeches,
session history. Kanji surfaces carry a green accent.

**Profiles & data** — file per profile, glyph-keyed export/import, reset behind
an explicit confirmation.

**Platform** — pywebview window and `--no-window` browser mode; post-edit lint
hook (black + ruff).

### Does not work / not done

| Gap | Detail | Roadmap |
|---|---|---|
| **Kanji audio** | 1,144 of 1,459 characters have no recorded clip and synthesise live on every press — correct, but slower and unvalidated. Which reading to record is also undecided | N3, N3b |
| **Reading-field accuracy** | ~530 single-reading entries had on'/kun' picked by a lexicon rule measured at 94.6%, implying ~30 mislabels. Card-back annotations only — kanji are graded on meaning — but wrong | N6 |
| **Stroke counts** | 1,138 kanji have `stroke_count = NULL`; the charts do not carry them | N7 |
| **Frontend JS untested** | 1,679 lines across three files, no runner, `node` not installed. Three of the four bugs found this project have been in exactly this code | Q2 |
| **No real-window test** | Everything runs through the Quart test client. Every WebKit-only defect so far — invisible `.view`, three class collisions, `localStorage` throwing — was invisible to it | Q8 |
| **Pace timing** | Four of the five holds never measured end to end | Q7 |
| **Below-the-fold panels** | Retention, accuracy-by-set, leeches and session history have not been visually confirmed *together* with real data. The rest have | U3 |
| **4 of 5 challenge types** | `recall`, `timed`, `listening`, `mixed` are stored, displayed as tags, and never branched on. Only `recognition` exists | M1–M7 |
| **Scored mode has a dominant strategy** | Flip reveals the answer and is free and unrecorded; skip is strictly dominated by guessing | D1–D4, C1 |
| **Mastery means recognition** | At a 33% chance floor, `miss_rate ≤ 0.15` is roughly 78% true recall. The meter says "mastered" | C4 |
| **Preferences are per-browser** | Pace, voice, volume live in `localStorage`, so two profiles on one machine share them | X2 |
| **Inline `style=` stopgaps** | Still present in `dashboard.html` | U2 |
| **Packaging** | Not started; an upgrade must also preserve profiles | P1–P3, P7 |
| **`.claude/rules/` duplicate** | `memory-rules.md` and `universal-memory-rules.md` are byte-identical; kept because the standards forbid removing universal rules | S1 |
| **Unused example rules/agents** | `backend-example.md`, `infra-example.md`, `react-example.md`, `chrome-ext.md`, `stream-engineer.md` do not apply to this stack | S2 |

### Resolved since the last handoff

- ~~Kanji beyond N5 not seeded~~ — 1,138 characters added 2026-08-08.
- ~~Top 200/500 decks withdrawn~~ — backed by `frequency_rank`.
- ~~No data export~~ — glyph-keyed save/load plus profiles and reset.
- ~~`first_vs_eventual` reads 0%~~ — the demo generator now produces in-session
  repeats, so it reports a real gap.
- ~~Detached `.btn`~~ — a class collision, not a flex problem. See §4.5.

---

## 6. Environment gotchas

| Gotcha | Detail |
|---|---|
| **venv must use `--system-site-packages`** | Otherwise pywebview cannot import `gi` and silently degrades to server-only |
| **`gh` CLI is not installed** | `~/.gitconfig` points its credential helper at a missing `/usr/bin/gh`, so plain `git push` fails |
| **Git auth works via header** | See below. Token lives in `~/.config/gh/hosts.yml` |
| **`pkill -f japanese_practice` kills the calling shell** | The pattern matches the shell's own command line. Use a narrower pattern |
| **Never `git checkout <file>` to undo a temporary patch** | That file may also hold uncommitted work. It cost the `/games` route: the route was added, temp-patched for a screenshot, then `git checkout`-ed to undo the patch — which silently deleted the route too. Copy the file aside first, or edit the patch back out |
| **Firefox headless screenshots are unreliable here** | It restores previous session tabs, times out, and renders app pages BLANK even when the app is correct. It cost significant debugging time chasing a non-bug. **Always verify UI in the real pywebview window** + ImageMagick `import -window <id>` |
| **The webview caches CSS hard** | `ctrl+r` is not enough — a stylesheet edit can appear not to apply. Restart the process. The `asset_version` stamp handles this for users, not for a running dev window |
| **Quotes inside `git commit -m "…"`** | A message containing `"` breaks the shell parse and git reports a bogus `pathspec` error. Write the message to a file and use `-F` |
| **`xdotool` IS installed** | An earlier note here said it was not. `wmctrl`, `import` (ImageMagick) and `xdotool` are all available |
| **Click with `--window`, not absolute coordinates** | `xdotool getwindowgeometry` returns the *frame* origin, and the client area starts below the decoration. Absolute clicks land ~30 px high, which still hits a large deck card but misses a 22 px topbar button entirely. Use `xdotool mousemove --window <id> <x> <y>`, with coordinates read straight off an `import -window` capture |
| **`xdotool --window key` does not work on WebKit** | Synthetic events sent to a specific window are ignored. Keystrokes must go through XTEST: `xdotool key <k>` with **no** `--window`, after `windowactivate --sync` |
| **The window resizes itself between runs** | Captures come back 1280×860 or 1920×1008 depending on the session. Always `identify` the capture before computing crop coordinates from it |
| **Scroll with the pointer in the left gutter** | Scrolling with the cursor over a deck card can activate it. Park at `x = 6` first |

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

Full register with QA criteria: [ROADMAP.md](ROADMAP.md).

1. **Rotate the ElevenLabs API key.** It was pasted into a session transcript and
   has never been rotated. Nothing else on this list matters as much.
2. **Narrate the 1,144 new kanji** (roadmap N3). The speaker button on a kanji
   card currently falls through to live VOICEVOX synthesis every time — correct,
   but slower and unvalidated. Decide which reading to record first (N3b).
3. **Audit the single-reading on/kun assignments** (roadmap N6). ~530 entries had
   their field picked by a lexicon rule measured at 94.6%, so roughly 30 are
   likely mislabelled. They are card-back annotations, not scored, but they are
   wrong.
4. **Add `pytest-cov`** and a coverage floor (Q1); coverage is still unmeasured
   across 290 tests.
5. **Get a JS test runner in place** (Q2). The frontend is now 1,679 untested
   lines and this cycle added the pace scaling, the heatmap, the streak panel and
   the settings dialog to it.
6. **Verify the remaining below-the-fold panels** (U3) — retention,
   accuracy-by-set, leeches and session history have not been confirmed together
   with real data.
7. **Close the game-theory decisions D1–D4.** They are cheap individually and
   interact; the scored mode still has a dominant strategy.
8. **Decide the `.claude/rules/` duplicate** and whether to drop the
   non-applicable example rules and agents (S1, S2).
9. ~~Retake the local backup~~ — **done 2026-08-08**, set `20260808-0015`,
   verified by restoring and running the suite from it (§10).
10. **Package** — `.deb` / AppImage (P1–P3), and make sure an upgrade preserves
    profiles (P7).

### Solved, do not redo

- ~~Detached `.btn`~~ — **2026-08-07.** Not a flex problem: `class="btn ghost"`
  collided with `.ghost`, the deck's fanned-sheet class (`position:absolute;
  inset:0`, with a 記 `::after`). **The second such collision** — see also
  `.skip`. Grep `theme.css` before naming a class.
- ~~Seed Kanji N4–N1~~ — **2026-08-08.** 1,138 characters from the reference
  charts.
- ~~Top 200 / Top 500 decks~~ — **2026-08-08.** Backed by a `frequency_rank`
  column rather than an id slice.
- ~~Data export~~ — **2026-08-08.** Glyph-keyed JSON, plus profiles and reset.
- ~~README has no screenshots~~ — **2026-08-08.** 13 captures, with
  `tools/demo_data.py` to regenerate the history behind them.

---

## 9. Document map

| Document | Purpose |
|---|---|
| `README.md` | Public-facing: what the app is, features, roadmap |
| `docs/RELEASE-NOTES.md` | What changed each cycle, with the reasoning and the known-unfixed list |
| `docs/HANDOFF.md` | **This file** — session-to-session continuity |
| `docs/ARCHITECTURE.md` | How the system works; stack rationale; supportability, applicability, universality |
| `docs/BUILD-SPEC.md` | Binding implementation contract — paths, signatures, schema |
| `docs/AUDIO.md` | Audio resolution chain, ElevenLabs setup, voice-selection criteria |
| `docs/FEATURES.md` | Complete feature and function reference |
| `docs/STACK-VERIFICATION.md` | Stack, modularity and universality audit |
| `LICENSE` | **Personal use only** — commercial use, modification and redistribution need written consent; §5 requires attribution for any derived language-learning app |
| `NOTICE` | The exact attribution text a derivative work must display, and where |
| `docs/ROADMAP.md` | **Every outstanding item with QA acceptance criteria** — start here for what is left |
| `docs/VOICE-LAB.md` | MECE toolset: credential → selection → derivation → synthesis → validation → storage → consumption |
| `docs/TESTING.md` | Test suite structure, what each layer proves, coverage gaps |
| `docs/PROJECT-CONTEXT.md` | Original brief, requirements decomposition, confirmed decisions |
| `docs/REPO-ACCESS.md` | **Local only, never pushed** — credential paths and working git commands |
| `mockups/COMPARISON.md` | Evaluation of the five design directions |
| `mockups/_reference/JAPANESE-CONTENT-MODEL.md` | Authoritative character data — binding |
| `tools/demo_data.py` | Deterministic generator for a plausible study history — needed to photograph or eyeball the analytics panels |
| `docs/screenshots/` | 13 captures used by the README; regenerate with the tool above |
| `changelog.md` | Append-only change log |
| `.claude/memory/decisions.md` | Architectural decisions with rationale |

---

## 10. Backups

Local backup set at `/home/user/projects/backups/japanese_practice/`, with
`RESTORE.md` alongside the artefacts.

| Artefact | Holds |
|---|---|
| `*.bundle` | Full git history — the authoritative copy |
| `*-worktree-*.tar.gz` | Working tree **including git-ignored files** (`REPO-ACCESS.md`, `settings.local.json`) |
| `*-userdata-*.tar.gz` | `~/.local/share/japanese-practice/` — the study database, `active-profile` and any `profiles/*.db`, minus the regenerable audio cache |

The bundle omits ignored files; the tarball omits history. Keep both.

### Current set — `20260808-0015`

**Verified 2026-08-08 by restoring it**, not by inspecting it: cloned the bundle
into a scratch directory → 29 commits, clean tree, 630 audio clips, 13
screenshots, five kanji seed modules, and **290/290 tests passed from the
restored tree**.

| Check | Result |
|---|---|
| `git bundle verify` | okay · records a complete history at `ec3410e` |
| `sha256sum -c SHA256SUMS.txt` | all 6 artefacts OK |
| Git-ignored files present in worktree tarball | `docs/REPO-ACCESS.md` ✓ · `.claude/settings.local.json` ✓ |
| Private/derived content excluded | `universal-instruction-set-main` 0 · `.venv` 0 · `__pycache__` 0 |
| Credential scan across all three artefacts | clean — the live token values appear in none of them |

The `20260807-0540` set is kept as a rollback point only. It predates 1,144
characters, profiles, save/load, the licence rewrite and the screenshots — and
**its userdata tarball is 121 bytes, an empty directory**, because no study
database existed when it was taken.

### Two traps in the procedure itself

1. **`git bundle verify` must run from inside a repository.** In the backup
   directory it fails with `need a repository to verify a bundle`, which reads
   like a corrupt bundle and is not. The command in `RESTORE.md` was wrong on
   this point and has been corrected.
2. **Commit and push before backing up.** The bundle carries committed history;
   the worktree tarball carries files. A dirty tree makes the two artefacts
   disagree, silently.

Keep the worktree tarball local — it contains `REPO-ACCESS.md`.
