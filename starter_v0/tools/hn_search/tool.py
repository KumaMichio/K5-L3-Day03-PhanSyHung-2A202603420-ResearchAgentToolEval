from __future__ import annotations

from typing import Any
import requests

from tools._shared import TIMEOUT, err

BASE = "https://hn.algolia.com/api/v1"


def hn_search(query: str = "", sort: str = "popular", limit: int = 5) -> dict[str, Any]:
    """Tìm thảo luận trên Hacker News qua Algolia API.

    Dùng khi: Hỏi dân dev, cộng đồng tech, Hacker News bàn gì.
    Không dùng khi: Hỏi bài đăng trên X/Twitter (dùng social_search).
    """
    try:
        try:
            limit_int = 5 if limit is None or limit == "" else int(limit)
        except (ValueError, TypeError):
            limit_int = 5
        limit_val = max(1, min(limit_int, 10))
        endpoint = "search_by_date" if sort == "recent" else "search"
        params = {"query": query, "tags": "story", "hitsPerPage": limit_val}
        response = requests.get(f"{BASE}/{endpoint}", params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        items = []
        for hit in data.get("hits", []):
            object_id = str(hit.get("objectID") or "")
            hn_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else None
            items.append({
                "title": hit.get("title") or hit.get("story_title") or "",
                "url": hit.get("url") or hn_url,
                "points": hit.get("points"),
                "num_comments": hit.get("num_comments"),
                "hn_url": hn_url,
                "created_at": hit.get("created_at"),
            })
        return {"tool": "hn_search", "query": query, "sort": sort, "items": items}
    except Exception as exc:
        return err("hn_search", exc)
