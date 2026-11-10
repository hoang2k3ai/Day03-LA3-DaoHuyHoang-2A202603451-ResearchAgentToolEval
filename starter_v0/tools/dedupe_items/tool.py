from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from tools._shared import fold_text

MAX_ITEMS = 200


def _norm_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")]
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def _norm_title(title: str) -> str:
    return " ".join(fold_text(title).split())


def dedupe_items(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Remove repeated news items by normalized URL first, then by normalized title. Keeps first occurrence."""
    if not isinstance(items, list):
        items = []
    if len(items) > MAX_ITEMS:
        return {"tool": "dedupe_items", "error": "TooManyItems", "message": f"max {MAX_ITEMS} items"}
    kept: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        url = _norm_url(item["url"]) if isinstance(item.get("url"), str) and item["url"].strip() else ""
        title = _norm_title(item["title"]) if isinstance(item.get("title"), str) else ""
        if (url and url in seen_urls) or (title and title in seen_titles):
            continue
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        kept.append(item)
    return {
        "tool": "dedupe_items",
        "items": kept,
        "item_count": len(kept),
        "removed": len(items) - len(kept),
    }
