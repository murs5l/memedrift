"""
Pre-bake a Cursor explanation for each curated pair, so a demo never waits on the model.

    /tmp/memedrift-venv/bin/python explain_server.py &    # must be running
    python3 cache_explains.py                            # ~40s per pair, resumable

Writes data/explains.js as `window.EXPLAINS = {"<subA>|<subB>|<snapshot>": "…"}`, keyed
the same way app/explain.js looks it up (the two names sorted). The payload posted here
is the exact context object the page would have sent, so the saved answer is the answer
you would have gotten by clicking Explain — the button still offers a live re-run.
"""
import json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "explains.js")
API = os.environ.get("EXPLAIN_URL", "http://127.0.0.1:8767/api/explain")
TIMEOUT = 300


def read_window(path, opener):
    src = open(path).read()
    return json.loads(src[src.index(opener):src.rstrip().rstrip(";").rindex({"{": "}", "[": "]"}[opener]) + 1])


def node_pack(n, i, theme):
    return {
        "id": n["id"],
        "theme": theme,
        "members": n["subs"],
        "signature": n["terms"][i][0][0] if n["terms"][i] else None,
        "top_words": [w for w, _ in n["terms"][i][:8]],
        "tracked_mentions": 0,
    }


def context_for(p, d, vmax):
    i = p["i"]
    theme = {c["id"]: c["name"] for c in d["categories"]}
    by_id = {n["id"]: n for n in d["nodes"]}
    link = next(l for l in d["links"]
                if {l["source"], l["target"]} == {p["a"], p["b"]})
    shared = link["shared"][i]
    proof = link["proof"][i]
    a, b = link["source"], link["target"]
    return {
        "kind": "edge",
        "snapshot": d["snapshots"][i],
        "tracked_word": None,
        "nodes": [node_pack(by_id[a], i, theme[by_id[a]["cat"]]),
                  node_pack(by_id[b], i, theme[by_id[b]["cat"]])],
        "edges": [{
            "from": a, "to": b,
            "bridge_word": shared[0] if shared else None,
            "also_share": shared[1:6],
            "similarity_0_100": round(100 * link["history"][i] / vmax),
            "mention_counts": {a: proof[0], b: proof[1]} if proof else None,
        }],
    }


def ask(ctx):
    req = urllib.request.Request(API, method="POST", data=json.dumps({"context": ctx}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)["text"]


def main():
    force = "--force" in sys.argv
    d = read_window(os.path.join(HERE, "data", "data.js"), "{")
    pairs = read_window(os.path.join(HERE, "data", "pairs.js"), "[")
    vmax = max(max(l["history"]) for l in d["links"])

    saved = {}
    if os.path.exists(OUT) and not force:
        saved = read_window(OUT, "{")

    for n, p in enumerate(pairs, 1):
        key = "|".join(sorted([p["a"], p["b"]])) + "|" + p["snap"]
        head = f"[{n}/{len(pairs)}] r/{p['a']} ~ r/{p['b']} · {p['kw']} · {p['snap']}"
        if key in saved:
            print(f"{head}  (cached)")
            continue
        print(f"{head}  asking…", end=" ", flush=True)
        t0 = time.time()
        try:
            saved[key] = ask(context_for(p, d, vmax))
        except urllib.error.URLError as e:
            print(f"\n  ! {e}. Is explain_server.py up on {API}?", file=sys.stderr)
            break
        print(f"{time.time() - t0:.0f}s, {len(saved[key])} chars")
        with open(OUT, "w") as f:   # write as we go; the run is resumable
            f.write("window.EXPLAINS = " + json.dumps(saved, ensure_ascii=False, indent=1) + ";\n")

    print(f"\n{len(saved)} of {len(pairs)} pairs cached in {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
