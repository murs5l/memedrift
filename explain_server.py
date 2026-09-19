#!/usr/bin/env python3
"""Serve Meme Drift + Cursor SDK explanations (uses Cursor credits).

  1. Create a User API key: https://cursor.com/dashboard/api
  2. Put it in .env as CURSOR_API_KEY=...  (or paste under Explain → Key)
  3. /tmp/memedrift-venv/bin/python explain_server.py

Each explain runs Agent.prompt() in an empty temp cwd so the agent cannot
edit this repo — it only answers from the JSON context in the prompt.
"""
from __future__ import annotations

import json
import os
import tempfile
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8765"))
MODEL = os.environ.get("CURSOR_MODEL", "composer-2.5")

SYSTEM = """You explain a Reddit vocabulary map for curious students.
Subreddits are linked when their post titles share vocabulary (TF-IDF / cosine). You get a focus node, an edge, or a path plus themes, signature words, and bridge keywords.

Write like a teacher, not a data dump:
- Lead with the *why* (what kind of conversation overlap this map is showing), then use 1–2 concrete bridge words as evidence — not a catalogue of every neighbor.
- Associations only; never claim causation or invent posts/events/sentiment.
- Be concise: at most 2 short paragraphs (3–5 sentences total). Skip filler like “overall” and “this suggests that both communities were posting about…”.
- Prefer interpretation: e.g. “they sit together because both were using headline language about X that month,” not a bullet list of sims and mention counts.
- Light Markdown only: **bold** months, tracked words, and key bridge words. Name subs as r/name. No headings, lists, or code fences.
- Do NOT edit files or use tools. Reply with the explanation only.
"""


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
    from cursor_sdk import Agent, AgentOptions, LocalAgentOptions

    prompt = (
        SYSTEM
        + "\n\n---\nExplain this selection on the Meme Drift map.\n\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )
    # Empty sandbox cwd: agent has nothing to edit; answer from the prompt only.
    with tempfile.TemporaryDirectory(prefix="memedrift-explain-") as tmp:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=model,
                local=LocalAgentOptions(cwd=tmp),
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
