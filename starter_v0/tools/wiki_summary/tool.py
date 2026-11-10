from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

SUPPORTED_LANGS = ("vi", "en")
USER_AGENT = "ResearchAgentLab/1.0 (educational lab)"


def wiki_summary(topic: str = "", lang: str = "vi") -> dict[str, Any]:
    """Get the short Wikipedia summary of a topic (no API key needed)."""
    try:
        title = (topic or "").strip()
        if not title:
            return {"tool": "wiki_summary", "error": "EmptyTopic", "message": "topic is empty"}
        if lang not in SUPPORTED_LANGS:
            return {"tool": "wiki_summary", "error": "UnsupportedLang", "message": "lang must be vi or en"}
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}"
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        if response.status_code == 404:
            return {"tool": "wiki_summary", "error": "NotFound", "message": f"no Wikipedia page for '{title}'"}
        response.raise_for_status()
        data = response.json()
        if data.get("type") == "disambiguation":
            return {"tool": "wiki_summary", "error": "Ambiguous", "message": f"'{title}' has several meanings; ask the user"}
        page = (data.get("content_urls") or {}).get("desktop", {}).get("page", "")
        return {
            "tool": "wiki_summary",
            "title": data.get("title", title),
            "lang": lang,
            "summary": (data.get("extract") or "")[:1200],
            "url": page,
        }
    except Exception as exc:
        return err("wiki_summary", exc)
