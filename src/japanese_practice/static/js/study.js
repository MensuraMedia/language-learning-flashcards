// Study view: one glyph at a time, true 3D flip, self-graded.
// The front face renders the glyph and nothing else — that is the whole point.

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);

const state = {
  sessionId: null,
  cards: [],
  index: 0,
  streak: 0,
  score: 0,
  flipped: false,
  shownAt: 0,
  scheme: "accuracy",
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

async function grade(correct) {
  const card = state.cards[state.index];
  if (!card) return;
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
  state.index += 1;
  render();
}

async function finish() {
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

async function playAudio() {
  const card = state.cards[state.index];
  if (!card) return;
  $("spk-note").textContent = "Playing…";
  $("speaker").classList.add("speaker-on");
  try {
    const audio = new Audio(`/api/audio/${card.id}`);
    await audio.play();
    audio.onended = () => {
      $("spk-note").textContent = "Play";
      $("speaker").classList.remove("speaker-on");
    };
  } catch {
    $("spk-note").textContent = "Play";
    $("speaker").classList.remove("speaker-on");
  }
}

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
$("speaker").addEventListener("click", (e) => {
  e.stopPropagation();
  playAudio();
});

document.addEventListener("keydown", (e) => {
  if (e.code === "Space") {
    e.preventDefault();
    flip();
  } else if (e.key === "j" || e.key === "J") {
    grade(true);
  } else if (e.key === "f" || e.key === "F") {
    grade(false);
  } else if (e.key === "Escape") {
    finish();
  }
});

start();
