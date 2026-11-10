from __future__ import annotations

from typing import Any

from tools._shared import err


# Owner: TV4. Skeleton only: keep the function name and parameter names,
# they must match artifacts/tools.yaml (checked by tests/test_tool_contract.py).
#
# TODO(TV4):
#   1. limit = max(1, min(int(limit or 5), 10)); sort not in {"popular", "recent"} -> "popular"
#   2. endpoint = "search_by_date" if sort == "recent" else "search"
#   3. GET https://hn.algolia.com/api/v1/<endpoint>?query=<query>&tags=story&hitsPerPage=<limit>
#   4. Map hits -> title, url, points, num_comments, created_at,
#                  hn_url = https://news.ycombinator.com/item?id=<objectID>
#   5. return {"tool": "hn_search", "query": query, "sort": sort, "items": [...]}
def hn_search(query: str = "", sort: str = "popular", limit: int = 5) -> dict[str, Any]:
    return err("hn_search", NotImplementedError("hn_search is not implemented yet"))
