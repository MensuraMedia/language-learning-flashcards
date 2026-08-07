// Study view: one glyph at a time, true 3D flip, self-graded.
// The front face renders the glyph and nothing else — that is the whole point.
//
// Keyboard is a first-class input, not an accessory: a learner drilling 100
// cards should never need the mouse. See KEYMAP below and the help overlay (?).

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);

// Small DOM helper. study.js is a standalone module — it cannot borrow
// dashboard.js's helpers, which is exactly the bug this replaces.
const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};

// How long the verdict stays on screen before the next card. A correct answer
// needs a beat to register; a wrong one needs longer, because that is the moment
// the learner actually studies the option they should have picked.
const REVEAL_CORRECT_MS = 1900;
const REVEAL_WRONG_MS = 2900;
const REVEAL_SKIP_MS = 250;

const VOLUME_STEP = 0.1;
const VOLUME_KEY = "jp.volume";
const MUTED_KEY = "jp.muted";
const VOICE_KEY = "jp.voice";

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
  outcomes: new Map(),   // index -> {glyph, answer, correct, skipped}
  furthest: 0,           // deepest card reached; Next is live only behind it
  advanceTimer: null,    // pending auto-advance, cancelled by manual navigation
  locked: false,
  volume: readVolume(),
  muted: readMuted(),
  voice: storageGet("jp.voice") === "male" ? "male" : "female",
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

  state.furthest = Math.max(state.furthest, state.index);
  renderChoices(card);
  updateNavPair();
  $("counter").textContent = `${state.index + 1} / ${state.cards.length}`;
  state.shownAt = performance.now();
}

// ── multiple choice ──────────────────────────────────────────────────────────
// The deck arrives with its options already shuffled by the server, so the
// correct answer is never in a predictable slot.

function renderChoices(card) {
  const host = $("choices");
  host.innerHTML = "";
  state.locked = state.graded.has(state.index);

  (card.choices || []).forEach((option, i) => {
    const button = el("button", "choice");
    button.type = "button";
    button.innerHTML = `<span class="key">${i + 1}</span><span class="txt">${option}</span>`;
    button.setAttribute("aria-label", `Option ${i + 1}: ${option}`);
    if (state.locked) button.disabled = true;
    button.addEventListener("click", () => choose(i));
    host.appendChild(button);
  });
}

function choose(index) {
  if (state.locked) return;
  const card = state.cards[state.index];
  const option = (card.choices || [])[index];
  if (option === undefined) return;

  state.locked = true;
  const correct = option === card.answer;
  const buttons = [...$("choices").children];

  buttons.forEach((b, i) => {
    b.disabled = true;
    const value = card.choices[i];
    if (value === card.answer) b.classList.add("is-right");
    else if (i === index) b.classList.add("is-wrong");
    else b.classList.add("is-muted");
  });

  // Show the reading behind the glyph so a wrong answer still teaches.
  if (!state.flipped) flip();

  grade(correct, { given: correct ? null : option });
}

function flip() {
  state.flipped = !state.flipped;
  $("card").classList.toggle("flipped", state.flipped);
}

// ── navigation ───────────────────────────────────────────────────────────────

// A pending auto-advance must never override a deliberate move. Without this,
// pressing Back during the reveal hold gets yanked forward when the timer
// fires — and the longer holds make that window several seconds wide.
function cancelPendingAdvance() {
  if (state.advanceTimer !== null) {
    clearTimeout(state.advanceTimer);
    state.advanceTimer = null;
  }
}

function goPrevious() {
  cancelPendingAdvance();
  if (state.index === 0) return toast("First card");
  state.index -= 1;
  render();
}

// Next is navigation, not an answer: it only returns you to where you already
// were. That is why it costs nothing and why Skip is not the way back — Skip
// means "I don't know this card", which is a different statement entirely.
function updateNavPair() {
  const next = $("next");
  if (!next) return;
  const canReturn = state.index < state.furthest;
  next.disabled = !canReturn;
  next.setAttribute("aria-disabled", String(!canReturn));
  next.title = canReturn ? "Return to where you were" : "Available after going back";

  const back = $("back");
  if (back) back.disabled = state.index === 0;
}

function goNext() {
  cancelPendingAdvance();
  // Returning forward after going back is free — the cards in between are
  // already answered and nothing is being escaped.
  //
  // Advancing PAST the frontier is a different act: it would leave an unanswered
  // card behind with no record, which strictly dominated the Skip button (same
  // escape, no penalty, streak preserved). So that is refused, and Skip is the
  // honest way to pass on a card you do not know.
  if (state.index >= state.furthest) {
    if (!state.graded.has(state.index)) {
      return toast("Answer it, or press S for don't know");
    }
    if (state.index >= state.cards.length - 1) return toast("Last card");
  }
  state.index = Math.min(state.index + 1, state.cards.length - 1);
  render();
}

// ── grading ──────────────────────────────────────────────────────────────────

async function grade(correct, { given = null, skipped = false } = {}) {
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
      skipped,
      latency_ms: latency,
      streak: state.streak,
      // The option actually chosen is what feeds the confusion-pair panel —
      // a real answer, not a guess at what the learner might have meant.
      given_answer: given,
    });
    state.streak = res.streak;
    state.score = res.score;
    $("score").textContent = res.score;
    $("streak").textContent = res.streak;
    if (skipped) toast("Skipped · −1");
  } catch (err) {
    console.error("attempt failed", err);
  }
  state.outcomes.set(state.index, {
    glyph: card.glyph,
    answer: card.answer,
    correct: Boolean(correct),
    skipped: Boolean(skipped),
  });

  const hold = skipped ? REVEAL_SKIP_MS : correct ? REVEAL_CORRECT_MS : REVEAL_WRONG_MS;
  state.advanceTimer = setTimeout(advanceAfterGrade, hold);
}

function advanceAfterGrade() {
  state.advanceTimer = null;
  if (state.index >= state.cards.length - 1) return finish();
  state.index += 1;
  render();
}

async function finish() {
  if (state.finished) return;
  cancelPendingAdvance();
  state.finished = true;
  let record = {};
  try {
    record = await post(`/api/session/${state.sessionId}/end`, {});
  } catch (err) {
    console.error(err);
  }
  const total = record.total ?? 0;
  const acc = total ? Math.round((record.correct / total) * 100) : 0;
  const score = record.score ?? state.score;
  const streak = record.max_streak ?? 0;

  // Score and streak are only meaningful against what was achievable, so grade
  // them as a proportion rather than against an absolute that varies by scheme
  // and deck length.
  const scoreCeiling = total * 10;
  $("recap-grid").innerHTML = `
    <div class="kv"><span class="lbl-sm">Score</span>
      <b class="num ${rateClass(scoreCeiling ? score / scoreCeiling : 0)}">${score}</b></div>
    <div class="kv"><span class="lbl-sm">Accuracy</span>
      <b class="num ${rateClass(acc / 100)}">${acc}%</b></div>
    <div class="kv"><span class="lbl-sm">Cards</span><b class="num">${total}</b></div>
    <div class="kv"><span class="lbl-sm">Best streak</span>
      <b class="num ${rateClass(total ? streak / total : 0)}">${streak}</b></div>`;

  renderRecapCards();
  $("recap").hidden = false;
}

// Green above 85%, amber 60-85%, red below. The thresholds match the mastery
// rule elsewhere in the app (miss_rate <= 0.15), so a green session and a
// mastered character mean the same standard.
function rateClass(ratio) {
  if (ratio >= 0.85) return "rate-good";
  if (ratio >= 0.6) return "rate-mid";
  return "rate-poor";
}

// Every card the session covered, in the order it was seen. Misses are red so
// the set to re-drill is readable at a glance rather than needing the dashboard.
function renderRecapCards() {
  const host = $("recap-cards");
  if (!host) return;
  host.innerHTML = "";

  const seen = [...state.outcomes.keys()].sort((a, b) => a - b);
  if (!seen.length) {
    $("recap-cards-note").textContent = "";
    return;
  }

  seen.forEach((index) => {
    const o = state.outcomes.get(index);
    const tile = el("div", "recap-card-tile" + (o.correct ? "" : " is-wrong"));
    tile.innerHTML =
      `<span class="rc-glyph jp">${o.glyph}</span>` +
      `<span class="rc-reading">${o.answer ?? ""}</span>`;
    tile.title = o.skipped
      ? `${o.glyph} — skipped`
      : `${o.glyph} — ${o.correct ? "correct" : "wrong"}`;
    host.appendChild(tile);
  });

  const missed = seen.filter((i) => !state.outcomes.get(i).correct).length;
  $("recap-cards-note").textContent = missed
    ? `${missed} of ${seen.length} to revisit`
    : `all ${seen.length} correct`;
}

function skipCard() {
  if (state.locked) return advanceAfterGrade();
  state.locked = true;
  [...$("choices").children].forEach((b) => {
    b.disabled = true;
    b.classList.add("is-muted");
  });
  grade(false, { skipped: true });
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

function toggleVoice() {
  state.voice = state.voice === "female" ? "male" : "female";
  storageSet(VOICE_KEY, state.voice);
  const label = $("voice-label");
  if (label) label.textContent = state.voice;
  toast(`Voice: ${state.voice}`);
  playAudio();
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
  $("speaker").classList.add("speaker-on");
  try {
    const audio = new Audio(`/api/audio/${card.id}?voice=${state.voice}`);
    audio.volume = effectiveVolume();
    state.audio = audio;
    audio.onended = () => {
          $("speaker").classList.remove("speaker-on");
    };
    await audio.play();
  } catch {
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
  Digit1: () => choose(0),
  Digit2: () => choose(1),
  Digit3: () => choose(2),
  Numpad1: () => choose(0),
  Numpad2: () => choose(1),
  Numpad3: () => choose(2),
  KeyS: skipCard,
  ArrowRight: goNext,
  ArrowLeft: goPrevious,
  ArrowUp: () => changeVolume(VOLUME_STEP),
  ArrowDown: () => changeVolume(-VOLUME_STEP),
  KeyM: toggleMute,
  KeyV: toggleVoice,
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
on("skip", "click", skipCard);
on("back", "click", goPrevious);
on("next", "click", goNext);
on("voice-toggle", "click", toggleVoice);
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
