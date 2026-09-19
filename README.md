# Meme Drift - Zeitgeist

**How does it spread?** 512 subreddits (the ~480 biggest SFW subs + 120 niche seeds), pulled together by the words they share, one snapshot per month from Jan 2020 → Aug 2026.
Type a word and watch it jump the fence between communities.

## Run

```bash
python3 build_data.py                              # monthly from 2020 (first run is long; cached after)
python3 -m http.server 8765                        # or: python3 explain_server.py
# 2D: http://localhost:8765   3D: http://localhost:8765/index3d.html
```

Stdlib + numpy. No API keys, no torch.

`index.html` is the 2D map (D3). `index3d.html` is the same thing as an orbitable 3D force graph (three.js via 3d-force-graph): same spring law, keywords, proof cards and timeline; drag to orbit, right-drag to pan, scroll to zoom.

## Layout

| path | what |
|---|---|
| `index.html` / `index3d.html` | entry pages |
| `app/` | UI scripts & CSS (`extras.js`, `story.js`, `explain.js`, `ui.css`, `story.css`) |
| `data/data.js` | graph payload |
| `data/posts/` | on-demand `posts_YYYY-MM.js` title files |
| `monthly/` | last-12-months mirror (same `app/` + `data/` layout) |
| `cache/` | Arctic Shift download cache |

## Timescales

- `python3 build_data.py` → monthly, Jan 2020 → Aug 2026, under `data/`.
- `python3 build_data.py monthly` → the last 12 months only, under `monthly/` (its own `data/`, post files and page copies). Both share `cache/`.

## Explore & play (`app/extras.js`, loaded by every page)

- **Connect two subreddits**: pick any two (or "surprise me"): the words both say with mention counts, and the shortest chain of lines between them on the map, one keyword per hop (e.g. r/Coronavirus → vaccine → r/Health → sweetener → r/keto → grams → r/budgetfood → aldi → r/Frugal → jar → r/mildlyinteresting). The chain is lit on the map and re-computed when you move the timeline.
- **Game: when was this?**: 5 rounds: the map is lit for a rising meme at a hidden snapshot; guess the snapshot from who says it. 3 pts exact, 1 pt one step off.
- **Tour**: 5-step spotlight on first visit (remembered per browser); the "tour" chip replays it.

## How it works

1. For each subreddit and each year, take the 100 most recent posts before July 1 (Arctic Shift = public Pushshift archive).
2. TF-IDF vector per (subreddit, year). Cosine similarity between vectors = the "proof" two communities talk alike.
3. Each subreddit links to its 5 most similar peers that year. D3 force layout turns similarity into spring length, so clusters emerge on their own, nobody hardcodes "gaming goes here".
4. Every line carries **one exact keyword**: the term that contributes most to that pair's similarity (click a bubble to see them on its lines; the panel lists neighbour · keyword · distance · similarity).
5. **Why the distance?** Each line is a spring with resting length `40 + 280 × (1 − sim/max)` px, so more shared vocabulary = shorter line. The link tooltip spells this out per pair.
6. Colours: 12 themes seeded with ~10 hand-picked subs each; the other ~400 subs get their theme by label propagation (copy your closest neighbours).
7. "Fastest spreading" = the terms that appear in the most new communities' top-40 vocabulary between 2020 and 2026.

## Bulk dataset (Parquet)

```bash
python3 export_parquet.py     # after build_data.py; needs pyarrow
```

Writes `dataset/`:

| file | rows | size | what |
|---|---|---|---|
| `posts.parquet` | 355,851 | 58 MB | one row per sampled post: `subreddit, theme, snapshot, post_id, created_utc, author, score, num_comments, title, selftext, flair, url, over_18, permalink` |
| `subreddits.parquet` | 512 | 0.4 MB | `subreddit, theme, subscribers, top_words_2020 … top_words_2026` |
| `links.parquet` | 13,770 | 0.3 MB | one row per (pair, year): `source, target, snapshot, cosine_similarity, keyword, shared_words, keyword_mentions_source/target` |

zstd-compressed; open with pandas / duckdb / polars. Every post has a Reddit permalink, so anything in the map can be traced to the original.
Source: Arctic Shift (https://arctic-shift.photon-reddit.com), the 100 most recent posts per subreddit before each snapshot date.

## The memetics pitch

The graph is the *host population*; words are the *memes*. Track `agents` or `openai` and the halo shows the infection
spreading from r/MachineLearning outward year by year; r/ChatGPT, r/LocalLLaMA and r/ClaudeAI literally don't exist in 2020
and pop into the map mid-timeline. Track `iran`, `israel`, `trump` to see news memes crossing into finance, science and gaming.

## Knobs

- `TOP_N` / `THEMES` in `build_data.py`: how many big subs to pull, and the seed subs per theme.
- `SNAPSHOTS`: more dates = finer timeline (7 now; pipeline cost is linear).
- `K = 5`: neighbours per node per snapshot; raise for a denser web.
