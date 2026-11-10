from __future__ import annotations

import os
import re
from typing import Any
import requests

from tools._shared import TIMEOUT, err


def _normalize(repo: str) -> str:
    m = re.search(r"([\w.-]+/[\w.-]+?)(?:\.git)?/?$", (repo or "").strip())
    return m.group(1) if m else ""


def github_repo(repo: str = "") -> dict[str, Any]:
    try:
        slug = _normalize(repo)
        if not slug:
            return {"tool": "github_repo", "error": "invalid_repo", "message": "Invalid repo format. Expected owner/name"}
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Day03-Research-Agent/1.0"}
        if os.getenv("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
        
        # 1. GET repo details
        resp = requests.get(f"https://api.github.com/repos/{slug}", headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # 2. GET latest release
        latest_release = None
        rel_resp = requests.get(f"https://api.github.com/repos/{slug}/releases/latest", headers=headers, timeout=TIMEOUT)
        if rel_resp.status_code == 200:
            latest_release = rel_resp.json().get("tag_name")

        return {
            "tool": "github_repo",
            "repo": slug,
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "description": data.get("description") or "",
            "last_push": data.get("pushed_at"),
            "latest_release": latest_release,
            "url": data.get("html_url") or f"https://github.com/{slug}",
        }
    except Exception as exc:
        return err("github_repo", exc)

