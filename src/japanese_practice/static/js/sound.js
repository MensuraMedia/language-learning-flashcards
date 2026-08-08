// Shared UI sound. Currently one cue: the chime for a correct answer.
//
// Kept separate from pronunciation playback, which is *content* — the thing
// being learned — whereas this is feedback about the interface. They are gated
// differently and live in different places: pronunciation is fetched per
// character from /api/audio, this is one bundled file reused everywhere.
//
// Three preferences apply, and they compose:
//
//   jp.sound   master switch, set in Settings. Off means silence everywhere.
//   jp.muted   the study view's M key. A quick mute for the current sitting.
//   jp.volume  the study view's up/down arrows.
//
// A cue is heard only when the master is on and nothing is muted. That way M
// still silences everything mid-session, and Settings still wins over M.

const SOUND_KEY = "jp.sound";
const MUTED_KEY = "jp.muted";
const VOLUME_KEY = "jp.volume";

// A correct answer should register without being startling — it fires on every
// right answer, which at a fast pace is several times a minute.
const CUE_GAIN = 0.55;

// localStorage throws in some WebKit configurations rather than returning null,
// and an uncaught throw here would kill the module that imported it. This
// already broke the study view once.
function get(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function set(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* preferences are best-effort; never block playback or a render on them */
  }
}

/** Master switch. Defaults to on, so a fresh install has sound. */
export function soundEnabled() {
  return get(SOUND_KEY) !== "off";
}

export function setSoundEnabled(on) {
  set(SOUND_KEY, on ? "on" : "off");
}

function level() {
  if (!soundEnabled() || get(MUTED_KEY) === "1") return 0;
  const stored = parseFloat(get(VOLUME_KEY) ?? "1");
  const volume = Number.isFinite(stored) ? Math.min(1, Math.max(0, stored)) : 1;
  return volume * CUE_GAIN;
}

// One element, reused. Answering quickly at the top pace fires this several
// times a minute, and a fresh Audio per answer leaks elements and re-fetches.
let cue = null;

function element() {
  if (cue === null) {
    // WAV, not MP3: the cue is feedback on a click, and MP3's encoder delay
    // put the sound ~14 ms late where the WAV starts at ~2 ms. See the README
    // beside the asset for the measurements.
    cue = new Audio("/static/audio/sounds/ding-correct.wav");
    cue.preload = "auto";
  }
  return cue;
}

/** Play the correct-answer chime, if the preferences allow it. */
export function playCorrect() {
  const gain = level();
  if (gain <= 0) return;
  try {
    const node = element();
    node.volume = gain;
    // Restart rather than ignore: two correct answers in quick succession
    // should sound twice, not once.
    node.currentTime = 0;
    // Autoplay policies reject silently until the page has been interacted
    // with. Answering a card *is* an interaction, so this normally resolves —
    // but a rejection must never surface as an unhandled rejection.
    node.play?.().catch(() => {});
  } catch {
    /* a missing or undecodable cue must not break answering */
  }
}

/** Warm the cue so the first correct answer is not late. */
export function primeCue() {
  try {
    element().load();
  } catch {
    /* best effort */
  }
}
