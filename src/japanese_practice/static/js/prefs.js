// Interface preferences — pace, voice, volume, sound cue, master mute.
//
// **Stored on the server, not in the browser.** This project has been bitten
// three times by `localStorage` in the desktop webview: once by it throwing on
// access, once by writes being accepted and silently dropped, and once by the
// consequence of that — a preference set on the dashboard never reached the
// study view, because a full page navigation starts a fresh JS context and
// there was nothing to read back. Selecting a different sound appeared to work
// and then did nothing.
//
// An in-memory cache cannot fix that in a multi-page application. The server
// can: each profile is already its own database file, so the `preferences`
// table is per-profile without a profile column, and settings now survive both
// navigation and restarting the app.
//
// Reads are synchronous against a cache primed at start-up. Writes update the
// cache immediately — so a control always reflects what you just did — and are
// flushed to the server on a short debounce.

const ENDPOINT = "/api/preferences";
const FLUSH_MS = 250;

const cache = new Map();
const pending = new Map();
let flushTimer = null;

/** Resolves once the cache holds the server's copy. */
export let prefsReady = Promise.resolve();

/** Whether the last write reached the server. */
export let available = true;

/** Read a preference. Synchronous; awaits nothing. */
export function readPref(key, fallback = null) {
  return cache.has(key) ? cache.get(key) : fallback;
}

/**
 * Write a preference. Takes effect immediately in this page and is persisted
 * shortly after — batching means dragging a volume slider is one request, not
 * one per step.
 */
export function writePref(key, value) {
  const text = String(value);
  cache.set(key, text);
  pending.set(key, text);
  // localStorage is still written when it works, purely so a page opened before
  // the server responds has something to start from. It is never the authority.
  try {
    localStorage.setItem(key, text);
  } catch {
    /* expected in this webview; the server is what actually persists */
  }
  if (flushTimer === null) flushTimer = setTimeout(flush, FLUSH_MS);
  return true;
}

async function flush() {
  flushTimer = null;
  if (pending.size === 0) return;
  const body = Object.fromEntries(pending);
  pending.clear();
  try {
    const res = await fetch(ENDPOINT, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    available = res.ok;
    if (!res.ok) throw new Error(`preferences: ${res.status}`);
  } catch {
    available = false;
    // Put them back so the next flush retries rather than losing the setting.
    for (const [k, v] of Object.entries(body)) if (!pending.has(k)) pending.set(k, v);
  }
}

/** Load the server's copy into the cache. Called once, at module load. */
async function load() {
  // Seed from localStorage first so the very first paint is not empty on the
  // rare browser where it does work.
  try {
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i);
      if (key && key.startsWith("jp.")) cache.set(key, localStorage.getItem(key));
    }
  } catch {
    /* fine — the server is the authority */
  }
  try {
    const res = await fetch(ENDPOINT, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(String(res.status));
    const stored = await res.json();
    for (const [key, value] of Object.entries(stored)) cache.set(key, String(value));
    available = true;
  } catch {
    available = false;
  }
}

prefsReady = load();

// Anything still queued when the window closes would otherwise be lost.
if (typeof window !== "undefined") {
  window.addEventListener("pagehide", () => {
    if (pending.size === 0) return;
    const body = JSON.stringify(Object.fromEntries(pending));
    try {
      // sendBeacon survives the page teardown that would abort a fetch.
      navigator.sendBeacon?.(ENDPOINT, new Blob([body], { type: "application/json" }));
    } catch {
      /* best effort on the way out */
    }
  });
}

/** Human-readable state, for the Settings diagnostics line. */
export function storageNote() {
  return available
    ? "Settings are saved to this profile."
    : "Settings could not be saved — they apply now but will reset.";
}
