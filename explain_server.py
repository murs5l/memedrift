#!/usr/bin/env python3
"""Serve Meme Drift + Cursor SDK explanations (uses Cursor credits).

  1. Create a User API key: https://cursor.com/dashboard/api
  2. Put it in .env as CURSOR_API_KEY=...  (or paste under Explain → Key)
  3. /tmp/memedrift-venv/bin/python explain_server.py

Each explain runs Agent.prompt() in an empty sandbox cwd under .explain-work
so the agent cannot edit this repo — it only answers from the JSON context
in the prompt. (System /var/folders temp is remapped by Cursor and EPERM's
on sdk-agent-store mkdir; keep cwd + store inside the workspace.)
"""
from __future__ import annotations

import json
import os
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPLAIN_WORK = ROOT / ".explain-work"
EXPLAIN_SANDBOX = EXPLAIN_WORK / "sandbox"
EXPLAIN_STORE = EXPLAIN_WORK / "store"
PORT = int(os.environ.get("PORT", "8765"))
MODEL = os.environ.get("CURSOR_MODEL", "composer-2.5")

SYSTEM = """You are explaining a Reddit vocabulary map to a curious student who keeps asking WHY.

How the map works (use this in your reasoning):
- Communities (subreddits) sit near each other when their post *titles* share distinctive words (TF-IDF / cosine).
- An edge’s bridge word is the vocabulary that pulls two subs together that month — not proof that one caused the other.
- Themes (News, Finance, AI, …) are neighborhood labels; distance on the map ≈ different vocab worlds.

Your job is to ANSWER THE WHY QUESTION, not recite the JSON:
1. State the why in the first sentence (because…).
2. Give a short chain of reasoning: shared topic/framing → bridge word(s) → why that puts these hosts in the same neighborhood that month.
3. Use only the provided evidence (themes, signatures, bridge words, mention counts, snapshot). Do not invent posts, events, or sentiment.
4. Associations only — never “X caused Y,” but you MAY say “they co-host this language because both were oriented toward [topic framing].”
5. Concise: 2 short paragraphs, ~4–6 sentences total. Prefer insight over lists of similarities.
6. Light Markdown: **bold** the month, the tracked word (if any), and the key bridge word(s). Subs as r/name. No headings, bullets, or code fences.
7. Do NOT edit files or use tools. Reply with the explanation only.
"""


def why_question(context: dict) -> str:
    kind = context.get("kind") or "selection"
    snap = context.get("snapshot") or "this month"
    tracked = context.get("tracked_word")
    track_bit = f' while tracking **{tracked}**' if tracked else ""
    if kind == "edge":
        nodes = context.get("nodes") or []
        a = nodes[0]["id"] if len(nodes) > 0 else "?"
        b = nodes[1]["id"] if len(nodes) > 1 else "?"
        edges = context.get("edges") or []
        bridge = (edges[0] or {}).get("bridge_word") if edges else None
        bridge_bit = f' (bridge word “{bridge}”)' if bridge else ""
        return (
            f"WHY question: In {snap}{track_bit}, why are r/{a} and r/{b} linked on this map{bridge_bit}? "
            f"What does that shared vocabulary imply about the kind of conversation they were both in?"
        )
    if kind == "path":
        nodes = context.get("nodes") or []
        chain = " → ".join(f"r/{n.get('id')}" for n in nodes if n.get("id"))
        return (
            f"WHY question: In {snap}{track_bit}, why does this path exist ({chain})? "
            f"What does each hop’s bridge word tell us about how attention/language moves between these neighborhoods?"
        )
    # focus
    nodes = context.get("nodes") or []
    nid = nodes[0]["id"] if nodes else "?"
    return (
        f"WHY question: In {snap}{track_bit}, why does r/{nid} sit where it sits among its neighbors? "
        f"What do the neighbor bridge words reveal about the conversational world it belongs to that month?"
    )


def load_dotenv():
    env = ROOT / ".env"
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


load_dotenv()


def cursor_explain(api_key: str, context: dict, model: str) -> str:
    from cursor_sdk import (
        Agent,
        AgentOptions,
        LocalAgentOptions,
        LocalAgentStoreConfig,
    )

    prompt = (
        SYSTEM
        + "\n\n---\n"
        + why_question(context)
        + "\n\nEvidence from the map (reason from this; do not dump it back):\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
        + "\n\nAnswer the WHY question first. Then support it briefly with the strongest bridge-word evidence."
    )
    # Empty sandbox under the workspace (writable); store beside it — not /var/folders.
    EXPLAIN_SANDBOX.mkdir(parents=True, exist_ok=True)
    EXPLAIN_STORE.mkdir(parents=True, exist_ok=True)
    result = Agent.prompt(
        prompt,
        AgentOptions(
            api_key=api_key,
            model=model,
            local=LocalAgentOptions(
                cwd=str(EXPLAIN_SANDBOX),
                store=LocalAgentStoreConfig(
                    type="jsonl",
                    root_dir=str(EXPLAIN_STORE),
                ),
            ),
            # Answer-only: block edit/shell tools (empty cwd is the real safety net).
            disallowed_tools=["piBash", "piWrite", "piEdit", "edit", "delete"],
        ),
    )
    if result.status == "error":
        err = getattr(result, "error", None)
        raise RuntimeError(f"Cursor agent run failed: {err or result.status}")
    text = (result.result or "").strip()
    if not text:
        raise RuntimeError("Cursor returned an empty explanation.")
    return text


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        if self.path.startswith("/api/"):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Cursor-Key")
            self.end_headers()
            return
        self.send_error(404)

    def do_POST(self):
        if self.path.rstrip("/") == "/api/explain":
            return self.handle_explain()
        self.send_error(404)

    def handle_explain(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self.json_err(400, "Invalid JSON body")

        key = (
            self.headers.get("X-Cursor-Key")
            or os.environ.get("CURSOR_API_KEY")
            or ""
        ).strip()
        if not key:
            return self.json_err(
                401,
                "No Cursor API key. Create one at https://cursor.com/dashboard/api "
                "(User API key), then paste it under Explain → Key or set CURSOR_API_KEY in .env.",
            )

        context = body.get("context") or body
        model = body.get("model") or MODEL
        try:
            text = cursor_explain(key, context, model)
        except Exception as e:
            msg = str(e)
            if "api key" in msg.lower() or "401" in msg or "auth" in msg.lower():
                return self.json_err(401, f"Cursor auth failed: {msg}")
            traceback.print_exc()
            return self.json_err(502, f"Cursor explain failed: {msg}")

        self.json_ok({"text": text, "model": model, "provider": "cursor"})

    def json_ok(self, obj, code=200):
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def json_err(self, code, message):
        self.json_ok({"error": message}, code=code)

    def log_message(self, fmt, *args):
        if str(args[0]).startswith("POST"):
            super().log_message(fmt, *args)


def main():
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    has = bool(os.environ.get("CURSOR_API_KEY"))
    print(f"Meme Drift + Cursor explain → http://127.0.0.1:{PORT}/")
    print(f"CURSOR_API_KEY {'set' if has else 'missing — paste under Explain → Key'}")
    print(f"model={MODEL}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
