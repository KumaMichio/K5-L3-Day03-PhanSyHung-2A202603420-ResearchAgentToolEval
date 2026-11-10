from __future__ import annotations

from typing import Any
import requests

from tools._shared import TIMEOUT, err

BASE = "https://hn.algolia.com/api/v1"


def hn_search(query: str = "", sort: str = "popular", limit: int = 5) -> dict[str, Any]:
    try:
        limit = max(1, min(int(limit or 5), 10))
        endpoint = "search_by_date" if sort == "recent" else "search"
        params = {"query": query, "tags": "story", "hitsPerPage": limit}
        resp = requests.get(f"{BASE}/{endpoint}", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        items = []
        for hit in hits:
            obj_id = hit.get("objectID") or ""
            items.append({
                "title": hit.get("title") or "",
                "url": hit.get("url") or (f"https://news.ycombinator.com/item?id={obj_id}" if obj_id else ""),
                "points": hit.get("points") or 0,
                "num_comments": hit.get("num_comments") or 0,
                "hn_url": f"https://news.ycombinator.com/item?id={obj_id}" if obj_id else "",
                "created_at": hit.get("created_at") or "",
            })
        return {"tool": "hn_search", "query": query, "sort": sort, "items": items}
    except Exception as exc:
        return err("hn_search", exc)

