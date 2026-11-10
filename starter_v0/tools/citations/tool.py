from __future__ import annotations

from typing import Any

from tools._shared import err


# Owner: TV4. Skeleton only: keep the function name and parameter names,
# they must match artifacts/tools.yaml (checked by tests/test_tool_contract.py).
#
# TODO(TV4):
#   1. paper = paper.strip(); empty -> error dict without any network call
#   2. arXiv id (\d{4}\.\d{4,5}) -> GET https://api.openalex.org/works/doi:10.48550/arXiv.<id>
#      otherwise                 -> GET https://api.openalex.org/works?search=<paper>&per-page=1
#   3. Add params["mailto"] for OpenAlex's polite pool
#   4. Map -> title, cited_by_count, publication_year,
#             venue = primary_location.source.display_name, url = id
#   5. return {"tool": "citations", "paper": paper, "items": [...]}
def citations(paper: str = "") -> dict[str, Any]:
    return err("citations", NotImplementedError("citations is not implemented yet"))
