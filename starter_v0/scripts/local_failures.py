"""Summarize run JSON files for the Small Local Model Challenge (REPORT B7).

Counts the small-model failure patterns from README Step 7:
  - hallucinated tool (name not declared in the run's tools.yaml)
  - invalid JSON args (args contain `_invalid_json_arguments`)
  - no tool call when the case expected one (answered in text)
  - missed clarify (expected clarify, called something else / nothing)
  - repeated / unnecessary calls (more calls than expected, or same tool twice)
  - tool call when no tool was expected

Usage: python scripts/local_failures.py runs/local/*.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def declared_tools(run: dict) -> set[str]:
    tools = run.get("tools")
    if isinstance(tools, list):
        return {t.get("name") or t.get("function", {}).get("name") for t in tools}
    path = Path(str(tools or ""))
    if path.exists():
        import yaml

        return {t["name"] for t in yaml.safe_load(path.read_text(encoding="utf-8"))["tools"]}
    return set()


def classify(run: dict) -> tuple[Counter, dict[str, list[str]]]:
    names = declared_tools(run)
    counts: Counter = Counter()
    examples: dict[str, list[str]] = {}

    def hit(key: str, case_id: str) -> None:
        counts[key] += 1
        examples.setdefault(key, []).append(case_id)

    for r in run["results"]:
        cid = r["id"]
        res = r["result"]
        expect = r["expect"]
        calls = res.get("actual_tool_calls") or []
        exp_calls = expect.get("tool_calls") or []
        exp_names = [c["name"] for c in exp_calls]
        if res.get("passed"):
            continue
        if res.get("failure_type") == "provider_error":
            hit("provider_error", cid)
            continue
        if names and any(c.get("name") not in names for c in calls):
            hit("hallucinated_tool", cid)
        if any("_invalid_json_arguments" in (c.get("args") or {}) for c in calls):
            hit("invalid_json_args", cid)
        if expect.get("no_tool"):
            if calls:
                hit("tool_when_no_tool_expected", cid)
            continue
        if not calls:
            hit("no_tool_call", cid)
        if "clarify" in exp_names and "clarify" not in [c.get("name") for c in calls]:
            hit("missed_clarify", cid)
        called = [c.get("name") for c in calls]
        if len(calls) > len(exp_calls) or len(set(called)) < len(called):
            hit("repeated_or_extra_calls", cid)
        if calls and not res.get("routing_correct") and "clarify" not in exp_names:
            hit("wrong_tool", cid)
        elif calls and res.get("routing_correct") and not res.get("args_correct"):
            hit("wrong_args", cid)
    return counts, examples


def main(paths: list[str]) -> None:
    for p in paths:
        run = json.loads(Path(p).read_text(encoding="utf-8"))
        s = run["summary"]
        print(f"\n== {p}")
        print(
            f"version={run['version']} model={run['model']} artifact={run['artifact_version']}\n"
            f"case={s['case_accuracy']} routing={s['tool_routing_accuracy']} "
            f"args={s['argument_accuracy']} multiturn={s['multiturn_accuracy']} "
            f"provider_errors={s['provider_error_cases']}"
        )
        counts, examples = classify(run)
        for k, v in counts.most_common():
            print(f"  {k}: {v}  {examples[k]}")
        for r in run["results"]:
            if not r["result"].get("passed"):
                calls = [(c.get("name"), c.get("args")) for c in r["result"].get("actual_tool_calls") or []]
                text = (r["result"].get("actual_text") or "")[:80].replace("\n", " ")
                print(f"    FAIL {r['id']}: {calls} {text!r}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
