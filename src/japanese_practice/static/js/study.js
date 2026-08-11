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
import { prefsReady, readPref, writePref } from "./prefs.js";
import { playCorrect, primeCue, soundEnabled } from "./sound.js";

// Preferences go through prefs.js, which keeps the authority in memory so a
// webview without working localStorage still honours what you set.
const storageGet = (key) => readPref(key);
const storageSet = (key, value) => writePref(key, value);

const REVEAL_CORRECT_MS = 1900;
const REVEAL_WRONG_MS = 2900;
const REVEAL_SKIP_MS = 250;

// Pace. The base holds above suit someone meeting a character for the first
// time; a learner who knows the deck wants it to move. Each step multiplies the
// verdict hold, so the fastest setting is roughly five times the pace of the
// slowest without ever dropping below what can be read.
const PACE_STEPS = [
  { name: "relaxed", factor: 1.0 },
  { name: "steady", factor: 0.7 },
  { name: "brisk", factor: 0.5 },
  { name: "fast", factor: 0.35 },
  { name: "relentless", factor: 0.2 },
];
const PACE_KEY = "jp.pace";

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
  pace: readPace(),
  audio: null,
  finished: false,
};

// localStorage is not guaranteed. Embedded webviews, private windows and
// restricted origins can all make it throw on access rather than return null,
// and this runs at module scope — an unguarded read takes the whole view down
// before the session ever starts. Preferences are a convenience; losing them
// must never cost the learner their study session.


function readVolume() {
  const raw = parseFloat(storageGet(VOLUME_KEY) ?? "1");
  return Number.isFinite(raw) ? Math.min(1, Math.max(0, raw)) : 1;
}

function readPace() {
  const raw = parseInt(storageGet(PACE_KEY) ?? "1", 10);
  return Number.isFinite(raw) && raw >= 1 && raw <= PACE_STEPS.length ? raw : 1;
}

function paceFactor() {
  return PACE_STEPS[state.pace - 1]?.factor ?? 1;
}

function applyPace(step, { announce = true } = {}) {
  state.pace = Math.min(PACE_STEPS.length, Math.max(1, step));
  storageSet(PACE_KEY, String(state.pace));
  const input = $("pace");
  if (input) input.value = String(state.pace);
  const name = $("pace-name");
  if (name) name.textContent = PACE_STEPS[state.pace - 1].name;
  if (announce) toast(`Pace: ${PACE_STEPS[state.pace - 1].name}`);
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

  // Every card back carries the same three registers in the same order —
  // glyph, sound, meaning — so a learner always knows where to look. Only the
  // *source* of the sound differs by script.
  //
  // The English used to appear on kanji cards alone, so a phrase card revealed
  // 見せてください / misete kudasai and never said it meant "please show me".
  // Flipping is the reveal; withholding the translation made the reveal
  // incomplete for the four scripts that need it most.
  const meaning = card.meaning && card.meaning !== card.romaji ? card.meaning : "";
  $("back-meaning").textContent = meaning;
  $("back-meaning").hidden = !meaning;

  if (card.script === "kanji") {
    // A kanji has no single romaji — it has readings, several of them, and they
    // carry their own transliteration below.
    $("back-sound").textContent = "";
    $("back-sound").hidden = true;
    // Readings carry their romaji: the options on a kanji card are English, so
    // the kana are reference material, and reference you cannot read is not.
    const krow = (label, kana, romaji) =>
      `<div class="krow"><em>${label}</em>` +
      `<span class="kread"><span class="jp">${kana}</span>` +
      (romaji ? `<span class="kroma">${romaji}</span>` : "") +
      `</span></div>`;
    const rows = [];
    if (card.onyomi) rows.push(krow("on", card.onyomi, card.onyomi_romaji));
    if (card.kunyomi) rows.push(krow("kun", card.kunyomi, card.kunyomi_romaji));
    $("back-readings").innerHTML = rows.join("");
  } else {
    $("back-sound").textContent = card.romaji || "";
    $("back-sound").hidden = !card.romaji;
    $("back-readings").innerHTML = "";
  }

  // Room scales with what is on the card. A kana answer is "kya"; a kanji answer
  // is "world/generation"; a word answer is "Wednesday" against a 月曜日 prompt,
  // which needs the most room of the three — on the card as well as the options.
  const isKanji = card.script === "kanji";
  const isWord = card.script === "vocab";
  const isPhrase = card.script === "phrase";

  // Card width is fixed for the whole session by sizeCardsForSession(); nothing
  // per-card, so the face does not resize between cards.
  $("choices").classList.toggle("wide", isKanji || isWord || isPhrase);
  $("choices").classList.toggle("wider", isWord || isPhrase);
  // theme-kanji is NOT set here. The accent belongs to the *exercise*, not the
  // card — toggling it per card made a mixed deck flash between palettes, and
  // left a kanji drill un-themed because the drill path has no kanji in its
  // difficulty key. It is applied once per session from the deck's script.
  document.body.classList.toggle("mode-word", isWord || isPhrase);
  document.body.classList.toggle("mode-phrase", isPhrase);

  // Some cards are unusable without their note: 強がり is not "a strong person"
  // but someone putting on a brave face. Shown on the back, under the meaning.
  const note = $("back-note");
  if (note) {
    note.textContent = card.note || "";
    note.hidden = !card.note;
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

  const readings = card.choice_readings || {};
  (card.choices || []).forEach((option, i) => {
    const button = el("button", "choice");
    button.type = "button";
    // The reading is reference, not the answer — a kanji option is English and
    // says nothing about how the character sounds without it.
    const reading = readings[option];
    button.innerHTML =
      `<span class="key">${i + 1}</span><span class="txt">${option}</span>` +
      (reading ? `<span class="opt-read">${reading}</span>` : "");
    button.setAttribute(
      "aria-label",
      reading ? `Option ${i + 1}: ${option}, read ${reading}` : `Option ${i + 1}: ${option}`
    );
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

  // Sounded before the network call, not after: this is feedback on the click,
  // and waiting for the attempt to be recorded would put it noticeably late.
  if (correct && !skipped) playCorrect();

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

  const base = skipped ? REVEAL_SKIP_MS : correct ? REVEAL_CORRECT_MS : REVEAL_WRONG_MS;
  // Floor at 260ms: below that the verdict colour is not perceivable, and the
  // point of the hold is that a wrong answer can be read.
  const hold = skipped ? base : Math.max(260, Math.round(base * paceFactor()));
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

  // The tiles are sized for the widest thing in *this* session, not for a single
  // character. 高い wrapped to two lines and "beautiful / clean" to two more,
  // inside a square built for あ — the same fault the study card had, in the one
  // place a learner reads every card at once.
  // Same rule as the card: one tile width for the whole grid, wide enough for
  // the longest item in it, with the type left alone.
  const longestGlyph = seen.reduce(
    (n, i) => Math.max(n, [...(state.outcomes.get(i).glyph || "")].length), 1);
  const longestAnswer = seen.reduce(
    (n, i) => Math.max(n, (state.outcomes.get(i).answer || "").length), 1);

  if (longestGlyph <= 2) {
    host.classList.remove("is-text");
    host.style.removeProperty("--tile-w");
  } else {
    const RECAP_GLYPH_PX = 26;
    const width = Math.min(
      360,
      Math.max(140, Math.ceil(Math.max(longestGlyph * RECAP_GLYPH_PX,
                                       longestAnswer * RECAP_GLYPH_PX * 0.46))) + 44
    );
    host.classList.add("is-text");
    host.style.setProperty("--tile-w", `${width}px`);
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

// Re-run the same exercise. `shuffle` makes the server deal a different order —
// without it a repeat is the same sequence, because after one session every card
// has a miss rate and the weakest-first sort is deterministic.
function practiceAgain() {
  const params = new URLSearchParams(location.search);
  params.set("shuffle", "1");
  location.href = `${location.pathname}?${params}`;
}

on("recap-again", "click", practiceAgain);

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
  if (!soundEnabled()) return 0;   // Settings master switch wins over M
  return state.muted ? 0 : state.volume;
}

// The inline slider mirrors state; the transient bar stays for the arrow keys,
// which give no other feedback.
function paintVolumeSlider() {
  const range = $("volume-range");
  const name = $("volume-name");
  const pct = state.muted ? 0 : Math.round(state.volume * 100);
  if (range) range.value = String(pct);
  if (name) name.textContent = state.muted ? "muted" : `${pct}%`;
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
  paintVolumeSlider();
  showVolume();
}

function paintVoice() {
  const label = $("voice-label");
  if (label) label.textContent = state.voice;
}

function toggleVoice() {
  state.voice = state.voice === "female" ? "male" : "female";
  storageSet(VOICE_KEY, state.voice);
  paintVoice();
  toast(`Voice: ${state.voice}`);
  playAudio();
}

function toggleMute() {
  state.muted = !state.muted;
  storageSet(MUTED_KEY, state.muted ? "1" : "0");
  paintVolumeSlider();
  if (state.audio) state.audio.volume = effectiveVolume();
  paintVolumeSlider();
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
  BracketLeft: () => applyPace(state.pace - 1),
  BracketRight: () => applyPace(state.pace + 1),
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

// ── card geometry ────────────────────────────────────────────────────────────
//
// One width for the whole session, wide enough for the *longest* prompt in it to
// sit on a single line at full size. Two rules drive this:
//
//   * **Do not shrink the type to fit.** A phrase set at 24px to avoid a wrap is
//     harder to read than the same phrase wrapped, and the point of the card is
//     to be read.
//   * **Do not resize between cards.** A face that changes width as you answer
//     is distracting, and the eye has to reacquire the prompt each time.
//
// So the width is computed once from the widest thing the session will show, and
// every card in that session uses it.

// The glyph size we refuse to go below, and roughly the width one CJK glyph
// occupies at it. Latin readings are far narrower, so the glyph count dominates.
const CARD_GLYPH_PX = 46;
const CARD_SIDE_PAD = 40;          // each side
const CARD_MAX_PX = 700;

// Height is the sum of the registers the back will show. Named separately so a
// new register is one constant plus one term, and so the reason for the number
// survives — a single opaque 372 could not say what it was paying for.
//
// Calibrated against the two heights that were known good: a text card with a
// reading and no note was 372 (BASE + SOUND) and with a note was 430
// (BASE + SOUND + NOTE). Those still come out identical; the meaning and
// readings terms are what is new.
const CARD_BASE_PX = 310;          // frame, glyph, speaker foot
const CARD_SOUND_PX = 62;          // the reading line
const CARD_MEANING_PX = 36;        // per wrapped line of English
const CARD_NOTE_PX = 58;           // the context note, when a set carries one
const CARD_READINGS_PX = 96;       // kanji's on/kun rows, which carry romaji too
const CARD_MEANING_CH = 30;        // the back's measure — must match .back-meaning

// Options follow the card's rule: one width for the session, wide enough for the
// longest answer it will offer. Sizing them by script instead meant every kanji
// deck got the same column whether its answers read "sun" or "world/generation",
// and every phrase deck the same whether they read "let's go" or "please speak
// slowly".
const OPTION_CHAR_PX = 8.4;        // a Latin character at the option's type size
const OPTION_SIDE_PAD = 44;

function sizeOptionsForSession() {
  const cards = state.cards || [];
  const longest = cards.reduce(
    (n, c) => Math.max(n, ...(c.choices || []).map((o) => String(o).length)),
    1
  );
  const width = Math.min(300, Math.max(96, Math.ceil(longest * OPTION_CHAR_PX) + OPTION_SIDE_PAD));
  const host = $("choices");
  if (host) host.style.setProperty("--option-w", `${width}px`);
  // Squares suit a three-letter romaji and nothing else.
  document.body.dataset.optionSize = longest <= 4 ? "tight" : "roomy";
}

function sizeCardsForSession() {
  const cards = state.cards || [];
  if (!cards.length) return;

  const longestGlyph = cards.reduce((n, c) => Math.max(n, [...(c.glyph || "")].length), 1);
  const longestAnswer = cards.reduce((n, c) => Math.max(n, (c.answer || "").length), 1);
  const anyNote = cards.some((c) => c.note);

  // A deck of single characters keeps the 5:7 playing-card face — it is 93% of
  // the content and the app's whole visual identity.
  if (longestGlyph <= 2 && !anyNote) {
    document.body.dataset.cardSize = "glyph";
    sizeOptionsForSession();
    return;
  }

  // Width: the longest prompt on one line, or the longest answer, whichever needs
  // more. The answer is Latin, so roughly half the width per character.
  const forGlyphs = longestGlyph * CARD_GLYPH_PX;
  const forAnswer = longestAnswer * (CARD_GLYPH_PX * 0.42);
  const width = Math.min(CARD_MAX_PX, Math.max(340, Math.ceil(Math.max(forGlyphs, forAnswer))) + CARD_SIDE_PAD * 2);

  // Height is built from the registers the back will actually show, rather than
  // guessed from whether a note exists. The English translation was added to
  // every back, not just kanji's, and a fixed 372px silently clipped it on the
  // phrase sets — where the meaning is the longest text on the card.
  //
  // Each term is a register: the glyph, the reading, the meaning, the note. A
  // register that will not render contributes nothing.
  const anyKanji = cards.some((c) => c.script === "kanji");
  const anyMeaning = cards.some((c) => c.meaning && c.meaning !== c.romaji);
  // A kanji card shows its readings instead of a single romaji line.
  const anySound = !anyKanji && cards.some((c) => c.romaji);
  // A meaning wraps at the back's measure, so a long one costs a line.
  const longestMeaning = cards.reduce((n, c) => Math.max(n, (c.meaning || "").length), 0);
  const meaningLines = Math.min(3, Math.ceil(longestMeaning / CARD_MEANING_CH)) || 0;
  const height =
    CARD_BASE_PX +
    (anySound ? CARD_SOUND_PX : 0) +
    (anyKanji ? CARD_READINGS_PX : 0) +
    (anyMeaning ? CARD_MEANING_PX * meaningLines : 0) +
    (anyNote ? CARD_NOTE_PX : 0);

  sizeOptionsForSession();

  document.body.dataset.cardSize = "text";
  document.body.style.setProperty("--card-w", `${width}px`);
  document.body.style.setProperty("--card-h", `${height}px`);
}

// ── boot ─────────────────────────────────────────────────────────────────────

async function start() {
  const drill = params.get("characters");
  // Set by "Practice again" — the server then deals a different order.
  const shuffle = params.get("shuffle") === "1";
  const body = drill
    ? {
        character_ids: drill.split(",").map(Number),
        challenge: "recognition",
        scoring: "accuracy",
        shuffle,
      }
    : {
        difficulty: params.get("difficulty") || "hiragana:gojuon",
        challenge: params.get("challenge") || "recognition",
        scoring: params.get("scoring") || "accuracy",
        shuffle,
      };
  try {
    const res = await post("/api/session", body);
    state.sessionId = res.session_id;
    state.cards = res.cards;
    state.scheme = res.scoring;
    sizeCardsForSession();
    // The deck's name, as it reads on the shelf. The raw key and the mode drop
    // to the sub-line beneath it.
    $("deck-title").textContent = drill
      ? `Drill — ${res.deck_title}`
      : res.deck_title || res.difficulty;
    $("breadcrumb").textContent = drill
      ? `Drill · ${res.cards.length} weak characters`
      : `${res.difficulty} · ${res.challenge}`;
    $("scheme-note").textContent = `scoring: ${res.scoring}`;
    // One decision, taken once, from the deck rather than the card in hand.
    document.body.classList.toggle("theme-kanji", res.script === "kanji");
    render();
  } catch (err) {
    $("deck-title").textContent = "Could not start";
    $("breadcrumb").textContent = `Could not start: ${err.message}`;
  }
}

$("card").addEventListener("click", flip);
$("flip").addEventListener("click", flip);
on("skip", "click", skipCard);
on("back", "click", goPrevious);
on("next", "click", goNext);
on("voice-toggle", "click", toggleVoice);
on("pace", "input", (event) => applyPace(Number(event.target.value), { announce: false }));
on("volume-range", "input", (event) => {
  state.volume = Number(event.target.value) / 100;
  // Dragging off zero is an unmute — leaving M set would make the slider look
  // broken, since it would move and nothing would sound.
  state.muted = state.volume === 0;
  storageSet(VOLUME_KEY, String(state.volume));
  storageSet(MUTED_KEY, state.muted ? "1" : "0");
  if (state.audio) state.audio.volume = effectiveVolume();
  paintVolumeSlider();
});
// Preview on release, not on every step of a drag.
on("volume-range", "change", () => {
  if (!state.muted) playCorrect();
});
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

// Preferences come from the server, so they are not known at module load. Adopt
// them before the first card is dealt — otherwise a pace, voice or cue chosen on
// the dashboard would not take effect until the second session.
prefsReady.then(() => {
  state.pace = readPace();
  state.volume = readVolume();
  state.muted = readMuted();
  state.voice = readPref("jp.voice") === "male" ? "male" : "female";
  applyPace(state.pace, { announce: false });
  paintVoice();
  paintVolumeSlider();
  primeCue();
  start();
});
