"""
Strange bedfellows: subreddit pairs that sit close on the map without belonging together.

    python3 find_pairs.py            # rank candidates, write data/pairs.js
    python3 find_pairs.py --show 40  # print more of the ranking for hand-picking

Reads data/data.js only — no network, no cache, nothing to rebuild.

The naive version of this ("strongest cross-theme edge") is useless: the top of that
list is r/Economics ~ r/europe at 0.713 similarity, bridged by `vallevirtual` with 11
mentions in a single month. Spam tokens and non-English proper nouns dominate raw
similarity because one weird word in a quiet month can carry a whole TF-IDF vector.
So a pair has to survive four filters before it counts as a finding:

  persistent   linked across many months, not one spike
  real word    the bridge word is used by lots of subreddits, so it isn't spam
  not tautological  `anime` linking r/anime to r/anime_irl proves nothing
  unrelated    different themes, and they share almost none of their other neighbours
"""
import json, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "data.js")
OUT = os.path.join(HERE, "data", "pairs.js")

MIN_MONTHS = 6          # linked in at least this many snapshots
MIN_TOP_MONTHS = 3      # ... and the same word does the linking in at least this many
MIN_BREADTH = 8         # the bridge word appears in this many subreddits overall
MIN_SUBS = 700_000      # both subs big enough that a judge recognises the names
MAX_JACCARD = .35       # share at most this fraction of their other neighbours
MIN_MENTIONS = 3        # receipts on both sides of the showcased month
KEEP = 12               # pairs written to pairs.js

# Hand-picked from the ranking, in the order they read best out loud. The scan finds
# all of these on its own; a human only chose which ones are worth a judge's attention
# and wrote the one-liners, which no ranking function can do.
# Anything short of KEEP is topped up from the ranking below.
PINNED = [
    ("Parenting", "dogs", "potty", "toddlers and puppies, same training"),
    ("CozyPlaces", "battlestations", "cozy", "a snug room, a snug desk"),
    ("JuJutsuKaisen", "cursedcomments", "cursed", "cursed energy vs cursed images"),
    ("AnimalCrossing", "CozyPlaces", "nook", "Tom Nook vs a reading nook"),
    ("Nails", "painting", "acrylic", "acrylic nails, acrylic paint"),
    ("Sneakers", "running", "nike", "the brand as fashion vs as kit"),
    ("IdiotsInCars", "teslamotors", "tesla", "dashcam fails meet the fan club"),
    ("analog", "spaceporn", "nikon", "film cameras pointed at the sky"),
    ("Graffiti", "painting", "canvas", "a wall is a canvas too"),
    ("comics", "drawing", "inktober", "one October prompt, two crowds"),
    ("cars", "formula1", "ferrari", "the road car and the race team"),
    ("LivestreamFail", "Twitch", "streamer", "the clip and the platform"),
]


def load():
    src = open(DATA).read()
    return json.loads(src[src.index("{"):src.rstrip().rstrip(";").rindex("}") + 1])


def tautological(kw, a, b):
    """`anime` linking r/anime to r/anime_irl proves nothing — the word is the name.
    A word merely *contained* in one name is still fair game: `cursed` linking
    r/cursedcomments to r/JuJutsuKaisen is the whole point, since the anime means
    something else by it."""
    stem = lambda s: s.lower().rstrip("s")
    names = [stem(a), stem(b)]
    return stem(kw) in names or all(stem(kw) in n for n in names)


def candidates(d):
    snaps, nodes, links = d["snapshots"], d["nodes"], d["links"]
    cat = {n["id"]: n["cat"] for n in nodes}
    subs = {n["id"]: int(n["subs"]) for n in nodes}
    weight = {n["id"]: [dict(per) for per in n["terms"]] for n in nodes}   # month -> word -> tf-idf

    seen = defaultdict(set)
    for n in nodes:
        for per in n["use"]:
            for w, _ in per:
                seen[w].add(n["id"])
    breadth = {w: len(v) for w, v in seen.items()}

    nbrs = defaultdict(set)
    for l in links:
        nbrs[l["source"]].add(l["target"])
        nbrs[l["target"]].add(l["source"])

    out = []
    for l in links:
        a, b = l["source"], l["target"]
        if min(subs.get(a, 0), subs.get(b, 0)) < MIN_SUBS:
            continue
        live = [i for i, v in enumerate(l["history"]) if v > 0]
        if len(live) < MIN_MONTHS:
            continue
        words = Counter(l["shared"][i][0] for i in live if l["shared"][i])
        if not words:
            continue
        kw, kw_months = words.most_common(1)[0]
        if kw_months < MIN_TOP_MONTHS or breadth.get(kw, 0) < MIN_BREADTH or tautological(kw, a, b):
            continue

        # "Unrelated" needs both halves: different neighbourhoods on the map, and hardly
        # any neighbours in common. Same-theme pairs (r/MakeupAddiction ~ r/Nails) are
        # real links but nobody is surprised by them.
        if cat[a] == cat[b]:
            continue
        A, B = nbrs[a] - {b}, nbrs[b] - {a}
        jac = len(A & B) / max(1, len(A | B))
        if jac > MAX_JACCARD:
            continue

        # Showcase the month where this word is doing the most work and the receipts are real.
        best, best_dom = None, 0
        for i in live:
            if not l["shared"][i] or l["shared"][i][0] != kw:
                continue
            proof = l["proof"][i] or [0, 0]
            if min(proof) < MIN_MENTIONS:
                continue
            wa, wb = weight[a][i].get(kw), weight[b][i].get(kw)
            if not wa or not wb:
                continue
            dom = wa * wb / l["history"][i]       # share of the cosine this single word explains
            if dom > best_dom:
                best, best_dom = i, dom
        if best is None:
            continue

        doms = []
        for i in live:
            wa, wb = weight[a][i].get(kw), weight[b][i].get(kw)
            if wa and wb and l["history"][i]:
                doms.append(wa * wb / l["history"][i])
        dom_med = sorted(doms)[len(doms) // 2]

        out.append({
            "a": a, "b": b, "catA": cat[a], "catB": cat[b], "kw": kw,
            "snap": snaps[best], "i": best,
            "sim": round(l["history"][best], 3),
            "months": len(live), "kwMonths": kw_months,
            "dom": round(best_dom, 3), "domMed": round(dom_med, 3), "jac": round(jac, 3),
            "proof": l["proof"][best],
            "also": [w for w in l["shared"][best][1:4]],
            # one word doing the work × genuinely separate neighbourhoods × sticking around.
            # Persistence is square-rooted: it should reward durability, not just outlast everything.
            "score": round(dom_med * (1 - jac) * (len(live) / len(snaps)) ** .5, 4),
        })
    out.sort(key=lambda p: -p["score"])
    return out


def main():
    show = int(sys.argv[sys.argv.index("--show") + 1]) if "--show" in sys.argv else 25
    d = load()
    found = candidates(d)
    print(f"{len(found)} pairs survive the filters\n")

    by_pair = {}
    for p in found:
        by_pair[(p["a"], p["b"], p["kw"])] = p
        by_pair[(p["b"], p["a"], p["kw"])] = p

    picked, used = [], set()
    for a, b, kw, why in PINNED:
        p = by_pair.get((a, b, kw))
        if not p:
            print(f"  ! hand-picked pair no longer survives the filters: r/{a} ~ r/{b} via '{kw}'", file=sys.stderr)
            continue
        picked.append({**p, "why": why})
        used.add((p["a"], p["b"]))
    for p in found:
        if len(picked) >= KEEP:
            break
        if (p["a"], p["b"]) in used:
            continue
        picked.append({**p, "why": f"{p['catA'].lower()} meets {p['catB'].lower()}"})
        used.add((p["a"], p["b"]))

    for n, p in enumerate(found[:show], 1):
        star = "*" if (p["a"], p["b"]) in used else " "
        print(f"{star}{n:3d}. {p['score']:.4f}  r/{p['a']} [{p['catA']}] ~ r/{p['b']} [{p['catB']}]"
              f"  via '{p['kw']}'  ·  {p['months']} mo, word carries {int(p['domMed'] * 100)}% of sim,"
              f" {int(p['jac'] * 100)}% shared neighbours, best {p['snap']} ({p['proof'][0]}/{p['proof'][1]} mentions)")

    with open(OUT, "w") as f:
        f.write("window.PAIRS = " + json.dumps(picked, separators=(",", ":")) + ";\n")
    print(f"\nwrote {os.path.relpath(OUT, HERE)}: {len(picked)} pairs (* above = kept)")
    for p in picked:
        print(f"  {p['snap']}  r/{p['a']} ~ r/{p['b']} via '{p['kw']}' "
              f"({p['proof'][0]}/{p['proof'][1]} mentions) — {p['why']}")


if __name__ == "__main__":
    main()
