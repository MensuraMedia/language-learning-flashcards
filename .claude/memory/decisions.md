# Decisions

Architectural and design decisions with rationale. Newest first.

## 2026-08-10: Headings are named by role, not styled by specificity
- **Reason:** `.lbl` served as both a gauge label and a section title. `#dashboard .lbl { font-size: 12px }`, added to lift chrome text, out-specified the heading rule by an ID and silently captured every shelf heading. The heading rule was correct and lost anyway.
- **Decision:** Headings use `.sec-title` / `.sec-desc`, which no gauge rule can match. Every size derives from a token on `:root`; per-view overrides may change *rhythm* (margins) but never *type*. Three ranks only — section 19/13.5, panel 15/12.5, chrome 9.5–12.
- **Alternatives considered:** Out-specifying with `#dashboard .sec .lbl` (wins the fight, loses the war — that is how the drift started); `!important` (same, worse).
- **Impact:** Documented in [docs/UI-FORMAT.md](../../docs/UI-FORMAT.md). The test for a new rule: *could this be captured by a more specific rule written for a different purpose?* If yes, rename the class rather than adding specificity.

## 2026-08-10: The accent belongs to the exercise, not the card
- **Reason:** `theme-kanji` was toggled per card in `render()`. A mixed deck flickered between palettes, and a kanji *drill* went un-themed because the drill path's difficulty key is `drill:custom` and carries no script.
- **Decision:** `session.deck_script()` is the single answer to "is this a kanji exercise?" — script from the difficulty key where there is one, from the cards otherwise. The API returns it and the view applies it once per session.
- **Impact:** Kanji decks, kanji drills, kanji games and both kanji shelves now agree. Asserted by tests.

## 2026-08-10: Card height is the sum of the registers the back will render
- **Reason:** Adding the English translation to every card back broke a fixed 372/430px height, which had silently clipped the phrase sets where the meaning is the longest text on the card.
- **Decision:** Height sums named per-register constants; a register that will not render contributes nothing. Calibrated so both previously known-good heights come out exactly.
- **Impact:** `CARD_MEANING_CH` must stay equal to `.back-meaning { max-width: 30ch }` — the same measurement in two languages.

## 2026-08-10: Interface audio is matched by loudness (RMS), not by peak
- **Reason:** One volume control governs both the correct-answer cue and the pronunciation clips, so they have to be *perceptually* level. Peak-normalising both to the same figure left the cue +10.1 dB louder to the ear, because speech has a far higher crest factor than a short tone.
- **Decision:** Cue assets are normalised to −14 dBFS **RMS over the audible part** (samples above 5% of peak, excluding decay tails), with peak demoted to a −1 dBFS clipping ceiling and a 0.35 sanity floor. `CUE_GAIN = 0.507` then aligns the cue to the narration median.
- **Alternatives considered:** Full EBU R128 / LUFS loudness (correct, but needs a gating implementation and a dependency for seven short files where windowed RMS is within a fraction of a dB); attenuating the cue by ear (unverifiable, and drifts every time an asset changes).
- **Impact:** Cue-to-speech gap −0.2 dB; spread across the seven cues 0.0 dB. Asserted by tests. **Peak must not be reinstated as a target** — the test carries a comment saying so, because that change is what caused the fault.

## 2026-08-10: A rejected clip is treated as absent, and validation measures the format actually shipped
- **Reason:** `validate_clip` gated duration and silence on WAV only while the entire shipped library is MP3, so the silence gate had never run on a single shipped clip. It shipped an inaudible あ.mp3 marked as validated.
- **Decision:** MP3s are decoded and measured like WAVs. Where ffmpeg is unavailable, validation degrades to the format sniff and records `peak=None`, so unmeasured is distinguishable from measured rather than silently passing. `_load_bundled` consults the manifest's rejected list, **fail-open** — an unreadable manifest serves clips unfiltered rather than muting the library.
- **Impact:** A bad clip now falls through to synthesis instead of stopping the resolution chain with silence. Present-but-silent is strictly worse than missing, because only the missing case recovers.

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
