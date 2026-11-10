from __future__ import annotations

from typing import Any

from tools._shared import err


# Owner: TV3. Skeleton only: keep the function name and parameter names,
# they must match artifacts/tools.yaml (checked by tests/test_tool_contract.py).
#
# TODO(TV3):
#   1. lang = lang if lang in {"en", "vi"} else "en"
#   2. GET https://{lang}.wikipedia.org/w/rest.php/v1/search/title?q=<query>&limit=1  -> page key
#   3. GET https://{lang}.wikipedia.org/api/rest_v1/page/summary/<key>              -> extract, content_urls.desktop.page
#   4. Send a User-Agent header; use requests.get(..., timeout=TIMEOUT)
#   5. return {"tool": "wiki", "query": query, "lang": lang, "items": [{"title", "summary", "url"}]}
def wiki_search(query: str = "", lang: str = "en") -> dict[str, Any]:
    return err("wiki", NotImplementedError("wiki is not implemented yet"))
