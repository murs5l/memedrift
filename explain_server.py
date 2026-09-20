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
import random
import secrets
import socket
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPLAIN_WORK = ROOT / ".explain-work"
EXPLAIN_SANDBOX = EXPLAIN_WORK / "sandbox"
EXPLAIN_STORE = EXPLAIN_WORK / "store"
PORT = int(os.environ.get("PORT", "8765"))
MODEL = os.environ.get("CURSOR_MODEL", "composer-2.5")

SYSTEM = """You are a memeticist reading a map of Reddit hosts. Words are memes; subreddits are the populations they live in. The map only tells you *that* two hosts share language this month. Your job is to say *what idea was spreading, mutating, or cohabiting* — not how the map was computed.

Never mention TF-IDF, cosine, similarity scores, mention-count arithmetic, springs, layout, or “the map pulled them together.” Those are instruments. Talk about the meme.

Each reply is a new reading. Do not reuse a template (“Because in MONTH both r/A and r/B were posting about…”). Do not repeat the Answer inside Reason.

Reply in exactly two labeled blocks, nothing else:

**Answer.** One or two sentences. The punch: what shared practice, frame, or mutating meaning made these communities kin this month.

**Reason.** Deeper, and it must not restate the Answer. Tell the meme’s evolution: where the idea likely lived, how its sense or host shifted, why *these* communities were both carrying it, what it was doing in each world. Use themes, signature words, and the bridge word as cultural clues — not as a checklist to recap. 4–7 sentences. Association only, never “X infected Y.” Do not invent posts, dates, or events that are not implied by the evidence.

Light Markdown: **bold** the meme/bridge word and the month. Subs as r/name. No bullets, no headings besides Answer/Reason. Do not edit files or use tools.
"""

LENSES = (
    "Treat the shared word as a meme looking for hosts: where it can live, where it mutates.",
    "Ask what everyday ritual or problem both communities were performing with this language.",
    "Assume the word might be a homonym or a sense-shift until the evidence says otherwise.",
    "Follow the idea’s career: who needed it as identity, who needed it as a tool, who needed it as a joke.",
    "Look under the word for the practice (training, decorating, cursing, speculating) that jumped hosts.",
    "Read it as cohabitation, not influence: two worlds using the same token for adjacent lives.",
)


def why_question(context: dict) -> str:
    kind = context.get("kind") or "selection"
    snap = context.get("snapshot") or "this month"
    tracked = context.get("tracked_word")
    track_bit = f" The tracked meme is **{tracked}**." if tracked else ""
    if kind == "edge":
        nodes = context.get("nodes") or []
        a = nodes[0]["id"] if len(nodes) > 0 else "?"
        b = nodes[1]["id"] if len(nodes) > 1 else "?"
        edges = context.get("edges") or []
        bridge = (edges[0] or {}).get("bridge_word") if edges else None
        meme = f" The hinge-word is **{bridge}**." if bridge else ""
        return (
            f"In {snap}, r/{a} and r/{b} are co-hosting language.{meme}{track_bit} "
            f"What meme or practice were they both carrying, and how did that idea evolve between their worlds?"
        )
    if kind == "path":
        nodes = context.get("nodes") or []
        chain = " → ".join(f"r/{n.get('id')}" for n in nodes if n.get("id"))
        return (
            f"In {snap}, this path exists: {chain}.{track_bit} "
            f"What idea is hopping hosts along this chain, and how does the meme change at each step?"
        )
    nodes = context.get("nodes") or []
    nid = nodes[0]["id"] if nodes else "?"
    return (
        f"In {snap}, why does r/{nid} belong with its neighbors, memetically?{track_bit} "
        f"What idea is this community hosting, and how is that idea evolving at the edge of its neighborhood?"
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

    lens = random.choice(LENSES)
    nonce = secrets.token_hex(3)
    prompt = (
        SYSTEM
        + "\n\n---\n"
        + why_question(context)
        + "\n\nEvidence (clues about the culture, not a script to recite):\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
        + f"\n\nFresh reading #{nonce}. Angle: {lens}\n"
        + "Write **Answer.** then **Reason.** Reason must add evolution, not repeat Answer. "
        + "No graph-construction talk."
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


class DualStackServer(ThreadingHTTPServer):
    """localhost on macOS often hits ::1; bind v6+v4 so both names work."""
    address_family = socket.AF_INET6
    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


def main():
    httpd = DualStackServer(("::", PORT), Handler)
    has = bool(os.environ.get("CURSOR_API_KEY"))
    print(f"Meme Drift + Cursor explain → http://127.0.0.1:{PORT}/  (also localhost)")
    print(f"CURSOR_API_KEY {'set' if has else 'missing — paste under Explain → Key'}")
    print(f"model={MODEL}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
