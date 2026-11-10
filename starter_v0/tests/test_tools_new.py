from __future__ import annotations

import pytest
from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

wiki_tool = TOOL_FUNCTIONS["wiki"]
github_tool = TOOL_FUNCTIONS["github_repo"]
hn_tool = TOOL_FUNCTIONS["hn_search"]
citations_tool = TOOL_FUNCTIONS["citations"]


# ---------------- wiki ----------------
# fake_http chỉ nhận 1 response, dùng side_effect bằng list chung

def _multi_responses(monkeypatch, *responses: FakeResponse) -> list[dict]:
    """Trả nhiều response theo thứ tự cho mỗi lần gọi requests.get."""
    import requests
    calls: list[dict] = []
    response_queue = list(responses)

    def _fake_get(url: str, **kwargs):
        calls.append({"url": url, "params": kwargs.get("params", {}), **kwargs})
        if not response_queue:
            raise ValueError("No more fake responses")
        return response_queue.pop(0)

    monkeypatch.setattr(requests, "get", _fake_get)
    return calls


def test_wiki_search_happy_path(monkeypatch) -> None:
    calls = _multi_responses(
        monkeypatch,
        FakeResponse({"pages": [{"key": "Reinforcement_learning"}]}),
        FakeResponse({
            "title": "Reinforcement learning",
            "extract": "An area of machine learning.",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Reinforcement_learning"}},
        }),
    )
    result = wiki_tool(query="RLHF", lang="en")
    assert len(calls) == 2
    assert "en.wikipedia.org" in calls[0]["url"]
    assert result["tool"] == "wiki"
    assert result["items"][0]["title"] == "Reinforcement learning"
    assert "machine learning" in result["items"][0]["summary"]


def test_wiki_search_not_found_returns_empty_items(fake_http) -> None:
    fake_http(FakeResponse({"pages": []}))
    result = wiki_tool(query="nonexistent_concept_123456")
    assert result["items"] == []


def test_wiki_search_invalid_lang_defaults_to_en(monkeypatch) -> None:
    calls = _multi_responses(
        monkeypatch,
        FakeResponse({"pages": [{"key": "AI"}]}),
        FakeResponse({"title": "AI", "extract": "Artificial Intelligence"}),
    )
    wiki_tool(query="AI", lang="invalid_lang")
    assert "en.wikipedia.org" in calls[0]["url"]


# ---------------- github_repo ----------------

def test_github_repo_normalizes_url_and_fetches_info(monkeypatch) -> None:
    calls = _multi_responses(
        monkeypatch,
        FakeResponse({"stargazers_count": 15000, "forks_count": 2000, "description": "Graph framework", "pushed_at": "2026-05-01"}),
        FakeResponse({"tag_name": "v0.2.0"}),
    )
    result = github_tool(repo="https://github.com/langchain-ai/langgraph.git")
    assert calls[0]["url"] == "https://api.github.com/repos/langchain-ai/langgraph"
    assert result["repo"] == "langchain-ai/langgraph"
    assert result["stars"] == 15000
    assert result["latest_release"] == "v0.2.0"


def test_github_repo_404_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse({}, status_code=404))
    result = github_tool(repo="nonexistent/repo123")
    assert "error" in result


def test_github_repo_without_release_returns_none_release(monkeypatch) -> None:
    _multi_responses(
        monkeypatch,
        FakeResponse({"stargazers_count": 10, "forks_count": 0, "description": "", "pushed_at": "", "html_url": "https://github.com/user/no-release-repo"}),
        FakeResponse({}, status_code=404),
    )
    result = github_tool(repo="user/no-release-repo")
    assert result["stars"] == 10
    assert result["latest_release"] is None


# ---------------- hn_search ----------------

def test_hn_search_popular_sort(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "hits": [
            {"title": "Rust in 2026", "url": "https://rust-lang.org", "points": 350, "num_comments": 120, "objectID": "12345"}
        ]
    }))
    result = hn_tool(query="Rust", sort="popular", limit=5)
    assert "/search" in calls[0]["url"]
    assert calls[0]["params"]["hitsPerPage"] == 5
    assert result["items"][0]["points"] == 350
    assert "news.ycombinator.com/item?id=12345" in result["items"][0]["hn_url"]


def test_hn_search_recent_sort(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hn_tool(query="Llama", sort="recent", limit=15)
    assert "/search_by_date" in calls[0]["url"]
    assert calls[0]["params"]["hitsPerPage"] == 10  # Clamped to 10


def test_hn_search_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse({}, status_code=429))
    result = hn_tool(query="error_trigger")
    assert "error" in result


# ---------------- citations ----------------

def test_citations_by_arxiv_id(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "id": "https://openalex.org/W1234",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "cited_by_count": 5200,
        "publication_year": 2021,
        "primary_location": {"source": {"display_name": "arXiv"}},
    }))
    result = citations_tool(paper="arXiv:2106.09685")
    assert "doi:10.48550/arXiv.2106.09685" in calls[0]["url"]
    assert result["items"][0]["cited_by_count"] == 5200
    assert result["items"][0]["publication_year"] == 2021


def test_citations_by_title_search(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "results": [
            {
                "id": "https://openalex.org/W5678",
                "title": "Attention Is All You Need",
                "cited_by_count": 120000,
                "publication_year": 2017,
                "primary_location": {"source": {"display_name": "NeurIPS"}},
            }
        ]
    }))
    result = citations_tool(paper="Attention Is All You Need")
    assert calls[0]["params"]["search"] == "Attention Is All You Need"
    assert result["items"][0]["cited_by_count"] == 120000


def test_citations_empty_paper_returns_error() -> None:
    result = citations_tool(paper="")
    assert "error" in result
