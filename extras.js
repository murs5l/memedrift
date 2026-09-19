// Shared by index.html (2D) and index3d.html (3D): the "connect two subreddits" chain,
// the "when was this?" game, and the first-visit tour. Talks to the page through the
// globals it defines (D, t, query, byId, alive, matches, vmax, update, restyle, $)
// and hands back `pathLinks` (an array of links to light up) which restyle() reads.

let quiz = null;   // pathLinks is declared by the page

// ---------------------------------------------------------------- back / reset
$("#panel").insertAdjacentHTML("afterbegin", `<button type="button" id="back" hidden>← Back to full map <kbd>esc</kbd></button>`);
function resetAll() {
  if (quiz) quitQuiz();
  query = ""; $("#q").value = ""; syncChips();
  focus = null; picked = null; pathLinks = null;
  $("#sub-a").value = $("#sub-b").value = ""; $("#connect-out").innerHTML = "";
  update();
}
$("#back").addEventListener("click", resetAll);
$("#proof").addEventListener("click", e => { if (e.target.id === "proof-close") { picked = null; restyle(); } });
$("#focus").addEventListener("click", e => { if (e.target.id === "focus-close") { focus = null; restyle(); } });
addEventListener("keydown", e => { if (e.key === "Escape") { $("#tour") ? showTour(99) : resetAll(); } });
// restyle() runs on every state change; piggyback to show/hide the bar
const _restyle = restyle;
restyle = function () { _restyle(); $("#back").hidden = !(query || focus || picked || pathLinks || quiz); };

// ---------------------------------------------------------------- panel markup
(document.querySelector(".stack-primary") || $("#spread").closest(".sec")).insertAdjacentHTML("afterend", `
  <div class="sec" id="connect">
    <div class="lbl"><span>Connect two subreddits</span><button type="button" class="btn-text" id="surprise" title="Two random subs from different themes">Surprise me</button></div>
    <div class="pair">
      <input list="subs" id="sub-a" placeholder="r/…" autocomplete="off" aria-label="First subreddit">
      <input list="subs" id="sub-b" placeholder="r/…" autocomplete="off" aria-label="Second subreddit">
    </div>
    <datalist id="subs">${D.nodes.map(n => `<option value="${n.id}">`).join("")}</datalist>
    <div id="connect-out"></div>
  </div>
  <div class="sec" id="quiz">
    <div class="lbl"><span>Game · when was this?</span><button type="button" class="btn-text" id="quiz-start">Play</button></div>
    <div id="quiz-body"></div>
  </div>`);
document.head.insertAdjacentHTML("beforeend", `<style>
  #back {
    position: sticky; top: -18px; z-index: 3;
    margin: -18px -16px 0; padding: 10px 16px;
    border: 0; border-bottom: 1px solid var(--line); border-radius: 0;
    background: var(--panel-2); color: var(--text);
    font: 500 12.5px var(--body); text-align: left; cursor: pointer;
    display: flex; justify-content: space-between; align-items: center; gap: 8px;
  }
  #back[hidden] { display: none !important; }
  #back kbd {
    font: 11px var(--mono); color: var(--muted);
    border: 1px solid var(--line); border-radius: 3px; padding: 1px 5px;
  }
  #back:hover { color: var(--accent); }
  .pair { display: flex; gap: 6px; }
  .pair input { flex: 1; min-width: 0; }
  #connect-out, #quiz-body { font-size: 12px; }
  #connect-out:empty, #quiz-body:empty { display: none; }
  #connect-out .hop, #quiz-body .q {
    padding: 7px 8px; margin-top: 6px;
    background: var(--ink); border: 1px solid var(--line); border-radius: var(--r);
  }
  #quiz-body .chips { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
  .spot { outline: 2px solid var(--accent) !important; outline-offset: 2px; border-radius: var(--r); }
  #tour {
    position: fixed; z-index: 20; max-width: 272px;
    background: var(--panel); border: 1px solid var(--line-strong); border-radius: var(--r);
    padding: 12px 14px; font-size: 13px; box-shadow: 0 6px 24px #0008;
  }
  #tour b { font: 600 14px var(--display); display: block; margin-bottom: 4px; letter-spacing: -.01em; }
  #tour .row { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; gap: 8px; }
</style>`);

// ---------------------------------------------------------------- connect
const liveLinks = () => D.links.filter(l => l.history[t] > 0 && alive(l.source.id ? l.source : byId.get(l.source)) && alive(l.target.id ? l.target : byId.get(l.target)));
const endId = x => x.id ?? x;

// shortest chain of lines from a to b; a hop costs more the weaker its similarity
function chain(a, b) {
  const links = liveLinks(), adj = new Map();
  for (const l of links) {
    const s = endId(l.source), d = endId(l.target);
    (adj.get(s) || adj.set(s, []).get(s)).push([d, l]);
    (adj.get(d) || adj.set(d, []).get(d)).push([s, l]);
  }
  const dist = new Map([[a, 0]]), prev = new Map(), todo = new Set([a]);
  while (todo.size) {   // ponytail: O(V²) Dijkstra, 500 nodes is nothing
    let u = null;
    for (const x of todo) if (u === null || dist.get(x) < dist.get(u)) u = x;
    todo.delete(u);
    if (u === b) break;
    for (const [v, l] of adj.get(u) || []) {
      const nd = dist.get(u) + .15 + (1 - l.value / vmax);
      if (nd < (dist.get(v) ?? Infinity)) { dist.set(v, nd); prev.set(v, [u, l]); todo.add(v); }
    }
  }
  if (!prev.has(b)) return null;
  const hops = [];
  for (let v = b; v !== a; v = prev.get(v)[0]) hops.unshift(prev.get(v)[1]);
  return hops;
}

function connect(a, b) {
  const out = $("#connect-out");
  pathLinks = null;
  const A = byId.get(a), B = byId.get(b);
  if (!A || !B) { out.innerHTML = ""; restyle(); return; }
  if (a === b) { out.innerHTML = `<span class="muted">pick two different subreddits</span>`; restyle(); return; }
  if (!alive(A) || !alive(B)) { out.innerHTML = `<span class="muted">one of them has no posts at ${D.snapshots[t]} (or its theme is switched off)</span>`; restyle(); return; }

  // direct evidence: signature words both use, else any word both use, with mention counts
  const ta = new Map(A.terms[t]), tb = new Map(B.terms[t]), ua = new Map(A.use[t]), ub = new Map(B.use[t]);
  let direct = [...ta].filter(([w]) => tb.has(w)).sort((p, q) => q[1] * tb.get(q[0]) - p[1] * tb.get(p[0])).map(([w]) => w);
  let kind = "signature words";
  if (!direct.length) { direct = [...ua].filter(([w]) => ub.has(w)).sort((p, q) => Math.min(q[1], ub.get(q[0])) - Math.min(p[1], ub.get(p[0]))).map(([w]) => w); kind = "words"; }
  const count = (n, w) => new Map(n.use[t]).get(w) ?? "<1";
  const directHtml = direct.length
    ? `<div>Both say <span class="kw2">${direct[0]}</span> <span class="muted">(r/${a} ${count(A, direct[0])}×, r/${b} ${count(B, direct[0])}× in their 100 posts)</span>${direct.length > 1 ? `<span class="muted"> · also ${direct.slice(1, 6).join(", ")}</span>` : ""}</div>`
    : `<div class="muted">No shared ${kind} at all at ${D.snapshots[t]}: these two live in different worlds.</div>`;

  // the chain: who has to be in the room for these two to understand each other
  const hops = chain(a, b);
  let chainHtml;
  if (!hops) chainHtml = `<div class="muted" style="margin-top:6px">And no chain of lines connects them on this map.</div>`;
  else {
    let cur = a;
    chainHtml = `<div class="muted" style="margin-top:8px">${hops.length === 1 ? "They're directly linked:" : `${hops.length} hops apart on the map:`}</div>` +
      hops.map(l => { const nxt = endId(l.source) === cur ? endId(l.target) : endId(l.source);
        const h = `<div class="hop">r/${cur} <span class="muted">·</span> <span class="kw2">${l.shared[t][0]}</span> <span class="muted">→</span> r/${nxt} <span class="muted" style="float:right">${Math.round(100 * l.value / vmax)}</span></div>`;
        cur = nxt; return h; }).join("");
    pathLinks = hops;
  }
  out.innerHTML = `<button type="button" class="x" id="connect-clear" title="clear">✕ clear</button>` + directHtml + chainHtml + `<div class="muted" style="margin-top:6px">Chain lit on the map. Move the timeline to see it change.</div>`;
  $("#connect-clear").onclick = () => { pathLinks = null; $("#sub-a").value = $("#sub-b").value = ""; out.innerHTML = ""; restyle(); };
  focus = null; picked = null;
  restyle();
}
const readPair = () => connect($("#sub-a").value.trim().replace(/^r\//i, ""), $("#sub-b").value.trim().replace(/^r\//i, ""));
$("#sub-a").addEventListener("change", readPair);
$("#sub-b").addEventListener("change", readPair);
$("#surprise").addEventListener("click", () => {
  const live = D.nodes.filter(alive);
  for (let i = 0; i < 40; i++) {   // two different themes, and a chain that exists
    const A = live[Math.random() * live.length | 0], B = live[Math.random() * live.length | 0];
    if (A.cat === B.cat || A === B) continue;
    if (i < 30 && !chain(A.id, B.id)) continue;
    $("#sub-a").value = A.id; $("#sub-b").value = B.id; connect(A.id, B.id); return;
  }
});
// re-run the chain when the snapshot changes so it never shows stale hops
const _update = update;
update = function () { _update(); if (pathLinks && $("#sub-a").value && $("#sub-b").value) readPair(); };

// ---------------------------------------------------------------- quiz: when was this?
$("#quiz-start").addEventListener("click", startQuiz);
function startQuiz() {
  quiz = { round: 0, score: 0, saved: { t, query } };
  pathLinks = null; focus = null; picked = null; $("#connect-out").innerHTML = "";   // a lit chain would clutter the clue
  $(".time").hidden = true; $("#spread").parentElement.hidden = true;   // the slider and the spread bars would give it away
  nextRound();
}
function nextRound() {
  if (quiz.round === 5) return endQuiz();
  quiz.round++;
  // a snapshot where at least 3 subs actually say the word (so the map shows something to reason from)
  const saying = (term, i) => D.nodes.filter(n => n.use[i].some(([w]) => w === term)).length;
  let m, candidates = [];
  for (let tries = 0; tries < 30 && candidates.length < 2; tries++) {
    m = D.memes[Math.random() * D.memes.length | 0];
    candidates = D.snapshots.map((_, i) => i).filter(i => saying(m.term, i) >= 3);
  }
  quiz.answer = candidates[Math.random() * candidates.length | 0];
  tf = t = quiz.answer; query = m.term; $("#q").value = m.term;
  update();
  $("#quiz-body").innerHTML = `<div class="q"><button type="button" class="x" id="quiz-quit">✕ quit</button>Round ${quiz.round}/5 · score ${quiz.score}<br>The map is lit for <span class="kw2">${m.term}</span>. Look at who says it, how many, and the shape of the graph. <b>When is this?</b></div>
    <div class="chips">${D.snapshots.map((s, i) => `<button type="button" class="chip" data-i="${i}">${s}</button>`).join("")}</div>`;
  $("#quiz-body .chips").addEventListener("click", e => {
    const b = e.target.closest(".chip"); if (!b || quiz.locked) return;
    quiz.locked = true;
    const g = +b.dataset.i, off = Math.abs(g - quiz.answer), pts = off === 0 ? 3 : off === 1 ? 1 : 0;
    quiz.score += pts;
    b.classList.add(pts ? "right" : "wrong");
    $(`#quiz-body .chip[data-i="${quiz.answer}"]`).classList.add("right");
    $("#quiz-body .q").insertAdjacentHTML("beforeend", `<div style="margin-top:6px">${pts === 3 ? "Exactly right" : pts ? "One step off" : "Not that one"}, it was <b>${D.snapshots[quiz.answer]}</b> (+${pts}). <button type="button" class="chip" id="quiz-next">next</button></div>`);
    $("#quiz-next").addEventListener("click", () => { quiz.locked = false; nextRound(); });
  });
  $("#quiz-quit").onclick = quitQuiz;
}
function quitQuiz() {   // restore what the player was looking at before the game
  $(".time").hidden = false; $("#spread").parentElement.hidden = false;
  $("#quiz-body").innerHTML = "";
  ({ t, query } = quiz.saved); tf = t; $("#q").value = query; quiz = null; syncChips(); update();
}
function endQuiz() {
  $(".time").hidden = false; $("#spread").parentElement.hidden = false;
  const s = quiz.score;
  $("#quiz-body").innerHTML = `<div class="q">Final score <b>${s} / 15</b>. ${s >= 12 ? "You can date a subreddit by its vocabulary. That is the whole thesis." : s >= 6 ? "Words drift fast; you caught most of it." : "Memes move faster than they look. Try tracking one with ▶ first."} <button type="button" class="chip" id="quiz-again">play again</button></div>`;
  $("#quiz-again").addEventListener("click", startQuiz);
  ({ t, query } = quiz.saved); tf = t; $("#q").value = query; quiz = null; update();
}

// ---------------------------------------------------------------- first-visit tour
const TOUR = [
  ["#q", "Track a meme", "Type an exact word (<i>ai</i>, <i>tariffs</i>, <i>brainrot</i>) and every subreddit saying it lights up, sized by how often."],
  ["#memes", "Fastest spreading", "These words jumped into the most new communities over the timeline. Click one."],
  [".time", "Play the timeline", "Hit ▶ and watch the word spread and the map re-knit itself, snapshot by snapshot."],
  ["#connect", "Connect two subreddits", "Pick any two, say r/cpp and r/Parenting, and see the exact words and the chain of communities that link them."],
  ["#stage", "The map", "Every line is shared vocabulary; shorter = more alike. Hover a line for the word, click it for the posts that prove it."],
];
let tourStep = -1;
function showTour(i) {
  document.querySelectorAll(".spot").forEach(e => e.classList.remove("spot"));
  $("#tour")?.remove();
  tourStep = i;
  if (i < 0 || i >= TOUR.length) { try { localStorage.setItem("memedrift-tour", "1"); } catch {} return; }
  const [sel, title, text] = TOUR[i], target = $(sel);
  target.classList.add("spot");
  if (sel !== "#stage") target.scrollIntoView({ block: "nearest" });
  document.body.insertAdjacentHTML("beforeend", `<div id="tour" role="dialog" aria-label="${title}"><b>${title}</b>${text}<div class="row"><span class="muted">${i + 1} / ${TOUR.length}</span><span><button type="button" class="chip" id="tour-skip">Skip</button> <button type="button" class="chip on" id="tour-next">${i === TOUR.length - 1 ? "Done" : "Next"}</button></span></div></div>`);
  const r = target.getBoundingClientRect(), card = $("#tour");
  const phone = innerWidth <= 720;
  card.style.left = phone ? "16px" : Math.min(innerWidth - 300, sel === "#stage" ? innerWidth / 2 - 140 : r.right + 14) + "px";
  card.style.top = phone ? "16px" : Math.max(16, Math.min(innerHeight - 180, sel === "#stage" ? innerHeight / 2 - 60 : r.top)) + "px";
  $("#tour-next").onclick = () => showTour(i + 1);
  $("#tour-skip").onclick = () => showTour(99);
}
const hintNav = document.querySelector(".hint .nav-inline") || document.querySelector(".hint");
hintNav.insertAdjacentHTML("beforeend", ` <button type="button" class="btn-text" id="tour-btn">Tour</button>`);
$("#tour-btn").addEventListener("click", () => showTour(0));
let seen = false;
try { seen = !!localStorage.getItem("memedrift-tour"); } catch {}
if (!seen) setTimeout(() => showTour(0), 1200);
