// Memory-training boards: Match Up, Pelmanism, Confusion Drill.
//
// One engine, three presentations. The board is seeded from the learner's
// weakest characters — a generic memory game with kana on it trains spatial
// memory; a board built from what you keep missing trains the failure.

import { playCorrect, primeCue } from "./sound.js";

const $ = (id) => document.getElementById(id);
const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};

const MISMATCH_HOLD_MS = 900;   // long enough to read the wrong pair

// Deep-linked from the dashboard game cards: /games?mode=pelmanism&script=kanji
const params = new URLSearchParams(location.search);
const requestedMode = params.get("mode");
const requestedScript = params.get("script");

const state = {
  mode: ["matchup", "pelmanism", "confusion"].includes(requestedMode) ? requestedMode : "matchup",
  script: ["hiragana", "katakana", "kanji"].includes(requestedScript) ? requestedScript : "hiragana",
  pairs: 6,
  tiles: [],
  selected: [],      // indices awaiting resolution
  matched: new Set(), // pair_ids cleared
  moves: 0,
  mismatches: 0,
  startedAt: 0,
  timer: null,
  locked: false,
};

async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).message || res.statusText);
  return res.json();
}

// ── clock ────────────────────────────────────────────────────────────────────

function startClock() {
  stopClock();
  state.startedAt = Date.now();
  state.timer = setInterval(() => {
    const s = Math.floor((Date.now() - state.startedAt) / 1000);
    $("g-time").textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  }, 500);
}

function stopClock() {
  if (state.timer !== null) {
    clearInterval(state.timer);
    state.timer = null;
  }
}

// ── board ────────────────────────────────────────────────────────────────────

async function deal() {
  stopClock();
  $("game-done").hidden = true;
  state.selected = [];
  state.matched = new Set();
  state.moves = 0;
  state.mismatches = 0;
  state.locked = false;
  $("g-moves").textContent = "0";
  $("g-time").textContent = "0:00";

  try {
    const board = await post("/api/game/board", {
      mode: state.mode,
      pairs: state.pairs,
      script: state.script,
    });
    state.tiles = board.tiles;
    $("g-pairs").textContent = board.pairs;
    $("g-source").textContent =
      board.source === "weakest"
        ? "built from your weakest characters"
        : board.source === "confusion-pairs"
          ? "built from known look-alike pairs"
          : board.source === "weakest+pool"
            ? "your weak characters, topped up from the deck"
            : "from the deck — study a little and these become your weak set";
    renderBoard(board.face_down);
    startClock();
  } catch (err) {
    $("board").innerHTML = `<p class="muted">Could not deal a board: ${err.message}</p>`;
  }
}

// Columns come in groups of three, and the board stays as square as that
// allows. A long horizontal strip is the worst possible shape for a memory
// game: position is the thing being remembered.
function columnsFor(tileCount) {
  // Try each multiple of three and keep the one whose grid is closest to
  // square. Ties go wider, which suits a landscape window.
  let best = 3;
  let bestDiff = Infinity;
  for (let cols = 3; cols <= 12; cols += 3) {
    const rows = Math.ceil(tileCount / cols);
    const diff = Math.abs(rows - cols);
    if (diff <= bestDiff) {
      bestDiff = diff;
      best = cols;
    }
  }
  return best;
}

function renderBoard(faceDown) {
  const host = $("board");
  host.innerHTML = "";
  host.classList.toggle("is-facedown", Boolean(faceDown));
  host.style.setProperty("--board-cols", String(columnsFor(state.tiles.length)));

  state.tiles.forEach((tile, index) => {
    const node = el("button", "tile" + (faceDown ? " is-hidden" : ""));
    node.type = "button";
    node.dataset.index = String(index);
    // Kanji boards pair a glyph with a meaning, and meanings are phrases —
    // "interval, between" does not fit at the size "kya" is set in.
    const long = tile.text.length > 9 ? " is-verylong" : tile.text.length > 5 ? " is-long" : "";
    const faceClass = tile.kind === "glyph" ? "tile-glyph jp" : `tile-reading${long}`;
    node.innerHTML =
      `<span class="tile-face">` +
      `<span class="${faceClass}">${tile.text}</span>` +
      `</span><span class="tile-back"></span>`;
    node.setAttribute(
      "aria-label",
      faceDown ? "Hidden tile" : `${tile.kind === "glyph" ? "Character" : "Reading"} ${tile.text}`
    );
    node.addEventListener("click", () => pick(index));
    host.appendChild(node);
  });
}

function tileNode(index) {
  return $("board").querySelector(`[data-index="${index}"]`);
}

// ── the loop ─────────────────────────────────────────────────────────────────

function pick(index) {
  if (state.locked) return;
  const tile = state.tiles[index];
  if (!tile || state.matched.has(tile.pair_id)) return;
  if (state.selected.includes(index)) return;

  const node = tileNode(index);
  node.classList.add("is-open");
  node.classList.remove("is-hidden");
  state.selected.push(index);

  if (state.selected.length < 2) return;

  state.moves += 1;
  $("g-moves").textContent = String(state.moves);

  const [a, b] = state.selected;
  const ta = state.tiles[a];
  const tb = state.tiles[b];

  // A pair is a glyph and its own reading — never two glyphs, never two readings.
  const isPair = ta.pair_id === tb.pair_id && ta.kind !== tb.kind;

  if (isPair) {
    // A correct pairing is a correct choice, so it gets the same cue the study
    // card does — the feedback should not depend on which view you are in.
    playCorrect();
    state.matched.add(ta.pair_id);
    [a, b].forEach((i) => tileNode(i).classList.add("is-matched"));
    state.selected = [];
    if (state.matched.size * 2 >= state.tiles.length) finish();
    return;
  }

  // Wrong. Record it as confusion data — a mis-pairing is an unambiguous
  // "I think this character reads as that", better evidence than a card guess.
  state.mismatches += 1;
  reportMispair(ta, tb);

  state.locked = true;
  [a, b].forEach((i) => tileNode(i).classList.add("is-wrong"));
  setTimeout(() => {
    [a, b].forEach((i) => {
      const n = tileNode(i);
      n.classList.remove("is-wrong", "is-open");
      if ($("board").classList.contains("is-facedown")) n.classList.add("is-hidden");
    });
    state.selected = [];
    state.locked = false;
  }, MISMATCH_HOLD_MS);
}

async function reportMispair(a, b) {
  // Attribute the error to the glyph, with the reading actually chosen.
  const glyph = a.kind === "glyph" ? a : b;
  const reading = a.kind === "reading" ? a : b;
  if (!glyph || !reading) return;
  try {
    await post("/api/game/mispair", {
      character_id: glyph.character_id,
      given_answer: reading.text,
    });
  } catch {
    /* recording is best-effort; it must never interrupt play */
  }
}

function finish() {
  stopClock();
  const seconds = Math.floor((Date.now() - state.startedAt) / 1000);
  const perfect = state.tiles.length / 2;
  const accuracy = state.moves ? Math.round((perfect / state.moves) * 100) : 0;

  $("done-stats").innerHTML = `
    <div class="kv"><span class="lbl-sm">Time</span><b class="num">${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}</b></div>
    <div class="kv"><span class="lbl-sm">Moves</span><b class="num">${state.moves}</b></div>
    <div class="kv"><span class="lbl-sm">Perfect</span><b class="num">${perfect}</b></div>
    <div class="kv"><span class="lbl-sm">Efficiency</span><b class="num ${rate(accuracy / 100)}">${accuracy}%</b></div>`;
  $("game-done").hidden = false;
}

function rate(r) {
  if (r >= 0.85) return "rate-good";
  if (r >= 0.6) return "rate-mid";
  return "rate-poor";
}

// ── controls ─────────────────────────────────────────────────────────────────

// What a board pairs and which look-alikes it stacks both depend on the script,
// so the mode descriptions are rewritten whenever the script changes.
const SCRIPT_COPY = {
  hiragana: { cue: "reading", confusables: "あ/お, ぬ/め, る/ろ" },
  katakana: { cue: "reading", confusables: "シ/ツ, ソ/ン, ク/ワ" },
  kanji: { cue: "meaning", confusables: "人/入, 大/犬, 問/門" },
};

function applyScriptCopy() {
  const c = SCRIPT_COPY[state.script];
  document.body.classList.toggle("theme-kanji", state.script === "kanji");
  const matchup = $("desc-matchup");
  const confusion = $("desc-confusion");
  if (matchup) matchup.textContent = `All face up — pair each character with its ${c.cue}`;
  if (confusion) confusion.textContent = `Deliberately full of look-alikes — ${c.confusables}`;
}

$("script-picker").addEventListener("click", (event) => {
  const btn = event.target.closest("[data-script]");
  if (!btn) return;
  state.script = btn.dataset.script;
  [...$("script-picker").children].forEach((b) => b.classList.toggle("is-on", b === btn));
  applyScriptCopy();
  deal();
});

// Reflect a deep-linked script in the picker before the first deal.
[...$("script-picker").children].forEach((b) =>
  b.classList.toggle("is-on", b.dataset.script === state.script)
);
applyScriptCopy();
primeCue();

$("mode-picker").addEventListener("click", (event) => {
  const btn = event.target.closest("[data-mode]");
  if (!btn) return;
  state.mode = btn.dataset.mode;
  [...$("mode-picker").children].forEach((b) => b.classList.toggle("is-on", b === btn));
  deal();
});

// Reflect a deep-linked mode in the picker before the first deal. This sat
// inside the click handler above, so arriving from a dashboard game card dealt
// the right board while the picker still highlighted Match Up.
[...$("mode-picker").children].forEach((b) =>
  b.classList.toggle("is-on", b.dataset.mode === state.mode)
);

$("pair-picker").addEventListener("click", (event) => {
  const btn = event.target.closest("[data-pairs]");
  if (!btn) return;
  state.pairs = Number(btn.dataset.pairs);
  [...$("pair-picker").children].forEach((b) => b.classList.toggle("is-on", b === btn));
  deal();
});

$("deal").addEventListener("click", deal);
$("again").addEventListener("click", deal);

document.addEventListener("keydown", (event) => {
  if (event.key === "d" || event.key === "D") deal();
  else if (event.key === "Escape") location.href = "/";
});

deal();
