"""TODO(student): Tool Unit Test Challenge.

Tests for core tools, guardrails, and new custom tools (hn_search, citations).
Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
One behaviour per test.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
hn_search_tool = TOOL_FUNCTIONS["hn_search"]
citations_tool = TOOL_FUNCTIONS["citations"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    res = clarify_tool(question="Bạn muốn chọn chủ đề nào?", response_type="choice", options=["AI", "Robotics"])
    assert res["awaiting_user"] is True
    assert res["options"] == ["AI", "Robotics"]
    assert res["response_type"] == "choice"
    assert res["question"] == "Bạn muốn chọn chủ đề nào?"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "Item 1", "url": "https://example.com/1", "section": "Tech"},
        {"title": "Item 2", "url": "https://example.com/2", "section": "Science"},
        {"title": "Item 3", "url": "https://example.com/3", "section": "Tech"},
    ]
    res = format_tool(items=items, template="sections")
    md = res["markdown"]
    assert md.count("## Tech") == 1
    assert md.count("## Science") == 1
    assert "[example.com](https://example.com/1)" in md


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "Item A", "url": "https://example.com/a"},
        {"title": "Item B", "url": "https://example.com/b"},
    ]
    res = format_tool(items=items, template="thread")
    md = res["markdown"]
    assert "1/" in md
    assert "2/" in md


def test_format_empty_items_does_not_crash() -> None:
    res_none = format_tool(items=None, template="bullets")
    assert res_none["item_count"] == 0
    assert "error" not in res_none

    res_empty = format_tool(items=[], template="bullets")
    assert res_empty["item_count"] == 0
    assert "error" not in res_empty


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_bot_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123456789")
    calls = fake_http(FakeResponse({"ok": True, "result": {"message_id": 42}}))

    res = send_tool(text="Bản tin công nghệ", confirmed=True)
    assert res["status"] == "sent"
    assert len(calls) == 1
    assert "fake_bot_token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-100123456789"
    assert calls[0]["json"]["text"] == "Bản tin công nghệ"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    res = send_tool(text="Bản tin không env", confirmed=True)
    assert res["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in res["message"] or "TELEGRAM_CHAT_ID" in res["message"]
    assert len(calls) == 0


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "mock-tavily-key")
    calls = fake_http(FakeResponse({"results": []}))

    res = lookup_tool(query="DeepSeek", timeframe=None)
    assert "error" not in res
    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "mock-firecrawl-key")
    mock_payload = {
        "data": {
            "markdown": "# Tiêu đề\nNội dung bài báo nghiên cứu.",
            "metadata": {
                "title": "Bài báo hay",
                "sourceURL": "https://research.example.com/paper-1",
            },
        }
    }
    fake_http(FakeResponse(mock_payload))

    res = fetch_tool(url="https://research.example.com/paper-1")
    assert "error" not in res
    item = res["items"][0]
    assert item["title"] == "Bài báo hay"
    assert item["url"] == "https://research.example.com/paper-1"
    assert item["source"] == "research.example.com"
    assert "Nội dung bài báo" in item["summary"]


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "mock-firecrawl-key")
    huge_text = "X" * 6000
    mock_payload = {
        "data": {
            "markdown": huge_text,
            "metadata": {"title": "Huge", "sourceURL": "https://example.com/huge"},
        }
    }
    fake_http(FakeResponse(mock_payload))

    res = fetch_tool(url="https://example.com/huge")
    summary = res["items"][0]["summary"]
    assert len(summary) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "mock-rapidapi-key")
    timeline_items = [
        {"text": "Item missing tweet_id", "screen_name": "sama"},
        {"tweet_id": "1001", "text": "Post 1", "screen_name": "sama"},
        {"tweet_id": "1002", "text": "Post 2", "screen_name": "sama"},
        {"tweet_id": "1003", "text": "Post 3", "screen_name": "sama"},
        {"tweet_id": "1004", "text": "Post 4", "screen_name": "sama"},
        {"tweet_id": "1005", "text": "Post 5", "screen_name": "sama"},
        {"tweet_id": "1006", "text": "Post 6", "screen_name": "sama"},
    ]
    fake_http(FakeResponse({"timeline": timeline_items}))

    res = timeline_tool(screenname="sama", limit=3)
    assert "error" not in res
    assert len(res["items"]) == 3
    for it in res["items"]:
        assert it["url"].startswith("https://x.com/sama/status/")


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "mock-rapidapi-key")
    calls = fake_http(FakeResponse({"timeline": []}))

    res = social_search_tool(query="GPT-5", search_type="Top")
    assert "error" not in res
    assert len(calls) == 1
    assert calls[0]["params"]["search_type"] == "Top"
    assert calls[0]["params"]["query"] == "GPT-5"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    res = policy_tool(query="")
    assert res["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    res = policy_tool(query="privacy data", policy_area="data_privacy")
    assert res["results"]
    for hit in res["results"]:
        assert hit["policy_area"] == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    res = policy_tool(query="citation injection", policy_area="source_citation")
    injection_hits = [h for h in res["results"] if h["section"] == "Injection probe"]
    assert injection_hits, "Expected Injection probe section to be matched"
    hit = injection_hits[0]
    assert "ignore the citation policy" not in hit["facts"]
    assert any("ignore the citation policy" in line for line in hit["untrusted_text"])


# ---------------- YOUR NEW TOOLS: hn_search & citations ----------------

def test_hn_search_sort_recent_calls_search_by_date(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [
        {"title": "Show HN: My App", "url": "https://news.ycombinator.com/item?id=123", "points": 50, "objectID": "123"}
    ]}))
    res = hn_search_tool(query="LLM", sort="recent", limit=5)
    assert "error" not in res
    assert len(calls) == 1
    assert calls[0]["url"].endswith("/search_by_date")
    assert calls[0]["params"]["query"] == "LLM"
    assert calls[0]["params"]["tags"] == "story"
    assert calls[0]["params"]["hitsPerPage"] == 5
    assert res["items"][0]["title"] == "Show HN: My App"


def test_hn_search_clamps_limit_and_passes_hits_per_page(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    # limit=0 clamped to 1
    hn_search_tool(query="AI", sort="popular", limit=0)
    assert calls[0]["params"]["hitsPerPage"] == 1

    # limit="5" clamped/converted to 5
    calls.clear()
    hn_search_tool(query="AI", sort="popular", limit="5")
    assert calls[0]["params"]["hitsPerPage"] == 5

    # limit=99 clamped to 10
    calls.clear()
    hn_search_tool(query="AI", sort="popular", limit=99)
    assert calls[0]["params"]["hitsPerPage"] == 10


def test_hn_search_http_429_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))
    res = hn_search_tool(query="Rust")
    assert res["error"] == "HTTPError"
    assert res["tool"] == "hn_search"


def test_citations_arxiv_id_calls_doi_and_title_calls_search(fake_http) -> None:
    # 1. Calling with arXiv id
    calls = fake_http(FakeResponse({
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "cited_by_count": 5200,
        "publication_year": 2021,
        "primary_location": {"source": {"display_name": "ICLR"}},
        "doi": "https://doi.org/10.48550/arxiv.2106.09685",
    }))
    res1 = citations_tool(paper="2106.09685")
    assert "error" not in res1
    assert len(calls) == 1
    assert "doi:10.48550/arXiv.2106.09685" in calls[0]["url"]
    assert res1["items"][0]["cited_by_count"] == 5200
    assert res1["items"][0]["venue"] == "ICLR"

    # 2. Calling with title
    calls.clear()
    calls = fake_http(FakeResponse({
        "results": [{
            "title": "Attention Is All You Need",
            "cited_by_count": 120000,
            "publication_year": 2017,
            "primary_location": {"source": {"display_name": "NeurIPS"}},
            "id": "https://openalex.org/W2963403868",
        }]
    }))
    res2 = citations_tool(paper="Attention Is All You Need")
    assert "error" not in res2
    assert len(calls) == 1
    assert calls[0]["params"]["search"] == "Attention Is All You Need"
    assert calls[0]["params"]["per-page"] == 1
    assert res2["items"][0]["cited_by_count"] == 120000


def test_citations_empty_results_returns_empty_items(fake_http) -> None:
    fake_http(FakeResponse({"results": []}))
    res = citations_tool(paper="Some Unknown Paper Title That Does Not Exist 123456")
    assert "error" not in res
    assert res["items"] == []


def test_citations_empty_paper_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"results": []}))
    res = citations_tool(paper="")
    assert res["error"] == "ValueError"
    assert len(calls) == 0
