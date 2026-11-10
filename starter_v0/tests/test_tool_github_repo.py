"""Offline contract/behavior tests for tool #2 (GitHub repository metadata)."""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
#from tools.github_repo.tool import _normalize


github_repo = TOOL_FUNCTIONS["github_repo"]


def test_github_full_url_normalizes_slug_and_maps_metadata(fake_http) -> None:
    calls = fake_http([
        FakeResponse({
            "stargazers_count": 84000,
            "forks_count": 12000,
            "description": "Graph framework",
            "pushed_at": "2026-11-01T00:00:00Z",
            "html_url": "https://github.com/langchain-ai/langgraph",
        }),
        FakeResponse({"tag_name": "v2.1.0", "html_url": "https://github.com/langchain-ai/langgraph/releases/tag/v2.1.0"}),
    ])

    result = github_repo(repo="https://github.com/langchain-ai/langgraph.git")

    assert [call["url"] for call in calls] == [
        "https://api.github.com/repos/langchain-ai/langgraph",
        "https://api.github.com/repos/langchain-ai/langgraph/releases/latest",
    ]
    assert result["repo"] == "langchain-ai/langgraph"
    assert result["stars"] == 84000
    assert result["forks"] == 12000
    assert result["latest_release"] == "v2.1.0"
    assert result["last_push"] == "2026-11-01T00:00:00Z"
    assert "Authorization" not in calls[0]["headers"]


def test_github_repo_404_returns_error_dict_and_does_not_check_release(fake_http) -> None:
    calls = fake_http([FakeResponse(status_code=404)])

    result = github_repo(repo="notexist/repository")

    assert len(calls) == 1
    assert result["tool"] == "github_repo"
    assert result["error"] == "HTTPError"


def test_github_latest_release_404_is_null_not_error(fake_http) -> None:
    calls = fake_http([
        FakeResponse({"stargazers_count": 7, "forks_count": 1, "description": "Test"}),
        FakeResponse(status_code=404),
    ])

    result = github_repo(repo="owner/repo")

    assert len(calls) == 2
    assert result["latest_release"] is None
    assert result["stars"] == 7
    assert "error" not in result


def test_github_token_is_sent_when_available(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-test-only-token")
    calls = fake_http([
        FakeResponse({"stargazers_count": 10}),
        FakeResponse(status_code=404),
    ])

    result = github_repo(repo="owner/repo")

    assert len(calls) == 2
    assert all(call["headers"]["Authorization"] == "Bearer fake-test-only-token" for call in calls)
    assert result["stars"] == 10


def test_github_invalid_repo_returns_value_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"stargazers_count": 1}))

    result = github_repo(repo="https://untrusted.example/a/b")

    assert result["error"] == "ValueError"
    assert calls == []


def test_github_slug_normalization_handles_url_query_and_trailing_slash() -> None:
    assert _normalize("https://github.com/owner/repo/?tab=readme") == "owner/repo"
    assert _normalize("github.com/owner/repo.git") == "owner/repo"
    assert _normalize("owner/repo") == "owner/repo"
    assert _normalize("https://github.com/owner/repo/issues") == ""


def test_github_http_429_on_release_returns_error_dict(fake_http) -> None:
    calls = fake_http([
        FakeResponse({"stargazers_count": 10}),
        FakeResponse(status_code=429),
    ])

    result = github_repo(repo="owner/repo")

    assert len(calls) == 2
    assert result["error"] == "HTTPError"
