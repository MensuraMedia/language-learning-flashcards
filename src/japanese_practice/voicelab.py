"""Voice lab — audition, build and verify pronunciation clip sets.

A small toolset, not a one-off script: the same three commands that pick today's
two voices will pick the next two, and rebuild the library when a voice is
replaced or the character set grows.

    python -m japanese_practice.voicelab audition            # sample candidates
    python -m japanese_practice.voicelab build --voice female --male-id ...
    python -m japanese_practice.voicelab verify              # validate + manifest
    python -m japanese_practice.voicelab cost                # estimate before spending

Design constraints that shaped this:

* **Spend is irreversible.** Every synthesis costs characters against a quota,
  so `build` is resumable, skips anything already present and validated, and
  `cost` exists to be run first.
* **Bad audio must never enter the library.** Every clip is validated by
  :mod:`japanese_practice.audio_library` *before* it is written to its final
  path, so a truncated or silent render never reaches a learner.
* **The API key never passes through a shell.** It is read inside the process
  from the environment or the private key file.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from . import audio_library as lib
from . import tts_elevenlabs as el
from .content.hiragana import HIRAGANA
from .content.kanji_n5 import KANJI_N5
from .content.katakana import KATAKANA
from .models import CharacterSeed

#: Written to on every request; the API is rate-limited and bursts get 429s.
REQUEST_SPACING_S = 0.35

#: Where audition samples land. Deliberately outside the package — these are
#: scratch files for a human to listen to, not shipped assets.
AUDITION_DIR = Path.home() / ".cache" / "japanese-practice" / "voice-audition"

#: A phrase that exercises the sounds a Japanese narrator most often gets wrong:
#: long vowels, the moraic n, palatalised yoon, and the tsu geminate.
AUDITION_PHRASE = "あいうえお。かきくけこ。しんぶん、きょう、がっこう。"

#: Candidate premade voices. Voice ids are stable and public; names are theirs.
#: This is a starting slate, not a recommendation — `audition` exists precisely
#: because naturalness in Japanese cannot be judged from metadata.
CANDIDATES: tuple[tuple[str, str, str], ...] = (
    ("female", "Sarah", "EXAVITQu4vr4xnSDxMaL"),
    ("female", "Alice", "Xb7hH8MSUJpSbSDYk0k2"),
    ("female", "Matilda", "XrExE9yKIg1WjnnlVkGX"),
    ("female", "Lily", "pFZP5JQG7iQjIQuC4Bku"),
    ("male", "Liam", "TX3LPaxmHKxFdv7VOQHJ"),
    ("male", "Daniel", "onwK4e9ZLuTAKqWW03F9"),
    ("male", "Brian", "nPczCjzI2devNBz1zQrb"),
    ("male", "George", "JBFqnCBsd6RMkjVDRZzb"),
    ("male", "Callum", "N2lVS1w4EtoT3dr4eOWO"),
)


@dataclass(frozen=True)
class Job:
    """One clip to render."""

    glyph: str
    script: str
    text: str
    voice: str  # "female" | "male"

    @property
    def path(self) -> Path:
        return lib.clip_path(self.script, self.glyph, self.voice, ".mp3")


def speech_text_for(seed: CharacterSeed) -> str:
    """What the narrator should say for this character.

    Kana are spoken as the glyph. Kanji are spoken as their primary kun'yomi,
    falling back to on'yomi — the same rule :func:`audio.speech_text` applies,
    kept in step deliberately so bundled clips and TTS say the same thing.
    """
    if seed.script in ("hiragana", "katakana"):
        return seed.glyph
    for raw in (seed.kunyomi, seed.onyomi):
        if raw:
            first = raw.split("/")[0]
            return first.replace("(", "").replace(")", "").strip()
    return seed.glyph


def all_seeds() -> list[CharacterSeed]:
    return [*HIRAGANA, *KATAKANA, *KANJI_N5]


def plan(voices: tuple[str, ...]) -> list[Job]:
    """Every clip the library wants, in a stable order."""
    jobs: list[Job] = []
    for seed in all_seeds():
        text = speech_text_for(seed)
        for voice in voices:
            jobs.append(Job(seed.glyph, seed.script, text, voice))
    return jobs


def outstanding(jobs: list[Job]) -> list[Job]:
    """Jobs whose clip is missing or fails validation. Makes `build` resumable."""
    todo = []
    for job in jobs:
        if job.path.is_file() and lib.validate_clip(job.path).ok:
            continue
        todo.append(job)
    return todo


# ── commands ────────────────────────────────────────────────────────────────


async def cmd_cost(args: argparse.Namespace) -> int:
    """Estimate spend before committing to it."""
    jobs = plan(tuple(args.voices))
    todo = outstanding(jobs)
    chars = sum(len(j.text) for j in todo)
    print(f"characters in set : {len(all_seeds())}")
    print(f"voices            : {', '.join(args.voices)}")
    print(f"clips wanted      : {len(jobs)}")
    print(f"already valid     : {len(jobs) - len(todo)}")
    print(f"clips to render   : {len(todo)}")
    print(f"API characters    : ~{chars}")
    print(
        f"est. requests     : {len(todo)}  (~{len(todo) * REQUEST_SPACING_S / 60:.1f} min at current spacing)"
    )
    return 0


async def cmd_audition(args: argparse.Namespace) -> int:
    """Render one Japanese phrase in every candidate voice, for a human to judge."""
    if not el.is_configured():
        print("No API key. Set ELEVENLABS_API_KEY or create", el.KEY_FILE, file=sys.stderr)
        return 2

    AUDITION_DIR.mkdir(parents=True, exist_ok=True)
    print(f"phrase: {AUDITION_PHRASE}")
    print(f"writing to: {AUDITION_DIR}\n")

    ok = 0
    for gender, name, voice_id in CANDIDATES:
        if args.gender and gender != args.gender:
            continue
        rendered = await _synthesize_with(AUDITION_PHRASE, voice_id)
        target = AUDITION_DIR / f"{gender}-{name}.mp3"
        if rendered is None:
            print(f"  {gender:6} {name:9} FAILED")
            continue
        target.write_bytes(rendered)
        report = lib.validate_clip(target)
        print(
            f"  {gender:6} {name:9} {len(rendered):>7} bytes  id={voice_id}  {'ok' if report.ok else report.reason}"
        )
        ok += 1
        time.sleep(REQUEST_SPACING_S)

    print(f"\n{ok} samples written. Listen, then pass the winners to `build`:")
    print("  python -m japanese_practice.voicelab build --female-id <id> --male-id <id>")
    return 0


async def cmd_build(args: argparse.Namespace) -> int:
    """Render and validate every clip for the chosen voices."""
    if not el.is_configured():
        print("No API key. Set ELEVENLABS_API_KEY or create", el.KEY_FILE, file=sys.stderr)
        return 2

    ids = {"female": args.female_id, "male": args.male_id}
    voices = tuple(v for v in args.voices if ids.get(v))
    if not voices:
        print("Give at least one of --female-id / --male-id", file=sys.stderr)
        return 2

    jobs = outstanding(plan(voices))
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"rendering {len(jobs)} clips for {', '.join(voices)}\n")

    written = failed = 0
    for i, job in enumerate(jobs, 1):
        rendered = await _synthesize_with(job.text, ids[job.voice])
        if rendered is None:
            print(f"  [{i}/{len(jobs)}] {job.voice:6} {job.glyph:<4} REQUEST FAILED")
            failed += 1
            if failed >= 5:
                print("\nfive consecutive failures — stopping. Re-run to resume.", file=sys.stderr)
                return 1
            continue

        # Validate BEFORE the clip enters the library, so bad audio never lands.
        job.path.parent.mkdir(parents=True, exist_ok=True)
        # The scratch file must keep a real audio suffix — the validator gates
        # on extension, so ".part" was rejected before the bytes were examined.
        scratch = job.path.with_name(f".{job.path.stem}.part.mp3")
        scratch.write_bytes(rendered)
        report = lib.validate_clip(scratch)
        if not report.ok:
            scratch.unlink(missing_ok=True)
            print(f"  [{i}/{len(jobs)}] {job.voice:6} {job.glyph:<4} REJECTED: {report.reason}")
            failed += 1
            continue

        scratch.replace(job.path)
        failed = 0
        written += 1
        if i % 25 == 0 or i == len(jobs):
            print(f"  [{i}/{len(jobs)}] {written} written")
        time.sleep(REQUEST_SPACING_S)

    print(f"\n{written} clips written")
    lib.write_manifest()
    print(f"manifest: {lib.MANIFEST_PATH}")
    return 0


async def cmd_verify(args: argparse.Namespace) -> int:
    """Validate the whole library and rewrite the manifest."""
    reports = lib.scan_library()
    good = [r for r in reports if r.ok]
    bad = [r for r in reports if not r.ok]

    print(f"clips found : {len(reports)}")
    print(f"valid       : {len(good)}")
    print(f"rejected    : {len(bad)}")
    for r in bad[:20]:
        print(f"  {r.path}: {r.reason}")

    if good:
        durations = [r.duration_ms for r in good if r.duration_ms]
        peaks = [r.peak for r in good if r.peak is not None]
        if durations:
            print(f"duration    : {min(durations)}–{max(durations)} ms")
        if peaks:
            print(f"peak amp    : {min(peaks):.2f}–{max(peaks):.2f}")

    lib.write_manifest(reports)
    print(f"manifest    : {lib.MANIFEST_PATH}")

    drift = lib.verify_against_manifest()
    print(f"drift       : {drift or 'none'}")

    # Acoustic review signals — these do not fail the run, they queue human
    # listening. Pronunciation accuracy cannot be confirmed any other way.
    findings = lib.cross_voice_report()
    print(f"review queue: {len(findings)}")
    for f in findings[:20]:
        print(f"  {f['script']}/{f['glyph']}  {f['issue']}: {f['detail']}")

    return 0 if not bad else 1


async def _synthesize_with(text: str, voice_id: str) -> bytes | None:
    """One synthesis call against an explicit voice id."""
    import json
    import urllib.error

    url = f"{el.API_ROOT}/text-to-speech/{voice_id}?output_format={el.DEFAULT_OUTPUT_FORMAT}"
    body = json.dumps(
        {"text": text, "model_id": el.DEFAULT_MODEL, "voice_settings": el.VOICE_SETTINGS}
    ).encode("utf-8")
    try:
        return await asyncio.to_thread(el._request, url, method="POST", body=body)
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:160].decode("utf-8", "replace")
        print(f"    HTTP {exc.code}: {detail}", file=sys.stderr)
        return None
    except Exception as exc:  # noqa: BLE001 - a failed clip must not stop the run
        print(f"    {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voicelab", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_cost = sub.add_parser("cost", help="estimate spend before rendering")
    p_cost.add_argument("--voices", nargs="+", default=["female", "male"])
    p_cost.set_defaults(func=cmd_cost)

    p_aud = sub.add_parser("audition", help="sample candidate voices")
    p_aud.add_argument("--gender", choices=["female", "male"])
    p_aud.set_defaults(func=cmd_audition)

    p_build = sub.add_parser("build", help="render and validate the clip library")
    p_build.add_argument("--female-id")
    p_build.add_argument("--male-id")
    p_build.add_argument("--voices", nargs="+", default=["female", "male"])
    p_build.add_argument("--limit", type=int, help="stop after N clips (for a trial run)")
    p_build.set_defaults(func=cmd_build)

    p_ver = sub.add_parser("verify", help="validate the library and rewrite the manifest")
    p_ver.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
