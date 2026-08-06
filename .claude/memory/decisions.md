# Decisions

Architectural and design decisions with rationale. Newest first.

## 2026-08-06: Universal standards adopted from `universal-instruction-set` @ 6099a45
- **Reason:** Mandated by the Core Mandate — every project under `/home/user/projects/` must copy and adapt all six universal standards.
- **Source:** Local extraction of `universal-instruction-set-main.zip`, verified byte-identical to private repo HEAD `6099a45`.
- **Impact:** `.claude/` contains agents, skills, roles, hooks, commands, rules, memory structure. Standards are immutable — project-specific additions go alongside, never instead of.

## 2026-08-06: Desktop shell = pywebview + Quart
- **Reason:** User decision. Satisfies "own application window" without shipping a full browser engine (unlike Electron), and keeps the UI a plain web app.
- **Alternatives considered:** Electron (heavy, Node dependency), GTK WebKit directly (more Debian-specific, less portable), browser-only (fails the "own window" requirement).
- **Impact:** Quart serves ASGI on localhost; pywebview hosts it in the system WebKit runtime. The identical UI opens unchanged in any browser, satisfying the cross-platform/browser-compatibility requirement.

## 2026-08-06: Audio = bundled files with TTS fallback
- **Reason:** User decision. Pre-recorded clips give correct native pronunciation for the fixed kana set; TTS covers the open-ended Kanji vocabulary where bundling every reading is impractical.
- **Impact:** Requires an audio asset pipeline plus a TTS abstraction layer. Generated audio is cached under `static/audio/generated/` and excluded from git.

## 2026-08-06: Standards vendored into the project, not referenced
- **Reason:** The instruction set requires copy-not-reference so projects stay portable and free of cross-project dependencies.
- **Impact:** `universal-instruction-set-main/` is git-ignored and `.claudeignore`d — it is a read-on-demand reference, not a runtime dependency. The adopted copies under `.claude/` are the live configuration.

## 2026-08-06: UI design language from `universal-themes`
- **Reason:** Standard requires consulting theme references for any project with a visual interface.
- **Observed language:** Dark charcoal/near-black grounds, layered gray panels, a single high-chroma accent per theme (yellow, orange, or green), technical HUD framing, data-dense dashboard composition.
- **Impact:** Mockups target a dark, accent-driven aesthetic rather than a light consumer-app look.
