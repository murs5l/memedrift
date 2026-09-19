"""
Meme Drift - Zeitgeist data pipeline. Python stdlib + numpy. No API keys, no torch.

Pulls ~100 posts per subreddit per snapshot from Arctic Shift (public Pushshift
successor), builds TF-IDF vectors, and writes data.js for index.html.

    python3 build_data.py            # ~25 min first run (3,800 requests), cached after

Similarity "proof" = cosine similarity of TF-IDF vectors. The shared top terms
on each link are the receipts: literally the words both communities use.
Communities (colours) are not hand-picked: label propagation over the graph.
"""
import json, math, os, re, sys, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np

API = "https://arctic-shift.photon-reddit.com"
UA = "memedrift/0.1 (hophacks memetics track)"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
os.makedirs(CACHE, exist_ok=True)

# One snapshot per month from Jan 2020 through Aug 2026 (posts before the 1st of the next month).
def _months(y0, m0, y1, m1):
    out, y, m = [], y0, m0
    while (y, m) <= (y1, m1):
        # label = calendar month of the posts; date = first day of the following month
        py, pm = (y, m - 1) if m > 1 else (y - 1, 12)
        out.append((f"{py}-{pm:02d}", f"{y}-{m:02d}-01"))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out

YEARLY = _months(2020, 2, 2026, 9)   # labels 2020-01 … 2026-08
# `python3 build_data.py monthly`: last 12 months only, written to ./monthly/
MONTHLY = YEARLY[-12:]
MODE = sys.argv[1] if len(sys.argv) > 1 else "yearly"
SNAPSHOTS = MONTHLY if MODE == "monthly" else YEARLY
OUT = os.path.join(HERE, "monthly") if MODE == "monthly" else HERE
os.makedirs(OUT, exist_ok=True)
TOP_N = 480          # biggest SFW subreddits by subscribers, plus the seeds below
K = 5                # neighbours per subreddit per snapshot

# Seed themes: these subs keep their label; every other sub adopts whatever its neighbours say.
THEMES = {
    "Coding":   "programming cpp rust Python javascript learnprogramming webdev linux devops cscareerquestions",
    "AI":       "MachineLearning artificial ChatGPT LocalLLaMA singularity datascience StableDiffusion OpenAI ClaudeAI",
    "Gaming":   "gaming pcgaming gamedev Unity3D unrealengine Minecraft leagueoflegends Steam nintendo IndieDev",
    "Finance":  "wallstreetbets stocks investing personalfinance CryptoCurrency Bitcoin ethereum options Economics quant",
    "Science":  "science askscience space Physics biology medicine nutrition Fitness running mentalhealth",
    "Art":      "Art Design graphic_design photography blender DigitalArt ArtistLounge typography architecture",
    "Culture":  "Music WeAreTheMusicMakers hiphopheads movies television anime books writing podcasts",
    "News":     "worldnews news politics Conservative geopolitics europe Futurology technology privacy",
    "Life":     "Cooking food travel relationships AskReddit LifeProTips Parenting Frugal DIY HomeImprovement",
    "Hardware": "buildapc hardware nvidia Amd raspberry_pi arduino 3Dprinting electronics robotics esp32",
    "Sports":   "sports nba nfl soccer baseball hockey formula1 MMA tennis golf",
    "General":  "funny memes pics aww videos todayilearned mildlyinteresting Showerthoughts Jokes AmItheAsshole",
}
SEED_OF = {s: theme for theme, subs in THEMES.items() for s in subs.split()}
SEEDS = list(SEED_OF)
EXCLUDE = {"announcements", "blog", "reddit.com", "RedditSessions", "redditrequest", "help", "modnews", "u_reddit",
           "de", "france", "mexico", "brasil", "argentina", "italy", "Polska", "ich_iel", "sex"}   # non-English: keywords would be "je", "der"...

STOP = set("""a about above after again against all am an and any are as at be because been before being below between
both but by can cannot could did do does doing don down during each few for from further had has have having he her here hers
him his how i if in into is it its itself just let me more most my no nor not now of off on once only or other our ours out over
own same she should so some such than that the their theirs them then there these they this those through to too under until up
very was we were what when where which while who whom why will with would you your yours
im ive dont cant didnt doesnt isnt wont thats whats youre theyre hes shes ill id
get got getting one two also like really thing things something anything still even much many make made makes want know
think see way going go goes new first last time year years day days week weeks month ago back need needs use used using
help please anyone someone everyone people good bad best better great pretty lot lots bit sure right well around
https http www com amp removed deleted reddit subreddit post posts posted comment comments edit thanks thank
je tu il elle nous vous ils les des une est pas pour dans sur avec mais qui que quoi ce cette ces son ses mon mes
el la los las un una por para con como pero mas ser fue hay muy todo esta este esto del al lo le
der die das und ist nicht ein eine ich sie wir ihr auch auf aus bei mit von zu den dem des ich wenn oder
nao uma com mas voce ele ela isso essa esse seu sua muito tem foi mais aqui
het een van voor niet ook maar dat dit zijn hebben wordt naar meer nog
nie jest sie tak jak czy ale juz tylko bardzo
uhh hmm huh tho wth bla oof brr yea ayo lol lmao omg wtf idk tbh imo btw ngl smh yall gonna wanna gotta kinda sorta
tsp tbsp lbs kgs oz mph kwh ghz mhz gb tb mb cm mm km ft inch inches min mins hrs pcs pls thx
""".split())
KEEP_SHORT = {"ai", "c#", "vr", "ar", "ml", "3d", "4k", "ev", "ui", "ux", "os", "cpu", "gpu"}   # real 2-letter memes
TOKEN = re.compile(r"[a-z][a-z0-9+#]*")
AGE_TAG = re.compile(r"^[mf]\d\d$")     # "f23", "m26": relationship-post age tags, not words


def get(path, **params):
    key = os.path.join(CACHE, re.sub(r"[^\w]+", "_", path + urlencode(sorted(params.items()))) + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    for attempt in range(5):
        try:
            req = Request(f"{API}{path}?{urlencode(params)}", headers={"User-Agent": UA})
            data = json.load(urlopen(req, timeout=60))["data"]
            json.dump(data, open(key, "w"))
            return data
        except Exception as e:  # ponytail: retry with backoff, no rate-limit parsing
            time.sleep(3 * (attempt + 1))
            err = e
    print(f"  ! {path} {params}: {err}", file=sys.stderr)
    return []


FIELDS = "id,created_utc,author,score,num_comments,url,title,selftext,link_flair_text,subreddit,over_18"


def raw_posts(sub, before):
    """the 100 most recent posts before `before`, as the API returns them (also what export_parquet.py reads)"""
    return get("/api/posts/search", subreddit=sub, before=before, limit=100, sort="desc", fields=FIELDS)


def fetch_posts(sub, before):
    """-> list of post strings (title + first 1500 chars of body), boilerplate stripped"""
    posts = raw_posts(sub, before)
    return [re.sub(r"\[ ?Removed by \w+ ?\]", "", f"{p.get('title') or ''}\n{(p.get('selftext') or '')[:1500]}").strip()
            for p in posts]



def tokens(text):
    # words only: ≥3 letters (or an allow-listed short one), no stopwords in 8 languages, no bare numbers
    return [t for t in TOKEN.findall(text.lower()) if (len(t) >= 3 or t in KEEP_SHORT) and t not in STOP and not t.isdigit() and not AGE_TAG.match(t)]


def communities(names, adj, seeds):
    """Seeded label propagation: seed nodes keep their theme; every other node keeps
    adopting the heaviest theme among its neighbours until nothing changes."""
    label = {n: seeds.get(n) for n in names}
    for _ in range(50):
        changed = 0
        for n in sorted(names):
            if n in seeds:
                continue
            votes = Counter()
            for m, w in adj[n].items():
                if label[m]:
                    votes[label[m]] += w
            if votes:
                best = max(votes, key=lambda l: (votes[l], l))   # deterministic tie-break
                if best != label[n]:
                    label[n] = best
                    changed += 1
        if not changed:
            break
    return {n: l or "Other" for n, l in label.items()}


def main():
    big = get("/api/subreddits/search", min_subscribers=400000, limit=1000, over18="false")
    names = [s["display_name"] for s in big if s["display_name"] not in EXCLUDE and not s["display_name"].startswith("u_")][:TOP_N]
    info = {s["display_name"].lower(): s for s in big}
    names = list(dict.fromkeys(names + SEEDS))          # dedupe, keep order
    jobs = [(s, snap) for s in names for snap in SNAPSHOTS]
    print(f"fetching {len(jobs)} snapshots for {len(names)} subreddits...")
    with ThreadPoolExecutor(4) as pool:
        posts = dict(zip(jobs, pool.map(lambda j: fetch_posts(j[0], j[1][1]), jobs)))
        texts = {j: " ".join(p) for j, p in posts.items()}
        missing = [s for s in names if s.lower() not in info]
        for s, r in zip(missing, pool.map(lambda s: (get("/api/subreddits/search", subreddit=s, limit=1) or [{}])[0], missing)):
            info[s.lower()] = r

    # --- TF-IDF -----------------------------------------------------------
    docs = {j: Counter(tokens(t)) for j, t in texts.items()}
    docs = {j: c for j, c in docs.items() if sum(c.values()) >= 200}   # sub didn't exist / too quiet
    df = Counter()
    for c in docs.values():
        df.update(c.keys())
    vocab = [t for t, n in df.items() if n >= 3]
    idx = {t: i for i, t in enumerate(vocab)}
    idf = np.log(len(docs) / (1 + np.array([df[t] for t in vocab], dtype=np.float32)))
    print(f"{len(docs)} live snapshots, vocab {len(vocab)}")

    vecs = {}   # (sub, snapshot) -> L2-normalised float32 row
    for j, c in docs.items():
        v = np.zeros(len(vocab), dtype=np.float32)
        for t, n in c.items():
            if t in idx:
                v[idx[t]] = 1 + math.log(n)
        v *= idf
        vecs[j] = v / (np.linalg.norm(v) or 1)

    def top_terms(v, n):
        ix = np.argpartition(-v, n)[:n]
        return [(vocab[i], round(float(v[i]), 4)) for i in ix[np.argsort(-v[ix])] if v[i] > 0]

    # --- links: per snapshot, each node's K nearest by cosine ---------------
    pairs = {}   # (a, b, si) -> sim
    adj = defaultdict(Counter)
    for si, snap in enumerate(SNAPSHOTS):
        live = [s for s in names if (s, snap) in vecs]
        M = np.stack([vecs[(s, snap)] for s in live])
        S = M @ M.T
        np.fill_diagonal(S, -1)
        for i, a in enumerate(live):
            for jx in np.argsort(-S[i])[:K]:
                b = live[jx]
                key = (min(a, b), max(a, b), si)
                pairs[key] = float(S[i, jx])
                adj[a][b] += S[i, jx]
                adj[b][a] += S[i, jx]
        print(f"  {snap[0]}: {len(live)} subs, {sum(1 for k in pairs if k[2] == si)} links")

    links = []
    for a, b in sorted({(a, b) for a, b, _ in pairs}):
        hist, shared, proof = [], [], []
        for si, snap in enumerate(SNAPSHOTS):
            s = pairs.get((a, b, si))
            if s is None:
                hist.append(0); shared.append([]); proof.append(None)
            else:
                hist.append(round(s, 3))
                shared.append([t for t, _ in top_terms(vecs[(a, snap)] * vecs[(b, snap)], 5)])
                kw = shared[-1][0]   # mention counts for the line's keyword; the posts themselves live in posts_<year>.js
                proof.append([docs[(a, snap)][kw], docs[(b, snap)][kw]])
        links.append({"source": a, "target": b, "history": hist, "shared": shared, "proof": proof})

    # --- communities (emergent categories) --------------------------------
    cat_of = communities(names, adj, SEED_OF)
    sizes = Counter(cat_of.values())
    # subtitle each theme with the three words its members lean on most (latest live snapshot)
    categories = []
    for l in list(THEMES) + ["Other"]:
        acc = np.zeros(len(vocab), dtype=np.float32)
        for n in names:
            if cat_of[n] == l:
                for snap in reversed(SNAPSHOTS):
                    if (n, snap) in vecs:
                        acc += vecs[(n, snap)]; break
        categories.append({"id": l, "name": l, "words": " · ".join(t for t, _ in top_terms(acc, 3)), "size": sizes[l]})
    categories = [c for c in categories if c["size"]]

    nodes = []
    for s in names:
        node = {"id": s, "cat": cat_of[s], "subs": info.get(s.lower(), {}).get("subscribers") or 1000, "terms": [], "use": []}
        for snap in SNAPSHOTS:
            v = vecs.get((s, snap))
            node["terms"].append(top_terms(v, 40) if v is not None else [])
            # raw mentions per 100 posts, so ubiquitous memes ("ai") are searchable even when TF-IDF hides them
            node["use"].append(docs[(s, snap)].most_common(60) if (s, snap) in docs else [])
        nodes.append(node)

    # --- meme drift leaderboard: terms whose spread (subs using them) grew most
    spread = defaultdict(lambda: [0] * len(SNAPSHOTS))
    for n in nodes:
        for si, terms in enumerate(n["terms"]):   # distinctive words, so "actually"/"never" can't top the chart
            for t, _ in terms:
                spread[t][si] += 1
    memes = sorted(spread.items(), key=lambda kv: -(kv[1][-1] - max(kv[1][:3] + [0])))[:30]
    memes = [{"term": t, "spread": sp} for t, sp in memes if sp[-1] >= 5]

    out = {"snapshots": [lbl for lbl, _ in SNAPSHOTS], "categories": categories,
           "nodes": nodes, "links": links, "memes": memes}
    data_dir = os.path.join(OUT, "data")
    posts_dir = os.path.join(data_dir, "posts")
    os.makedirs(posts_dir, exist_ok=True)
    with open(os.path.join(data_dir, "data.js"), "w") as f:
        f.write("window.DATA = " + json.dumps(out, separators=(",", ":")) + ";\n")
    # every post title per sub per year, so the UI can list ALL posts behind a keyword (one file per year, loaded on demand)
    for lbl, date in SNAPSHOTS:
        titles = {s: [p.split("\n", 1)[0][:140] for p in posts[(s, (lbl, date))]] for s in names}
        with open(os.path.join(posts_dir, f"posts_{lbl}.js"), "w") as f:
            f.write(f"window.POSTS = window.POSTS || {{}}; window.POSTS[{lbl!r}] = " + json.dumps(titles, separators=(",", ":")) + ";\n")
    if OUT != HERE:   # monthly build: ship copies of the two pages next to its data, with the timescale chip pointing back
        import shutil
        app_src = os.path.join(HERE, "app")
        app_dst = os.path.join(OUT, "app")
        os.makedirs(app_dst, exist_ok=True)
        for name in ("extras.js", "story.js", "explain.js", "ui.css", "story.css"):
            src = os.path.join(app_src, name)
            if os.path.exists(src):
                shutil.copy(src, app_dst)
        for page in ("index.html", "index3d.html"):
            html = open(os.path.join(HERE, page)).read()
            html = html.replace(f'href="monthly/{page}"', f'href="../{page}"').replace(">monthly timeline<", ">yearly timeline<")
            html = html.replace("<title>Meme Drift - Zeitgeist", "<title>Meme Drift - Zeitgeist · Monthly")
            open(os.path.join(OUT, page), "w").write(html)
    print(f"wrote data.js: {len(nodes)} nodes, {len(links)} links, {len(categories)} communities")
    for c in categories:
        print(f"  [{c['size']:3d}] {c['name']}: {c['words']}")
    print("rising memes:", ", ".join(m["term"] for m in memes[:12]))


if __name__ == "__main__":
    # self-checks on the maths before touching the network
    assert tokens("C++ and Rust vs the Web! Je suis AI, U.S. GPU x F23 lol") == ["c++", "rust", "web", "suis", "ai", "gpu"]
    lab = communities(["a", "b", "c", "d"], {"a": {"b": 1}, "b": {"a": 1}, "c": {"d": 1}, "d": {"c": 1}}, {"a": "X", "c": "Y"})
    assert lab == {"a": "X", "b": "X", "c": "Y", "d": "Y"}
    main()
