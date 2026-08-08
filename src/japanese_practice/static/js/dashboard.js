// Dashboard: renders the full analytics surface from /api/summary.
// Charts are inline SVG built here — no library, no external request.

import { playCorrect, setSoundEnabled, soundEnabled } from "./sound.js";

const $ = (id) => document.getElementById(id);
const pct = (v) => `${Math.round((v || 0) * 100)}%`;
const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};

const SVG = "http://www.w3.org/2000/svg";
function svg(w, h) {
  const s = document.createElementNS(SVG, "svg");
  s.setAttribute("viewBox", `0 0 ${w} ${h}`);
  s.setAttribute("preserveAspectRatio", "none");
  s.style.width = "100%";
  s.style.height = `${h}px`;
  return s;
}
function node(name, attrs) {
  const n = document.createElementNS(SVG, name);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
}

// ── deck shelves ────────────────────────────────────────────────────────────
// A deck is a physical object: fanned sheets, a rung badge, a glyph preview,
// and an obi band that doubles as its mastery meter. Everything on it is real
// data — the preview glyphs are the deck's first three characters, and the
// meter is the same mastery rule the analytics use.

function deckNode(deck) {
  const pct = deck.count ? Math.round((deck.mastered / deck.count) * 100) : 0;
  const node = el("button", "deck");
  node.type = "button";
  node.setAttribute(
    "aria-label",
    `${deck.label} — ${deck.challenge}, ${deck.scoring} scoring, ${deck.count} cards, ${pct}% mastered`
  );
  node.innerHTML = `
    <span class="sheet s3"></span>
    <span class="sheet s2"></span>
    <span class="deck-face">
      <span class="deck-top">
        <span class="rung">${deck.rung}</span>
        <span class="deck-count">${deck.count}</span>
      </span>
      <span class="deck-glyphs jp">${deck.glyphs.map((g) => `<span>${g}</span>`).join("")}</span>
      <span class="deck-id">
        <span class="deck-name" style="display:block">${deck.label}</span>
        <span class="deck-jp jp" style="display:block">${deck.jp}</span>
      </span>
      <span class="obi" style="display:block">
        <span class="obi-row" style="display:flex"><span class="lbl">Mastered</span><b>${pct}%</b></span>
        <span class="track" style="display:block"><span class="fill" style="display:block;width:${pct}%"></span></span>
        <span class="obi-sub" style="display:flex">
          <span>${deck.mastered} / ${deck.count}</span><span>acc ${pct2(deck.accuracy)}</span>
        </span>
      </span>
      <span class="deck-tags" style="display:flex">
        <span class="tag">${deck.challenge}</span>
        <span class="tag sc">${deck.scoring}</span>
      </span>
    </span>`;
  const go = () => {
    location.href =
      `/study?difficulty=${encodeURIComponent(deck.key)}` +
      `&challenge=${deck.challenge}&scoring=${deck.scoring}`;
  };
  node.addEventListener("click", go);
  return node;
}

function renderShelves(decks) {
  for (const shelf of ["hiragana", "katakana", "jlpt", "vol"]) {
    const host = $(`shelf-${shelf}`);
    if (!host) continue;
    host.innerHTML = "";
    const mine = decks.filter((d) => d.shelf === shelf);
    mine.forEach((d) => host.appendChild(deckNode(d)));
    // Hide a shelf with nothing on it rather than leaving an empty rail.
    if (!mine.length) {
      host.hidden = true;
      const heading = host.previousElementSibling;
      if (heading && heading.classList.contains("sec")) heading.hidden = true;
    }
  }
}

// ── headline instrument row ─────────────────────────────────────────────────

const pct2 = (v) => `${Math.round((v || 0) * 100)}%`;

function renderStats(totals, fve, trend, decks) {
  const inPlay = decks.filter((d) => d.mastered > 0).length;
  const avgSeconds = (totals.avg_latency_ms || 0) / 1000;
  // Six tiles, matching the approved design's instrument row.
  const tiles = [
    { l: "Sessions run", v: totals.sessions ?? 0, s: `score ${totals.score ?? 0}` },
    { l: "Cards reviewed", v: totals.attempts ?? 0, s: "all time" },
    { l: "Overall accuracy", v: pct2(totals.accuracy), s: `first-attempt ${pct2(fve.first_attempt_accuracy)}` },
    { l: "Best streak", v: totals.best_streak ?? 0, u: "consecutive", s: "personal best" },
    { l: "Avg response", v: avgSeconds ? avgSeconds.toFixed(1) : "—", u: avgSeconds ? "s" : "", s: "per card" },
    { l: "Decks in play", v: `${inPlay}`, s: `${decks.length} available` },
  ];
  const host = $("stats");
  host.innerHTML = "";
  tiles.forEach((t) => {
    const n = el("div", "stat");
    n.innerHTML =
      `<div class="lbl">${t.l}</div>` +
      `<div class="v">${t.v}${t.u ? `<small>${t.u}</small>` : ""}</div>` +
      `<div class="sub"><span>${t.s}</span></div>`;
    host.appendChild(n);
  });

  // Sparkline of the accuracy trend, dropped into the accuracy tile — the
  // number says where you are, the line says which way you are going.
  if (trend.length > 1) {
    const sub = host.children[2].querySelector(".sub");
    const s = svg(68, 18);
    s.style.width = "68px";
    s.style.height = "18px";
    s.style.marginLeft = "auto";
    const xs = (i) => (i * 66) / (trend.length - 1) + 1;
    const ys = (v) => 16.5 - v * 15;
    s.appendChild(
      node("path", {
        d: trend.map((r, i) => `${i ? "L" : "M"}${xs(i)},${ys(r.accuracy)}`).join(" "),
        fill: "none",
        stroke: "#f0b429",
        "stroke-width": 1.4,
        "stroke-linejoin": "round",
        "stroke-linecap": "round",
      })
    );
    sub.appendChild(s);
  }
}

// ── memory-training cards ───────────────────────────────────────────────────
// Deliberately a different object from a study deck. A deck is a stack of cards
// with a mastery meter; a game is a board. So these are landscape, show a
// miniature of the board they will deal, and report what they train rather than
// how far through you are — because none of them are scored.

function gameCard(game) {
  const node = el("a", `game-card motif-${game.motif}`);
  node.href =
    `/games?mode=${encodeURIComponent(game.mode)}` +
    `&script=${encodeURIComponent(game.script)}`;
  node.setAttribute("aria-label", `${game.name} — ${game.detail}`);

  // A miniature of the board. Real characters, so the card previews what it
  // will actually deal rather than showing decoration.
  const cells = [];
  for (let i = 0; i < 6; i += 1) {
    const glyph = game.preview[i % Math.max(game.preview.length, 1)];
    const hidden = game.motif === "hidden" && i % 2 === 1;
    cells.push(
      `<span class="mini-tile${hidden ? " is-covered" : ""}">${hidden ? "" : (glyph ?? "")}</span>`
    );
  }

  node.innerHTML = `
    <span class="game-mini">${cells.join("")}</span>
    <span class="game-body">
      <span class="game-name">${game.name}</span>
      <span class="game-jp jp">${game.jp}</span>
      <span class="game-trains">${game.trains}</span>
    </span>
    <span class="game-foot">
      <span class="tag">unscored</span>
      <span class="game-go">Play →</span>
    </span>`;
  return node;
}

async function renderGames() {
  // Each script's boards sit directly under that script's decks, so a learner
  // sees the drill and the game for what they are working on in one place.
  const rails = ["hiragana", "katakana", "kanji"]
    .map((script) => [script, $(`games-${script}`)])
    .filter(([, host]) => host);
  if (!rails.length) return;
  try {
    const payload = await fetch("/api/games").then((r) => r.json());
    const games = payload.games || [];
    for (const [script, host] of rails) {
      host.innerHTML = "";
      const mine = games.filter((g) => g.script === script);
      mine.forEach((g) => host.appendChild(gameCard(g)));
      host.hidden = !mine.length;
    }
  } catch {
    for (const [, host] of rails) host.innerHTML = `<p class="muted">Games unavailable.</p>`;
  }
}

// ── session history ─────────────────────────────────────────────────────────

function renderHistory(rows) {
  const table = $("history");
  if (!rows.length) {
    table.innerHTML = `<tbody><tr><td class="muted">No sessions recorded yet.</td></tr></tbody>`;
    return;
  }
  const head =
    "<thead><tr>" +
    ["Date", "Deck", "Challenge", "Scoring", "Cards", "Accuracy", "Avg", "Streak", "Score"]
      .map((h) => `<td class="lbl-sm">${h}</td>`)
      .join("") +
    "</tr></thead>";
  const body = rows
    .map(
      (r) =>
        "<tr>" +
        `<td class="num">${r.started_at.slice(0, 10)}</td>` +
        `<td>${r.difficulty}</td>` +
        `<td><span class="tag">${r.challenge}</span></td>` +
        `<td><span class="tag sc">${r.scoring}</span></td>` +
        `<td class="num">${r.total}</td>` +
        `<td class="num">${pct2(r.accuracy)}</td>` +
        `<td class="num">${r.avg_latency_ms ? (r.avg_latency_ms / 1000).toFixed(1) + "s" : "—"}</td>` +
        `<td class="num">${r.max_streak}</td>` +
        `<td class="num">${r.score}</td>` +
        "</tr>"
    )
    .join("");
  table.innerHTML = head + `<tbody>${body}</tbody>`;
  $("history-note").textContent = `${rows.length} most recent`;
}

// ── accuracy by set ─────────────────────────────────────────────────────────

function renderBySet(decks) {
  const box = $("by-set");
  box.innerHTML = "";
  const played = decks.filter((d) => d.mastered > 0 || d.accuracy > 0);
  if (!played.length) {
    box.appendChild(el("p", "muted", "No deck has been studied yet."));
    return;
  }
  played.forEach((d) => {
    box.appendChild(
      el(
        "div",
        "bar-row",
        `<span class="bar-name">${d.label} <em>${d.count}</em></span>
         <span class="bar-t"><i class="bar-f" style="width:${(d.accuracy * 100).toFixed(0)}%"></i></span>
         <b class="bar-val">${pct2(d.accuracy)}</b>`
      )
    );
  });
}

// ── per-character miss-rate heatmap (the headline panel) ─────────────────────
//
// A map of a *set*, not of your attempt log: every character in the chosen set
// is on it, including ones never seen. An untouched cell is the most actionable
// thing the panel can show, and a grid drawn from attempts alone hides them.

// Sets worth mapping. The kanji levels run to several hundred characters, which
// the grid scrolls rather than truncates — a truncated map lies about coverage.
const HM_SETS = [
  { key: "hiragana:all", label: "Hiragana" },
  { key: "katakana:all", label: "Katakana" },
  { key: "kanji:N5", label: "Kanji N5" },
  { key: "kanji:N4", label: "N4" },
  { key: "kanji:N3", label: "N3" },
  { key: "kanji:N2", label: "N2" },
  { key: "kanji:N1", label: "N1" },
  { key: "kanji:top200", label: "Top 200" },
];

// Miss rate is clamped at 30% for colour. Above that a character is simply
// failing; below it is where the differences a learner can act on live, and a
// 0–100% ramp flattens all of them into the same dim amber.
const HM_CEILING = 0.3;

const hmState = { key: "hiragana:all", table: false, data: null };

const hmTint = (rate) => {
  if (rate == null) return "transparent";
  const t = Math.min(rate / HM_CEILING, 1);
  return `rgba(var(--amber-rgb),${(t * 0.92 + 0.08).toFixed(3)})`;
};

function hmCell(r) {
  const cell = el("button", `hm-cell${r.seen ? "" : " is-unseen"}`);
  cell.type = "button";
  cell.textContent = r.glyph;
  cell.style.background = hmTint(r.miss_rate);
  if (r.miss_rate != null && r.miss_rate / HM_CEILING > 0.55) cell.style.color = "#0d0d0f";
  cell.title = r.seen
    ? `${r.glyph} — seen ${r.seen}, missed ${r.missed} (${pct(r.miss_rate)})`
    : `${r.glyph} — not yet seen`;
  cell.setAttribute("aria-label", cell.title);
  cell.addEventListener("click", () => {
    location.href = `/study?characters=${r.character_id}`;
  });
  return cell;
}

function hmTable(rows) {
  const body = rows
    .slice()
    // Worst first, then most-seen: the table is a work list, not a census.
    .sort((a, b) => (b.miss_rate ?? -1) - (a.miss_rate ?? -1) || b.seen - a.seen)
    .map(
      (r) => `<tr>
        <td class="jp hm-t-glyph">${r.glyph}</td>
        <td class="muted">${r.romaji || r.meaning || ""}</td>
        <td class="num">${r.seen || "—"}</td>
        <td class="num">${r.seen ? r.missed : "—"}</td>
        <td class="num">${r.miss_rate == null ? "—" : pct(r.miss_rate)}</td>
      </tr>`
    )
    .join("");
  return `<table class="hm-table">
      <thead><tr><th>Character</th><th>Reading</th><th class="num">Seen</th>
      <th class="num">Missed</th><th class="num">Miss rate</th></tr></thead>
      <tbody>${body}</tbody></table>`;
}

function renderHeatmapView() {
  const data = hmState.data;
  const grid = $("heatmap");
  const wrap = $("hm-table-wrap");
  if (!data) return;

  grid.hidden = hmState.table;
  wrap.hidden = !hmState.table;

  if (hmState.table) {
    wrap.innerHTML = hmTable(data.characters);
  } else {
    grid.innerHTML = "";
    data.characters.forEach((r) => grid.appendChild(hmCell(r)));
  }

  const parts = [`${data.count} characters`];
  if (data.set_accuracy != null) parts.push(`set mean ${pct(data.set_accuracy)}`);
  if (data.weakest) parts.push(`weakest ${data.weakest}`);
  if (!data.attempted) parts.push("no attempts yet");
  $("hm-stats").textContent = parts.join(" · ");
}

async function loadHeatmap(key) {
  hmState.key = key;
  document.querySelector(".hm-panel")?.classList.toggle("theme-kanji", key.startsWith("kanji:"));
  [...$("hm-sets").children].forEach((b) => b.classList.toggle("is-on", b.dataset.key === key));
  try {
    hmState.data = await fetch(
      `/api/heatmap?difficulty=${encodeURIComponent(key)}`
    ).then((r) => r.json());
  } catch {
    $("heatmap").innerHTML = `<p class="muted">Heatmap unavailable.</p>`;
    return;
  }
  renderHeatmapView();
}

function initHeatmap() {
  const sets = $("hm-sets");
  if (!sets) return;
  sets.innerHTML = "";
  HM_SETS.forEach((s) => {
    const btn = el("button", "seg-btn", s.label);
    btn.type = "button";
    btn.dataset.key = s.key;
    sets.appendChild(btn);
  });
  sets.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-key]");
    if (btn) loadHeatmap(btn.dataset.key);
  });

  const toggle = $("hm-table");
  toggle.addEventListener("click", () => {
    hmState.table = !hmState.table;
    toggle.classList.toggle("is-on", hmState.table);
    toggle.setAttribute("aria-pressed", String(hmState.table));
    renderHeatmapView();
  });

  $("hm-scale").innerHTML = [0, 0.25, 0.5, 0.75, 1]
    .map((v) => `<i style="background:${hmTint(v * HM_CEILING)}"></i>`)
    .join("");

  loadHeatmap(hmState.key);
}

// ── accuracy trend ───────────────────────────────────────────────────────────
function renderTrend(rows) {
  const wrap = $("trend");
  wrap.innerHTML = "";
  if (rows.length < 2) return wrap.appendChild(el("p", "muted", "Two sessions needed for a trend."));
  const W = 800, H = 190, P = 26;
  const s = svg(W, H);
  const x = (i) => P + (i * (W - 2 * P)) / (rows.length - 1);
  const y = (v) => H - P - v * (H - 2 * P);
  [0, 0.5, 1].forEach((g) => {
    s.appendChild(node("line", { x1: P, x2: W - P, y1: y(g), y2: y(g), class: "gridline" }));
  });
  const d = rows.map((r, i) => `${i ? "L" : "M"}${x(i)},${y(r.accuracy)}`).join(" ");
  s.appendChild(node("path", { d, class: "trend-line" }));
  rows.forEach((r, i) => {
    const c = node("circle", { cx: x(i), cy: y(r.accuracy), r: 3, class: "trend-dot" });
    c.appendChild(node("title", {})).textContent = `${r.started_at.slice(0, 10)} — ${pct(r.accuracy)} (${r.total} cards)`;
    s.appendChild(c);
  });
  wrap.appendChild(s);
}

// ── retention curve ──────────────────────────────────────────────────────────
function renderRetention(rows) {
  const wrap = $("retention");
  wrap.innerHTML = "";
  const withData = rows.filter((r) => r.samples > 0);
  if (!withData.length) return wrap.appendChild(el("p", "muted", "Needs repeat reviews over several days."));
  const W = 420, H = 170, P = 26;
  const s = svg(W, H);
  const x = (i) => P + (i * (W - 2 * P)) / Math.max(rows.length - 1, 1);
  const y = (v) => H - P - v * (H - 2 * P);
  const d = rows.map((r, i) => `${i ? "L" : "M"}${x(i)},${y(r.accuracy)}`).join(" ");
  s.appendChild(node("path", { d, class: "trend-line-2" }));
  rows.forEach((r, i) => {
    const c = node("circle", { cx: x(i), cy: y(r.accuracy), r: 3, class: "trend-dot" });
    c.appendChild(node("title", {})).textContent = `${r.days_since_last}d — ${pct(r.accuracy)} (n=${r.samples})`;
    s.appendChild(c);
    const t = node("text", { x: x(i), y: H - 8, class: "axis-t", "text-anchor": "middle" });
    t.textContent = `${r.days_since_last}d`;
    s.appendChild(t);
  });
  wrap.appendChild(s);
}


function renderWeak(rows) {
  const box = $("weak");
  box.innerHTML = "";
  if (!rows.length) return box.appendChild(el("p", "muted", "Nothing failing yet."));
  rows.forEach((r) => {
    const card = el("button", "wcard");
    card.type = "button";
    // The bar is the error rate itself, so the cards read as a ranked column
    // even before you take in the numbers.
    card.innerHTML = `<span class="jp wc-glyph">${r.glyph}</span>
      <span class="lbl-sm wc-read">${r.romaji || r.meaning || ""}</span>
      <b class="num wc-rate">${pct(r.miss_rate)}</b>
      <span class="wc-bar"><i style="width:${Math.max(6, Math.round(r.miss_rate * 100))}%"></i></span>`;
    card.title = `${r.glyph} — missed ${r.missed} of ${r.seen}`;
    card.addEventListener("click", () => {
      location.href = `/study?characters=${r.character_id}`;
    });
    box.appendChild(card);
  });
  const sessions = new Set(rows.map((r) => r.last_seen)).size;
  $("weak-note").textContent =
    `${rows.length} flagged · ${sessions ? "rolling 30 sessions" : "all time"}`;
  $("drill-weak").onclick = () => {
    location.href = `/study?characters=${rows.map((r) => r.character_id).join(",")}`;
  };
}


// ── leeches ──────────────────────────────────────────────────────────────────
function renderLeeches(rows) {
  const box = $("leeches");
  box.innerHTML = "";
  if (!rows.length) return box.appendChild(el("p", "muted", "No leeches — nothing is being re-forgotten."));
  rows.forEach((r) => {
    box.appendChild(
      el(
        "div",
        "log-row",
        `<span class="jp">${r.glyph}</span><span class="lbl-sm">${r.romaji || r.meaning || ""}</span>
         <b class="num">${r.lapses}</b><span class="lbl-sm">lapses / ${r.reps} reps</span>`
      )
    );
  });
}

// ── streak ───────────────────────────────────────────────────────────────────
// Four load steps, not a continuous ramp: the question a learner asks of this
// strip is "did I study, and roughly how hard", which four bands answer and a
// 256-step gradient does not.
const LOAD_STEPS = 4;
const loadTint = (step) =>
  step === 0 ? "var(--panel-3)" : `rgba(var(--amber-rgb),${(0.22 + step * 0.26).toFixed(2)})`;

function renderStreak(days, weeks, streak) {
  const byDate = new Map(days.map((r) => [r.date, r]));
  const max = Math.max(...days.map((r) => r.attempts), 1);

  $("streak-days").textContent = streak.longest ?? 0;
  $("streak-note").textContent =
    streak.current === streak.longest && streak.longest
      ? "longest on record · running now"
      : `longest on record · ${streak.current ?? 0} current`;

  const strip = $("act-strip");
  strip.innerHTML = "";
  const today = new Date();
  for (let i = 27; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    const hit = byDate.get(key);
    const step = hit ? Math.max(1, Math.ceil((hit.attempts / max) * LOAD_STEPS)) : 0;
    const cell = el("i", "act-cell");
    cell.style.background = loadTint(step);
    cell.title = hit ? `${key} — ${hit.attempts} cards, ${pct(hit.accuracy)}` : `${key} — no study`;
    strip.appendChild(cell);
  }

  $("act-scale").innerHTML = [0, 1, 2, 3, 4]
    .map((v) => `<i style="background:${loadTint(v)}"></i>`)
    .join("");

  const table = $("wk-table");
  if (!weeks.length) {
    table.innerHTML = `<tbody><tr><td class="muted">No activity recorded yet.</td></tr></tbody>`;
    return;
  }
  table.innerHTML =
    `<thead><tr><th>Week</th><th class="num">Sessions · Reps · Mean acc</th></tr></thead><tbody>` +
    weeks
      .map(
        (w) => `<tr>
          <td class="wk-label">${w.label} · ${w.week_start.slice(5)}</td>
          <td class="num">${w.sessions} · ${w.reps} · ${pct(w.accuracy)}</td>
        </tr>`
      )
      .join("") +
    `</tbody>`;
}

// ── settings: profiles and the data that belongs to them ─────────────────────
//
// Switching profiles reopens the database server-side, so every panel on the
// page is describing the wrong learner the moment it succeeds. Rather than
// re-render each one and risk missing any, the page reloads.

// "1 attempts" reads as a bug in a confirmation dialog, which is exactly where
// the user is deciding whether to trust the thing.
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

const setStatus = (message, tone = "") => {
  const node = $("set-status");
  node.textContent = message;
  node.className = `set-status lbl-sm ${tone}`;
};

async function api(url, options) {
  const res = await fetch(url, options);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.message || res.statusText);
  return body;
}

function profileRow(profile) {
  const row = el("div", `prof-row${profile.active ? " is-on" : ""}`);
  const size = profile.size_bytes ? `${Math.round(profile.size_bytes / 1024)} KB` : "empty";
  row.innerHTML = `
    <span class="prof-name">${profile.name}</span>
    <span class="lbl-sm prof-meta">${profile.active ? "active" : size}</span>`;

  if (!profile.active) {
    const use = el("button", "btn btn-sm", "Use");
    use.type = "button";
    use.addEventListener("click", async () => {
      try {
        await api("/api/profiles/activate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slug: profile.slug }),
        });
        location.reload();
      } catch (err) {
        setStatus(err.message, "bad");
      }
    });
    row.appendChild(use);

    if (profile.slug !== "default") {
      const remove = el("button", "btn btn-sm btn-danger", "Delete");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!confirm(`Delete the profile "${profile.name}" and all of its history?`)) return;
        try {
          await api(`/api/profiles/${encodeURIComponent(profile.slug)}`, { method: "DELETE" });
          setStatus(`Deleted "${profile.name}".`, "good");
          loadProfiles();
        } catch (err) {
          setStatus(err.message, "bad");
        }
      });
      row.appendChild(remove);
    }
  }
  return row;
}

async function loadProfiles() {
  try {
    const payload = await api("/api/profiles");
    const host = $("prof-list");
    host.innerHTML = "";
    payload.profiles.forEach((p) => host.appendChild(profileRow(p)));
  } catch (err) {
    setStatus(err.message, "bad");
  }
}

async function loadDataSummary() {
  try {
    const d = await api("/api/data/summary");
    const span =
      d.first_attempt && d.last_attempt
        ? ` · ${d.first_attempt.slice(0, 10)} → ${d.last_attempt.slice(0, 10)}`
        : "";
    $("data-note").textContent =
      `${plural(d.sessions, "session")} · ${plural(d.attempts, "card")} reviewed${span}`;
    $("reset-note").textContent = d.attempts
      ? `This removes ${plural(d.attempts, "attempt")} across ${plural(d.sessions, "session")}. ` +
        "It cannot be undone — save first."
      : "Nothing recorded yet, so there is nothing to clear.";
  } catch (err) {
    setStatus(err.message, "bad");
  }
}

// Painted whenever the dialog opens; wired exactly once. Attaching the listener
// on open would stack a fresh one every time the dialog is shown.
function paintSoundToggle() {
  const toggle = $("snd-toggle");
  if (toggle) toggle.setAttribute("aria-checked", String(soundEnabled()));
}

function initSoundToggle() {
  const toggle = $("snd-toggle");
  if (!toggle) return;
  paintSoundToggle();
  toggle.addEventListener("click", () => {
    const on = !soundEnabled();
    setSoundEnabled(on);
    paintSoundToggle();
    // Turning it on plays the cue once. A silent switch gives no evidence it
    // worked, and this is the exact sound the setting governs.
    if (on) playCorrect();
  });
}

function initSettings() {
  const dialog = $("settings");
  if (!dialog) return;
  initSoundToggle();

  const open = () => {
    dialog.hidden = false;
    setStatus("");
    paintSoundToggle();
    loadProfiles();
    loadDataSummary();
  };
  const close = () => {
    dialog.hidden = true;
  };

  $("settings-open").addEventListener("click", open);
  $("settings-close").addEventListener("click", close);
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) close();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !dialog.hidden) close();
  });

  $("prof-new").addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = $("prof-name").value.trim();
    if (!name) return;
    try {
      await api("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      location.reload();
    } catch (err) {
      setStatus(err.message, "bad");
    }
  });

  // Saved through a blob rather than by navigating to the endpoint: a webview
  // has no download chrome, so navigation would simply display the JSON.
  $("data-export").addEventListener("click", async () => {
    try {
      const payload = await api("/api/data/export");
      const stamp = payload.exported_at.slice(0, 10);
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" })
      );
      const link = el("a");
      link.href = url;
      link.download = `japanese-practice-${stamp}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setStatus(
        `Saved ${plural(payload.counts.attempts, "attempt")} across ` +
          `${plural(payload.counts.sessions, "session")}.`,
        "good"
      );
    } catch (err) {
      setStatus(err.message, "bad");
    }
  });

  $("data-import").addEventListener("click", () => $("data-file").click());
  $("data-file").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    event.target.value = "";
    if (!confirm("Loading replaces this profile's current progress. Continue?")) return;
    try {
      const payload = JSON.parse(await file.text());
      const result = await api("/api/data/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payload, replace: true }),
      });
      const skipped = result.skipped_unknown_glyphs
        ? ` ${plural(result.skipped_unknown_glyphs, "unknown character")} skipped.`
        : "";
      setStatus(`Loaded ${plural(result.attempts, "attempt")}.${skipped} Reloading…`, "good");
      setTimeout(() => location.reload(), 900);
    } catch (err) {
      setStatus(err.message, "bad");
    }
  });

  $("data-reset").addEventListener("click", async () => {
    if (!confirm("Reset this profile to zero? Saved files are unaffected, but this profile's history is deleted.")) {
      return;
    }
    try {
      const result = await api("/api/data/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: true }),
      });
      setStatus(`Cleared ${plural(result.cleared.attempts, "attempt")}. Reloading…`, "good");
      setTimeout(() => location.reload(), 900);
    } catch (err) {
      setStatus(err.message, "bad");
    }
  });
}

// ── boot ─────────────────────────────────────────────────────────────────────
async function main() {
  const summary = await fetch("/api/summary").then((r) => r.json());
  const decks = summary.decks || [];
  const trend = summary.accuracy_by_session || [];
  const totals = summary.totals || {};

  renderShelves(decks);
  renderStats(totals, summary.first_vs_eventual || {}, trend, decks);
  renderTrend(trend);
  renderBySet(decks);
  renderRetention(summary.retention_curve || []);
  renderWeak(summary.weakest_characters || []);
  renderLeeches(summary.leeches || []);
  renderStreak(
    summary.streak_calendar || [],
    summary.weekly_activity || [],
    summary.daily_streak || {}
  );
  renderHistory(summary.session_history || []);
  renderGames();
  initHeatmap();
  initSettings();

  $("tb-streak").textContent = totals.best_streak ?? 0;
  $("tb-sessions").textContent = totals.sessions ?? 0;
  const latest = (summary.session_history || [])[0];
  $("tb-last").textContent = latest ? `last run ${latest.started_at.slice(0, 10)}` : "no runs yet";
  $("trend-note").textContent = trend.length ? `last ${trend.length} sessions` : "";

  // Attribution is a licence condition, not decoration — render whatever the
  // active provider requires.
  try {
    const credits = await fetch("/api/credits").then((r) => r.json());
    if (credits.required && credits.required.length) {
      $("credits").textContent = `Pronunciation audio: ${credits.required.join(" · ")}`;
      $("credits").hidden = false;
    }
  } catch {
    /* attribution is best-effort; never block the dashboard on it */
  }

  if (!totals.attempts) $("empty").hidden = false;
}

main().catch((err) => {
  console.error(err);
  document.getElementById("empty").hidden = false;
});
