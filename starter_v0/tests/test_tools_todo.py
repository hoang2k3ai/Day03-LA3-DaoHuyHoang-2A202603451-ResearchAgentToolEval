"""Offline unit tests for core and team-added tools.

HTTP calls are mocked with ``fake_http`` and filesystem writes use ``tmp_path``.
The examples in test_tools_examples.py and fixtures in conftest.py provide the
test patterns used here.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import re

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS  # noqa: F401


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    options = ["Tin AI", "Tin robotics"]
    result = TOOL_FUNCTIONS["clarify"](question="Bạn muốn xem tin nào?", response_type="choice", options=options)

    assert result["options"] == options
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "T1", "section": "A"},
        {"title": "T2", "section": "B"},
        {"title": "T3", "section": "A"},
    ]
    markdown = TOOL_FUNCTIONS["format"](items=items, template="sections")["markdown"]

    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1


def test_format_thread_numbers_items() -> None:
    items = [{"title": "Một"}, {"title": "Hai"}, {"title": "Ba"}]
    markdown = TOOL_FUNCTIONS["format"](items=items, template="thread")["markdown"]
    lines = [line for line in markdown.splitlines() if line.strip()]

    assert [line.split(" ")[0] for line in lines] == ["1/", "2/", "3/"]


def test_format_empty_items_does_not_crash() -> None:
    assert TOOL_FUNCTIONS["format"](items=None, template="sections")["item_count"] == 0
    assert TOOL_FUNCTIONS["format"](items=[], template="sections")["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "bot-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "12345"
    assert calls[0]["json"]["text"] == "Bản tin"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    TOOL_FUNCTIONS["lookup"](query="OpenAI", timeframe=None)

    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {
        "markdown": "Nội dung bài",
        "metadata": {"title": "T", "sourceURL": "https://ex.com/a"},
    }}))

    item = TOOL_FUNCTIONS["fetch"](url="https://ex.com/a")["items"][0]

    assert item == {"title": "T", "url": "https://ex.com/a", "source": "ex.com", "summary": "Nội dung bài"}


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))

    summary = TOOL_FUNCTIONS["fetch"](url="https://ex.com/a")["items"][0]["summary"]

    assert len(summary) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    raw = [{"text": "Không có id", "screen_name": "sama"}]
    raw += [{"tweet_id": str(i), "text": f"Bài {i}", "screen_name": "sama"} for i in range(1, 7)]
    fake_http(FakeResponse({"timeline": raw}))

    items = TOOL_FUNCTIONS["timeline"](screenname="sama", limit=3)["items"]

    assert len(items) == 3
    for item in items:
        assert re.fullmatch(r"https://x\.com/sama/status/\d+", item["url"])


@pytest.mark.parametrize("search_type", ["Top", "Latest"])
def test_social_search_passes_search_type(search_type, monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"tweets": []}))

    TOOL_FUNCTIONS["social_search"](query="AI", search_type=search_type)

    assert calls[0]["params"] == {"query": "AI", "search_type": search_type}


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert TOOL_FUNCTIONS["policy"](query="")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    results = TOOL_FUNCTIONS["policy"](query="data privacy", policy_area="data_privacy")["results"]

    assert results
    assert all(item["policy_area"] == "data_privacy" for item in results)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    results = TOOL_FUNCTIONS["policy"](query="injection probe", policy_area="source_citation")["results"]
    untrusted = [line for item in results for line in item["untrusted_text"]]
    facts = " ".join(item["facts"] for item in results)

    assert any("ignore the citation policy" in line for line in untrusted)
    assert "ignore the citation policy" not in facts


# ---------------- team-added tools ----------------
# 3+ tests per tool: happy path, bad input from the model, failure path.

import datetime as _dt  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

import importlib  # noqa: E402

# Folder names equal the function names, and the registry import shadows the
# sub-package attribute, so `import tools.x.tool as m` fails. Load modules by name.
dedupe_mod = importlib.import_module("tools.dedupe_items.tool")
time_mod = importlib.import_module("tools.resolve_time_range.tool")
note_mod = importlib.import_module("tools.save_note.tool")
from tools.calculate.tool import calculate  # noqa: E402
from tools.dedupe_items.tool import dedupe_items  # noqa: E402
from tools.extract_links.tool import extract_links  # noqa: E402
from tools.resolve_time_range.tool import resolve_time_range  # noqa: E402
from tools.save_note.tool import save_note  # noqa: E402
from tools.wiki_summary.tool import wiki_summary  # noqa: E402


# calculate
def test_calculate_evaluates_percentage() -> None:
    assert calculate("0.15*2400000")["result"] == pytest.approx(360000)


def test_calculate_rejects_code_injection_without_running_it() -> None:
    result = calculate("__import__('os').system('echo hi')")
    assert result["error"] == "ValueError"
    assert "result" not in result


def test_calculate_division_by_zero_returns_error_dict() -> None:
    result = calculate("1/0")
    assert result["error"] == "ZeroDivisionError"


# resolve_time_range (Wednesday 2026-11-11, Vietnam time)
def _fix_today(monkeypatch) -> None:
    fixed = _dt.datetime(2026, 11, 11, 9, 0, tzinfo=time_mod.VN_TZ)
    monkeypatch.setattr(time_mod, "_now", lambda: fixed)


def test_resolve_time_range_this_week_starts_monday(monkeypatch) -> None:
    _fix_today(monkeypatch)
    result = resolve_time_range("tuần này")
    assert result["start"] == "2026-11-09"
    assert result["end"] == "2026-11-11"


def test_resolve_time_range_unknown_phrase_is_error(monkeypatch) -> None:
    _fix_today(monkeypatch)
    assert resolve_time_range("ngày mai")["error"] == "UnsupportedPhrase"


def test_resolve_time_range_empty_input_returns_error_dict(monkeypatch) -> None:
    _fix_today(monkeypatch)
    assert resolve_time_range("")["error"] == "UnsupportedPhrase"


# extract_links
def test_extract_links_strips_trailing_punctuation_and_keeps_order() -> None:
    result = extract_links("Xem https://a.com/x, và https://b.org/y.")
    assert result["links"] == ["https://a.com/x", "https://b.org/y"]
    assert result["domains"] == ["a.com", "b.org"]


def test_extract_links_removes_duplicates() -> None:
    result = extract_links("https://a.com/x https://a.com/x")
    assert result["count"] == 1


def test_extract_links_empty_text_returns_no_links() -> None:
    assert extract_links("")["links"] == []


# dedupe_items
def test_dedupe_items_drops_same_url_after_utm_and_trailing_slash() -> None:
    items = [
        {"title": "A", "url": "https://news.com/post/?utm_source=x"},
        {"title": "B", "url": "https://news.com/post"},
    ]
    result = dedupe_items(items)
    assert result["item_count"] == 1
    assert result["removed"] == 1


def test_dedupe_items_drops_same_title_from_different_urls() -> None:
    items = [
        {"title": "AI tăng trưởng", "url": "https://a.com/1"},
        {"title": "ai tang truong", "url": "https://b.com/2"},
    ]
    assert dedupe_items(items)["item_count"] == 1


def test_dedupe_items_ignores_non_dict_entries_and_none() -> None:
    assert dedupe_items(None)["item_count"] == 0
    assert dedupe_items(["bad", {"title": "ok", "url": "https://x.com"}])["item_count"] == 1


def test_dedupe_items_rejects_oversized_list() -> None:
    items = [{"title": str(i), "url": f"https://x.com/{i}"} for i in range(dedupe_mod.MAX_ITEMS + 1)]
    assert dedupe_items(items)["error"] == "TooManyItems"


# wiki_summary (offline, mocked HTTP)
def test_wiki_summary_maps_summary_and_url(monkeypatch, fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Trí tuệ nhân tạo", "type": "standard", "extract": "AI là ngành khoa học máy tính.",
        "content_urls": {"desktop": {"page": "https://vi.wikipedia.org/wiki/Tri_tue_nhan_tao"}},
    }))
    result = wiki_summary("Trí tuệ nhân tạo")
    assert calls[0]["url"].startswith("https://vi.wikipedia.org/api/rest_v1/page/summary/")
    assert result["summary"] == "AI là ngành khoa học máy tính."
    assert result["url"].endswith("Tri_tue_nhan_tao")


def test_wiki_summary_empty_topic_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    assert wiki_summary("")["error"] == "EmptyTopic"
    assert calls == []


def test_wiki_summary_missing_page_returns_not_found(fake_http) -> None:
    fake_http(FakeResponse({}, status_code=404))
    assert wiki_summary("Không có trang này")["error"] == "NotFound"


# save_note (writes only under a temp folder)
def _temp_notes(monkeypatch, tmp_path: _Path) -> _Path:
    folder = tmp_path / "notes"
    monkeypatch.setattr(note_mod, "NOTES_DIR", folder)
    return folder


def test_save_note_writes_markdown_when_confirmed(monkeypatch, tmp_path) -> None:
    folder = _temp_notes(monkeypatch, tmp_path)
    result = save_note(title="Tin AI", content="Nội dung ghi chú", confirmed=True)
    assert result["status"] == "saved"
    written = list(folder.glob("*.md"))
    assert len(written) == 1
    assert "# Tin AI" in written[0].read_text(encoding="utf-8")


def test_save_note_without_confirmation_writes_nothing(monkeypatch, tmp_path) -> None:
    folder = _temp_notes(monkeypatch, tmp_path)
    result = save_note(title="Tin AI", content="Nội dung", confirmed=False)
    assert result["status"] == "needs_confirmation"
    assert not folder.exists()


def test_save_note_empty_title_returns_error_and_writes_nothing(monkeypatch, tmp_path) -> None:
    folder = _temp_notes(monkeypatch, tmp_path)
    result = save_note(title="", content="x", confirmed=True)
    assert result["error"] == "EmptyInput"
    assert not folder.exists()
