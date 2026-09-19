// Educational story mode — drives existing map globals (setTime, focus, query, fit, …).
// Loaded after extras.js. Does not replace the product Tour.

(function () {
  const claudeStory = {
    id: "claude-drift",
    kicker: "A finding",
    menuTitle: "claude — meaning handoff",
    menuBlurb: "Gaming character → AI model",
    finding: "One spelling, two eras of meaning.",
    why: "Early on the map pins <b>claude</b> in r/GTA (Claude Speed). Years later the same string sits in AI/Coding hosts — Anthropic’s model. The graph records a semantic takeover without reading the posts for sense.",
    title: "One word, two meanings",
    steps: [
      {
        title: "One word. Watch where it lives.",
        body: "Track <b>claude</b> in early 2020. Almost every mention sits in <b>r/GTA</b> — Claude Speed, a racing character.",
        lit: [".time", "#q", "#spread"],
        lock: true,
        actions: [
          { op: "reset" },
          { op: "setTime", snap: "2020-02" },
          { op: "track", term: "claude" },
          { op: "focus", id: "GTA" },
          { op: "annotate", ids: ["GTA"] },
          { op: "waitMs", ms: 350 },
          { op: "zoomTo", ids: ["GTA"], neighbors: true, pad: 200, maxK: 1.55 },
          { op: "waitMs", ms: 400 },
        ],
      },
      {
        title: "Still a gamer’s word",
        body: "May 2023: still almost only <b>r/GTA</b>. Same spelling — not a chatbot yet.",
        lit: [".time", "#spread", "#outbreak", "#focus"],
        lock: true,
        actions: [
          { op: "setTime", snap: "2023-05" },
          { op: "track", term: "claude" },
          { op: "focus", id: "GTA" },
          { op: "annotate", ids: ["GTA"] },
          { op: "spot", sel: "#spread" },
          { op: "waitMs", ms: 350 },
          { op: "zoomTo", ids: ["GTA"], neighbors: true, pad: 200, maxK: 1.55 },
          { op: "waitMs", ms: 350 },
        ],
      },
      {
        title: "What if a new meaning arrives?",
        body: "Vocabulary maps follow the <i>string</i>, not the sense. When a new referent shows up, the hosts should move.",
        lit: ["#spread", ".time"],
        lock: true,
        actions: [
          { op: "spot", sel: "#spread" },
          { op: "annotate", ids: ["GTA"] },
          { op: "zoomTo", ids: ["GTA"], neighbors: true, pad: 200, maxK: 1.55 },
        ],
      },
      {
        title: "The flip",
        body: "March 2024: <b>r/ChatGPT</b> takes the word. Same letters — Anthropic’s model, not Claude Speed.",
        lit: [".time", "#spread", "#outbreak", "#focus", "#q"],
        lock: true,
        actions: [
          { op: "setTime", snap: "2024-03" },
          { op: "track", term: "claude" },
          { op: "focus", id: "ChatGPT" },
          { op: "annotate", ids: ["ChatGPT"] },
          { op: "spot", sel: "#outbreak" },
          { op: "waitMs", ms: 350 },
          { op: "zoomTo", ids: ["ChatGPT"], neighbors: true, pad: 200, maxK: 1.55 },
          { op: "waitMs", ms: 350 },
        ],
      },
      {
        title: "Hosts shifted",
        body: "Outbreak and focus panels now point at AI communities. The map recorded a meaning handoff.",
        lit: ["#outbreak", "#focus", "#spread"],
        lock: true,
        actions: [
          { op: "track", term: "claude" },
          { op: "focus", id: "ChatGPT" },
          { op: "annotate", ids: ["ChatGPT"] },
          { op: "spot", sel: "#focus" },
          { op: "zoomTo", ids: ["ChatGPT"], neighbors: true, pad: 200, maxK: 1.55 },
        ],
      },
      {
        title: "Takeover complete",
        body: "March 2026: <b>AI</b> and <b>Coding</b> own it — ChatGPT, singularity, programming, learnprogramming.",
        lit: [".time", "#spread", "#q"],
        lock: true,
        actions: [
          { op: "setTime", snap: "2026-03" },
          { op: "track", term: "claude" },
          { op: "clearFocus" },
          { op: "annotate", ids: ["ChatGPT", "singularity", "programming", "learnprogramming"] },
          { op: "waitMs", ms: 400 },
          { op: "zoomTo", ids: ["ChatGPT", "singularity", "programming", "learnprogramming"], neighbors: true, pad: 220, maxK: 1.45 },
          { op: "waitMs", ms: 400 },
        ],
      },
      {
        title: "Semantic capture",
        body: "Meme drift isn’t only <i>who says it</i> — it’s <i>what it means</i>. One token, two eras.",
        lit: ["#q", "#spread", ".time"],
        lock: true,
        actions: [
          { op: "track", term: "claude" },
          { op: "clearFocus" },
          { op: "annotate", ids: ["ChatGPT", "singularity", "programming"] },
          { op: "spot", sel: "#q" },
          { op: "zoomTo", ids: ["ChatGPT", "singularity", "programming"], neighbors: true, pad: 220, maxK: 1.45 },
        ],
      },
      {
        title: "Keep exploring",
        body: "You’re back in the live map with <b>claude</b> still tracked at 2026. Scrub earlier to watch the handoff yourself.",
        lit: [".time", "#q", "#spread", "#memes", "#curated"],
        lock: false,
        handoff: true,
        actions: [
          { op: "setTime", snap: "2026-03" },
          { op: "track", term: "claude" },
          { op: "clearFocus" },
          { op: "clearAnnot" },
          { op: "fit" },
        ],
      },
    ],
  };

  const openaiStory = {
    id: "openai-neighborhoods",
    kicker: "A finding",
    menuTitle: "openai — two neighborhoods",
    menuBlurb: "Same company: AI talk vs market talk",
    finding: "Same company, two far-apart neighborhoods.",
    why: "For years <b>openai</b> lives almost only in AI hosts. Later Finance (stocks / StockMarket) co-hosts the same name. Distance on the map shows dual framing — capability talk vs market-object talk — as association, not causation.",
    title: "One company, two neighborhoods",
    steps: [
      {
        title: "One company. Watch the map.",
        body: "Track <b>openai</b> — the lab/company, not a pun. In 2023 it lives almost only among AI hosts.",
        lit: [".time", "#q", "#spread"],
        lock: true,
        actions: [
          { op: "reset" },
          { op: "setTime", snap: "2023-01" },
          { op: "track", term: "openai" },
          { op: "focus", id: "OpenAI" },
          { op: "annotate", ids: ["OpenAI", "ChatGPT", "singularity", "MachineLearning"] },
          { op: "waitMs", ms: 350 },
          { op: "zoomTo", ids: ["OpenAI", "ChatGPT", "singularity", "MachineLearning"] },
          { op: "waitMs", ms: 400 },
        ],
      },
      {
        title: "AI neighborhood",
        body: "r/OpenAI, r/ChatGPT, r/singularity — product and future talk. Finance is quiet.",
        lit: [".time", "#spread", "#outbreak", "#focus"],
        lock: true,
        actions: [
          { op: "track", term: "openai" },
          { op: "focus", id: "singularity" },
          { op: "annotate", ids: ["OpenAI", "ChatGPT", "singularity"] },
          { op: "spot", sel: "#spread" },
          { op: "zoomTo", ids: ["OpenAI", "ChatGPT", "singularity"] },
        ],
      },
      {
        title: "What if another neighborhood joins?",
        body: "Same referent. If market communities start saying the name, the map should light a <i>different</i> cluster — not rename the company.",
        lit: ["#spread", ".time"],
        lock: true,
        actions: [
          { op: "spot", sel: "#spread" },
          { op: "annotate", ids: ["OpenAI", "ChatGPT", "singularity"] },
        ],
      },
      {
        title: "Finance shows up",
        body: "September 2025: <b>r/stocks</b> carries the same name alongside AI hosts. Two neighborhoods, one company.",
        lit: [".time", "#q", "#spread", "#outbreak"],
        lock: true,
        actions: [
          { op: "setTime", snap: "2025-09" },
          { op: "track", term: "openai" },
          { op: "clearFocus" },
          { op: "annotate", ids: ["OpenAI", "singularity", "ChatGPT", "stocks"] },
          { op: "waitMs", ms: 400 },
          { op: "zoomTo", ids: ["OpenAI", "singularity", "ChatGPT", "stocks"], neighbors: false, pad: 150 },
          { op: "waitMs", ms: 400 },
        ],
      },
      {
        title: "Both light up together",
        body: "January 2026: AI hosts <b>and</b> StockMarket / stocks co-host <b>openai</b>. Watch the gap between clusters.",
        lit: [".time", "#spread", "#q"],
        lock: true,
        actions: [
          { op: "setTime", snap: "2026-01" },
          { op: "track", term: "openai" },
          { op: "clearFocus" },
          { op: "annotate", ids: ["OpenAI", "ChatGPT", "singularity", "StockMarket", "stocks"] },
          { op: "spot", sel: "#spread" },
          { op: "waitMs", ms: 400 },
          { op: "zoomTo", ids: ["OpenAI", "ChatGPT", "singularity", "StockMarket", "stocks"], neighbors: false, pad: 170 },
          { op: "waitMs", ms: 450 },
        ],
      },
      {
        title: "AI framing",
        body: "Focus the AI side: singularity / ChatGPT — capability and future talk about the same company.",
        lit: ["#focus", "#outbreak", "#spread"],
        lock: true,
        actions: [
          { op: "track", term: "openai" },
          { op: "focus", id: "singularity" },
          { op: "annotate", ids: ["OpenAI", "ChatGPT", "singularity"] },
          { op: "spot", sel: "#focus" },
          { op: "zoomTo", ids: ["OpenAI", "ChatGPT", "singularity"] },
        ],
      },
      {
        title: "Market framing",
        body: "Same month, same name — now in <b>r/StockMarket</b>. Attention sits with portfolio talk, not lab talk.",
        lit: ["#focus", "#spread", ".time"],
        lock: true,
        actions: [
          { op: "track", term: "openai" },
          { op: "focus", id: "StockMarket" },
          { op: "annotate", ids: ["StockMarket", "stocks"] },
          { op: "spot", sel: "#focus" },
          { op: "zoomTo", ids: ["StockMarket", "stocks"] },
        ],
      },
      {
        title: "Same referent, two contexts",
        body: "AI and Finance neighborhoods stay far on the map, but they <b>co-host</b> the word. Association — not proof that one caused the other.",
        lit: ["#q", "#spread", ".time"],
        lock: true,
        actions: [
          { op: "track", term: "openai" },
          { op: "clearFocus" },
          { op: "annotate", ids: ["OpenAI", "ChatGPT", "singularity", "StockMarket", "stocks"] },
          { op: "spot", sel: "#q" },
          { op: "zoomTo", ids: ["OpenAI", "ChatGPT", "singularity", "StockMarket", "stocks"], neighbors: false, pad: 180 },
        ],
      },
      {
        title: "Keep exploring",
        body: "You’re free on the map with <b>openai</b> at Jan 2026. Scrub around that month to compare the two neighborhoods yourself.",
        lit: [".time", "#q", "#spread", "#memes", "#curated"],
        lock: false,
        handoff: true,
        actions: [
          { op: "setTime", snap: "2026-01" },
          { op: "track", term: "openai" },
          { op: "clearFocus" },
          { op: "clearAnnot" },
          { op: "fit" },
        ],
      },
    ],
  };

  const STORIES = [claudeStory, openaiStory];
  let active = null;
  let step = 0;
  let saved = null;
  let storyAnnotIds = null;
  let running = false;
  window.storyActive = false;

  const card = document.createElement("div");
  card.id = "story";
  card.hidden = true;
  card.setAttribute("role", "dialog");
  card.setAttribute("aria-label", "Educational finding");
  card.innerHTML = `
    <button type="button" class="story-exit" aria-label="Exit finding">×</button>
    <div class="story-kicker"></div>
    <h2 class="story-title"></h2>
    <p class="story-body"></p>
    <div class="story-row">
      <span class="story-prog"></span>
      <div class="story-actions">
        <button type="button" data-act="back">Back</button>
        <button type="button" class="primary" data-act="next">Next</button>
      </div>
    </div>`;
  const brand = document.querySelector("#panel .brand");
  if (brand) brand.insertAdjacentElement("afterend", card);
  else $("#panel").insertAdjacentElement("afterbegin", card);

  const chooser = document.createElement("div");
  chooser.id = "story-chooser";
  chooser.hidden = true;
  chooser.innerHTML = `
    <div class="story-chooser-head">
      <span class="story-kicker">Findings</span>
      <button type="button" class="story-chooser-x" aria-label="Close">×</button>
    </div>
    <p class="story-chooser-lead">Guided paths on the live map. Each one shows a real pattern in who says a word — and why that pattern is worth watching.</p>
    <div class="story-chooser-list"></div>`;
  if (brand) brand.insertAdjacentElement("afterend", chooser);
  else $("#panel").insertAdjacentElement("afterbegin", chooser);

  const list = chooser.querySelector(".story-chooser-list");
  STORIES.forEach(s => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "story-pick";
    b.dataset.id = s.id;
    b.innerHTML = `
      <span class="story-pick-title">${s.menuTitle}</span>
      <span class="story-pick-blurb">${s.menuBlurb}</span>
      <span class="story-pick-finding"><b>Finding.</b> ${s.finding}</span>
      <span class="story-pick-why"><b>Why it matters.</b> ${s.why}</span>`;
    b.onclick = () => { hideChooser(); enterStory(s.id); };
    list.appendChild(b);
  });
  chooser.querySelector(".story-chooser-x").onclick = () => hideChooser();

  const nav = document.querySelector("#panel .nav");
  if (nav && !document.getElementById("story-btn")) {
    nav.insertAdjacentHTML("beforeend", `<button type="button" id="story-btn" title="Guided findings">Findings</button>`);
  }
  document.querySelectorAll(".hint #story-btn, .hint .nav-inline #story-btn").forEach(el => {
    if (el.parentElement !== nav) el.remove();
  });
  const btn = document.getElementById("story-btn");
  if (btn) {
    btn.textContent = "Findings";
    btn.title = "Guided findings";
    btn.addEventListener("click", () => {
      if (window.storyActive) return;
      if (document.getElementById("tour") && typeof showTour === "function") showTour(99);
      chooser.hidden = !chooser.hidden;
    });
  }

  function hideChooser() { chooser.hidden = true; }

  card.querySelector(".story-exit").onclick = () => exitStory(false);
  card.querySelector('[data-act="back"]').onclick = () => goStep(step - 1);
  card.querySelector('[data-act="next"]').onclick = () => {
    if (!active) return;
    if (step >= active.steps.length - 1) exitStory(true);
    else goStep(step + 1);
  };

  addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    if (!chooser.hidden) { hideChooser(); e.stopImmediatePropagation(); return; }
    if (!window.storyActive) return;
    e.stopImmediatePropagation();
    exitStory(false);
  }, true);

  if (typeof sim !== "undefined" && sim && typeof sim.on === "function") {
    sim.on("tick.story", () => { if (storyAnnotIds) drawAnnot(); });
  }

  function snapIndex(snap) {
    return D.snapshots.indexOf(snap);
  }

  function nodeAlive(id) {
    return byId.has(id);
  }

  function zoomToNodes(ids, padExtra, withNeighbors = true, maxKOpt) {
    if (!ids || !ids.length) {
      if (typeof fit === "function") fit(true);
      else if (typeof G !== "undefined" && G && G.zoomToFit) G.zoomToFit(600, 80);
      return;
    }

    const want = new Set(ids);
    if (withNeighbors && typeof D !== "undefined" && D.links && typeof t === "number") {
      for (const l of D.links) {
        if (!(l.history[t] > 0)) continue;
        const a = l.source.id ?? l.source, b = l.target.id ?? l.target;
        if (want.has(a) || want.has(b)) { want.add(a); want.add(b); }
      }
    }
    ids = [...want];

    const stageEl = document.getElementById("stage");
    const is3d = typeof G !== "undefined" && G && typeof G.zoomToFit === "function" && stageEl && stageEl.tagName !== "svg";
    if (is3d) {
      const set = new Set(ids);
      G.zoomToFit(750, 80, n => set.has(n.id));
      return;
    }

    if (typeof sim === "undefined" || typeof svg === "undefined" || typeof zoom === "undefined") return;
    const targets = sim.nodes().filter(n => ids.includes(n.id) && Number.isFinite(n.x) && Number.isFinite(n.y));
    if (!targets.length) {
      if (typeof fit === "function") fit(true);
      return;
    }
    const rOf = n => (typeof radius === "function" ? radius(n.subs) : 12);
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const n of targets) {
      const r = rOf(n);
      x0 = Math.min(x0, n.x - r);
      x1 = Math.max(x1, n.x + r);
      y0 = Math.min(y0, n.y - r);
      y1 = Math.max(y1, n.y + r);
    }
    // Slightly tighter than full-fit so r/ labels stay readable (map labels scale with k).
    const pad = padExtra != null ? padExtra : 110;
    x0 -= pad; x1 += pad; y0 -= pad; y1 += pad;
    const phone = innerWidth <= 720;
    const px = phone ? 0 : (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--panel-w")) || 360);
    const py = phone ? innerHeight * .46 : 0;
    const w = Math.max(120, innerWidth - px - 48);
    const h = Math.max(120, innerHeight - py - 64);
    const spanX = Math.max(x1 - x0, 40);
    const spanY = Math.max(y1 - y0, 40);
    const maxK = maxKOpt != null ? maxKOpt : 2.35;
    const minK = 0.5;
    let kk = Math.min(w / spanX, h / spanY);
    kk = Math.max(minK, Math.min(maxK, kk));
    const tx = px + 24 + (w - kk * spanX) / 2 - kk * x0;
    const ty = 32 + (h - kk * spanY) / 2 - kk * y0;
    svg.transition().duration(750).ease(d3.easeCubicOut)
      .call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(kk));
  }

  async function applyActions(actions) {
    for (const a of actions || []) {
      switch (a.op) {
        case "reset": {
          if (typeof stopPlay === "function") stopPlay();
          query = "";
          if ($("#q")) $("#q").value = "";
          focus = null;
          picked = null;
          pathLinks = null;
          if (typeof syncChips === "function") syncChips();
          if (typeof update === "function") update();
          break;
        }
        case "setTime": {
          const i = snapIndex(a.snap);
          if (i < 0) break;
          setTime(i);
          break;
        }
        case "track": {
          query = a.term || "";
          if ($("#q")) $("#q").value = query;
          if (typeof syncChips === "function") syncChips();
          if (typeof restyle === "function") restyle();
          break;
        }
        case "clearTrack": {
          query = "";
          if ($("#q")) $("#q").value = "";
          if (typeof syncChips === "function") syncChips();
          if (typeof restyle === "function") restyle();
          break;
        }
        case "focus": {
          if (!nodeAlive(a.id)) break;
          focus = a.id;
          if (typeof restyle === "function") restyle();
          break;
        }
        case "clearFocus": {
          focus = null;
          if (typeof restyle === "function") restyle();
          break;
        }
        case "fit": {
          if (typeof fit === "function") fit(true);
          else if (typeof G !== "undefined" && G && G.zoomToFit) G.zoomToFit(600, 80);
          break;
        }
        case "zoomTo": {
          const ids = (a.ids || []).filter(nodeAlive);
          zoomToNodes(ids, a.pad, a.neighbors !== false, a.maxK);
          break;
        }
        case "annotate": {
          storyAnnotIds = (a.ids || []).filter(nodeAlive);
          drawAnnot();
          break;
        }
        case "clearAnnot": {
          storyAnnotIds = null;
          clearAnnot();
          break;
        }
        case "spot": {
          clearSpot();
          const el = a.sel && document.querySelector(a.sel);
          if (el) {
            el.classList.add("story-spot", "story-lit");
            el.scrollIntoView({ block: "nearest" });
          }
          break;
        }
        case "waitMs": {
          await new Promise(r => setTimeout(r, a.ms || 0));
          break;
        }
        default:
          break;
      }
    }
  }

  function clearSpot() {
    document.querySelectorAll(".story-spot").forEach(el => el.classList.remove("story-spot"));
  }

  function clearLit() {
    document.querySelectorAll(".story-lit").forEach(el => el.classList.remove("story-lit"));
  }

  function clearAnnot() {
    if (typeof g !== "undefined" && g && typeof g.select === "function") {
      g.select("#story-annot").remove();
    } else {
      const el = document.getElementById("story-annot");
      if (el) el.remove();
    }
  }

  function drawAnnot() {
    clearAnnot();
    if (!storyAnnotIds || !storyAnnotIds.length) return;
    if (typeof g === "undefined" || typeof sim === "undefined" || typeof d3 === "undefined") return;
    const layer = g.append("g").attr("id", "story-annot").attr("pointer-events", "none");
    const data = sim.nodes().filter(n => storyAnnotIds.includes(n.id));
    layer.selectAll("circle")
      .data(data, d => d.id)
      .join("circle")
      .attr("cx", d => d.x)
      .attr("cy", d => d.y)
      .attr("r", d => (typeof radius === "function" ? radius(d.subs) : 12) + 12);
  }

  function setLit(sels) {
    clearLit();
    (sels || []).forEach(sel => {
      document.querySelectorAll(sel).forEach(el => el.classList.add("story-lit"));
    });
  }

  function renderCard() {
    if (!active) return;
    const s = active.steps[step];
    card.querySelector(".story-kicker").textContent = active.kicker;
    card.querySelector(".story-title").textContent = s.title;
    card.querySelector(".story-body").innerHTML = s.body;
    card.querySelector(".story-prog").textContent = `${step + 1} / ${active.steps.length}`;
    const back = card.querySelector('[data-act="back"]');
    const next = card.querySelector('[data-act="next"]');
    back.disabled = step === 0 || running;
    next.disabled = running;
    next.textContent = step >= active.steps.length - 1 ? "Done" : "Next";
  }

  async function goStep(i) {
    if (running || !active) return;
    if (i < 0 || i >= active.steps.length) return;
    running = true;
    step = i;
    renderCard();
    const s = active.steps[step];
    document.body.classList.toggle("story-lock", !!s.lock);
    clearSpot();
    setLit(s.lit);
    try {
      await applyActions(s.actions);
    } finally {
      running = false;
      renderCard();
    }
  }

  function enterStory(id) {
    if (window.storyActive) return;
    const story = STORIES.find(s => s.id === id) || STORIES[0];
    if (document.getElementById("tour") && typeof showTour === "function") showTour(99);
    hideChooser();

    saved = {
      tf,
      query,
      focus,
      picked,
      pathLinks,
      crossOnly,
      cats: new Set(activeCats),
    };
    active = story;
    window.storyActive = true;
    document.body.classList.add("story-mode");
    card.hidden = false;
    step = 0;
    goStep(0);
  }

  function exitStory(keepHandoff) {
    if (!window.storyActive) return;
    window.storyActive = false;
    running = false;
    document.body.classList.remove("story-mode", "story-lock");
    card.hidden = true;
    clearSpot();
    clearLit();
    storyAnnotIds = null;
    clearAnnot();
    active = null;

    if (keepHandoff) {
      if (typeof stopPlay === "function") stopPlay();
      return;
    }

    if (saved) {
      if (typeof stopPlay === "function") stopPlay();
      activeCats.clear();
      saved.cats.forEach(c => activeCats.add(c));
      document.querySelectorAll("#cats .cat").forEach(b => b.classList.toggle("off", !activeCats.has(b.dataset.cat)));
      crossOnly = !!saved.crossOnly;
      const ct = $("#cross-theme");
      if (ct) {
        ct.classList.toggle("on", crossOnly);
        ct.setAttribute("aria-pressed", crossOnly ? "true" : "false");
      }
      query = saved.query || "";
      if ($("#q")) $("#q").value = query;
      if (typeof syncChips === "function") syncChips();
      focus = saved.focus;
      picked = saved.picked;
      pathLinks = saved.pathLinks;
      setTime(saved.tf);
      saved = null;
    } else if (typeof resetAll === "function") {
      resetAll();
    }
  }

  window.enterStory = enterStory;
  window.exitStory = exitStory;
})();
