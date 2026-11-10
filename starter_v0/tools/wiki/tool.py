from __future__ import annotations

import os
from typing import Any
import requests

from tools._shared import TIMEOUT, err

UA = {"User-Agent": "Day03-Research-Agent/1.0 (educational lab)"}


def wiki_search(query: str = "", lang: str = "en") -> dict[str, Any]:
    try:
        query = (query or "").strip()
        if not query:
            return {"tool": "wiki", "query": query, "items": []}
        lang = lang if lang in {"en", "vi"} else "en"
        # 1. Search title to get page key
        search_url = f"https://{lang}.wikipedia.org/w/rest.php/v1/search/title"
        resp = requests.get(search_url, params={"q": query, "limit": 1}, headers=UA, timeout=TIMEOUT)
        resp.raise_for_status()
        pages = resp.json().get("pages", [])
        if not pages:
            return {"tool": "wiki", "query": query, "items": []}
        key = pages[0].get("key")
        # 2. Get summary
        summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{key}"
        s_resp = requests.get(summary_url, headers=UA, timeout=TIMEOUT)
        s_resp.raise_for_status()
        data = s_resp.json()
        title = data.get("title") or key
        extract = data.get("extract") or ""
        page_url = (data.get("content_urls", {}).get("desktop", {}) or {}).get("page", "")
        return {
            "tool": "wiki",
            "query": query,
            "items": [
                {
                    "title": title,
                    "summary": extract,
                    "url": page_url,
                    "source": f"{lang}.wikipedia.org",
                }
            ],
        }
    except Exception as exc:
        return err("wiki", exc)

