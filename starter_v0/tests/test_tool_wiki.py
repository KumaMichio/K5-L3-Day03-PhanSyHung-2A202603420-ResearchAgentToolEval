"""Offline unit tests for the wiki tool (TV3)."""
from __future__ import annotations

from typing import Any

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

wiki = TOOL_FUNCTIONS["wiki"]

SEARCH_HIT = {"pages": [{"id": 1, "key": "Reinforcement_learning_from_human_feedback",
                         "title": "Reinforcement learning from human feedback"}]}
SUMMARY = {
    "title": "Reinforcement learning from human feedback",
    "extract": "RLHF is a technique to align an intelligent agent with human preferences.",
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Reinforcement_learning_from_human_feedback"}},
}


@pytest.fixture
def fake_http_seq(monkeypatch: pytest.MonkeyPatch):
    """Like conftest.fake_http, but returns the given responses one per call, in order."""

    def _install(*responses: FakeResponse) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []
        queue = list(responses)

        def _get(url: str, **kwargs: Any) -> FakeResponse:
            calls.append({"method": "GET", "url": url, **kwargs})
            assert queue, f"Unexpected extra request: {url}"
            return queue.pop(0)

        monkeypatch.setattr(requests, "get", _get)
        return calls

    return _install


def test_wiki_happy_path_searches_then_fetches_summary(fake_http_seq) -> None:
    calls = fake_http_seq(FakeResponse(SEARCH_HIT), FakeResponse(SUMMARY))

    result = wiki(query="RLHF", lang="en")

    assert [c["url"] for c in calls] == [
        "https://en.wikipedia.org/w/rest.php/v1/search/title",
        "https://en.wikipedia.org/api/rest_v1/page/summary/Reinforcement_learning_from_human_feedback",
    ]
    assert calls[0]["params"] == {"q": "RLHF", "limit": 1}
    assert all("User-Agent" in c["headers"] for c in calls)
    assert result["tool"] == "wiki"
    assert result["lang"] == "en"
    assert result["items"] == [{
        "title": SUMMARY["title"],
        "summary": SUMMARY["extract"],
        "url": SUMMARY["content_urls"]["desktop"]["page"],
    }]


def test_wiki_vi_uses_vietnamese_wikipedia(fake_http_seq) -> None:
    calls = fake_http_seq(FakeResponse(SEARCH_HIT), FakeResponse(SUMMARY))

    result = wiki(query="Học tăng cường", lang="vi")

    assert all(c["url"].startswith("https://vi.wikipedia.org/") for c in calls)
    assert result["lang"] == "vi"


def test_wiki_unknown_lang_falls_back_to_english(fake_http_seq) -> None:
    calls = fake_http_seq(FakeResponse(SEARCH_HIT), FakeResponse(SUMMARY))

    result = wiki(query="RLHF", lang="xx")

    assert calls[0]["url"].startswith("https://en.wikipedia.org/")
    assert result["lang"] == "en"


def test_wiki_no_page_found_returns_empty_items_without_summary_call(fake_http_seq) -> None:
    calls = fake_http_seq(FakeResponse({"pages": []}))

    result = wiki(query="zzqxnotarealconcept")

    assert len(calls) == 1
    assert result["items"] == []
    assert "error" not in result


def test_wiki_empty_query_returns_error_without_network(fake_http_seq) -> None:
    calls = fake_http_seq()

    result = wiki(query="   ")

    assert result == {"tool": "wiki", "error": "ValueError", "message": "query is required"}
    assert calls == []


def test_wiki_page_key_is_url_encoded(fake_http_seq) -> None:
    calls = fake_http_seq(FakeResponse({"pages": [{"key": "AC/DC", "title": "AC/DC"}]}), FakeResponse({"title": "AC/DC"}))

    result = wiki(query="AC/DC")

    assert calls[1]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/AC%2FDC"
    assert result["items"][0]["url"] == "https://en.wikipedia.org/wiki/AC/DC"


def test_wiki_http_error_returns_error_dict(fake_http_seq) -> None:
    fake_http_seq(FakeResponse(status_code=503))

    result = wiki(query="RLHF")

    assert result["tool"] == "wiki"
    assert result["error"] == "HTTPError"
