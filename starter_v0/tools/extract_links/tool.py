from __future__ import annotations

import re
from typing import Any

from tools._shared import domain

_URL_RE = re.compile(r"https?://[^\s<>\"']+")
_TRAILING = ".,;:!?)]}"


def extract_links(text: str = "") -> dict[str, Any]:
    """Find http(s) links in free text, strip trailing punctuation and drop duplicates."""
    source = text or ""
    seen: list[str] = []
    for match in _URL_RE.findall(source):
        url = match.rstrip(_TRAILING)
        if url and url not in seen:
            seen.append(url)
    return {
        "tool": "extract_links",
        "links": seen,
        "count": len(seen),
        "domains": sorted({domain(url) for url in seen}),
    }
