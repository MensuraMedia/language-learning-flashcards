// Dashboard: renders the full analytics surface from /api/summary.
// Charts are inline SVG built here — no library, no external request.

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
  for (const shelf of ["kana", "jlpt", "vol"]) {
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
function renderHeatmap(rows) {
  const hm = $("heatmap");
  hm.innerHTML = "";
  if (!rows.length) {
    hm.appendChild(el("p", "muted", "No attempts yet."));
    return;
  }
  rows.forEach((r) => {
    const cell = el("button", "hm-cell");
    cell.type = "button";
    cell.textContent = r.glyph;
    // Amber alpha encodes miss rate: transparent = mastered, solid = failing.
    cell.style.background = `rgba(240,180,41,${(r.miss_rate * 0.85 + 0.05).toFixed(3)})`;
    cell.style.color = r.miss_rate > 0.5 ? "#0d0d0f" : "var(--ink)";
    cell.title = `${r.glyph} — seen ${r.seen}, missed ${r.missed} (${pct(r.miss_rate)})`;
    cell.setAttribute("aria-label", cell.title);
    cell.addEventListener("click", () => {
      location.href = `/study?characters=${r.character_id}`;
    });
    hm.appendChild(cell);
  });
  $("hm-scale").innerHTML = [0, 0.25, 0.5, 0.75, 1]
    .map((v) => `<i style="background:rgba(240,180,41,${(v * 0.85 + 0.05).toFixed(2)})"></i>`)
    .join("");
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

// ── latency histogram ────────────────────────────────────────────────────────
function renderLatency(rows) {
  const box = $("latency");
  box.innerHTML = "";
  const max = Math.max(...rows.map((r) => r.count), 1);
  rows.forEach((r) => {
    const col = el("div", "histo-col");
    col.innerHTML = `<i style="height:${(r.count / max) * 100}%"></i><span class="histo-axis">${r.label}</span><b>${r.count}</b>`;
    box.appendChild(col);
  });
}

// ── time of day ──────────────────────────────────────────────────────────────
function renderTod(rows) {
  const wrap = $("tod");
  wrap.innerHTML = "";
  const active = rows.filter((r) => r.attempts > 0);
  if (!active.length) return wrap.appendChild(el("p", "muted", "No attempts yet."));
  const W = 420, H = 170, P = 26;
  const s = svg(W, H);
  const x = (h) => P + (h * (W - 2 * P)) / 23;
  const y = (v) => H - P - v * (H - 2 * P);
  // Dots, not bars — a bar under a clipped axis would overstate a single attempt.
  active.forEach((r) => {
    const c = node("circle", {
      cx: x(r.hour),
      cy: y(r.accuracy),
      r: Math.min(3 + Math.sqrt(r.attempts), 9),
      class: "dp",
    });
    c.appendChild(node("title", {})).textContent = `${String(r.hour).padStart(2, "0")}:00 — ${pct(r.accuracy)} (${r.attempts})`;
    s.appendChild(c);
  });
  [0, 6, 12, 18, 23].forEach((h) => {
    const t = node("text", { x: x(h), y: H - 8, class: "axis-t", "text-anchor": "middle" });
    t.textContent = String(h).padStart(2, "0");
    s.appendChild(t);
  });
  wrap.appendChild(s);
}

// ── weakest characters (drill queue) ─────────────────────────────────────────
function renderWeak(rows) {
  const box = $("weak");
  box.innerHTML = "";
  if (!rows.length) return box.appendChild(el("p", "muted", "Nothing failing yet."));
  rows.forEach((r) => {
    const card = el("button", "wcard");
    card.type = "button";
    card.innerHTML = `<span class="jp">${r.glyph}</span>
      <span class="lbl-sm">${r.romaji || r.meaning || ""}</span>
      <b class="num">${pct(r.miss_rate)}</b>
      <span class="lbl-sm">${r.missed}/${r.seen}</span>`;
    card.addEventListener("click", () => {
      location.href = `/study?characters=${r.character_id}`;
    });
    box.appendChild(card);
  });
  $("drill-weak").onclick = () => {
    location.href = `/study?characters=${rows.map((r) => r.character_id).join(",")}`;
  };
}

// ── confusion pairs ──────────────────────────────────────────────────────────
function renderConfusions(rows) {
  const box = $("confusions");
  box.innerHTML = "";
  if (!rows.length) return box.appendChild(el("p", "muted", "No confusions recorded yet."));
  rows.forEach((r) => {
    box.appendChild(
      el(
        "div",
        "conf-row",
        `<span class="jp">${r.glyph}</span><em>mistaken for</em><span class="jp">${r.mistaken_for}</span><b class="num">${r.count}×</b>`
      )
    );
  });
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

// ── mastery by group ─────────────────────────────────────────────────────────
function renderMastery(rows) {
  const box = $("mastery");
  box.innerHTML = "";
  rows.forEach((r) => {
    const share = r.total ? r.mastered / r.total : 0;
    box.appendChild(
      el(
        "div",
        "bar-row",
        `<span class="bar-name">${r.script} <em>${r.group}</em></span>
         <span class="bar-t"><i class="bar-f" style="width:${share * 100}%"></i></span>
         <b class="bar-val">${r.mastered}/${r.total}</b>`
      )
    );
  });
}

// ── streak calendar ──────────────────────────────────────────────────────────
function renderCalendar(rows) {
  const box = $("calendar");
  box.innerHTML = "";
  const byDate = new Map(rows.map((r) => [r.date, r]));
  const max = Math.max(...rows.map((r) => r.attempts), 1);
  const today = new Date();
  for (let i = 89; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    const hit = byDate.get(key);
    const cell = el("i", "hit");
    const intensity = hit ? 0.15 + (hit.attempts / max) * 0.85 : 0;
    cell.style.background = hit ? `rgba(240,180,41,${intensity.toFixed(2)})` : "var(--panel-3)";
    cell.title = hit ? `${key} — ${hit.attempts} cards, ${pct(hit.accuracy)}` : `${key} — no study`;
    box.appendChild(cell);
  }
}

// ── boot ─────────────────────────────────────────────────────────────────────
async function main() {
  const summary = await fetch("/api/summary").then((r) => r.json());
  const decks = summary.decks || [];
  const trend = summary.accuracy_by_session || [];
  const totals = summary.totals || {};

  renderShelves(decks);
  renderStats(totals, summary.first_vs_eventual || {}, trend, decks);
  renderHeatmap(summary.per_character_miss_rate || []);
  renderTrend(trend);
  renderBySet(decks);
  renderRetention(summary.retention_curve || []);
  renderLatency(summary.latency_distribution || []);
  renderTod(summary.time_of_day || []);
  renderWeak(summary.weakest_characters || []);
  renderConfusions(summary.confusion_pairs || []);
  renderLeeches(summary.leeches || []);
  renderMastery(summary.mastery_by_group || []);
  renderCalendar(summary.streak_calendar || []);
  renderHistory(summary.session_history || []);

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
