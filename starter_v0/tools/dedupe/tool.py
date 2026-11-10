from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit


def _url_key(url: str) -> str:
    """Normalize URL host, trailing path slash, and fragment for comparison."""
    parts = urlsplit(url.strip())
    if not parts.scheme or not parts.netloc:
        return url.strip()
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), parts.query, ""))


def deduplicate_items(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return research items with duplicate URLs removed, preserving first occurrence."""
    if items is None:
        items = []
    if not isinstance(items, list):
        return {"tool": "dedupe", "error": "InvalidInput", "message": "items must be a list of objects"}

    kept: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            return {"tool": "dedupe", "error": "InvalidInput", "message": "every item must be an object"}
        url = item.get("url")
        if not isinstance(url, str) or not url.strip():
            # Items without URLs cannot be safely identified as duplicates.
            kept.append(item)
            continue
        key = _url_key(url)
        if key in seen_urls:
            continue
        seen_urls.add(key)
        kept.append(item)

    return {
        "tool": "dedupe",
        "items": kept,
        "item_count": len(kept),
        "duplicate_count": len(items) - len(kept),
    }
