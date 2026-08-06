# MEMORY.md — Project Memory Index
# Keep under 200 lines. One entry per line. Link to detail files.

## Session Logs
<!-- Add newest first -->
- [2026-08-06 Setup](sessions/2026-08-06_0503_setup-and-mockups.md) — context recovery, standards adoption, mockup round

## Changes
<!-- Add newest first -->
- See [changelog.md](../../changelog.md) — append-only local change log

## Decisions
- [Decision Log](decisions.md) — Architectural and design decisions

## Project Context
<!-- User info, project goals, references -->
- [PROJECT-CONTEXT.md](../../docs/PROJECT-CONTEXT.md) — original brief, requirements decomposition, confirmed decisions
- [REPO-ACCESS.md](../../docs/REPO-ACCESS.md) — private standards repo access (gh absent; use git extraheader or REST API)
- Goal: local desktop flash-card app for Hiragana / Katakana / Kanji
- Stack: Quart (ASGI) + pywebview desktop shell, Python 3.10, Debian bookworm/sid
- Standards source: `universal-instruction-set` @ 6099a45, vendored at `universal-instruction-set-main/`

## Feedback & Preferences
<!-- User corrections, confirmed approaches -->
- Desktop window delivery: pywebview + Quart (user-selected)
- Audio: hybrid — bundled clips with TTS fallback (user-selected)
- Standards access: use existing git CLI credentials; repo is owned by the user with full rights
- Deliverable order: mockups of multiple approaches BEFORE any implementation
