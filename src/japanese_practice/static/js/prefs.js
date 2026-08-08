// Preference storage that cannot silently fail.
//
// This project has already been bitten twice by `localStorage` in the desktop
// webview: once by it *throwing* on access, which killed the study module
// before it started, and once by writes appearing to succeed while nothing was
// stored — which made the Settings audio toggle look inert. A toggle that does
// not toggle is worse than an absent one, because the user reasonably concludes
// the whole feature is broken.
//
// So every preference is held in memory as the authority for the current
// session, and mirrored to `localStorage` only as a best-effort attempt at
// persisting across restarts. Reads come from memory, which means:
//
//   * a control always reflects what you just did, storage or no storage
//   * a throwing or silently-dropping backend degrades to "settings work now
//     but reset when you relaunch", instead of "settings do nothing"
//
// `available` records which of those you are getting, so the UI can say so
// rather than leaving the user to guess.

const memory = new Map();

/** Whether the browser gave us usable persistent storage. */
export let available = false;

// Probe once, with a real write-read-delete round trip. Feature-detecting by
// `"localStorage" in window` is not enough: the object exists in configurations
// where every write throws, and in others where writes are accepted and dropped.
try {
  const probe = "__jp_probe__";
  localStorage.setItem(probe, "1");
  available = localStorage.getItem(probe) === "1";
  localStorage.removeItem(probe);
} catch {
  available = false;
}

// Seed memory from storage so a restart picks up where the last session left
// off, when storage is working.
if (available) {
  try {
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i);
      if (key && key.startsWith("jp.")) memory.set(key, localStorage.getItem(key));
    }
  } catch {
    available = false;
  }
}

/** Read a preference. Memory is the authority for the running session. */
export function readPref(key, fallback = null) {
  if (memory.has(key)) return memory.get(key);
  return fallback;
}

/** Write a preference. Always takes effect; persists when it can. */
export function writePref(key, value) {
  const text = String(value);
  memory.set(key, text);
  if (!available) return false;
  try {
    localStorage.setItem(key, text);
    return true;
  } catch {
    available = false;
    return false;
  }
}

/** Human-readable state, for the Settings diagnostics line. */
export function storageNote() {
  return available
    ? "Settings persist between sessions."
    : "This window has no persistent storage — settings apply now but reset when you relaunch.";
}
