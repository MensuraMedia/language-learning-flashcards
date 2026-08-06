# Japanese Practice — Project Context

**Status:** Pre-implementation. No application code written yet.
**Last updated:** 2026-08-06
**Working directory:** `/home/user/projects/japanese_practice`

This document reconstructs the design session of 2026-08-06 (04:30–05:03), which
ended when the terminal session closed before implementation began. It exists so
that context — especially the decisions already confirmed by the user — is not
re-litigated in a future session.

---

## 1. Session provenance

Transcripts are stored as JSONL under
`/home/user/.claude/projects/-home-user-projects-japanese-practice/`.

| Session ID | Time (2026-08-06) | Contents |
|---|---|---|
| `7e344b92-d7ae-429c-a4a7-3d66da2e4716` | 04:30–05:01 | Original brief, environment discovery, GitHub auth, three design decisions |
| `30934411-b032-409d-b40c-65f3ca3a485d` | 05:01–05:03 | Recovery session; produced this document |

To resume the original session with its full context:

```bash
claude --resume 7e344b92-d7ae-429c-a4a7-3d66da2e4716
```

Or type `/resume` on its own line inside Claude Code and pick it from the list.
Note that a leading word before the slash (e.g. `claude /resume`) causes the CLI
to send the line as a chat message instead of running the command.

---

## 2. Original brief (verbatim)

> act as a linux debian expert with advanced knowledge of desktop applications.
> today we want to create some learning resources for learning Japanese Hiragana,
> Katakana, and Kanji. we need to creae a local desktop application with it's own
> application window built on python flask quart. in this case we want to ensure
> the application process follows all the standards as described in the universal
> instruction set found here: https://github.com/MensuraMedia/universal-instruction-set
> we want to create a basic flash-card application that shows characters. the cards
> should then animate or 'flip' upon being clicked. on the character side of the
> card (is the default display). it is only a simple character display. when clicked
> the card should flip and on the reverse side it should have the sound written and
> a speaker icon where it will play the sound of the character. the app should keep
> a score for each time the user wants to use the application and there should be a
> general landing page which is where the user can see statistical informattion on
> performance of each time they did an exercise. the dashboard also featuers
> different types of segments for flash card exercises. there should be listed
> different challenges, different scoring, different levels difficulty. the
> flash-card application should be created with modularity and universality in mind;
> cross platformed or compatible in different browsers if necessary. the application
> should be created according to best practices depending on the best technology
> stack to employ that works extremely efficiently with python flask quart. create a
> mockup of a varity of different approaches for the dashboard, the appearance and
> style of the flash card system, choices, statistical tracking, etc.

---

## 3. Requirements decomposition

### 3.1 Flash-card core
- Character sets: **Hiragana, Katakana, Kanji**.
- Default card face: the character alone, nothing else.
- Click triggers a **flip animation**.
- Reverse face carries: the romaji/sound written out, plus a **speaker icon** that
  plays the character's pronunciation.

### 3.2 Dashboard / landing page
- Serves as the general landing page.
- Shows **per-session statistical performance** across every past exercise.
- Lists **segments** of flash-card exercises, broken out by:
  - different challenges
  - different scoring schemes
  - different difficulty levels

### 3.3 Scoring
- A score is recorded **each time** the user runs the application.
- Historical scores feed the dashboard statistics.

### 3.4 Cross-cutting
- Modular and universal in construction.
- Cross-platform; browser-compatible where relevant.
- Must run as a **local desktop application with its own window**, not merely a
  browser tab.

### 3.5 Requested deliverable at this stage
Mockups of **several different approaches** covering the dashboard, flash-card
appearance and style, choice/interaction design, and statistical tracking. The
brief asks for variety to choose from — not a single committed design.

---

## 4. Confirmed decisions

These were answered directly by the user in the prior session. Treat them as
settled; do not re-ask.

| Question | Decision |
|---|---|
| The `universal-instruction-set` repo 404s. How to get those standards? | "you have rights and access already formerly established through git cli" — use the existing local GitHub credentials |
| How should the desktop window be delivered on Debian? | **pywebview + Quart** |
| Where should the character audio come from? | **Hybrid: bundled audio files with TTS fallback** |

Implication of the pywebview + Quart choice: Quart serves the app over localhost
ASGI, and pywebview hosts it in a native window using the system WebKit runtime.
This satisfies both "own application window" and "browser-compatible" — the same
served UI opens in a normal browser unchanged.

---

## 5. Verified environment

Confirmed by direct inspection, not assumed:

- **OS:** Debian `bookworm/sid`
- **Python:** 3.10.12
- **Flask:** 3.1.3 (installed; Quart install status not yet verified)
- **git:** 2.34.1 at `/usr/bin/git`
- **`gh` CLI:** **not installed** — `gh: command not found`
- **SSH keys:** none present in `~/.ssh`

### GitHub access
Full owner-level access to the standards repo is established and verified —
`admin`/`push` permissions, scopes `repo, write:org, write:packages`. The `gh`
binary is absent, so *plain* `git` fails, but both `git` with an explicit auth
header and the REST API work.

**See [REPO-ACCESS.md](REPO-ACCESS.md) for verified working commands.**

---

## 6. External dependency: `universal-instruction-set`

`https://github.com/MensuraMedia/universal-instruction-set`

Confirmed via authenticated API call:

```json
{
  "full_name": "MensuraMedia/universal-instruction-set",
  "private": true,
  "default_branch": "main",
  "description": "A standard Ai build instruction set for all new projects"
}
```

It 404s anonymously **because it is private**, not because it is missing. Web
search found nothing for the same reason.

**Resolved 2026-08-06.** The standards were retrieved and adopted. The user
supplied a local zip (`universal-instruction-set-main.zip`) which was verified
byte-identical to repo HEAD `6099a45` and extracted to
`universal-instruction-set-main/` (git-ignored, read on demand).

The instruction set's Core Mandate requires every project under
`/home/user/projects/` to **copy and adapt** all six universal standards into its
own `.claude/` directory — never reference them at runtime. Standards are
**immutable once adopted**: project-specific additions go alongside them, never
instead of them. Adoption is complete — see §10.

### Japanese content reference

A second repo, `MensuraMedia/language-learning` (public), supplies the
authoritative Japanese content model — real character counts, JLPT/Joyo level
structure, and terminology. Distilled to
[`mockups/_reference/JAPANESE-CONTENT-MODEL.md`](../mockups/_reference/JAPANESE-CONTENT-MODEL.md),
which is binding on all content decisions.

---

## 7. Open questions

**Resolved:**
- ~~Kanji scope and grading source~~ — settled by the content model: JLPT N5→N1
  (107/174/394/248/382) and Joyo Grade 1–6 + Secondary (1,521), plus Top
  200/500/Complete volume tiers.
- ~~Mockups: static comps or interactive?~~ — interactive, self-contained HTML,
  so the flip animation can actually be judged.
- ~~Frontend approach~~ — server-rendered templates plus vanilla JS/CSS, no
  bundler. Keeps the app portable and browser-compatible per the brief.

**Still open:**
- Persistence layer — SQLite via `aiosqlite` is the working assumption recorded
  in CLAUDE.md, but not user-confirmed.
- Which TTS engine backs the audio fallback, and licensing of any bundled clips.
- Whether to seed content from the `language-learning` PDFs (extraction work) or
  from a public kana/kanji dataset.

---

## 8. Next actions

1. ~~Read the standards~~ — done.
2. ~~Adopt the universal standards into `.claude/`~~ — done, see §10.
3. ~~Produce mockup variations~~ — five interactive directions generated; see
   [`mockups/COMPARISON.md`](../mockups/COMPARISON.md).
4. **User selects a direction** from the mockups.
5. Scaffold the Quart + pywebview application against the chosen direction.
6. Optionally repair GitHub tooling — see [REPO-ACCESS.md](REPO-ACCESS.md) §6.

---

## 9. Git configuration status

Per the `universal-git-settings` checklist:

| Item | Status |
|---|---|
| `.git/` exists | Yes — initialized 2026-08-06 |
| `.gitignore` | Created, covers Python/venv/secrets/vendored standards |
| `user.name` | **NOT SET** — commits will fail until configured |
| `user.email` | **NOT SET** — commits will fail until configured |
| `credential.helper` | **BROKEN** — points at missing `/usr/bin/gh` |
| Remote | None configured |

**Manual action required** before the first commit:

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

---

## 10. Universal standards adoption (2026-08-06)

Applied from `universal-instruction-set` @ `6099a45`:

| Standard | Status |
|---|---|
| `universal-memory` | Rules, memory structure, changelog, `.claudeignore`, hooks, commands |
| `universal-agents` | 9 agents, 8 skills, 2 roles, board, agent-teams, routing rules |
| `universal-permissions` | `settings.local.json` — **`defaultMode: "dontAsk"`** |
| `universal-git-settings` | Checklist run — see §9 |
| `universal-themes` | Consulted for UI direction — dark + single accent |
| `universal-instruction-set` | Governs the above |

Deviations and notes:

- **`defaultMode` is now `"dontAsk"`**, as the standard mandates. This is a
  meaningful broadening of what runs without prompting. Revert by editing
  `.claude/settings.local.json` if that is not wanted.
- `.claude/rules/` contains **both** `memory-rules.md` (the name the compliance
  checklist requires) and `universal-memory-rules.md` (the source filename the
  setup script copies). They are identical. Both were kept because the standard
  forbids removing universal rules — worth a decision on which to drop.
- Example rules `backend-example.md`, `infra-example.md`, `react-example.md` and
  agents `chrome-ext.md`, `stream-engineer.md` were deployed but do not apply to
  this stack. The standard permits removing non-applicable example rules.
- The Python block in `.claude/hooks/post-edit-lint.sh` was uncommented, so
  `black` and `ruff` run after Python edits. Neither is installed yet — the hook
  fails silently until they are.
