// UI sound: the cue for a correct answer.
//
// **Web Audio, not HTMLAudioElement.** `new Audio(url).play()` is built for
// media playback — a track you start, scrub and stop. For a short cue fired
// several times a minute it is the wrong tool in three specific ways:
//
//   1. `play()` returns a promise the autoplay policy can reject, and a
//      rejection is the normal state until the page has been interacted with.
//      Swallowing it makes a blocked cue indistinguishable from a working one.
//   2. Restarting with `currentTime = 0` is not sample accurate and cancels the
//      cue already sounding, so two quick correct answers give one blip.
//   3. Every play goes through the media pipeline, adding latency that varies
//      with what else the engine is doing.
//
// Web Audio decodes the file **once** into an AudioBuffer. Each cue is then a
// fresh BufferSourceNode started immediately — sub-millisecond, overlapping
// safely, with an explicit GainNode for level. This is the standard approach
// for interface sound and it is what the platform provides it for.
//
// The one obligation it adds is unlocking: an AudioContext starts `suspended`
// until a user gesture resumes it. That is handled below, once, on the first
// interaction with the page.

const CUE_URL = "/static/audio/sounds/ding-correct.wav";

const SOUND_KEY = "jp.sound";
const MUTED_KEY = "jp.muted";
const VOLUME_KEY = "jp.volume";

// The asset is peak-normalised to −0.4 dBFS, so the file is loud and the code
// decides how loud it should actually be. The previous arrangement — a quiet
// file attenuated further in code — reached the speakers at about −19 dBFS,
// which is why it could not be heard.
const CUE_GAIN = 0.9;

// localStorage throws rather than returning null in some WebKit configurations,
// and an uncaught throw here would take down the module that imported this.
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
    /* preferences are best effort; never block playback on them */
  }
}

/** Master switch, set in Settings. Defaults to on. */
export function soundEnabled() {
  return get(SOUND_KEY) !== "off";
}

export function setSoundEnabled(on) {
  set(SOUND_KEY, on ? "on" : "off");
  if (on) unlock();
}

// Master switch, the study view's M mute and its volume all apply, and they
// compose: M silences the current sitting, Settings wins over M.
function level() {
  if (!soundEnabled() || get(MUTED_KEY) === "1") return 0;
  const stored = parseFloat(get(VOLUME_KEY) ?? "1");
  const volume = Number.isFinite(stored) ? Math.min(1, Math.max(0, stored)) : 1;
  return volume * CUE_GAIN;
}

// ── the audio graph ─────────────────────────────────────────────────────────

let ctx = null;
let buffer = null;
let loading = null;

/** Diagnostics. A cue that never sounds should be able to say why. */
export const soundStatus = {
  supported: typeof window !== "undefined" && !!(window.AudioContext || window.webkitAudioContext),
  contextState: "none",
  decoded: false,
  plays: 0,
  lastError: null,
};

function context() {
  if (ctx === null) {
    const Ctor = window.AudioContext || window.webkitAudioContext;
    if (!Ctor) return null;
    ctx = new Ctor();
  }
  soundStatus.contextState = ctx.state;
  return ctx;
}

async function decode() {
  const audio = context();
  if (!audio) throw new Error("Web Audio is unavailable");
  const res = await fetch(CUE_URL, { cache: "force-cache" });
  if (!res.ok) throw new Error(`cue fetch failed: ${res.status}`);
  const bytes = await res.arrayBuffer();
  // Safari and older WebKit only offer the callback form of decodeAudioData.
  buffer = await new Promise((resolve, reject) => {
    const maybe = audio.decodeAudioData(bytes, resolve, reject);
    if (maybe && typeof maybe.then === "function") maybe.then(resolve, reject);
  });
  soundStatus.decoded = true;
  return buffer;
}

/**
 * Decode the cue ahead of time. Safe to call repeatedly; the work happens once.
 */
export function primeCue() {
  if (buffer || loading) return loading;
  loading = decode().catch((err) => {
    soundStatus.lastError = String(err);
    loading = null;          // let a later attempt retry rather than fail forever
  });
  return loading;
}

/**
 * Resume the AudioContext. An AudioContext created before any user gesture
 * starts suspended, and every cue from it is silent until something resumes it.
 * Called on the first interaction, and again whenever a cue is requested, since
 * the engine may suspend it when the window loses focus.
 */
export function unlock() {
  const audio = context();
  if (!audio) return;
  if (audio.state === "suspended") {
    audio.resume().then(
      () => {
        soundStatus.contextState = audio.state;
      },
      (err) => {
        soundStatus.lastError = String(err);
      }
    );
  }
  soundStatus.contextState = audio.state;
  primeCue();
}

// One listener, removed after it fires. Any of these counts as the gesture the
// autoplay policy is waiting for.
if (typeof window !== "undefined") {
  const first = () => {
    unlock();
    ["pointerdown", "keydown", "touchstart"].forEach((e) =>
      window.removeEventListener(e, first, true)
    );
  };
  ["pointerdown", "keydown", "touchstart"].forEach((e) =>
    window.addEventListener(e, first, true)
  );
}

/** Play the correct-answer cue, if the preferences allow it. */
export function playCorrect() {
  const gain = level();
  if (gain <= 0) return;

  const audio = context();
  if (!audio) {
    soundStatus.lastError = "Web Audio is unavailable";
    return;
  }
  // Resuming is idempotent and cheap; the context can be suspended again by the
  // engine at any point, typically when the window loses focus.
  if (audio.state === "suspended") audio.resume().catch(() => {});
  soundStatus.contextState = audio.state;

  if (!buffer) {
    // Not decoded yet — start it, and let the next cue be the one that sounds
    // rather than queueing a burst of late blips.
    primeCue();
    return;
  }

  try {
    const source = audio.createBufferSource();
    source.buffer = buffer;
    const volume = audio.createGain();
    volume.gain.value = gain;
    source.connect(volume);
    volume.connect(audio.destination);
    source.start();
    soundStatus.plays += 1;
  } catch (err) {
    soundStatus.lastError = String(err);
  }
}

// Exposed for manual diagnosis from the webview console, and used by the test
// button in Settings.
if (typeof window !== "undefined") {
  window.jpSound = { playCorrect, primeCue, unlock, soundStatus, soundEnabled };
}
