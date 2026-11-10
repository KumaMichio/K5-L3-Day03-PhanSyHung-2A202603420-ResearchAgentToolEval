from __future__ import annotations

from typing import Any

from tools._shared import err


# Owner: TV3. Skeleton only: keep the function name and parameter names,
# they must match artifacts/tools.yaml (checked by tests/test_tool_contract.py).
#
# TODO(TV3):
#   1. Normalize `repo`: accept "owner/name" or a full https://github.com/owner/name URL
#   2. GET https://api.github.com/repos/<owner>/<name>                 (404 -> error dict)
#   3. GET https://api.github.com/repos/<owner>/<name>/releases/latest (404 -> latest_release None)
#   4. If GITHUB_TOKEN is set, send "Authorization: Bearer <token>" (60 req/h per IP without it)
#   5. return {"tool": "github_repo", "repo": slug, "stars", "forks", "description",
#              "last_push", "latest_release", "url"}
def github_repo(repo: str = "") -> dict[str, Any]:
    return err("github_repo", NotImplementedError("github_repo is not implemented yet"))
