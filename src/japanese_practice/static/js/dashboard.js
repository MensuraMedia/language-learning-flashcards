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

// ── deck shelf ───────────────────────────────────────────────────────────────
function renderShelf(segments) {
  const shelf = $("shelf");
  shelf.innerHTML = "";
  segments.forEach((seg) => {
    const deck = el("article", "deck");
    // .deck3d defaults to a viewport-relative width; inside the fixed-width
    // .deck slot it must fill the slot instead, or it overflows the shelf.
    deck.innerHTML = `
      <div class="deck3d" style="width:100%;aspect-ratio:auto;height:150px">
        <div class="deck-face">
          <div class="deck-id">${seg.script}</div>
          <div class="deck-jp">${seg.script === "kanji" ? "漢字" : seg.script === "katakana" ? "カタ" : "かな"}</div>
        </div>
      </div>
      <div class="deck-top">
        <div class="deck-name">${seg.label}</div>
        <div class="deck-count">${seg.count} cards</div>
      </div>
      <div class="obi"><div class="obi-row"><span>start</span><b>→</b></div></div>`;
    deck.tabIndex = 0;
    deck.setAttribute("role", "button");
    const go = () => {
      location.href = `/study?difficulty=${encodeURIComponent(seg.key)}&challenge=recognition&scoring=accuracy`;
    };
    deck.addEventListener("click", go);
    deck.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.code === "Space") {
        e.preventDefault();
        go();
      }
    });
    shelf.appendChild(deck);
  });
  $("deck-note").textContent = `${segments.length} segments available`;
}

// ── headline tiles ───────────────────────────────────────────────────────────
function renderTiles(t, fve) {
  const tiles = [
    ["Sessions", t.sessions ?? 0, "runs recorded"],
    ["Attempts", t.attempts ?? 0, "cards answered"],
    ["Accuracy", pct(t.accuracy), "all time"],
    ["Best streak", t.best_streak ?? 0, "consecutive"],
    ["Score", t.score ?? 0, "cumulative"],
    ["First-attempt", pct(fve.first_attempt_accuracy), `gap ${pct(fve.gap)}`],
  ];
  $("tiles").innerHTML = tiles
    .map(
      ([k, v, d]) =>
        `<div class="tile"><span class="lbl-sm">${k}</span><b class="num">${v}</b><span class="d">${d}</span></div>`
    )
    .join("");
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
  const [summary, segs] = await Promise.all([
    fetch("/api/summary").then((r) => r.json()),
    fetch("/api/segments").then((r) => r.json()),
  ]);

  renderShelf(segs.segments || []);
  renderTiles(summary.totals || {}, summary.first_vs_eventual || {});
  renderHeatmap(summary.per_character_miss_rate || []);
  renderTrend(summary.accuracy_by_session || []);
  renderRetention(summary.retention_curve || []);
  renderLatency(summary.latency_distribution || []);
  renderTod(summary.time_of_day || []);
  renderWeak(summary.weakest_characters || []);
  renderConfusions(summary.confusion_pairs || []);
  renderLeeches(summary.leeches || []);
  renderMastery(summary.mastery_by_group || []);
  renderCalendar(summary.streak_calendar || []);

  if (!(summary.totals || {}).attempts) $("empty").hidden = false;
}

main().catch((err) => {
  console.error(err);
  document.getElementById("empty").hidden = false;
});
