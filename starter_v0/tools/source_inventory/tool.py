from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from tools._shared import err


def inventory_sources(urls: list[str] | None = None) -> dict[str, Any]:
    """Group distinct source URLs by host without visiting them."""
    if not isinstance(urls, list) or not urls:
        return err("source_inventory", ValueError("urls must be a non-empty list"))

    by_host: dict[str, list[str]] = {}
    seen: set[str] = set()
    for index, url in enumerate(urls, start=1):
        if not isinstance(url, str):
            return err("source_inventory", ValueError(f"URL {index} must be a string"))
        url = url.strip()
        try:
            parsed = urlsplit(url)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username is not None
                or any(char.isspace() for char in url)
            ):
                raise ValueError
            host = parsed.hostname.removeprefix("www.")
        except ValueError:
            return err("source_inventory", ValueError(f"URL {index} must be an absolute HTTP(S) URL"))

        source_url = url.split("#", 1)[0]
        if source_url not in seen:
            seen.add(source_url)
            by_host.setdefault(host, []).append(source_url)

    return {
        "tool": "source_inventory",
        "source_count": len(seen),
        "domain_count": len(by_host),
        "groups": [{"domain": host, "urls": links} for host, links in by_host.items()],
    }
