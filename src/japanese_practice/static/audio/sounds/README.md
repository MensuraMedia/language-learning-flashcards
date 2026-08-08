# UI sounds

| File | Role |
|---|---|
| `ding-correct.wav` | **What plays** on a correct answer, in the study view and on a matched pair in the games |
| `ding-correct-source.mp3` | The cue as originally supplied, kept so the trim below can be redone or revised |

## Why WAV, and why so short

The cue is feedback on a click, so latency between the two is the whole quality
bar. The source had **64 ms of leading silence** and ran for 1.056 s — audible
until 0.63 s, then silence. Two consequences: the sound arrived noticeably after
the click, and at the study view's fastest pace (a 380 ms verdict hold) it was
still ringing when the next card appeared.

WAV rather than MP3 because MP3 carries an inherent encoder delay — the trimmed
MP3 still started 14 ms late, where the WAV starts at 2 ms. For a 28 KB asset
that decodes instantly and restarts exactly on `currentTime = 0`, the format
costs nothing and removes the last of the lag.

| | Duration | Onset | Size |
|---|---:|---:|---:|
| Source MP3 | 1.056 s | 66 ms | 33 KB |
| Trimmed MP3 | 0.341 s | 14 ms | 4.9 KB |
| **Trimmed WAV (shipped)** | **0.320 s** | **2 ms** | **28 KB** |

## Regenerating

Cut at the true onset, keep the attack and its useful decay, fade the tail so
the cut does not click:

```bash
ffmpeg -i ding-correct-source.mp3 \
  -af "atrim=start=0.064,asetpts=PTS-STARTPTS,afade=t=out:st=0.24:d=0.08" \
  -t 0.32 -ac 1 -ar 44100 -c:a pcm_s16le ding-correct.wav
```

`tests/test_audio_library.py` decodes the result and asserts it is audible and
short. **Never judge an audio file by its size** — a silent stub of exactly the
right length once passed for working synthesis in this project.
