
from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urlparse

import requests

from tools._shared import TIMEOUT, err

_API = "https://api.github.com/repos"
_OWNER_REPO = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9_.-]+)$"
)


def _normalize(repo: str) -> str:
    """Normalize GitHub URL or owner/name to owner/name."""
    if not isinstance(repo, str):
        return ""

    value = repo.strip()
    if not value:
        return ""

    if value.startswith(("https://", "http://")) or value.startswith(
        ("github.com/", "www.github.com/")
    ):
        if not value.startswith(("https://", "http://")):
            value = "https://" + value

        parsed = urlparse(value)

        if parsed.scheme not in {"http", "https"}:
            return ""

        if (parsed.hostname or "").lower() not in {
            "github.com",
            "www.github.com",
        }:
            return ""

        segments = [
            p for p in parsed.path.strip("/").split("/") if p
        ]

        if len(segments) != 2:
            return ""

        value = "/".join(segments)

    value = value.strip("/")

    if value.endswith(".git"):
        value = value[:-4]

    return value if _OWNER_REPO.fullmatch(value) else ""


def github_repo(repo: str = "") -> dict[str, Any]:
    try:
        slug = _normalize(repo)

        if not slug:
            raise ValueError(
                "repo must be an owner/name slug or a GitHub repository URL"
            )

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Day03-Research-Agent/1.0 (educational research lab)",
        }

        token = os.getenv("GITHUB_TOKEN")

        if token:
            headers["Authorization"] = f"Bearer {token}"

        # 1. Get repository metadata
        repo_response = requests.get(
            f"{_API}/{slug}",
            headers=headers,
            timeout=TIMEOUT,
        )
        repo_response.raise_for_status()
        data = repo_response.json()

        # 2. Get latest release
        release_response = requests.get(
            f"{_API}/{slug}/releases/latest",
            headers=headers,
            timeout=TIMEOUT,
        )

        if release_response.status_code == 404:
            latest_release = None
        else:
            release_response.raise_for_status()
            release_data = release_response.json()
            latest_release = (
                release_data.get("tag_name")
                or release_data.get("name")
                or None
            )

        # 3. Return structured result
        return {
            "tool": "github_repo",
            "repo": slug,
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "description": data.get("description"),
            "last_push": data.get("pushed_at"),
            "latest_release": latest_release,
            "url": data.get("html_url")
                   or f"https://github.com/{slug}",
        }

    except Exception as exc:
        return err("github_repo", exc)
