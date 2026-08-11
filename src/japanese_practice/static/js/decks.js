// The full exercise catalogue, reached from the "More…" card on any shelf.
//
// Shows two things side by side: every deck that actually works, and every
// exercise that is designed but not built. Listing the second group is
// deliberate — a catalogue that shows only what works tells a learner nothing
// about where the app is going, and each entry says what is blocking it rather
// than implying it is coming next week.

const $ = (id) => document.getElementById(id);
const el = (tag, cls, html) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
};

const pct2 = (v) => `${Math.round((v || 0) * 100)}%`;

// Shelf order and titles, matching the dashboard so the two read as one app.
// `kanji: true` carries the green accent. Marked on the shelf rather than
// inferred from the title, so a future kanji shelf cannot be missed by a string
// match on "Kanji".
const SHELVES = [
  { id: "hiragana", title: "Hiragana", note: "gojuon → dakuon → han-dakuon → yoon → 104 mixed" },
  { id: "katakana", title: "Katakana", note: "the same five rungs, in the script used for loanwords" },
  { id: "jlpt", title: "Kanji — proficiency", note: "JLPT N5 → N1", kanji: true },
  { id: "vol", title: "Kanji — volume", note: "Top 200 → Top 500 by teaching frequency", kanji: true },
  { id: "words", title: "Words & grammar", note: "whole words rather than single characters" },
  { id: "general", title: "General words", note: "one English word, many Japanese ones — each card carries an example sentence" },
  { id: "phrases", title: "Phrase sets", note: "one pattern, many phrases — learn the shape and the set follows" },
];

function deckNode(deck) {
  const pct = deck.count ? Math.round((deck.mastered / deck.count) * 100) : 0;
  const wide =
    deck.shelf === "words" ? " deck-wide"
    : deck.shelf === "phrases" || deck.shelf === "general" ? " deck-phrase"
    : "";
  const node = el("button", `deck${wide}`);
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
  node.addEventListener("click", () => {
    location.href =
      `/study?difficulty=${encodeURIComponent(deck.key)}` +
      `&challenge=${deck.challenge}&scoring=${deck.scoring}`;
  });
  return node;
}

function plannedNode(item) {
  const node = el("div", `plan-card is-${item.status}`);
  node.innerHTML = `
    <span class="plan-head">
      <span class="plan-name">${item.name}</span>
      <span class="plan-jp jp">${item.jp}</span>
      <span class="tag plan-status">${item.status}</span>
    </span>
    <span class="plan-detail">${item.detail}</span>
    <span class="plan-blocker"><em>Blocked on</em> ${item.blocker}</span>`;
  return node;
}

async function main() {
  let payload;
  try {
    payload = await fetch("/api/catalogue").then((r) => r.json());
  } catch {
    $("cat-shelves").innerHTML = `<p class="muted">Catalogue unavailable.</p>`;
    return;
  }

  const host = $("cat-shelves");
  host.innerHTML = "";
  const decks = payload.decks || [];

  for (const shelf of SHELVES) {
    const mine = decks.filter((d) => d.shelf === shelf.id);
    if (!mine.length) continue;      // a shelf with nothing on it is not a heading
    const head = el("section", `sec${shelf.kanji ? " theme-kanji" : ""}`);
    head.innerHTML =
      `<span class="sec-title">${shelf.title}</span><span class="sec-desc">${shelf.note}</span>`;
    host.appendChild(head);
    const rail = el("div", `shelf-wrap${shelf.kanji ? " theme-kanji" : ""}`);
    mine.forEach((d) => rail.appendChild(deckNode(d)));
    host.appendChild(rail);
  }

  const planned = $("cat-planned");
  planned.innerHTML = "";
  (payload.planned || []).forEach((p) => planned.appendChild(plannedNode(p)));

  const c = payload.counts || {};
  $("cat-count").textContent =
    `${c.available ?? 0} available · ${c.experimental ?? 0} experimental · ${c.planned ?? 0} planned`;
}

main();
