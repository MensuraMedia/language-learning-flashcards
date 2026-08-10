# Project Change Log

> Local record of all changes. Does NOT depend on git. Updated every time a change is made.

| Date-Time | Change Description |
|-----------|-------------------|
| 2026-08-06T05:03:00 | Recovered prior session context; created docs/PROJECT-CONTEXT.md |
| 2026-08-06T05:15:00 | Verified repo access paths; created docs/REPO-ACCESS.md |
| 2026-08-06T05:18:00 | Extracted universal-instruction-set-main.zip (identical to repo HEAD 6099a45) |
| 2026-08-06T05:20:00 | git init; deployed universal-agents + universal-permissions standards |
| 2026-08-06T05:21:00 | Created .claude/memory structure, .claudeignore, .gitignore, changelog.md |
| 2026-08-06T05:21:30 | Uncommented Python block in .claude/hooks/post-edit-lint.sh |
| 2026-08-06T05:40:00 | Created mockups/01-hud-command-deck.html (direction 01: HUD Command Deck, amber #f5c518) |
| 2026-08-06T00:00:00 | Created src/japanese_practice/content/kanji_n5.py — KANJI_N5 seed list, 107 JLPT N5 kanji |
| 2026-08-06T05:56:00 | Added persistence foundation: __init__.py, config.py, models.py, schema.sql, db.py, content/loader.py |
| 2026-08-06T05:50:00 | Added docs/BUILD-SPEC.md — binding implementation contract |
| 2026-08-06T05:55:00 | Added docs/ARCHITECTURE.md — stack rationale, supportability, universality |
| 2026-08-06T06:00:00 | Built content layer: hiragana 104, katakana 104, kanji N5 107; verified counts and Hepburn |
| 2026-08-06T06:05:00 | Built session.py, analytics.py (13 metrics), app.py, routes, templates, frontend JS |
| 2026-08-06T06:06:00 | Fixed circular import: get_db moved into routes/api.py |
| 2026-08-06T06:10:00 | Verified all API endpoints; audio confirmed as real espeak synthesis |
| 2026-08-06T06:13:00 | Recreated venv with --system-site-packages so pywebview can find gi |
| 2026-08-06T06:14:00 | Fixed .view visibility — templates must carry class="view on" |
| 2026-08-06T06:15:00 | Fixed CJK-in-mono font bug in .back-sound (renders tofu) |
| 2026-08-06T06:16:00 | Restructured dashboard.html to theme.css layout contract; shelf now horizontal |
| 2026-08-06T06:20:00 | Added docs/HANDOFF.md — living session-continuity document |
| 2026-08-06T20:30:00 | Rebuilt study.html to theme.css DOM contract (.deck3d > .tilt > .lift > .card3d) |
| 2026-08-06T20:35:00 | Verified study view in pywebview: front glyph-only, back reading + speaker, flip works |
| 2026-08-06T20:38:00 | Added tts_elevenlabs.py — ElevenLabs TTS backend, env-keyed, male/female voices |
| 2026-08-06T20:39:00 | Wired ElevenLabs into audio.get_audio ahead of local TTS, cached per (text, voice) |
| 2026-08-06T20:40:00 | Added docs/AUDIO.md — resolution chain, credentials, voice criteria, cost |
| 2026-08-06T21:00:00 | Added tests/: conftest, scoring (35), content (58), analytics (41), API (21) |
| 2026-08-06T21:02:00 | Full suite green — 155 passed, ruff clean, black clean |
| 2026-08-06T21:05:00 | Added docs/TESTING.md; updated HANDOFF with test status and revised next actions |
| 2026-08-06T21:30:00 | Installed xdotool; verified every keyboard control against the live pywebview window |
| 2026-08-06T21:35:00 | Added keyboard map: arrows navigate, up/down volume, M mute, P play, H/? help overlay |
| 2026-08-06T21:40:00 | Fixed localStorage crash in WebKit — module died before start(); preferences now guarded |
| 2026-08-06T21:45:00 | Fixed .recap never displaying (display:none base rule); hidden attr now authoritative |
| 2026-08-06T21:50:00 | Added asset cache-busting (?v=mtime) — embedded webviews cached stale CSS/JS |
| 2026-08-06T22:00:00 | Installed espeak-ng; CORRECTED false claim that audio was real synthesis (was silent stub) |
| 2026-08-06T22:05:00 | Added audio_library.py — local clip tree, validation gates, manifest with checksums |
| 2026-08-06T22:10:00 | Added tests/test_audio_library.py (26); full suite 181 passing |
| 2026-08-06T22:20:00 | Verified audio end to end: /api/audio returns audible WAV (peaks 0.385-0.786), ja voice, cached |
| 2026-08-06T22:30:00 | Enlarged reverse-face glyph: .back-mini 38px -> clamp(64px, 8.5vw, 96px), full ink |
| 2026-08-06T22:35:00 | Verified enlarged back face on kana and worst-case kanji — no overflow |
| 2026-08-06T22:50:00 | Added analytics.deck_shelves + session_history; totals gained avg_latency_ms |
| 2026-08-06T23:00:00 | Rebuilt dashboard to the approved mockup: deck cards with rung/glyphs/obi meter/tags |
| 2026-08-06T23:02:00 | Added 6-tile instrument row with accuracy sparkline, session history table, accuracy-by-set |
| 2026-08-06T23:05:00 | Tests 187 passing; empty shelves hidden rather than rendered as blank cards |
| 2026-08-06T23:20:00 | Removed cursor-tilt hover motion — only the flip animation remains |
| 2026-08-06T23:25:00 | Replaced self-grading Right/Wrong with 3-option multiple choice beside the card |
| 2026-08-06T23:30:00 | Choices drawn from same kana group / JLPT level so they cannot be solved by elimination |
| 2026-08-06T23:35:00 | Added skipped state: schema column + migration, -1 score, 1.25x weight in weakness |
| 2026-08-06T23:40:00 | Fixed .skip class collision with the accessibility skip-link; renamed .btn-skip |
| 2026-08-06T23:45:00 | Tests 193 passing (+12 for choices and skipping) |
| 2026-08-07T03:05:00 | Yoon deck preview trimmed to 2 glyphs — 3 digraphs overran the card border |
| 2026-08-07T03:10:00 | Study symmetry: squared half-size choices, half-size controls, added Back button |
| 2026-08-07T03:12:00 | Audio button reduced to the speaker icon alone |
| 2026-08-07T03:15:00 | Dashboard type scale raised for all chrome text outside card faces |
| 2026-08-07T03:18:00 | Added app icon — あ in amber on gray; window icon, favicon and brand mark |
| 2026-08-07T03:20:00 | Withheld kanji Top 200/500 decks — frequency rank is not stored, labels were unbacked |
| 2026-08-07T03:22:00 | Fixed calendar cells sized as SVG rects; fixed accuracy-by-set row wrapping |
| 2026-08-07T03:30:00 | Choice cards: romaji centred at 21px, shortcut number moved to bottom-right corner |
| 2026-08-07T03:50:00 | Game-theory review of the answer flow — found 4 real defects, see docs/GAME-DESIGN-REVIEW.md |
| 2026-08-07T03:52:00 | FIX: build_deck shuffled `unseen` after concatenation — a no-op; decks always dealt in id order |
| 2026-08-07T03:54:00 | FIX: first_attempt was hardcoded 1, making first_vs_eventual a structural zero |
| 2026-08-07T03:56:00 | FIX: wired CONFUSION_PAIRS into build_choices — 45 curated traps were dead data |
| 2026-08-07T03:58:00 | FIX: added voicing-sibling distractors so han-dakuon finally tests は/ば/ぱ |
| 2026-08-07T04:00:00 | FIX: closed the free-skip loophole — arrow-right no longer bypasses grading |
| 2026-08-07T04:10:00 | ElevenLabs key verified working (TTS scope only); stored at ~/.config outside the repo |
| 2026-08-07T04:15:00 | Added voicelab.py — audition/cost/build/verify toolset for pronunciation clip sets |
| 2026-08-07T04:20:00 | Auditioned 9 candidate voices; selected Matilda (female) and Daniel (male) on measured pace |
| 2026-08-07T04:30:00 | Built 630 clips (315 characters x 2 voices) — all validated, zero rejected, no drift |
| 2026-08-07T04:35:00 | /api/audio gained ?voice=female|male; bundled lookup is now per-voice |
| 2026-08-07T04:40:00 | Added docs/VOICE-LAB.md — MECE decomposition of the whole audio pipeline |
| 2026-08-07T04:50:00 | Added voice toggle to study view (V key / button), persisted; /api/audio?voice= honoured |
| 2026-08-07T04:52:00 | Verified live: window served the 15,926-byte male clip after toggling — bundled, not synthesised |
| 2026-08-07T05:00:00 | Added docs/ROADMAP.md — 50 outstanding items with QA acceptance criteria, grouped and sequenced |
| 2026-08-07T05:05:00 | Acoustic QA over all 630 clips via ffprobe; found and re-rendered a truncated hiragana/female/へ (0.24s) |
| 2026-08-07T05:08:00 | Added cross-voice consistency check — an absolute duration floor cannot catch a clip too short for its character |
| 2026-08-07T05:20:00 | Evaluated VOICEVOX: ran engine 0.25.2 locally, verified pitch accent on minimal pairs |
| 2026-08-07T05:25:00 | Added docs/VOICEVOX-EVALUATION.md — verdict: adopt as primary, ElevenLabs as fallback |
| 2026-08-07T05:28:00 | Roadmap A8 closed; A9-A12 added (integration, shipping model, attribution, pitch-accent aid) |
| 2026-08-07T05:40:00 | Local backup: git bundle (15 commits) + worktree archive + user data, checksummed |
| 2026-08-07T05:42:00 | Verified restore — bundle cloned clean, 630 clips intact, 216/216 tests passed from it |
| 2026-08-07T05:55:00 | Added tts_voicevox.py — Japanese-native provider, optional engine, silent fallback |
| 2026-08-07T05:58:00 | VOICEVOX slotted above bundled clips in get_audio; cached per (text, speaker) |
| 2026-08-07T06:00:00 | voicelab gained warm / speakers / accent commands |
| 2026-08-07T06:02:00 | Added /api/credits + dashboard attribution — required by the VOICEVOX voice terms |
| 2026-08-07T06:05:00 | Verified fallback: dead engine -> bundled clip in 20ms, zero errors, probe memoised |
| 2026-08-07T06:15:00 | Auditioned No.7 styles; set No.7 アナウンス (30) as female default on measured consistency |
| 2026-08-07T06:20:00 | Verified audio reaches the speakers from the pywebview window (sink IDLE -> RUNNING) |
| 2026-08-07T06:35:00 | Warmed the VOICEVOX cache — 619 clips, 18 MB, zero failures |
| 2026-08-07T06:40:00 | Verdict hold: correct 1.9s, wrong 2.9s — a miss is when the learner actually studies |
| 2026-08-07T06:45:00 | Session recap grid: every card at option size, misses in red, romaji beneath |
| 2026-08-07T18:40:00 | Fixed .ghost class collision — 'End' inherited the deck sheet's absolute positioning |
| 2026-08-07T18:42:00 | Recap panel border made uniform; scrolling moved to an inner element |
| 2026-08-07T18:45:00 | Score/accuracy/streak colour-coded green/amber/red against achievable maxima |
| 2026-08-07T18:50:00 | Removed 'Response latency' and 'Confused with' dashboard panels |
| 2026-08-07T19:00:00 | Added games.py + /games — Match Up, Pelmanism, Confusion Drill |
| 2026-08-07T19:05:00 | Boards seed from weakest characters; mis-pairs feed confusion data, not the drill queue |
| 2026-08-07T19:20:00 | Memory tiles: unmistakable selection state (amber border, fill, lift, glow, corner dot) |
| 2026-08-07T19:22:00 | Boards laid out as a centred square block, columns in groups of three |
| 2026-08-07T19:30:00 | FIX: restored the /games route, lost to a `git checkout` used to undo a temp patch |
| 2026-08-07T19:32:00 | Added a route-reachability test so a lost view cannot ship silently again |
| 2026-08-07T19:50:00 | Dashboard game cards linking to each mode, styled as boards rather than decks |
| 2026-08-07T20:00:00 | Verified stack/modularity/universality: 0 import cycles, 0 platform paths, 33-package closure |
| 2026-08-07T20:05:00 | Added docs/FEATURES.md and docs/STACK-VERIFICATION.md |
| 2026-08-07T20:08:00 | Added LICENSE — personal use only; corrected pyproject (was MIT) and README (was "free to distribute") |

## 2026-08-07T19:05:00Z — Study pace slider
- Added a 5-step pace control under the answer options: relaxed → steady → brisk →
  fast → relentless. Scales the post-answer verdict hold (1900 ms correct / 2900 ms
  wrong) by 1.0 → 0.2, floored at 260 ms so a verdict stays readable.
- Persisted as `jp.pace` in localStorage; keyboard `[` and `]` step it.
- Centred the control in the gap between the last option and the control row
  (measured: 31 px above, 32 px below at 1280×860).
- Removed the keymap recital under the control row — the shortcuts panel already
  covers it. The `? shortcuts` link is now centred with a 22 px separation.
- Files: static/js/study.js, static/css/theme.css, templates/study.html

## 2026-08-08T00:20:00Z — Content expansion, per-script games, dashboard rework
- **Kanji N4–N1 seeded**: 1,138 new characters extracted from the reference
  charts in `MensuraMedia/language-learning`. Totals now 1,245 kanji / 1,453
  characters. Readings converted from wapuro romaji to kana mechanically and
  verified by round-trip; the on/kun split for single-reading entries is picked
  by a lexicon built from 664 explicit pairs (94.6% on held-out N1 data).
- **N5 corrected**: added 夕 田 外 青 赤 言, present in the reference chart but
  missing from the transcription. N5 is now 113.
- **Kanji volume tiers made real**: new `frequency_rank` column (additive
  migration) + `content/kanji_frequency.py`, the 500-glyph teaching order taken
  from the printed Top 200/500 decks. `kanji:top200` / `kanji:top500` now slice
  that ranking instead of the id sequence.
- **Dashboard reorganised**: separate Hiragana, Katakana and Kanji shelves, each
  followed by its own games rail. 17 decks in total.
- **Per-script games**: 9 boards (3 modes × 3 scripts). Board dealing, confusion
  pairs and card copy are all script-scoped; games view gains a script picker.
- **Confusion pairs**: 45 → 84, adding 39 kanji look-alikes. Both halves of a
  pair are now dealt together — previously look-alikes arrived without their
  partner, which made the drill an ordinary memory game.
- **Per-character miss rate rebuilt**: set selector, table view, 0–30% colour
  ceiling, and unseen characters shown rather than hidden. New
  `analytics.character_grid()` + `GET /api/heatmap`.
- **Streak and Weak characters panels** rebuilt as instrument modules; new
  `weekly_activity()` and `daily_streak()`. **Removed** Time of day and Mastery
  by group end to end.
- **Kanji accent**: kanji surfaces take the green accent from
  `mockups/03-arcade-ladder.html`; kana keeps amber.
- **Kanji readings as reference**: new `kana.py` (kana → Hepburn romaji, 24
  tests). Card backs show romaji under each reading, and kanji options are
  double height carrying the reading of the character they stand for.
- Tests 240 → 268.

## 2026-08-08T01:30:00Z — Settings: profiles, save/load and reset
- **Profiles** (`profiles.py`): one database file per learner rather than a
  shared table with a filter column, so a forgotten `WHERE` cannot mix two
  histories. The default profile keeps the existing `db_path`, so existing
  installs need no migration. Switching reopens the connection.
- **Save / load** (`userdata.py`): export every session, attempt and review
  state as JSON keyed by glyph rather than id, so a file survives seed-order
  changes and moves between installs. Loading replaces the active profile;
  unknown glyphs are skipped and counted rather than aborting the restore.
- **Reset**: clears progress for the active profile, keeps the seeded
  characters, requires explicit confirmation and reports what it removed.
- New endpoints: `GET/POST /api/profiles`, `POST /api/profiles/activate`,
  `DELETE /api/profiles/<slug>`, `GET /api/data/summary`, `GET /api/data/export`,
  `POST /api/data/import`, `POST /api/data/reset`.
- Settings dialog reached from the dashboard top bar.
- Kanji option text enlarged to 15.5px with the reading at 13px.
- Tests 268 → 289.

## 2026-08-08T02:10:00Z — Documentation pass
- **New** `docs/RELEASE-NOTES.md`: a full catalogue of this cycle — headline
  numbers before/after, one section per feature with the reasoning behind each
  decision, the corrections made along the way, and an explicit known-unfixed
  list pointing at roadmap ids.
- `docs/FEATURES.md` substantially expanded: an at-a-glance table, the pace
  table, the kanji reading reference, per-script shelves and games, the rebuilt
  miss-rate/streak/weak panels and what was removed, all 17 difficulty keys, all
  23 endpoints, and a module reference covering all 32 modules.
- `docs/ROADMAP.md`: N1, N2, U1 and P6 closed; N3 restated (1,144 characters now
  lack audio, not a handful); new items N3b, N6, N7, U7, U8, Q7, Q8, P7, P8 and a
  new §7a covering profiles/data follow-ups; completed-this-cycle table extended.
- `docs/TESTING.md`, `docs/STACK-VERIFICATION.md`, `docs/HANDOFF.md` and
  `README.md` refreshed against measured figures.
- **Corrected stale counts**: the docs said 1,453 characters / 1,245 kanji, which
  was true when written and wrong after six characters were added to N5. Now
  1,459 / 1,251, and asserted by `test_documented_totals_match_the_seed_set` so
  the drift cannot recur silently.

## 2026-08-08T02:40:00Z — Licence: attribution for derived language-learning apps
- **LICENSE §5 (new)**: anyone who builds a flash-card, spaced-repetition,
  character-drill, vocabulary or other language-learning application derived
  from this project must display an attribution notice naming Mensura Media,
  reasonably discoverable by an ordinary user — not buried in a source comment.
  Explicitly covers ports, transpilation and model-assisted rewrites into other
  languages or frameworks, and covers use of the Curated Data on its own.
- §5.4 states plainly that attribution grants no rights: a derivative still needs
  consent under §4.
- §5.5 states the limits honestly — the obligation binds licensees, not
  independent creators; no claim is made over ideas, methods, the Japanese
  language, or the JLPT levels; and nothing restricts discussing or reviewing the
  project.
- §7 termination gains a 30-day cure window for a first attribution-only breach.
- New "Curated Data" and "Derivative Application" definitions in §1.
- Sections renumbered: old 5–10 are now 6–11. Third-party materials moved from
  §7 to §8; README updated accordingly.
- **New `NOTICE` file** with the verbatim attribution text, where it must appear,
  and the third-party credits this project itself owes.

## 2026-08-08T03:20:00Z — Screenshots
- **New** `tools/demo_data.py`: deterministic generator for a plausible study
  history (46 sessions, ~1,000 attempts, 31 study days, repeats, stubborn
  characters, skips), so the analytics panels can be photographed and eyeballed
  instead of rendering correct-but-empty states.
- **13 screenshots** captured from the running pywebview window at 1280×860 and
  committed under `docs/screenshots/`, with a README section covering the
  dashboard, both card types front and back, the session recap, a memory board,
  all four measurement panels and the settings dialog.
- **Two defects found while capturing, both fixed:**
  - A deep-linked game mode was never reflected in the mode picker. The
    reflection statement sat *inside* the picker's click handler, so arriving
    from a dashboard game card dealt the right board while the picker still
    highlighted Match Up.
  - Kanji meanings overflowed their board tiles — "interval, between" ran off
    the edge at the size "kya" is set in. Tile readings now wrap and step down
    through two smaller sizes.
- Also fixed: `Drill weak set` stretched full width (`.btn` carries `flex: 1`
  for the study foot's three-across row), and the weak-characters empty state
  was squeezed into an 88px grid column.

## 2026-08-08T03:45:00Z — Handoff brought current
- `docs/HANDOFF.md` §3 rewritten: every claim is now something a command
  produced this session, with a separate "measured, but not fully" heading for
  the pace timing rather than letting a computed table read as verified.
- §5 rewritten. It still said 193 tests, "Kanji beyond N5 is not seeded" and
  "13 segments"; the gap list is now a table with a roadmap id per row.
- §4 grew from 4 entries to 10: the third class collision, `.btn` carrying
  `flex: 1`, a statement nested inside the handler it was meant to precede,
  kana-sized surfaces not fitting kanji, `sqlite_sequence` not existing under
  this schema, and documented counts drifting.
- §6 gotchas corrected — an earlier note claimed `xdotool` was unavailable; it
  is installed. Added the window-frame click offset, XTEST vs `--window` for
  keystrokes, webview CSS caching, and quotes breaking `git commit -m`.
- §10 renumbered (there had never been a §10) and the backup set flagged stale:
  it predates 1,144 characters, profiles, save/load and the licence rewrite.
- Fixed two broken cross-document anchors: `TESTING.md` pointed at the old §4
  heading, and `ARCHITECTURE.md` pointed at a README section that no longer
  exists. All internal links and anchors across every document now resolve.

## 2026-08-08T04:15:00Z — Local backup retaken
- New set `20260808-0015`: bundle (11.7 MB, 29 commits), worktree tarball
  (24.5 MB, including git-ignored files), userdata tarball (48 KB — the first
  one to actually carry a study database; the previous was 121 bytes of empty
  directory).
- **Verified by restoring, not by inspecting**: cloned the bundle to a scratch
  directory and ran the suite from the restored tree — 290/290, clean tree, 630
  clips, 13 screenshots, five kanji seed modules.
- Credential scan across all three artefacts: clean.
- `RESTORE.md` corrected — its own "take a fresh backup" recipe ran
  `git bundle verify` from the backup directory, where it fails with "need a
  repository to verify a bundle" and looks like corruption. Also adds the
  commit-before-backup rule and a clone-and-test verification step.
- HANDOFF §10 rewritten with the verification table.

## 2026-08-08T04:40:00Z — Installed as a desktop application on this machine
- **New** `tools/install-desktop.sh`: builds a wheel, installs it non-editable
  into its own venv at `~/.local/opt/japanese-practice`, links a launcher into
  `~/.local/bin`, installs five icon sizes into the hicolor theme, and writes a
  validated `.desktop` entry. User-scoped; no root.
- **New** `tools/uninstall-desktop.sh`: removes all of the above and **keeps
  study history** by default. `--purge` deletes it, behind a typed confirmation.
- Verified: wheel carries all 630 audio clips, 4 templates, 6 icons, schema and
  11 content modules; the app launches from `PATH` and from the menu entry; and
  `/proc/<pid>/maps` shows **zero mappings from the project tree**, so the
  install is genuinely independent of the checkout.
- Uninstall/reinstall cycle exercised end to end; study data survived it.
- The install script routes build output to a log and surfaces it only on
  failure — modern setuptools emits a PEP 639 deprecation notice about this
  project's `license = {file = ...}` metadata, and migrating to SPDX would need
  setuptools>=77 and break `pip install -e .` here. Logged as roadmap P9.

## 2026-08-08T05:05:00Z — Recap button spacing
- `.recap-act` gains `margin-top: 22px`. The Back to dashboard action sat tight
  under the card grid, reading as another row of it rather than as the control
  that closes the summary.

## 2026-08-08T05:50:00Z — Correct-answer sound cue and an audio toggle
- New `static/js/sound.js`: one shared cue, imported by the study, games and
  dashboard modules. Plays on a correct answer in the study view and on a
  matched pair in the games — the feedback should not depend on which view you
  are in.
- Fired **before** the attempt is posted, not after: the cue is feedback on the
  click, and waiting on the round trip put it noticeably late.
- **Settings → Audio → Sound** master switch (`jp.sound`). Off silences the cue
  and pronunciation everywhere. It composes with the study view's `M` mute and
  volume: a cue is heard only when the master is on and nothing is muted.
  Turning it on plays the cue once, so the switch proves itself.
- **Cue trimmed and converted to WAV.** The supplied MP3 had 64 ms of leading
  silence — pure click-to-sound latency — and ran 1.056 s, still ringing when
  the next card appeared at the fastest pace. Now 0.320 s with a 2 ms onset.
  WAV rather than MP3 because MP3's encoder delay left 14 ms of lag even after
  trimming. Source kept beside it, with the ffmpeg recipe in a README.
- Tests: the cue must be served, must be audible (decoded and measured, not
  judged by file size), must start within 20 ms and must be shorter than the
  fastest verdict hold.
- `install-desktop.sh` now clears `build/` first. setuptools reuses it, so a
  file deleted from the tree survived into the wheel — which shipped the removed
  MP3 once.

## 2026-08-08T06:20:00Z — Sound cue rebuilt on Web Audio, and made audible
Two separate faults, both real, found by measuring rather than guessing.

**It was inaudible.** The cue kept the source's −8.2 dBFS peak and was then
multiplied by an 0.55 app gain; at 51% system volume that arrived at the
speakers around **−19 dBFS**. Now peak-normalised to −0.4 dBFS with the app gain
raised to 0.9. Measured at the speaker monitor: **−1.4 dBFS**, up ~17 dB.

**It was on the wrong API.** `new Audio().play()` is for media playback. For a
short cue it has three defects: the autoplay policy rejects the returned promise
until the page has been interacted with, and swallowing that rejection makes a
blocked cue look identical to a working one; `currentTime = 0` restarts are not
sample accurate and cancel the cue already sounding; and every play crosses the
media pipeline, adding variable latency.

Rebuilt on the **Web Audio API** — the file is decoded once into an AudioBuffer
and each cue is a fresh BufferSourceNode through a GainNode. Sub-millisecond,
overlapping safely, with an explicit level. The AudioContext is unlocked on the
first pointer/key/touch event and re-resumed on each cue, since the engine
suspends it when the window loses focus.

- Failures now surface: `soundStatus` records support, context state, decode
  state, play count and the last error, exposed as `window.jpSound`.
- **Settings → Audio → Test sound** plays the cue and reports what happened —
  off, unsupported, blocked, still loading, or played — so an unheard cue can
  say why instead of leaving the user to guess.
- Test asserts the asset peaks above 0.80 and does not clip.

## 2026-08-08T07:10:00Z — Seven selectable cues, and a toggle that actually works
- **Cue set**: `ding` (the supplied sound, trimmed and normalised) plus six
  synthesised by the new `tools/make_cues.py` — chime, bell, marimba, arpeggio,
  sparkle, blip. Each is a different *character* of positive rather than a
  different pitch of one sound, because this fires several times a minute.
  All meet one contract: mono 44.1 kHz WAV, onset < 20 ms, ≤ 380 ms, peak
  ≈ −0.4 dBFS. Asserted per cue by the suite, which decodes and measures them.
- **Settings → Audio** gains a picker. Choosing a cue plays it, so nobody
  chooses blind.
- **Fixed: the Sound toggle did nothing.** `localStorage` in this webview
  accepts writes and drops them, so `setSoundEnabled(false)` wrote nothing and
  the next read returned the old value — the switch repainted itself back on and
  audio kept playing. This is the third time storage has bitten this project.
  New `static/js/prefs.js` keeps preferences in memory as the authority for the
  session and mirrors to `localStorage` best-effort, so a control always
  reflects what you just did. `study.js` now uses it too, which means pace,
  volume and voice were silently failing to persist as well.
  Verified by recording the speakers across six steps: on → sound, off →
  silence for both the picker and Test sound, back on → sound. Six for six.
- **Fixed: a preview click was silent if its cue had not finished decoding.**
  `playCorrect` returned early rather than waiting. It now decodes and plays,
  bounded at 400 ms so a slow decode is dropped rather than arriving over the
  next card. This is why five of seven cues made no sound on first use.
- **Fixed: cue tiles were uneven.** Grid items stretch to their row, so a hint
  wrapping to two lines made that row taller, and the last row — one tile —
  different again. Fixed height, single-line hints, full text on the title.
- Diagnostics report storage availability alongside audio state.

## 2026-08-08T07:55:00Z — Preferences moved to the server, so selections apply
- **Fixed: choosing a different cue changed nothing in the study view.** The
  root cause was the page boundary. `prefs.js` held preferences in memory, but
  `/study` is a *full page navigation* — a fresh JS context with an empty cache
  — and the `localStorage` mirror is silently dropped by this webview. So the
  study view always fell back to the default cue. Pace, voice and volume were
  crossing the same boundary and failing the same way.
- **New `preferences` table and `GET`/`PUT`/`POST /api/preferences`.** Settings
  now live in the profile's own database file, which makes them **per-profile
  for free** and persistent across restarts. The key set is closed and values
  are length-capped: an open key-value store reachable from the page is a way
  to fill someone's database.
- `prefs.js` rewritten: synchronous reads from a cache primed at start-up,
  writes applied immediately and flushed on a 250 ms debounce, with
  `navigator.sendBeacon` on `pagehide` so a setting changed just before closing
  is not lost. `POST` is accepted because a beacon cannot `PUT`.
- The study view now adopts pace, voice, volume and cue **before dealing the
  first card**, rather than reading them at module load when nothing has arrived.
- Verified end to end by selecting *marimba*, navigating into a session, and
  identifying the sound recorded from the speakers: 0.23 s at 1070 Hz, matching
  marimba (0.26 s / 1116 Hz) and not ding (0.32 s / 625 Hz).
- Six new tests: round trip, merge, unknown-key rejection, oversize rejection,
  `POST` for beacons, and per-profile isolation.

## 2026-08-08T08:20:00Z — Interface sound documented
- **New** `docs/INTERFACE-SOUND.md`: the cue set with measured characteristics,
  the asset contract and why each constraint exists, the Web Audio graph and
  what `HTMLAudioElement` got wrong, autoplay unlocking, the level arithmetic
  that made the first version inaudible, the three-attempt path to server-side
  preferences, diagnostics, how to add a cue, and the recording method used to
  verify all of it.
- `docs/AUDIO.md` scoped explicitly to **pronunciation**, with a pointer across;
  the two subsystems share only the master switch.
- `README.md`, `docs/FEATURES.md` and `docs/HANDOFF.md` cross-linked.
- **Three environment gotchas recorded in HANDOFF §6**, each of which cost real
  time on this feature: `localStorage` here accepts writes and drops them;
  `/study` and `/games` are full page navigations, so nothing in memory crosses
  a view; and audio faults are invisible from the source, so verification means
  recording the sink monitor and measuring onset, duration, peak and centroid.
- Every figure in the new document was checked against the code and the assets
  rather than written from memory — 7 cues declared and 7 on disk, all mono
  44.1 kHz, ≤0.38 s, peak 0.95.

## 2026-08-08T09:10:00Z — Word decks, a More… card, and the exercise catalogue
- **Six word decks**, 106 entries: days 7, months 12, numbers 36, time 16
  (extracted from the reference worksheets) plus demonstratives 20 and
  particles 15 (authored — both are closed, rigidly structured sets, unlike
  open vocabulary which would have to be invented).
- **`characters` is now unique on `(glyph, script)`.** Seeding words against the
  old glyph-unique table silently overwrote 41 characters — は the particle
  replaced は the hiragana, 一 the number replaced 一 the kanji, and the Top 200
  deck quietly shrank to 175. Migration rebuilds the table preserving ids, so
  attempt history still points at the same characters.
- **More… deck closes every shelf**, opening `/decks`: all 23 working decks
  grouped by shelf, plus eight designed-but-unbuilt exercises each carrying a
  status and **what is blocking it** — phrases, expressions, verbs, word
  combinations, counters, adjectives, typed recall, listening.
- **Wider cards where the content needs it**: word prompts and their options,
  and the deck faces on the Words shelf.
- Fixed a `NameError` that stopped the app booting: `db.py` used `log` without a
  logger. It failed loudly at startup, which is the right way for it to fail.
- Tests 312 → 322.

## 2026-08-09T00:20:00Z — Catalogue typography, and three more planned exercises
- `/decks` headings resized and spaced. `.lbl` is 9.5px, which suits a label
  beside a dense shelf but reads as fine print on a page whose whole job is
  naming groups. The page title is now its own element at 26px with a subtitle,
  shelf titles are 17px, and the gap above a title no longer differs visibly
  from the gap below it.
- **Alternate phrases** added to In development — thanks as ありがとう / どうも /
  感謝します, sorry as すみません / ごめん / 失礼します, and the same for interest,
  agreement and liking something. Marked experimental with a real blocker: it
  needs a card type that grades a **set** of correct answers, and the engine has
  exactly one correct option per card.
- **Politeness registers** (食べる / 食べます / いただきます) and **Reactions**
  (相槌 — へえ, なるほど, そうですね) added alongside it; the first shares the
  one-to-many blocker, the second needs sourcing.
- In development is now 11 entries: 5 experimental, 6 planned.

## 2026-08-09T01:10:00Z — Phrase sets built on shared patterns
- **Five phrase decks, 48 cards**, on a new Phrase Sets shelf: Saying you like
  it (10), At the convenience store (10), Let's — ましょう (10), Please —
  てください (8), Getting by (10).
- Each set is chosen because **one structure generates all of it**. 〜ましょう
  and 〜てください are mechanical rules, so learning the shape delivers the whole
  set rather than ten unrelated sentences. The convenience-store set is ordered
  as the transaction actually happens.
- Politeness is kept uniform inside a set; mixing 行こう with 食べましょう would
  teach register as noise rather than as a choice.
- **Corrected one supplied example.** "I'm a fan — tsugi no wa" was wrong: 次のは
  means "the next one". Shipped as ファンです.
- Phrase deck titles drop the script prefix — "At the convenience store" rather
  than "Phrases · At the convenience store", which was redundant under a shelf
  called Phrase Sets and wrapped the card onto two lines.
- Card and option widths step again for phrases: ゆっくり話してください needs more
  room than a word, which needed more than a character.
- Catalogue's "Phrases" entry replaced with "More phrase sets", stating what
  ships now and what the bar is for adding another.
- Tests 322 → 330.

## 2026-08-09T02:10:00Z — Five context sets, and a note field on every card
- **New `note` column** on `characters` (additive migration), surfaced through
  the card payload and rendered beneath the reading on the card back. Some cards
  are unusable without one: 強がり is not "a strong person" but someone putting
  on a brave face, and a learner who sees only the gloss learns the opposite.
- **Five sets, 45 cards, every one with a note**: Praising someone (10),
  Encouraging someone (10), Describing things (8), Rough language (10),
  Personality — がり (7).
- **〜がり is rule-governed** like 〜ましょう — adjective stem + がり names the kind
  of person who feels that way: 寒い → 寒がり, 面倒くさい → 面倒くさがり.
- **Rough language is included for recognition, not production.** These appear
  constantly in manga and television whether or not a course admits it; each
  note states how hard the word lands, and the deck is labelled
  `ROUGH — RECOGNISE ONLY`.
- **Rebalanced the likes set**: かわいい and おいしい moved to Describing things,
  where their notes can cover the range each spans. They describe the thing;
  the likes set is statements about you. This also resolved a `(glyph, script)`
  collision that would have failed the upsert.
- Fixed a placeholder that slipped into the describing set before it shipped.
- Tests 330 → 341, including one asserting every card in a context set has a
  note of real length.

## 2026-08-10T00:30:00Z — Card size follows content, not script
- **Fixed: phrase cards were enormously oversized.** `.deck3d` is a 5:7
  playing-card portrait, which is right for a single glyph that fills the face
  and wrong for text. Combined with a script-driven width, every phrase card got
  520 × 728 — so 頭悪い, three characters, sat in the middle of a mostly empty
  face.
- The card now picks one of four sizes from its **content**: the prompt's length
  and whether it carries a note. Each step up widens and shortens, because extra
  text runs across the face rather than down it.
- 336 × 470 (unchanged, 1,545 single-glyph cards) · 350 × 378 (94) ·
  410 × 385 (15) · 460 × 405 (4). Type scales with the face rather than the
  script, so a short phrase is not set at the size a long one needs.
- Kana and kanji cards are untouched — the classic playing-card look is intact.

## 2026-08-10T01:05:00Z — Card and options top-aligned
- The stage centred its two columns, so whichever was taller pushed the other's
  top out of line — and which is taller varies, since the card is sized by its
  content and the options by the length of the answers. A kana card sat 23 px
  above the options; a phrase card sat 27 px below them.
- `.deck3d` also rotated about its centre, which moves the top edge down by an
  amount proportional to card height, so the drift differed per size. It now
  pivots on `transform-origin: 50% 0%` — the top edge, which cannot move.
- Measured at **0 px** on both a kana card and a phrase card.

## 2026-08-10T01:40:00Z — Cycle documented
- `docs/RELEASE-NOTES.md` gains the 2026-08-08 → 08-10 cycle: eighteen commits
  across four unrelated pieces of work — ownership (licence, install, backup),
  sound, content beyond single characters, and the defects that extension
  exposed. Headline numbers before and after, the reasoning behind each
  decision, the corrections made along the way, and the known-unfixed list.
- `docs/HANDOFF.md` §1 and §5 brought current; §4 grew from 10 entries to 15,
  adding the patterns that recurred this cycle: a stale `build/` shipping
  deleted files, `localStorage` accepting writes and dropping them, a view
  boundary being a process boundary, sizing by category rather than by content
  (which caused the same class of bug three times), and centring two columns
  that change height independently.
- `docs/ROADMAP.md`: N4 closed, X2 and X6 already closed; new N8, N9 and X7 —
  the last being the structural blocker shared by alternate phrases, politeness
  registers and typed recall, all of which need a card type that grades a *set*
  of correct answers.
- Every figure quoted was checked against the tree before committing: 1,658
  cards, 33 decks, 106 words, 93 phrases, 45 notes, 8,635 Python lines, 2,378
  frontend lines, 36 modules, 27 endpoints, 7 cues.

## 2026-08-10T07:10:00Z — Local backup retaken
- New set `20260810-0704`: bundle 12.0 MB (44 commits), worktree 26.2 MB
  (including git-ignored files), userdata 0.1 MB (`practice.db` 291 KB).
- **Verified by restoring, not inspecting**: cloned to a scratch directory and
  ran the suite from the restored tree — 341/341, clean tree, 638 audio files,
  13 screenshots, 15 content modules.
- `build/` added to the worktree exclusions. setuptools leaves it behind, it
  contains nothing that is not rebuilt, and it is the same directory that once
  shipped a deleted file into a wheel.
- Credential scan across all three artefacts: clean.
- `RESTORE.md` and HANDOFF §10 updated; older sets now list what each predates,
  so nobody restores `20260807-0540` expecting study history and finds an empty
  directory.

## 2026-08-10T08:00:00Z — Recap tiles sized to the session, and a sizing standard
- **Fixed: recap tiles were squares built for a single character.** 高い wrapped
  to two lines and "expensive / tall" to two more, in the one place a learner
  reads every card at once. Tiles are now sized from the widest item in *that*
  session — a grid of mixed widths reads worse than one sized for its longest
  member — across four steps: 84px square · 122 · 158 · 206.
- **The answer counts toward the width**, divided by 2.4 to bring Latin
  characters onto roughly the same scale as Japanese. Without that term the
  tiles fit 高い but not its meaning, which is what the defect looked like.
- **New `docs/CARD-DIMENSIONS.md`** — the sizing standard for every surface that
  shows Japanese: the rule, the thresholds for the study card, its options, the
  recap tiles, deck faces and game tiles, the alignment rule, and a checklist to
  run before shipping a new content set. Written because the same mistake —
  sizing by category rather than by content — has now been made four times, and
  each time it looked fine on the content that existed when it was written.
- The document records **measured headroom**: the longest prompt today is
  ゆっくり話してください at 11 glyphs, and one more bucket would be needed at
  roughly 15.
- Every threshold in the document was checked against the code before commit.
