"""Eval dashboard data for the Streamlit UI (app.py).

Reads artifacts/version_log.csv and runs/*.json, and lists the prompt/tools
snapshots in artifacts/versions/<version>/ so the UI can chat with any version.
Pure functions here (no streamlit import) so they can be unit tested.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
VERSIONS_DIR = ARTIFACTS_DIR / "versions"
RUNS_DIR = ROOT / "runs"
VERSION_LOG = ARTIFACTS_DIR / "version_log.csv"

METRICS = ["case_accuracy", "tool_routing_accuracy", "argument_accuracy", "multiturn_accuracy"]
METRIC_LABELS = {
    "case_accuracy": "Case",
    "tool_routing_accuracy": "Routing",
    "argument_accuracy": "Args",
    "multiturn_accuracy": "Multi-turn",
}

# Short label, one-line summary and chips per version for the UI timeline and
# "What changed" panel. The full reason/hypothesis comes from version_log.csv.
VERSION_NOTES: dict[str, dict[str, Any]] = {
    "v0": {"name": "Baseline", "summary": "Prompt và tools của starter, chưa sửa gì.",
           "chips": ["starter prompt", "starter tools.yaml"]},
    "v1": {"name": "Prompt rules", "summary": "Viết lại system prompt: hỏi lại thay vì đoán, xác nhận trước khi gửi, giữ phạm vi.",
           "chips": ["system_prompt.md", "clarify thay vì đoán", "send cần yes_no", "ngoài phạm vi: không tool"]},
    "v2": {"name": "Tool docs", "summary": "Viết lại mô tả mọi tool và quy ước args; khai báo 4 tool mới.",
           "chips": ["tools.yaml", "topic=news", "query chỉ là chủ đề", "+ wiki · github_repo · hn_search · citations"]},
    "v3": {"name": "Follow the user", "summary": "Làm theo câu chữ của user: đăng/gửi luôn hỏi yes/no, bỏ nguồn thì không quay lại.",
           "chips": ["system_prompt.md", "đăng/gửi → yes_no", "bỏ Twitter là bỏ"]},
    "v4": {"name": "Scope guard", "summary": "Từ chối nhất quán mọi câu ngoài phạm vi bằng một câu mẫu.",
           "chips": ["system_prompt.md", "kể cả 2+2, 1/0", "1 câu trả lời mẫu"]},
    "v5": {"name": "HN sort scope", "summary": "sort=recent chỉ khi hỏi bài HN mới nhất; sửa bug search_by_date.",
           "chips": ["tools.yaml", "hn_search.sort", "+ fix tool code"]},
}


def version_note(version: str) -> dict[str, Any]:
    note = VERSION_NOTES.get(version)
    if note:
        return note
    return {"name": version, "summary": "", "chips": []}


# Prompts that behave differently across versions. `case` links to the eval case
# whose real tool calls per version are shown next to the prompt.
COMPARE_PROMPTS: list[dict[str, Any]] = [
    {
        "case": "R08_out_of_scope",
        "turns": ["Giải giúp mình bài toán tích phân: nguyên hàm của x^2 là gì?"],
        "watch": "Ngoài phạm vi. v0 dùng `send` (Telegram) để trả lời; từ v1 không gọi tool. v4 luôn từ chối bằng cùng một câu (v3 đôi khi vẫn giải). Thử thêm '1 chia 0 bằng mấy?' hoặc 'giải phương trình x^2 = -1' trên v3 và v4.",
    },
    {
        "case": "R10_missing_handle",
        "turns": ["Tóm tắt 5 tweet mới nhất giúp mình"],
        "watch": "Thiếu tên account. v0 tự đoán `sama`; từ v1 gọi `clarify` hỏi lại.",
    },
    {
        "case": "R11_missing_url",
        "turns": ["Tóm tắt bài viết này hộ mình"],
        "watch": "Thiếu URL. v0 bịa `https://example.com/article`; từ v1 gọi `clarify` xin link.",
    },
    {
        "case": "R12_confirm_before_send",
        "turns": ["Đăng bản tin này lên Telegram giúp mình"],
        "watch": "v0 gửi luôn; v1, v2 hỏi nội dung (`response_type=text`); chỉ v3 hỏi xác nhận `yes_no`.",
    },
    {
        "case": "R13_parallel_web_and_tweets",
        "turns": ["Tìm trên web tin AI hôm nay và tìm thêm tweet về AI."],
        "watch": "v0 `query='AI news'`; v1 thiếu `topic=news`; từ v2 đúng `lookup(query='AI', topic='news')` + `social_search`.",
    },
    {
        "case": "M06_switch_tool",
        "turns": [
            "Mọi người nói gì về OpenAI trên Twitter?",
            "Bỏ Twitter, chuyển sang tìm trên web tin tức đi",
            "Giữ chủ đề OpenAI",
        ],
        "watch": "Hội thoại 3 lượt, gõ lần lượt. v1 quay lại Twitter, v2 gọi cả web lẫn Twitter; v3 chỉ gọi `lookup`.",
    },
    {
        "case": "G04_citations_by_title",
        "turns": ["Bài báo Attention Is All You Need có bao nhiêu lượt trích dẫn?"],
        "watch": "Tool mới `citations` (chỉ có từ v2). v2, v3 truyền arXiv id `1706.03762` thay vì tên: đúng paper, grader chấm fail. v4 pass nhưng chạy lại chỉ 2/3.",
    },
]


def available_versions() -> list[str]:
    """Versions that have a prompt/tools snapshot, oldest first."""
    if not VERSIONS_DIR.is_dir():
        return []
    found = [p.name for p in VERSIONS_DIR.iterdir()
             if (p / "system_prompt.md").is_file() and (p / "tools.yaml").is_file()]
    return sorted(found, key=_version_key)


def version_paths(version: str) -> tuple[Path, Path]:
    folder = VERSIONS_DIR / version
    return folder / "system_prompt.md", folder / "tools.yaml"


def _version_key(version: str) -> tuple[int, str]:
    digits = "".join(ch for ch in version.lstrip("v") if ch.isdigit())
    return (int(digits) if digits else 10**6, version)


def load_version_log(path: Path = VERSION_LOG) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_runs(runs_dir: Path = RUNS_DIR) -> dict[tuple[str, str], dict[str, Any]]:
    """Latest run per (version, suite). Unreadable files are skipped."""
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or "summary" not in data:
            continue
        key = (str(data.get("version")), str(data.get("suite")))
        data["_file"] = f"runs/{path.name}"
        if key not in latest or str(data.get("generated_at", "")) >= str(latest[key].get("generated_at", "")):
            latest[key] = data
    return latest


def summary_rows(runs: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per (version, suite) with the four accuracy metrics."""
    rows = []
    for (version, suite), run in sorted(runs.items(), key=lambda kv: (_version_key(kv[0][0]), kv[0][1])):
        s = run["summary"]
        row = {
            "Version": version,
            "Suite": suite,
            "Pass": f"{s.get('passed_cases', 0)}/{s.get('total_cases', 0)}",
        }
        for metric in METRICS:
            row[METRIC_LABELS[metric]] = s.get(metric)
        row["Model"] = run.get("model") or ""
        row["Run file"] = run["_file"]
        rows.append(row)
    return rows


def case_matrix(runs: dict[tuple[str, str], dict[str, Any]], suite: str, *, only_changed: bool) -> list[dict[str, str]]:
    """Rows = cases, columns = versions, cells = ✅ / ❌ / — (not run)."""
    versions = sorted({v for (v, s) in runs if s == suite}, key=_version_key)
    status: dict[str, dict[str, str]] = {}
    for version in versions:
        for result in runs[(version, suite)].get("results", []):
            passed = bool(result.get("result", {}).get("passed"))
            status.setdefault(result["id"], {})[version] = "✅" if passed else "❌"
    rows = []
    for case_id, cells in status.items():
        values = [cells.get(v, "—") for v in versions]
        if only_changed and all(v == "✅" for v in values):
            continue
        rows.append({"Case": case_id, **dict(zip(versions, values))})
    return rows


def case_calls(runs: dict[tuple[str, str], dict[str, Any]], case_id: str) -> list[dict[str, str]]:
    """What each version actually called for one case (from run JSON)."""
    rows = []
    for (version, _suite), run in sorted(runs.items(), key=lambda kv: _version_key(kv[0][0])):
        for result in run.get("results", []):
            if result.get("id") != case_id:
                continue
            res = result.get("result", {})
            calls = res.get("actual_tool_calls") or []
            if calls:
                shown = "; ".join(f"{c['name']}({_fmt_args(c.get('args') or {})})" for c in calls)
            else:
                shown = "(không gọi tool, trả lời bằng text)"
            rows.append({
                "Version": version,
                "Kết quả": "✅ pass" if res.get("passed") else "❌ fail",
                "Tool calls thật": shown,
                "Lỗi": "; ".join(res.get("failures") or []),
            })
    return rows


def _fmt_args(args: dict[str, Any], max_len: int = 60) -> str:
    parts = []
    for key, value in args.items():
        text = json.dumps(value, ensure_ascii=False)
        if len(text) > max_len:
            text = text[: max_len - 3] + "..."
        parts.append(f"{key}={text}")
    return ", ".join(parts)
