"""Tests for eval_dashboard.py (version snapshots + run summaries shown in the UI)."""
from __future__ import annotations

import json
from pathlib import Path

import eval_dashboard as ed
from versioning import build_artifact_version


def _run(version: str, suite: str, results: list[tuple[str, bool]], generated_at: str) -> dict:
    passed = sum(ok for _, ok in results)
    return {
        "version": version,
        "suite": suite,
        "model": "fake",
        "generated_at": generated_at,
        "summary": {"passed_cases": passed, "total_cases": len(results), "case_accuracy": passed / len(results)},
        "results": [
            {"id": cid, "result": {"passed": ok, "actual_tool_calls": [{"name": "lookup", "args": {"query": "AI"}}],
                                   "failures": [] if ok else ["boom"]}}
            for cid, ok in results
        ],
    }


def _write_runs(tmp_path: Path, runs: dict[str, dict]) -> Path:
    for name, data in runs.items():
        (tmp_path / name).write_text(json.dumps(data), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    return tmp_path


def test_snapshot_hashes_match_version_log() -> None:
    """Each artifacts/versions/<v>/ snapshot must reproduce the hash logged for <v>."""
    log = {row["version"]: row for row in ed.load_version_log()}
    versions = ed.available_versions()
    assert versions, "no snapshots in artifacts/versions/"
    for version in versions:
        prompt, tools = ed.version_paths(version)
        built = build_artifact_version(version, prompt, tools)
        assert built.artifact_version == log[version]["artifact_version"], version


def test_load_runs_keeps_latest_per_version_and_skips_broken(tmp_path: Path) -> None:
    runs_dir = _write_runs(tmp_path, {
        "v1_old.json": _run("v1", "base", [("A", False)], "2026-01-01"),
        "v1_new.json": _run("v1", "base", [("A", True)], "2026-01-02"),
        "v2.json": _run("v2", "base", [("A", True)], "2026-01-03"),
    })
    runs = ed.load_runs(runs_dir)
    assert set(runs) == {("v1", "base"), ("v2", "base")}
    assert runs[("v1", "base")]["_file"] == "runs/v1_new.json"


def test_summary_rows_sorted_by_version_number(tmp_path: Path) -> None:
    runs_dir = _write_runs(tmp_path, {
        "a.json": _run("v10", "base", [("A", True)], "1"),
        "b.json": _run("v2", "base", [("A", False)], "1"),
    })
    rows = ed.summary_rows(ed.load_runs(runs_dir))
    assert [r["Version"] for r in rows] == ["v2", "v10"]
    assert rows[0]["Pass"] == "0/1" and rows[0]["Case"] == 0.0


def test_case_matrix_only_changed_hides_always_passing(tmp_path: Path) -> None:
    runs_dir = _write_runs(tmp_path, {
        "v0.json": _run("v0", "base", [("A", True), ("B", False)], "1"),
        "v1.json": _run("v1", "base", [("A", True), ("B", True)], "1"),
    })
    runs = ed.load_runs(runs_dir)
    assert ed.case_matrix(runs, "base", only_changed=True) == [{"Case": "B", "v0": "❌", "v1": "✅"}]
    assert len(ed.case_matrix(runs, "base", only_changed=False)) == 2


def test_case_calls_shows_real_calls_per_version(tmp_path: Path) -> None:
    runs_dir = _write_runs(tmp_path, {"v0.json": _run("v0", "base", [("B", False)], "1")})
    rows = ed.case_calls(ed.load_runs(runs_dir), "B")
    assert rows == [{"Version": "v0", "Kết quả": "❌ fail", "Tool calls thật": 'lookup(query="AI")', "Lỗi": "boom"}]


def test_compare_prompts_point_at_real_cases() -> None:
    runs = ed.load_runs()
    known = {r["id"] for run in runs.values() for r in run.get("results", [])}
    for item in ed.COMPARE_PROMPTS:
        assert item["case"] in known, item["case"]
