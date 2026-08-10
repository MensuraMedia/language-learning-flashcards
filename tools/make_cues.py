#!/usr/bin/env python3
"""Synthesise the correct-answer cue set.

Six short positive sounds, generated rather than sourced, so that they are
consistent with each other and reproducible. Every cue is built to the same
contract, because the study view fires them several times a minute:

    format      mono 44.1 kHz 16-bit WAV
    onset       first sample is the attack — no leading silence, which is pure
                latency between the click and the sound
    duration    <= 320 ms, shorter than the fastest verdict hold (380 ms), so a
                cue is never still ringing over the next card
    level       **loudness**-normalised to -14 dBFS RMS, peak capped at -1 dBFS

**Loudness, not peak.** These were peak-normalised first, and peak is not what an
ear hears: a short bright tone at -0.4 dBFS peak sat **+10 dB above** the
pronunciation clips at the same volume setting, because speech has a far higher
peak-to-average ratio. Matching RMS is what makes one volume control govern both
convincingly. The measured median for the 630 narration clips is -19.9 dBFS RMS,
and CUE_GAIN in sound.js closes the remaining gap.

Loud in the file, attenuated in code. The reverse — a quiet asset multiplied by
an app gain and then by system volume — put the first version at about -19 dBFS
at the speakers, which is inaudible.

WAV rather than MP3: MP3 carries an encoder delay that left ~14 ms of lag even
after trimming the silence out, and the Web Audio API decodes the file once into
memory anyway, so the format costs nothing at play time.

    python tools/make_cues.py
"""

from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100
MAX_SECONDS = 0.32
#: RMS over the audible part, not peak — see the module docstring.
TARGET_RMS = 0.1995  # -14 dBFS
PEAK_CEILING = 0.891  # -1 dBFS, so normalising can never clip

#: Equal-tempered frequencies, so the multi-note cues are actually in tune.
NOTE = {
    "C5": 523.25,
    "E5": 659.26,
    "G5": 783.99,
    "A5": 880.00,
    "C6": 1046.50,
    "D6": 1174.66,
    "E6": 1318.51,
    "G6": 1567.98,
    "A6": 1760.00,
    "C7": 2093.00,
    "E7": 2637.02,
}


def envelope(n: int, attack: float, decay: float) -> list[float]:
    """Fast linear attack into an exponential decay.

    The attack is never zero: a waveform that starts at full amplitude begins
    with a step, and a step is a click.
    """
    attack_samples = max(1, int(attack * SAMPLE_RATE))
    out = []
    for i in range(n):
        if i < attack_samples:
            amp = i / attack_samples
        else:
            amp = math.exp(-(i - attack_samples) / (decay * SAMPLE_RATE))
        out.append(amp)
    return out


def tone(
    freq: float, seconds: float, partials: list[tuple[float, float, float]], attack: float = 0.003
) -> list[float]:
    """One struck note.

    ``partials`` are ``(ratio, gain, decay_seconds)``. Giving each partial its
    own decay is what separates a struck bell — where the upper partials die
    first — from a plain additive drone.
    """
    n = int(seconds * SAMPLE_RATE)
    out = [0.0] * n
    for ratio, gain, decay in partials:
        env = envelope(n, attack, decay)
        w = 2 * math.pi * freq * ratio / SAMPLE_RATE
        for i in range(n):
            out[i] += gain * env[i] * math.sin(w * i)
    return out


def sequence(events: list[tuple[float, list[float]]], seconds: float) -> list[float]:
    """Mix notes at given start offsets into one buffer."""
    n = int(seconds * SAMPLE_RATE)
    out = [0.0] * n
    for start, samples in events:
        offset = int(start * SAMPLE_RATE)
        for i, v in enumerate(samples):
            j = offset + i
            if j < n:
                out[j] += v
    return out


def fade_tail(samples: list[float], seconds: float = 0.03) -> list[float]:
    """Ramp the last few ms to zero so the hard end of the buffer cannot click."""
    n = int(seconds * SAMPLE_RATE)
    total = len(samples)
    for i in range(max(0, total - n), total):
        samples[i] *= (total - i) / n
    return samples


def normalise(samples: list[float]) -> list[float]:
    """Scale to a target RMS, backing off if that would clip.

    RMS is measured over the audible part only: these cues are mostly decay, and
    including the tail would make a long-decaying bell read as quieter than a
    short blip that is actually the same loudness.
    """
    peak = max((abs(v) for v in samples), default=0.0)
    if peak == 0:
        return samples
    floor = peak * 0.05
    live = [v for v in samples if abs(v) > floor]
    if not live:
        return samples
    rms = math.sqrt(sum(v * v for v in live) / len(live))
    if rms == 0:
        return samples
    scale = TARGET_RMS / rms
    if peak * scale > PEAK_CEILING:
        scale = PEAK_CEILING / peak
    return [v * scale for v in samples]


def write(path: Path, samples: list[float]) -> None:
    samples = normalise(fade_tail(samples))
    frames = b"".join(struct.pack("<h", max(-32768, min(32767, int(v * 32767)))) for v in samples)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(frames)


# ── the cue set ─────────────────────────────────────────────────────────────
# Each is a different *character* of positive, not a different pitch of the same
# sound: a learner picks the one that will not grate after two hundred repeats.


def cue_chime() -> list[float]:
    """Two notes rising a perfect fifth. Clear and unambiguous."""
    bell = [(1.0, 1.0, 0.14), (2.0, 0.35, 0.09), (3.01, 0.16, 0.05)]
    return sequence(
        [
            (0.000, tone(NOTE["C6"], 0.20, bell)),
            (0.075, tone(NOTE["G6"], 0.24, bell)),
        ],
        0.32,
    )


def cue_bell() -> list[float]:
    """A single struck bell. Inharmonic partials, long-ish shimmer."""
    return tone(
        NOTE["E6"],
        0.32,
        [(1.0, 1.0, 0.16), (2.76, 0.30, 0.10), (5.40, 0.12, 0.06), (8.93, 0.05, 0.04)],
    )


def cue_marimba() -> list[float]:
    """Warm and wooden. Fundamental plus its fourth harmonic, decaying fast."""
    return tone(
        NOTE["C6"],
        0.26,
        [(1.0, 1.0, 0.075), (4.0, 0.28, 0.030), (10.0, 0.06, 0.015)],
        attack=0.002,
    )


def cue_arpeggio() -> list[float]:
    """A major triad, three quick ascending notes. The most 'well done' of them."""
    pluck = [(1.0, 1.0, 0.075), (2.0, 0.22, 0.045)]
    return sequence(
        [
            (0.000, tone(NOTE["C6"], 0.14, pluck)),
            (0.055, tone(NOTE["E6"], 0.14, pluck)),
            (0.110, tone(NOTE["G6"], 0.20, pluck)),
        ],
        0.32,
    )


def cue_blip() -> list[float]:
    """One soft sine. The least intrusive option, for long sittings."""
    return tone(NOTE["A6"], 0.13, [(1.0, 1.0, 0.035), (2.0, 0.10, 0.020)], attack=0.004)


def cue_sparkle() -> list[float]:
    """Two high pings, quick and bright. Small and cheerful."""
    ping = [(1.0, 1.0, 0.055), (2.0, 0.20, 0.030), (3.0, 0.08, 0.020)]
    return sequence(
        [
            (0.000, tone(NOTE["C7"], 0.14, ping)),
            (0.045, tone(NOTE["E7"], 0.20, ping)),
        ],
        0.30,
    )


CUES = {
    "chime": cue_chime,
    "bell": cue_bell,
    "marimba": cue_marimba,
    "arpeggio": cue_arpeggio,
    "blip": cue_blip,
    "sparkle": cue_sparkle,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "src/japanese_practice/static/audio/sounds",
        help="directory to write the cues into",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"  writing to {args.out}")
    for name, build in CUES.items():
        samples = build()
        assert len(samples) <= MAX_SECONDS * SAMPLE_RATE + 1, f"{name} exceeds {MAX_SECONDS}s"
        path = args.out / f"cue-{name}.wav"
        write(path, samples)
        peak = max(abs(v) for v in normalise(samples))
        print(
            f"    cue-{name}.wav   {len(samples) / SAMPLE_RATE:.3f}s   "
            f"peak {peak:.3f}   {path.stat().st_size / 1024:.1f} KB"
        )


if __name__ == "__main__":
    main()
