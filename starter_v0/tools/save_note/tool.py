from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from tools._shared import err, fold_text

ROOT = Path(__file__).resolve().parents[2]
NOTES_DIR = ROOT / "artifacts" / "notes"
MAX_CONTENT_CHARS = 20000


def _slug(title: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in fold_text(title))
    return "-".join(part for part in cleaned.split("-") if part)[:60] or "note"


def save_note(title: str = "", content: str = "", confirmed: bool = False) -> dict[str, Any]:
    """Write a markdown note to artifacts/notes/. Only writes when confirmed is true."""
    try:
        if not confirmed:
            return {"tool": "save_note", "status": "needs_confirmation",
                    "message": "ask the user to confirm before saving this note"}
        if not (title or "").strip() or not (content or "").strip():
            return {"tool": "save_note", "error": "EmptyInput", "message": "title and content are required"}
        if len(content) > MAX_CONTENT_CHARS:
            return {"tool": "save_note", "error": "TooLong", "message": f"max {MAX_CONTENT_CHARS} characters"}
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d")
        base = f"{stamp}-{_slug(title)}"
        path = NOTES_DIR / f"{base}.md"
        counter = 2
        while path.exists():  # never overwrite an earlier note
            path = NOTES_DIR / f"{base}-{counter}.md"
            counter += 1
        path.write_text(f"# {title.strip()}\n\n{content.strip()}\n", encoding="utf-8")
        try:
            shown = str(path.relative_to(ROOT))
        except ValueError:  # NOTES_DIR was overridden outside the project
            shown = str(path)
        return {"tool": "save_note", "status": "saved", "path": shown}
    except Exception as exc:
        return err("save_note", exc)
