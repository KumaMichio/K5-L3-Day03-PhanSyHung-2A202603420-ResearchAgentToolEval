from __future__ import annotations

import re
from typing import Any
import requests

from tools._shared import TIMEOUT, err

BASE = "https://api.openalex.org/works"


def citations(paper: str = "") -> dict[str, Any]:
    """Tra cứu số trích dẫn và nơi công bố của một bài báo khoa học qua OpenAlex API.

    Dùng khi: Hỏi paper cụ thể được trích dẫn bao nhiêu, đăng ở đâu.
    Không dùng khi: Tìm paper theo chủ đề (dùng papers).
    """
    try:
        paper_clean = (paper or "").strip()
        if not paper_clean:
            raise ValueError("paper is required")

        m = re.search(r"\d{4}\.\d{4,5}", paper_clean)
        if m:
            doi_endpoint = f"{BASE}/doi:10.48550/arXiv.{m.group(0)}"
            params = {"mailto": "research-agent-lab@example.com"}
            response = requests.get(doi_endpoint, params=params, timeout=TIMEOUT)
            if response.status_code == 404:
                return {"tool": "citations", "paper": paper_clean, "items": []}
            response.raise_for_status()
            work = response.json()
        else:
            params = {
                "search": paper_clean,
                "per-page": 1,
                "mailto": "research-agent-lab@example.com",
            }
            response = requests.get(BASE, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            work = results[0] if results else None

        items = []
        if work and isinstance(work, dict):
            primary_loc = work.get("primary_location") or {}
            source = primary_loc.get("source") or {}
            venue = source.get("display_name")
            items.append({
                "title": work.get("title") or "",
                "cited_by_count": work.get("cited_by_count", 0),
                "publication_year": work.get("publication_year"),
                "venue": venue,
                "url": work.get("doi") or work.get("id"),
            })

        return {"tool": "citations", "paper": paper_clean, "items": items}
    except Exception as exc:
        return err("citations", exc)

