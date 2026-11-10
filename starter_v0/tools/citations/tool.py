from __future__ import annotations

import re
from typing import Any
import requests

from tools._shared import TIMEOUT, err

BASE = "https://api.openalex.org/works"


def citations(paper: str = "") -> dict[str, Any]:
    try:
        paper = (paper or "").strip()
        if not paper:
            raise ValueError("paper is required")
        m = re.search(r"\d{4}\.\d{4,5}", paper)
        headers = {"User-Agent": "Day03-Research-Agent/1.0 (mailto:lab@example.com)"}
        if m:
            resp = requests.get(f"{BASE}/doi:10.48550/arXiv.{m.group(0)}", headers=headers, timeout=TIMEOUT)
        else:
            resp = requests.get(BASE, params={"search": paper, "per-page": 1, "mailto": "lab@example.com"}, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        work = data.get("results", [{}])[0] if "results" in data else data
        if not work or not work.get("id"):
            return {"tool": "citations", "paper": paper, "items": []}
        primary_loc = work.get("primary_location") or {}
        source = (primary_loc.get("source") or {}).get("display_name") or ""
        return {
            "tool": "citations",
            "paper": paper,
            "items": [
                {
                    "title": work.get("title") or paper,
                    "cited_by_count": work.get("cited_by_count", 0),
                    "publication_year": work.get("publication_year"),
                    "venue": source,
                    "url": work.get("id") or "",
                }
            ],
        }
    except Exception as exc:
        return err("citations", exc)

