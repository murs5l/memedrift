"""
Bulk export of everything Meme Drift is built on, as Parquet.

    python3 build_data.py       # first (fills the cache and writes data.js)
    python3 export_parquet.py   # then

Writes to ./dataset/
  posts.parquet        one row per Reddit post we sampled (~358k rows)
  subreddits.parquet   one row per subreddit: subscribers, theme, per-year top words
  links.parquet        one row per (pair, year) similarity edge, with the linking keyword and mention counts

Read them with anything: pandas.read_parquet, duckdb, polars, Spark.
"""
import json, os
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq

import build_data as B

OUT = os.path.join(B.HERE, "dataset")
os.makedirs(OUT, exist_ok=True)

data = json.loads(open(os.path.join(B.HERE, "data.js")).read()[len("window.DATA = "):-2])
theme_of = {n["id"]: n["cat"] for n in data["nodes"]}
names = [n["id"] for n in data["nodes"]]

# --- posts -------------------------------------------------------------------
rows = []
for sub in names:
    for lbl, before in B.SNAPSHOTS:
        for p in B.raw_posts(sub, before):        # served from cache; no network after build_data.py
            rows.append({
                "subreddit": sub, "theme": theme_of[sub], "snapshot": lbl, "snapshot_before": before,
                "post_id": p.get("id"), "created_utc": datetime.fromtimestamp(p["created_utc"], tz=timezone.utc) if p.get("created_utc") else None,
                "author": p.get("author"), "score": p.get("score"), "num_comments": p.get("num_comments"),
                "title": p.get("title"), "selftext": p.get("selftext"), "flair": p.get("link_flair_text"),
                "url": p.get("url"), "over_18": p.get("over_18"),
                "permalink": f"https://www.reddit.com/r/{sub}/comments/{p['id']}/" if p.get("id") else None,
            })
posts = pa.Table.from_pylist(rows)
pq.write_table(posts, os.path.join(OUT, "posts.parquet"), compression="zstd")

# --- subreddits ---------------------------------------------------------------
subs = pa.Table.from_pylist([{
    "subreddit": n["id"], "theme": n["cat"], "subscribers": n["subs"],
    **{f"top_words_{lbl}": [t for t, _ in n["terms"][i][:20]] for i, lbl in enumerate(data["snapshots"])},
} for n in data["nodes"]])
pq.write_table(subs, os.path.join(OUT, "subreddits.parquet"), compression="zstd")

# --- links --------------------------------------------------------------------
edges = []
for l in data["links"]:
    for i, lbl in enumerate(data["snapshots"]):
        if l["history"][i]:
            edges.append({"source": l["source"], "target": l["target"], "snapshot": lbl,
                          "cosine_similarity": l["history"][i], "keyword": l["shared"][i][0],
                          "shared_words": l["shared"][i], "keyword_mentions_source": l["proof"][i][0],
                          "keyword_mentions_target": l["proof"][i][1]})
links = pa.Table.from_pylist(edges)
pq.write_table(links, os.path.join(OUT, "links.parquet"), compression="zstd")

for f in ("posts", "subreddits", "links"):
    path = os.path.join(OUT, f + ".parquet")
    print(f"{f:11s} {pq.read_metadata(path).num_rows:>8,} rows  {os.path.getsize(path) / 1e6:6.1f} MB")
