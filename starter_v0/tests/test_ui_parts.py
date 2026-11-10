"""Tests for ui_parts.py (HTML/SVG snippets used by the Streamlit UI)."""
from __future__ import annotations

import ui_parts as ui


def test_delta_badge_direction_and_flat() -> None:
    assert 'class="badge up"' in ui.delta_badge(0.9, 0.65) and "+25.0 pts" in ui.delta_badge(0.9, 0.65)
    assert 'class="badge down"' in ui.delta_badge(0.6, 0.7)
    assert "= 0 pts" in ui.delta_badge(1.0, 1.0)
    assert "—" in ui.delta_badge(None, 0.5)


def test_collect_sources_dedupes_and_reads_nested_tool_results() -> None:
    item = {"title": "Rust 1.0", "url": "https://www.rust-lang.org/a", "points": 10, "num_comments": 2}
    turns = [{"rounds": [{"tool_results": [
        {"tool": "hn_search", "result": {"items": [item, dict(item)]}},
        {"tool": "lookup", "result": {"error": "x"}},
    ]}]}]
    sources = ui.collect_sources(turns)
    assert len(sources) == 1
    assert sources[0]["domain"] == "rust-lang.org"
    assert sources[0]["snippet"] == "10 điểm · 2 bình luận"


def test_html_escapes_user_text() -> None:
    out = ui.thread_head_html("<script>x</script>", 1, 0)
    assert "<script>" not in out and "&lt;script&gt;" in out
    src = ui.sources_html([{"title": "<b>t</b>", "url": "", "domain": "d", "snippet": "", "tool": "t"}])
    assert "<b>t</b>" not in src


def test_trend_svg_skips_missing_points_and_draws_one_marker_per_value() -> None:
    svg = ui.trend_svg([("v0", 0.65), ("v1", None), ("v2", 1.0)], start="v0", end="v2")
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert svg.count("<title>") == 2
    assert "v0: 65.0%" in svg and "v2: 100.0%" in svg


def test_timeline_marks_selected_endpoints() -> None:
    versions = [{"version": f"v{i}", "name": f"n{i}", "when": ""} for i in range(4)]
    out = ui.timeline_html(versions, "v1", "v3")
    assert out.count('class="tl on"') == 2


def test_matrix_html_maps_marks() -> None:
    out = ui.matrix_html([{"Case": "R08", "v0": "❌", "v1": "✅", "v2": "—"}])
    assert 'class="ko"' in out and 'class="ok"' in out and 'class="na"' in out
