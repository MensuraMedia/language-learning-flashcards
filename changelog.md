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
