// Cursor SDK explanations for focus / path / picked edge.
// Needs explain_server.py (CURSOR_API_KEY or paste under Explain → Key).

(function () {
  const KEY_LS = "memedrift-cursor-key";
  const panel = document.createElement("div");
  panel.id = "explain";
  panel.hidden = true;
  panel.innerHTML = `
    <div class="lbl">
      <span>Explain · Cursor</span>
      <span class="explain-tools">
        <button type="button" class="btn-text" id="explain-key-btn" title="API key">Key</button>
        <button type="button" class="x" id="explain-close" aria-label="Close">✕</button>
      </span>
    </div>
    <div id="explain-keybox" hidden>
      <label class="explain-key-label">Cursor User API key
        <input type="password" id="explain-key" autocomplete="off" spellcheck="false" placeholder="cursor_… or key_…">
      </label>
      <p class="muted explain-key-hint">Create one at <a href="https://cursor.com/dashboard/api" target="_blank" rel="noopener">cursor.com/dashboard/api</a>. Uses your Cursor credits. Stored only in this browser.</p>
      <button type="button" class="chip on" id="explain-key-save">Save key</button>
    </div>
    <div id="explain-body" class="explain-body muted">Select a subreddit, a line, or a connect-path, then hit Explain.</div>
    <button type="button" class="chip on" id="explain-run" disabled>Explain selection</button>`;

  const host = document.getElementById("focus") || document.getElementById("proof");
  if (host) host.insertAdjacentElement("afterend", panel);
  else document.getElementById("panel")?.appendChild(panel);

  document.head.insertAdjacentHTML("beforeend", `<style>
    #explain {
      display: none; margin: 10px 0 12px; padding: 10px 12px;
      background: var(--panel-2); border: 1px solid var(--line); border-radius: var(--r);
    }
    #explain:not([hidden]) { display: block; }
    #explain .explain-tools { display: inline-flex; gap: 8px; align-items: center; }
    #explain .explain-body {
      font: 400 12.5px/1.5 var(--body); color: var(--text);
      margin: 8px 0 10px; white-space: normal;
    }
    #explain .explain-body.muted { color: var(--muted); white-space: pre-wrap; }
    #explain .explain-body.err { color: #e8a0a0; white-space: pre-wrap; }
    #explain .explain-body p { margin: 0 0 0.65em; }
    #explain .explain-body p:last-child { margin-bottom: 0; }
    #explain .explain-kicker {
      display: block; font: 500 10.5px var(--mono); color: var(--accent);
      letter-spacing: .08em; text-transform: uppercase; margin-bottom: 4px;
    }
    #explain .explain-answer { font-size: 13.5px; color: var(--text); }
    #explain .explain-reason { color: #c9cedb; }
    #explain .explain-body b, #explain .explain-body strong { color: var(--text); font-weight: 600; }
    #explain .explain-body i, #explain .explain-body em { font-style: italic; color: var(--text); }
    #explain .explain-body code {
      font: 500 11.5px var(--mono); color: var(--accent);
      background: var(--ink); padding: 1px 4px; border-radius: 3px;
    }
    #explain-keybox { margin: 8px 0; }
    #explain .explain-key-label {
      display: block; font: 500 11px var(--mono); color: var(--muted); margin-bottom: 6px;
    }
    #explain-key {
      width: 100%; box-sizing: border-box; margin-top: 4px;
      background: var(--ink); border: 1px solid var(--line); border-radius: var(--r);
      color: var(--text); padding: 8px 10px; font: 12px var(--mono);
    }
    #explain .explain-key-hint { font-size: 11px; margin: 6px 0 8px; }
    #explain .explain-key-hint a { color: var(--accent); }
    #explain-run { width: 100%; justify-content: center; }
    #explain-run:disabled { opacity: .45; cursor: default; }
    .explain-inline {
      margin-top: 8px; width: 100%;
      border: 1px solid var(--line); background: var(--panel);
      color: var(--accent); border-radius: var(--r);
      font: 600 11px var(--mono); letter-spacing: .04em; text-transform: uppercase;
      padding: 8px 10px; cursor: pointer;
    }
    .explain-inline:hover { border-color: var(--accent); background: var(--accent-dim); }
  </style>`);

  const bodyEl = panel.querySelector("#explain-body");
  const runBtn = panel.querySelector("#explain-run");
  const keyBox = panel.querySelector("#explain-keybox");
  const keyInput = panel.querySelector("#explain-key");

  // Park next to whichever UI owns the selection (proof is at panel top; focus is lower).
  function parkExplain() {
    let anchor = null;
    if (picked) anchor = document.getElementById("proof");
    else if (pathLinks && pathLinks.length) anchor = document.getElementById("connect-out") || document.getElementById("connect");
    else if (focus) anchor = document.getElementById("focus");
    if (!anchor) anchor = document.getElementById("focus") || document.getElementById("proof");
    if (!anchor) return;
    if (panel.previousElementSibling === anchor) return;
    anchor.insertAdjacentElement("afterend", panel);
  }

  parkExplain();

  try { keyInput.value = localStorage.getItem(KEY_LS) || ""; } catch {}

  panel.querySelector("#explain-close").onclick = () => { panel.hidden = true; };
  panel.querySelector("#explain-key-btn").onclick = () => {
    keyBox.hidden = !keyBox.hidden;
    if (!keyBox.hidden) keyInput.focus();
  };
  panel.querySelector("#explain-key-save").onclick = () => {
    const v = keyInput.value.trim();
    try {
      if (v) localStorage.setItem(KEY_LS, v);
      else localStorage.removeItem(KEY_LS);
    } catch {}
    keyBox.hidden = true;
    bodyEl.className = "explain-body muted";
    bodyEl.textContent = v ? "Key saved in this browser. Click Explain selection." : "Key cleared.";
  };
  runBtn.onclick = () => explainNow();

  function getKey() {
    try { return (localStorage.getItem(KEY_LS) || "").trim(); } catch { return ""; }
  }

  function escHtml(s) {
    return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  // Safe subset: escape HTML, then **bold**, *italic*, `code`, blank-line paragraphs.
  function formatExplain(text) {
    let s = escHtml(text || "").replace(/\r\n/g, "\n").trim();
    s = s.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*Answer\.?\*\*/gi, '<span class="explain-kicker">Answer</span>');
    s = s.replace(/\*\*Reason\.?\*\*/gi, '<span class="explain-kicker">Reason</span>');
    s = s.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
    s = s.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<i>$2</i>");
    s = s.replace(/\*\*/g, "");
    const parts = s.split(/\n{2,}/).map(p => p.replace(/\n/g, " ").trim()).filter(Boolean);
    if (!parts.length) return "(empty reply)";
    return parts.map((p, i) => `<p class="${i === 0 ? "explain-answer" : "explain-reason"}">${p}</p>`).join("");
  }

  function setExplainHtml(html, cls) {
    bodyEl.className = "explain-body" + (cls ? " " + cls : "");
    bodyEl.innerHTML = html;
  }

  function setExplainText(text, cls) {
    bodyEl.className = "explain-body" + (cls ? " " + cls : "");
    bodyEl.textContent = text;
  }

  function nodePack(n) {
    if (!n) return null;
    return {
      id: n.id,
      theme: (typeof catName !== "undefined" && catName[n.cat]) || n.cat,
      members: n.subs,
      signature: n.terms?.[t]?.[0]?.[0] || null,
      top_words: (n.terms?.[t] || []).slice(0, 8).map(x => x[0]),
      tracked_mentions: (typeof query === "string" && query && typeof heat === "function") ? (heat(n) || 0) : 0,
    };
  }

  function edgePack(l) {
    const a = l.source.id ?? l.source, b = l.target.id ?? l.target;
    const shared = l.shared?.[t] || [];
    const proof = l.proof?.[t];
    return {
      from: a,
      to: b,
      bridge_word: shared[0] || null,
      also_share: shared.slice(1, 6),
      similarity_0_100: (typeof vmax === "number" && vmax) ? Math.round(100 * l.value / vmax) : null,
      mention_counts: proof ? { [a]: proof[0], [b]: proof[1] } : null,
    };
  }

  function buildContext() {
    const snap = D.snapshots[t];
    if (picked) {
      return {
        kind: "edge",
        snapshot: snap,
        tracked_word: query || null,
        nodes: [nodePack(picked.source.id ? picked.source : byId.get(picked.source)),
                nodePack(picked.target.id ? picked.target : byId.get(picked.target))].filter(Boolean),
        edges: [edgePack(picked)],
      };
    }
    if (pathLinks && pathLinks.length) {
      const ids = [];
      const seen = new Set();
      for (const l of pathLinks) {
        for (const id of [l.source.id ?? l.source, l.target.id ?? l.target]) {
          if (!seen.has(id)) { seen.add(id); ids.push(id); }
        }
      }
      return {
        kind: "path",
        snapshot: snap,
        tracked_word: query || null,
        nodes: ids.map(id => nodePack(byId.get(id))).filter(Boolean),
        edges: pathLinks.map(edgePack),
        hop_count: pathLinks.length,
      };
    }
    if (focus) {
      const n = byId.get(focus);
      const fl = (typeof linksOf === "function") ? linksOf(focus) : [];
      return {
        kind: "focus",
        snapshot: snap,
        tracked_word: query || null,
        nodes: [nodePack(n)].filter(Boolean),
        neighbor_bridges: fl.slice(0, 8).map(l => {
          const o = (typeof other === "function") ? other(l, focus) : null;
          return {
            neighbor: o?.id,
            bridge_word: l.shared?.[t]?.[0] || null,
            similarity_0_100: vmax ? Math.round(100 * l.value / vmax) : null,
          };
        }),
      };
    }
    return null;
  }

  function syncPanel() {
    parkExplain();
    const ctx = buildContext();
    const show = !!ctx;
    panel.hidden = !show;
    runBtn.disabled = !show;
    if (!show) return;
    if (bodyEl.dataset.locked === "1") return;
    const label = ctx.kind === "path"
      ? `Path · ${ctx.nodes.map(n => "r/" + n.id).join(" → ")}`
      : ctx.kind === "edge"
        ? `Edge · r/${ctx.nodes[0]?.id} ↔ r/${ctx.nodes[1]?.id} · ${ctx.edges[0]?.bridge_word || "…"}`
        : `Focus · r/${ctx.nodes[0]?.id}`;
    const hint = `${label} (${ctx.snapshot}). Explain writes a fresh reading each time.`;
    if (bodyEl.dataset.hint === hint) return;
    bodyEl.dataset.hint = hint;
    runBtn.textContent = "Explain selection";
    bodyEl.className = "explain-body muted";
    bodyEl.textContent = hint;
  }

  async function explainNow() {
    const ctx = buildContext();
    if (!ctx) return;
    parkExplain();
    panel.hidden = false;
    panel.scrollIntoView({ block: "nearest", behavior: "smooth" });
    bodyEl.dataset.locked = "1";
    setExplainText("Asking Cursor… (first reply can take ~30–60s)", "muted");
    runBtn.textContent = "Explain selection";
    runBtn.disabled = true;
    const headers = { "Content-Type": "application/json" };
    const key = getKey();
    if (key) headers["X-Cursor-Key"] = key;
    const payload = JSON.stringify({ context: ctx });
    const urls = [
      "/api/explain",
      "http://127.0.0.1:8765/api/explain",
      "http://127.0.0.1:8767/api/explain",
    ];
    try {
      let res, lastErr;
      for (const url of urls) {
        try {
          res = await fetch(url, { method: "POST", headers, body: payload });
          lastErr = null;
          break;
        } catch (err) { lastErr = err; }
      }
      if (!res) throw lastErr || new Error("no explain server");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setExplainText(data.error || `Request failed (${res.status})`, "err");
        if (res.status === 401) keyBox.hidden = false;
        return;
      }
      setExplainHtml(formatExplain(data.text || "(empty reply)"));
      panel.scrollIntoView({ block: "nearest", behavior: "smooth" });
    } catch (e) {
      setExplainText("Explain server not on this page. Open http://127.0.0.1:8765/ and try again.", "err");
    } finally {
      bodyEl.dataset.locked = "0";
      runBtn.disabled = !buildContext();
    }
  }

  function ensureInlineButton(root, id) {
    if (!root || root.querySelector("#" + id)) return;
    const b = document.createElement("button");
    b.type = "button";
    b.id = id;
    b.className = "explain-inline";
    b.textContent = "Explain with Cursor";
    b.onclick = e => {
      e.stopPropagation();
      parkExplain();
      panel.hidden = false;
      explainNow();
    };
    root.appendChild(b);
  }

  if (typeof restyle === "function") {
    const prev = restyle;
    let lastSel = "";
    restyle = function () {
      prev();
      const sel = `${focus || ""}|${picked ? 1 : 0}|${pathLinks ? pathLinks.length : 0}|${typeof t === "number" ? t : ""}`;
      const focusEl = document.getElementById("focus");
      if (focus && focusEl && focusEl.style.display !== "none") {
        ensureInlineButton(focusEl, "explain-focus-btn");
      }
      const proofEl = document.getElementById("proof");
      if (picked && proofEl && proofEl.style.display !== "none") {
        ensureInlineButton(proofEl, "explain-proof-btn");
      }
      const out = document.getElementById("connect-out");
      if (out && pathLinks && pathLinks.length) {
        ensureInlineButton(out, "explain-path-btn");
      }
      if (sel !== lastSel) { lastSel = sel; syncPanel(); }
    };
  }

  syncPanel();
  window.explainSelection = explainNow;
})();
