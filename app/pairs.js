// "Strange bedfellows": curated subreddit pairs that sit close without belonging together.
// The list comes from find_pairs.py (data/pairs.js); this only presents it and drives the
// page's globals (setTime, picked, restyle, liveLinks_, activeCats) the way extras.js does.
// Shared by index.html (2D) and index3d.html (3D).

if (window.PAIRS && window.PAIRS.length) (function () {
  const host = document.getElementById("connect") || document.querySelector(".stack-primary");
  if (!host) return;

  const row = (p, i) => `
    <button type="button" class="bedfellow" data-i="${i}" title="${p.a} ~ ${p.b}: ${p.months} of the ${D.snapshots.length} months">
      <span class="bf-pair">r/${p.a} <i>·</i> r/${p.b}</span>
      <span class="bf-kw">${p.kw}</span>
      <span class="bf-why">${p.why}</span>
    </button>`;

  host.insertAdjacentHTML("afterend", `
    <div class="sec" id="bedfellows">
      <div class="lbl"><span>Strange bedfellows</span><span class="side">one word apart</span></div>
      <p class="bf-lead">Two communities from different themes, held together by a single word. Click one for the line, the mention counts, and the posts.</p>
      <div class="bf-list">${window.PAIRS.map(row).join("")}</div>
    </div>`);

  document.head.insertAdjacentHTML("beforeend", `<style>
    .bf-lead { font-size: 11.5px; color: var(--muted); margin: 0 0 8px; line-height: 1.45; }
    .bf-list { display: flex; flex-direction: column; gap: 4px; }
    .bedfellow {
      display: grid; grid-template-columns: 1fr auto; gap: 2px 8px;
      padding: 7px 8px; text-align: left; cursor: pointer;
      background: var(--ink); border: 1px solid var(--line); border-radius: var(--r);
      color: var(--text); font: inherit;
    }
    .bedfellow:hover { border-color: var(--line-strong); }
    .bedfellow.on { border-color: var(--accent); background: var(--accent-dim); }
    .bf-pair { font: 500 12px var(--body); }
    .bf-pair i { color: var(--muted); font-style: normal; }
    .bf-kw { font: 500 11px var(--mono); color: var(--accent); align-self: center; }
    .bf-why { grid-column: 1 / -1; font-size: 11px; color: var(--muted); }
  </style>`);

  const list = document.querySelector(".bf-list");

  const ends = l => [l.source.id ?? l.source, l.target.id ?? l.target];
  const linkFor = p => D.links.find(l => {
    const [a, b] = ends(l);
    return (a === p.a && b === p.b) || (a === p.b && b === p.a);
  });

  function show(p, el) {
    if (typeof stopPlay === "function") stopPlay();
    query = "";
    if ($("#q")) $("#q").value = "";
    if (typeof syncChips === "function") syncChips();
    focus = null; pathLinks = null; picked = null;

    // the line only exists while both themes are switched on
    for (const id of [p.a, p.b]) {
      const n = byId.get(id);
      if (n) activeCats.add(n.cat);
    }
    setTime(p.i);
    let l = linkFor(p);
    if (!l || !liveLinks_.includes(l)) { update(); l = linkFor(p); }   // a theme was off, or time didn't move
    picked = l || null;
    // borrow the connect-chain highlight: one line lit, the rest of the map dimmed out,
    // which is the whole point of a pair nobody expected
    pathLinks = l ? [l] : null;
    restyle();

    [...list.children].forEach(b => b.classList.toggle("on", b === el));
    if (typeof window.zoomToNodes === "function") window.zoomToNodes([p.a, p.b], 260, false, 1.5);
    else if (typeof G !== "undefined" && G && G.zoomToFit) {
      const want = new Set([p.a, p.b]);
      G.zoomToFit(750, 90, n => want.has(n.id));
    }
    $("#proof")?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  list.addEventListener("click", e => {
    const el = e.target.closest(".bedfellow");
    if (!el) return;
    const p = window.PAIRS[+el.dataset.i];
    if (el.classList.contains("on")) { picked = null; pathLinks = null; restyle(); return; }
    show(p, el);
  });

  // any other click on the map drops the selection, so drop the highlight with it
  const _restyle = restyle;
  restyle = function (...args) {
    _restyle(...args);
    if (!picked) [...list.children].forEach(b => b.classList.remove("on"));
  };
})();
