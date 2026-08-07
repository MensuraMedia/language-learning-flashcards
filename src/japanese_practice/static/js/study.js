// Study view: one glyph at a time, true 3D flip, self-graded.
// The front face renders the glyph and nothing else — that is the whole point.
//
// Keyboard is a first-class input, not an accessory: a learner drilling 100
// cards should never need the mouse. See KEYMAP below and the help overlay (?).

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);

const VOLUME_STEP = 0.1;
const VOLUME_KEY = "jp.volume";
const MUTED_KEY = "jp.muted";

const state = {
  sessionId: null,
  cards: [],
  index: 0,
  streak: 0,
  score: 0,
  flipped: false,
  shownAt: 0,
  scheme: "accuracy",
  graded: new Set(),
  volume: readVolume(),
  muted: readMuted(),
  audio: null,
  finished: false,
};

// localStorage is not guaranteed. Embedded webviews, private windows and
// restricted origins can all make it throw on access rather than return null,
// and this runs at module scope — an unguarded read takes the whole view down
// before the session ever starts. Preferences are a convenience; losing them
// must never cost the learner their study session.
function storageGet(key) {
  try {
    return window.localStorage?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

function storageSet(key, value) {
  try {
    window.localStorage?.setItem(key, value);
  } catch {
    /* preferences simply do not persist in this context */
  }
}

function readVolume() {
  const raw = parseFloat(storageGet(VOLUME_KEY) ?? "1");
  return Number.isFinite(raw) ? Math.min(1, Math.max(0, raw)) : 1;
}

function readMuted() {
  return storageGet(MUTED_KEY) === "1";
}

async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).message || res.statusText);
  return res.json();
}

// ── card rendering ───────────────────────────────────────────────────────────

function render() {
  const card = state.cards[state.index];
  if (!card) return finish();

  state.flipped = false;
  $("card").classList.remove("flipped");
  $("glyph").textContent = card.glyph;
  $("back-glyph").textContent = card.glyph;

  if (card.script === "kanji") {
    $("back-sound").textContent = "";
    $("back-meaning").textContent = card.meaning || "";
    const rows = [];
    if (card.onyomi) rows.push(`<div class="krow"><em>on</em><span class="jp">${card.onyomi}</span></div>`);
    if (card.kunyomi) rows.push(`<div class="krow"><em>kun</em><span class="jp">${card.kunyomi}</span></div>`);
    $("back-readings").innerHTML = rows.join("");
  } else {
    $("back-sound").textContent = card.romaji || "";
    $("back-meaning").textContent = "";
    $("back-readings").innerHTML = "";
  }

  $("counter").textContent = `${state.index + 1} / ${state.cards.length}`;
  $("spk-note").textContent = "Play";
  state.shownAt = performance.now();
}

function flip() {
  state.flipped = !state.flipped;
  $("card").classList.toggle("flipped", state.flipped);
}

// ── navigation ───────────────────────────────────────────────────────────────

function goPrevious() {
  if (state.index === 0) return toast("First card");
  state.index -= 1;
  render();
}

function goNext() {
  if (state.index >= state.cards.length - 1) return toast("Last card — J or F to finish");
  state.index += 1;
  render();
}

// ── grading ──────────────────────────────────────────────────────────────────

async function grade(correct) {
  const card = state.cards[state.index];
  if (!card || state.finished) return;

  // Navigating back and forth must not double-count a card.
  if (state.graded.has(state.index)) {
    return advanceAfterGrade();
  }
  state.graded.add(state.index);

  const latency = Math.round(performance.now() - state.shownAt);
  try {
    const res = await post(`/api/session/${state.sessionId}/attempt`, {
      character_id: card.id,
      correct,
      latency_ms: latency,
      streak: state.streak,
      // On a miss, record the neighbouring card as what it was confused with —
      // this is what feeds the confusion-pair panel.
      given_answer: correct ? null : (state.cards[(state.index + 1) % state.cards.length] || {}).glyph,
    });
    state.streak = res.streak;
    state.score = res.score;
    $("score").textContent = res.score;
    $("streak").textContent = res.streak;
  } catch (err) {
    console.error("attempt failed", err);
  }
  advanceAfterGrade();
}

function advanceAfterGrade() {
  if (state.index >= state.cards.length - 1) return finish();
  state.index += 1;
  render();
}

async function finish() {
  if (state.finished) return;
  state.finished = true;
  let record = {};
  try {
    record = await post(`/api/session/${state.sessionId}/end`, {});
  } catch (err) {
    console.error(err);
  }
  const acc = record.total ? Math.round((record.correct / record.total) * 100) : 0;
  $("recap-grid").innerHTML = `
    <div class="kv"><span class="lbl-sm">Score</span><b class="num">${record.score ?? state.score}</b></div>
    <div class="kv"><span class="lbl-sm">Accuracy</span><b class="num">${acc}%</b></div>
    <div class="kv"><span class="lbl-sm">Cards</span><b class="num">${record.total ?? 0}</b></div>
    <div class="kv"><span class="lbl-sm">Best streak</span><b class="num">${record.max_streak ?? 0}</b></div>`;
  $("recap").hidden = false;
}

// ── audio ────────────────────────────────────────────────────────────────────

function effectiveVolume() {
  return state.muted ? 0 : state.volume;
}

function showVolume() {
  const level = Math.round(state.volume * 100);
  $("volume-fill").style.width = `${state.muted ? 0 : level}%`;
  $("volume-label").textContent = state.muted ? "Muted" : `Volume ${level}%`;
  const bar = $("volume-bar");
  bar.hidden = false;
  clearTimeout(showVolume._t);
  showVolume._t = setTimeout(() => {
    bar.hidden = true;
  }, 1400);
}

function changeVolume(delta) {
  state.volume = Math.min(1, Math.max(0, +(state.volume + delta).toFixed(2)));
  if (state.volume > 0) state.muted = false;
  storageSet(VOLUME_KEY, String(state.volume));
  storageSet(MUTED_KEY, state.muted ? "1" : "0");
  if (state.audio) state.audio.volume = effectiveVolume();
  showVolume();
}

function toggleMute() {
  state.muted = !state.muted;
  storageSet(MUTED_KEY, state.muted ? "1" : "0");
  if (state.audio) state.audio.volume = effectiveVolume();
  showVolume();
}

async function playAudio() {
  const card = state.cards[state.index];
  if (!card) return;
  $("spk-note").textContent = "Playing…";
  $("speaker").classList.add("speaker-on");
  try {
    const audio = new Audio(`/api/audio/${card.id}`);
    audio.volume = effectiveVolume();
    state.audio = audio;
    audio.onended = () => {
      $("spk-note").textContent = "Play";
      $("speaker").classList.remove("speaker-on");
    };
    await audio.play();
  } catch {
    $("spk-note").textContent = "Play";
    $("speaker").classList.remove("speaker-on");
  }
}

// ── transient toast ──────────────────────────────────────────────────────────

function toast(message) {
  const node = $("toast");
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => {
    node.hidden = true;
  }, 1200);
}

function toggleHelp() {
  $("help").hidden = !$("help").hidden;
}

// ── keyboard ─────────────────────────────────────────────────────────────────
//
// Every action is reachable without the mouse. ArrowUp/ArrowDown carry volume
// because the OS usually swallows the hardware media keys before the browser
// sees them; the media codes are mapped too, for the cases where it does not.

const KEYMAP = {
  Space: flip,
  Enter: flip,
  KeyJ: () => grade(true),
  KeyF: () => grade(false),
  ArrowRight: goNext,
  ArrowLeft: goPrevious,
  ArrowUp: () => changeVolume(VOLUME_STEP),
  ArrowDown: () => changeVolume(-VOLUME_STEP),
  KeyM: toggleMute,
  KeyP: playAudio,
  KeyR: playAudio,
  Escape: finish,
  Slash: toggleHelp,
  KeyH: toggleHelp,
  AudioVolumeUp: () => changeVolume(VOLUME_STEP),
  AudioVolumeDown: () => changeVolume(-VOLUME_STEP),
  AudioVolumeMute: toggleMute,
};

// Keys whose default browser behaviour would fight the app (page scroll,
// quick-find). Everything else is left alone.
const SWALLOW = new Set([
  "Space",
  "Enter",
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "Slash",
]);

document.addEventListener("keydown", (event) => {
  const handler = KEYMAP[event.code] || KEYMAP[event.key];
  if (!handler) return;
  if (SWALLOW.has(event.code)) event.preventDefault();
  handler();
});

// ── boot ─────────────────────────────────────────────────────────────────────

async function start() {
  const drill = params.get("characters");
  const body = drill
    ? { character_ids: drill.split(",").map(Number), challenge: "recognition", scoring: "accuracy" }
    : {
        difficulty: params.get("difficulty") || "hiragana:gojuon",
        challenge: params.get("challenge") || "recognition",
        scoring: params.get("scoring") || "accuracy",
      };
  try {
    const res = await post("/api/session", body);
    state.sessionId = res.session_id;
    state.cards = res.cards;
    state.scheme = res.scoring;
    $("breadcrumb").textContent = drill
      ? `Drill · ${res.cards.length} weak characters`
      : `${res.difficulty} · ${res.challenge}`;
    $("scheme-note").textContent = `scoring: ${res.scoring}`;
    render();
  } catch (err) {
    $("breadcrumb").textContent = `Could not start: ${err.message}`;
  }
}

$("card").addEventListener("click", flip);
$("flip").addEventListener("click", flip);
$("right").addEventListener("click", () => grade(true));
$("wrong").addEventListener("click", () => grade(false));
$("speaker").addEventListener("click", (event) => {
  event.stopPropagation();
  playAudio();
});
// Bind defensively: a template that drops an optional control must not stop
// the session from starting.
function on(id, event, handler, options) {
  const node = $(id);
  if (node) node.addEventListener(event, handler, options);
  else console.warn(`study: #${id} missing, control unavailable`);
}
on("help-open", "click", toggleHelp);
on("help-close", "click", toggleHelp);

start();
