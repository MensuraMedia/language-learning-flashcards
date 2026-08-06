# Project: Japanese Practice — CLAUDE.md (v2026.04 — Claude Code Native)

## Overview
Local desktop flash-card application for learning Japanese Hiragana, Katakana and Kanji. Runs in its own native window via pywebview over a Quart ASGI server, and remains fully usable in a plain browser.

## Architecture
- Language/Framework: Python 3.10 + Quart (ASGI) + pywebview desktop shell
- Build system: pip / pyproject.toml, venv-based
- Key dependencies: quart, pywebview, aiosqlite (persistence), a TTS engine (audio fallback)
- Frontend: server-rendered templates + vanilla JS/CSS (no build step — keeps browser compatibility and portability)

## Build & Runtime Standards (Enforced)
```
# Build (env setup)
python3 -m venv .venv && .venv/bin/pip install -e .

# Test
.venv/bin/python -m pytest

# Lint
.venv/bin/python -m ruff check . && .venv/bin/python -m black --check .

# Run (desktop window)
.venv/bin/python -m japanese_practice

# Run (browser / headless)
.venv/bin/python -m japanese_practice --no-window
```
- Use /plan-first for complex features or multi-file changes
- Use /build-test to run the full pipeline
- Every card interaction must stay under 100ms perceived latency; flip animation targets 60fps

## Project Conventions
- Python: black formatting, ruff linting, type hints on all public functions
- Async throughout — Quart handlers are `async def`; never block the event loop with audio or DB work
- Character data lives in versioned JSON/SQLite seed files, never hardcoded in templates
- Frontend uses no framework and no bundler; CSS custom properties carry the theme
- Audio: bundled clips first, TTS fallback second, cached under `static/audio/generated/`
- UI follows the dark + single-accent language from `universal-themes` (see decisions.md)

## Sector-Specific Rules
<!-- Path-scoped rules load automatically when editing matching files -->
@.claude/rules/ for all active rules

## Memory & Workflow
- Use official Auto Memory (/memory) for Claude's own learnings across sessions
- Human-readable history supplements Auto Memory:
  - Session logs: `.claude/memory/sessions/`
  - Change manifests: `.claude/memory/changes/`
  - Decision log: `.claude/memory/decisions.md`
  - Pending items: `.claude/memory/pending.md`
  - Memory index: `.claude/memory/MEMORY.md`
- End every significant session with /session-end or the session-end checklist
- Update changelog.md as changes are made, not after

## Hooks (Automated)
Lifecycle hooks are configured in `.claude/settings.json`:
- **SessionStart**: Injects pending items, last session log, and recent changelog
- **PreToolUse**: Security gate blocks secret file access and destructive commands
- **PostToolUse**: Auto-lint/format after file edits — Python (black + ruff) is active

## Custom Commands
- `/plan-first` — Plan complex tasks before executing
- `/build-test` — Run full build + test pipeline from CLAUDE.md
- `/session-end` — End-of-session wrap-up and logging

## Project Reference
- @docs/PROJECT-CONTEXT.md — brief, requirements decomposition, confirmed decisions
- @docs/REPO-ACCESS.md — how to reach the private standards repo from this machine
- `universal-instruction-set-main/` — vendored standards (git-ignored, read on demand)

## References
- @docs/ for project documentation
- @.claude/rules/ for path-scoped rules
- @.claude/memory/decisions.md for architectural decision history
