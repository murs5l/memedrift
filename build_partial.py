"""
Incremental data.js builder. Reads only the Arctic Shift cache (no network),
keeps every month that already has posts for enough subreddits, and rewrites
data.js + data.meta.json so the live UI can pick up history as the long fetch runs.

    python3 build_partial.py          # one shot
    python3 build_partial.py watch    # rebuild whenever coverage grows
"""
from __future__ import annotations

import json, math, os, sys, time
from collections import Counter, defaultdict
from urllib.parse import urlencode

import numpy as np

import build_data as bd

HERE = bd.HERE
CACHE = bd.CACHE
MIN_SUBS = 80          # ship a month once this many subs are cached for it
GROW_BY = 20           # watch mode: rebuild after this many new unique subs
WATCH_S = 90           # watch poll interval


def cache_path(path, **params):
    return os.path.join(CACHE, bd.re.sub(r"[^\w]+", "_", path + urlencode(sorted(params.items()))) + ".json")


def load_json(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def posts_cache_key(sub, before):
    return cache_path("/api/posts/search", subreddit=sub, before=before, limit=100, sort="desc", fields=bd.FIELDS)


def cached_posts(sub, before):
    data = load_json(posts_cache_key(sub, before))
    if data is None:
        return None
    return [bd.re.sub(r"\[ ?Removed by \w+ ?\]", "", f"{p.get('title') or ''}\n{(p.get('selftext') or '')[:1500]}").strip()
            for p in data]


def coverage(names, snapshots):
    """label -> list of subs with a cache hit (existence only)."""
    hit = {lbl: [] for lbl, _ in snapshots}
    for s in names:
        for lbl, before in snapshots:
            if os.path.exists(posts_cache_key(s, before)):
                hit[lbl].append(s)
    return hit


def unique_cached_subs(names, before="2023-07-01"):
    return sum(1 for s in names if os.path.exists(posts_cache_key(s, before)))


def name_list(big):
    names = [s["display_name"] for s in big if s["display_name"] not in bd.EXCLUDE and not s["display_name"].startswith("u_")][:bd.TOP_N]
    return list(dict.fromkeys(names + bd.SEEDS))


def build(force=False):
    big = load_json(cache_path("/api/subreddits/search", min_subscribers=400000, limit=1000, over18="false"))
    if not big:
        print("subreddit list not cached yet; waiting for the main fetch to land it", flush=True)
        return None

    names = name_list(big)
    info = {s["display_name"].lower(): s for s in big}
    snapshots = bd.YEARLY

    hit = coverage(names, snapshots)
    ready = [(lbl, before) for lbl, before in snapshots if len(hit[lbl]) >= MIN_SUBS]
    if len(ready) < 2:
        best = max((len(v) for v in hit.values()), default=0)
        print(f"not enough months ready yet (need ≥{MIN_SUBS} subs/month); best={best}", flush=True)
        return None

    n_subs = len({s for lbl, _ in ready for s in hit[lbl]})
    meta_path = os.path.join(HERE, "data.meta.json")
    prev = load_json(meta_path) or {}
    if not force and prev.get("subs") == n_subs and prev.get("snapshots") == [lbl for lbl, _ in ready]:
        print(f"unchanged: {len(ready)} months, {n_subs} subs", flush=True)
        return prev

    print(f"building {len(ready)} months × ~{n_subs} subs from cache…", flush=True)
    t0 = time.time()

    posts, texts = {}, {}
    for s in names:
        for snap in ready:
            raw = cached_posts(s, snap[1])
            if raw is None:
                continue
            j = (s, snap)
            posts[j] = raw
            texts[j] = " ".join(raw)

    docs = {j: Counter(bd.tokens(t)) for j, t in texts.items()}
    docs = {j: c for j, c in docs.items() if sum(c.values()) >= 200}
    df = Counter()
    for c in docs.values():
        df.update(c.keys())
    vocab = [t for t, n in df.items() if n >= 3]
    if len(vocab) < 50 or len(docs) < 50:
        print(f"too thin to ship yet (docs={len(docs)}, vocab={len(vocab)})", flush=True)
        return None
    idx = {t: i for i, t in enumerate(vocab)}
    idf = np.log(len(docs) / (1 + np.array([df[t] for t in vocab], dtype=np.float32)))

    vecs = {}
    for j, c in docs.items():
        v = np.zeros(len(vocab), dtype=np.float32)
        for t, n in c.items():
            if t in idx:
                v[idx[t]] = 1 + math.log(n)
        v *= idf
        vecs[j] = v / (np.linalg.norm(v) or 1)

    def top_terms(v, n):
        if v is None or not len(v):
            return []
        k = min(n, max(len(v) - 1, 1))
        ix = np.argpartition(-v, k)[:n]
        return [(vocab[i], round(float(v[i]), 4)) for i in ix[np.argsort(-v[ix])] if v[i] > 0]

    live_names = sorted({s for s, _ in vecs})
    pairs, adj = {}, defaultdict(Counter)
    for si, snap in enumerate(ready):
        live = [s for s in live_names if (s, snap) in vecs]
        if len(live) < 3:
            continue
        M = np.stack([vecs[(s, snap)] for s in live])
        S = M @ M.T
        np.fill_diagonal(S, -1)
        for i, a in enumerate(live):
            for jx in np.argsort(-S[i])[:bd.K]:
                b = live[jx]
                key = (min(a, b), max(a, b), si)
                pairs[key] = float(S[i, jx])
                adj[a][b] += S[i, jx]
                adj[b][a] += S[i, jx]

    links = []
    for a, b in sorted({(a, b) for a, b, _ in pairs}):
        hist, shared, proof = [], [], []
        for si, snap in enumerate(ready):
            s = pairs.get((a, b, si))
            if s is None:
                hist.append(0); shared.append([]); proof.append(None)
            else:
                hist.append(round(s, 3))
                shared.append([t for t, _ in top_terms(vecs[(a, snap)] * vecs[(b, snap)], 5)])
                kw = shared[-1][0]
                proof.append([docs[(a, snap)][kw], docs[(b, snap)][kw]])
        links.append({"source": a, "target": b, "history": hist, "shared": shared, "proof": proof})

    cat_of = bd.communities(live_names, adj, bd.SEED_OF)
    sizes = Counter(cat_of.values())
    categories = []
    for l in list(bd.THEMES) + ["Other"]:
        acc = np.zeros(len(vocab), dtype=np.float32)
        for n in live_names:
            if cat_of[n] != l:
                continue
            for snap in reversed(ready):
                if (n, snap) in vecs:
                    acc += vecs[(n, snap)]; break
        categories.append({"id": l, "name": l, "words": " · ".join(t for t, _ in top_terms(acc, 3)), "size": sizes[l]})
    categories = [c for c in categories if c["size"]]

    nodes = []
    for s in live_names:
        node = {"id": s, "cat": cat_of[s], "subs": info.get(s.lower(), {}).get("subscribers") or 1000, "terms": [], "use": []}
        for snap in ready:
            v = vecs.get((s, snap))
            node["terms"].append(top_terms(v, 40) if v is not None else [])
            node["use"].append(docs[(s, snap)].most_common(60) if (s, snap) in docs else [])
        nodes.append(node)

    spread = defaultdict(lambda: [0] * len(ready))
    for n in nodes:
        for si, terms in enumerate(n["terms"]):
            for t, _ in terms:
                spread[t][si] += 1
    memes = sorted(spread.items(), key=lambda kv: -(kv[1][-1] - max(kv[1][:3] + [0])))[:30]
    memes = [{"term": t, "spread": sp} for t, sp in memes if sp[-1] >= 3]

    out = {"snapshots": [lbl for lbl, _ in ready], "categories": categories,
           "nodes": nodes, "links": links, "memes": memes}
    with open(os.path.join(HERE, "data.js"), "w") as f:
        f.write("window.DATA = " + json.dumps(out, separators=(",", ":")) + ";\n")
    for lbl, date in ready:
        titles = {s: [p.split("\n", 1)[0][:140] for p in posts[(s, (lbl, date))]]
                  for s in live_names if (s, (lbl, date)) in posts}
        with open(os.path.join(HERE, f"posts_{lbl}.js"), "w") as f:
            f.write(f"window.POSTS = window.POSTS || {{}}; window.POSTS[{lbl!r}] = " + json.dumps(titles, separators=(",", ":")) + ";\n")

    meta = {
        "snapshots": out["snapshots"],
        "nodes": len(nodes),
        "links": len(links),
        "subs": n_subs,
        "months": len(ready),
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "span": f"{out['snapshots'][0]} → {out['snapshots'][-1]}",
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f)
    print(f"wrote data.js in {time.time() - t0:.1f}s: {meta['span']}, "
          f"{meta['nodes']} nodes, {meta['links']} links, {meta['subs']} cached subs", flush=True)
    return meta


def watch():
    print(f"watching cache every {WATCH_S}s (rebuild every +{GROW_BY} subs)…", flush=True)
    last_subs = -1
    while True:
        try:
            big = load_json(cache_path("/api/subreddits/search", min_subscribers=400000, limit=1000, over18="false")) or []
            names = name_list(big) if big else []
            n = unique_cached_subs(names) if names else 0
            if n >= MIN_SUBS and (last_subs < 0 or n >= last_subs + GROW_BY):
                print(f"coverage ~{n} subs (was {last_subs}) — rebuilding", flush=True)
                meta = build(force=True)
                if meta:
                    last_subs = meta["subs"]
            else:
                nxt = last_subs + GROW_BY if last_subs >= 0 else MIN_SUBS
                print(f"waiting… ~{n} cached subs (next rebuild at {nxt})", flush=True)
        except Exception as e:
            print(f"watch tick failed: {e}", flush=True)
        time.sleep(WATCH_S)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        watch()
    else:
        build(force=True)
