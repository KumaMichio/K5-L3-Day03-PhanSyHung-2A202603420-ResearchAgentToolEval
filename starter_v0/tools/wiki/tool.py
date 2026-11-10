from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

# Owner: TV3. Keep the function name and parameter names: they must match
# artifacts/tools.yaml (checked by tests/test_tool_contract.py).

SUPPORTED_LANGS = {"en", "vi"}
# Wikipedia rejects requests without a descriptive User-Agent.
HEADERS = {"User-Agent": "Day03-Research-Agent/1.0 (educational research lab)"}


def wiki_search(query: str = "", lang: str = "en") -> dict[str, Any]:
    """Find the best-matching Wikipedia page for `query` and return its summary."""
    try:
        query = (query or "").strip() if isinstance(query, str) else ""
        if not query:
            raise ValueError("query is required")
        lang = lang.strip().lower() if isinstance(lang, str) else "en"
        if lang not in SUPPORTED_LANGS:
            lang = "en"
        base = f"https://{lang}.wikipedia.org"

        # 1. Title search -> page key
        search = requests.get(
            f"{base}/w/rest.php/v1/search/title",
            params={"q": query, "limit": 1},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        search.raise_for_status()
        pages = (search.json() or {}).get("pages") or []
        if not pages or not pages[0].get("key"):
            return {"tool": "wiki", "query": query, "lang": lang, "items": []}
        key = pages[0]["key"]

        # 2. Page summary -> extract + canonical URL
        summary = requests.get(
            f"{base}/api/rest_v1/page/summary/{quote(key, safe='')}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        summary.raise_for_status()
        data = summary.json() or {}
        url = (
            ((data.get("content_urls") or {}).get("desktop") or {}).get("page")
            or f"{base}/wiki/{quote(key)}"
        )
        item = {
            "title": data.get("title") or pages[0].get("title") or key,
            "summary": data.get("extract") or "",
            "url": url,
        }
        return {"tool": "wiki", "query": query, "lang": lang, "items": [item]}
    except Exception as exc:
        return err("wiki", exc)
