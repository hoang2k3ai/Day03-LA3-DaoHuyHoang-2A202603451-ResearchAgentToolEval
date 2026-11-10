from __future__ import annotations

from tools import TOOL_FUNCTIONS


dedupe = TOOL_FUNCTIONS["dedupe"]


def test_dedupe_removes_duplicate_urls_and_preserves_first_item() -> None:
    first = {"title": "Original", "url": "https://Example.com/story/#top"}
    duplicate = {"title": "Repeat", "url": "https://example.com/story"}
    other = {"title": "Other", "url": "https://example.com/other"}

    result = dedupe(items=[first, duplicate, other])

    assert result["items"] == [first, other]
    assert result["item_count"] == 2
    assert result["duplicate_count"] == 1


def test_dedupe_invalid_items_returns_error_dict() -> None:
    result = dedupe(items="not-a-list")

    assert result["error"] == "InvalidInput"
    assert "list" in result["message"]


def test_dedupe_malformed_list_entry_returns_error_dict() -> None:
    result = dedupe(items=[{"title": "Valid"}, "not-an-object"])

    assert result["error"] == "InvalidInput"
    assert "object" in result["message"]


def test_dedupe_item_without_url_is_preserved() -> None:
    item = {"title": "No source URL"}

    result = dedupe(items=[item])

    assert result["items"] == [item]
    assert result["duplicate_count"] == 0
