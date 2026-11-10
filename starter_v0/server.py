"""HTTP backend for the Research Agent (version v0).

Exposes POST /api/chat for a web UI hosted elsewhere (v0.app). The API key stays
on this machine; the browser never sees it. Uses only the standard library.

Run:  .venv/bin/python server.py --port 8000
Then: cloudflared tunnel --url http://localhost:8000
"""
from __future__ import annotations

import argparse
import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_TURNS = 10
VERSION_LOG = ARTIFACTS_DIR / "version_log.csv"
COMPARE_PAGE = ROOT / "compare.html"


def load_versions() -> list[dict[str, Any]]:
    """One row per logged version, with metrics read from its run JSON when the file exists."""
    if not VERSION_LOG.exists():
        return []
    rows: list[dict[str, Any]] = []
    with VERSION_LOG.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            summary: dict[str, Any] = {}
            run_path = ROOT / (row.get("run_file") or "")
            if row.get("run_file") and run_path.is_file():
                try:
                    summary = json.loads(run_path.read_text(encoding="utf-8")).get("summary", {})
                except (ValueError, OSError):
                    summary = {}
            rows.append({
                "version": row.get("version", ""),
                "changed_artifact": row.get("changed_artifact", ""),
                "hypothesis": row.get("hypothesis", ""),
                "reason": row.get("reason", ""),
                "metric_before": row.get("metric_before", ""),
                "metric_after": row.get("metric_after", ""),
                "run_file": row.get("run_file", ""),
                "case_accuracy": summary.get("case_accuracy"),
                "tool_routing_accuracy": summary.get("tool_routing_accuracy"),
                "argument_accuracy": summary.get("argument_accuracy"),
                "multiturn_accuracy": summary.get("multiturn_accuracy"),
                "passed_cases": summary.get("passed_cases"),
                "total_cases": summary.get("total_cases"),
                "failure_counts": summary.get("failure_counts", {}),
            })
    return rows


class AgentService:
    def __init__(self, provider_name: str, version: str, model: str | None) -> None:
        self.version = version
        self.system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        self.tools = to_openai_tools(load_tool_declarations(ARTIFACTS_DIR / "tools.yaml"))
        self.provider = make_provider(provider_name)
        self.model = model
        self.tool_list = [
            {"name": t["name"], "description": (t.get("description") or "").strip()}
            for t in load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
        ]

    def chat(self, message: str, history: list[dict[str, str]]) -> dict[str, Any]:
        messages = [{"role": "system", "content": self.system_prompt}]
        messages += history[-MAX_HISTORY_TURNS * 2:]
        messages.append({"role": "user", "content": message})
        out = run_model_tool_loop(
            provider=self.provider,
            messages=messages,
            tools=self.tools,
            model=self.model,
            max_tool_rounds=3,
        )
        return {
            "version": self.version,
            "status": out["status"],
            "reply": out["assistant_text"],
            "tool_calls": [
                {"name": e["tool"], "args": e.get("args", {})} for e in out["tool_events"]
            ],
        }


def make_handler(service: AgentService, allowed_origin: str):
    class Handler(BaseHTTPRequestHandler):
        def _cors(self) -> None:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, body: bytes) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path == "/api/health":
                self._json(200, {"ok": True, "version": service.version})
            elif path == "/api/tools":
                self._json(200, {"tools": service.tool_list})
            elif path == "/api/versions":
                self._json(200, {"versions": load_versions()})
            elif path == "/compare":
                self._html(COMPARE_PAGE.read_bytes())
            else:
                self._json(404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/chat":
                self._json(404, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length) or b"{}")
            except (ValueError, json.JSONDecodeError):
                self._json(400, {"error": "invalid_json"})
                return
            message = str(data.get("message", "")).strip()
            if not message:
                self._json(400, {"error": "empty_message"})
                return
            if len(message) > MAX_MESSAGE_CHARS:
                self._json(400, {"error": "message_too_long"})
                return
            history = [
                {"role": m["role"], "content": str(m["content"])}
                for m in data.get("history", [])
                if isinstance(m, dict) and m.get("role") in ("user", "assistant")
            ]
            try:
                self._json(200, service.chat(message, history))
            except Exception as exc:  # return a readable error instead of a bare 500
                self._json(500, {"error": type(exc).__name__, "message": str(exc)})

        def log_message(self, fmt: str, *args: Any) -> None:
            print(f"[{self.address_string()}] {fmt % args}")

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Agent HTTP backend.")
    parser.add_argument("--provider", default="anthropic", choices=["openrouter", "openai", "anthropic", "gemini", "ollama"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", default="v0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--allowed-origin", default="*", help="CORS origin for the UI, e.g. https://your-app.vercel.app")
    args = parser.parse_args()

    service = AgentService(args.provider, args.version, args.model)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(service, args.allowed_origin))
    print(f"Research Agent backend: version={args.version} provider={args.provider} http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
