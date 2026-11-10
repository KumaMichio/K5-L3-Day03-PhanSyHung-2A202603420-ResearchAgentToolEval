"""Offline unit tests for the github_repo tool (TV3)."""
from __future__ import annotations

from typing import Any

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
from tools.github_repo.tool import _normalize

github_repo = TOOL_FUNCTIONS["github_repo"]


@pytest.fixture(autouse=True)
def no_github_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """conftest.clean_env does not know GITHUB_TOKEN; never depend on the developer's env."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


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


def test_github_full_url_normalizes_slug_and_maps_metadata(fake_http_seq) -> None:
    calls = fake_http_seq(
        FakeResponse({
            "stargazers_count": 84000,
            "forks_count": 12000,
            "description": "Graph framework",
            "pushed_at": "2026-11-01T00:00:00Z",
            "html_url": "https://github.com/langchain-ai/langgraph",
        }),
        FakeResponse({"tag_name": "v2.1.0"}),
    )

    result = github_repo(repo="https://github.com/langchain-ai/langgraph.git")

    assert [call["url"] for call in calls] == [
        "https://api.github.com/repos/langchain-ai/langgraph",
        "https://api.github.com/repos/langchain-ai/langgraph/releases/latest",
    ]
    assert result["repo"] == "langchain-ai/langgraph"
    assert result["stars"] == 84000
    assert result["forks"] == 12000
    assert result["description"] == "Graph framework"
    assert result["latest_release"] == "v2.1.0"
    assert result["last_push"] == "2026-11-01T00:00:00Z"
    assert result["url"] == "https://github.com/langchain-ai/langgraph"
    assert "Authorization" not in calls[0]["headers"]


def test_github_repo_404_returns_error_dict_and_does_not_check_release(fake_http_seq) -> None:
    calls = fake_http_seq(FakeResponse(status_code=404))

    result = github_repo(repo="notexist/repository")

    assert len(calls) == 1
    assert result["tool"] == "github_repo"
    assert result["error"] == "HTTPError"


def test_github_latest_release_404_is_null_not_error(fake_http_seq) -> None:
    calls = fake_http_seq(
        FakeResponse({"stargazers_count": 7, "forks_count": 1, "description": "Test"}),
        FakeResponse(status_code=404),
    )

    result = github_repo(repo="owner/repo")

    assert len(calls) == 2
    assert result["latest_release"] is None
    assert result["stars"] == 7
    assert result["url"] == "https://github.com/owner/repo"
    assert "error" not in result


def test_github_token_is_sent_when_available(monkeypatch, fake_http_seq) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-test-only-token")
    calls = fake_http_seq(
        FakeResponse({"stargazers_count": 10}),
        FakeResponse(status_code=404),
    )

    result = github_repo(repo="owner/repo")

    assert len(calls) == 2
    assert all(call["headers"]["Authorization"] == "Bearer fake-test-only-token" for call in calls)
    assert result["stars"] == 10


def test_github_invalid_repo_returns_value_error_without_network(fake_http_seq) -> None:
    calls = fake_http_seq()

    result = github_repo(repo="https://untrusted.example/a/b")

    assert result["error"] == "ValueError"
    assert calls == []


def test_github_slug_normalization_handles_url_query_and_trailing_slash() -> None:
    assert _normalize("https://github.com/owner/repo/?tab=readme") == "owner/repo"
    assert _normalize("github.com/owner/repo.git") == "owner/repo"
    assert _normalize("  owner/repo  ") == "owner/repo"
    assert _normalize("https://github.com/owner/repo/issues") == ""
    assert _normalize("") == ""


def test_github_http_429_on_release_returns_error_dict(fake_http_seq) -> None:
    calls = fake_http_seq(
        FakeResponse({"stargazers_count": 10}),
        FakeResponse(status_code=429),
    )

    result = github_repo(repo="owner/repo")

    assert len(calls) == 2
    assert result["error"] == "HTTPError"
