"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py

The UI reuses the exact multi-round tool loop from chat.py (run_model_tool_loop),
so the agent behaves the same as the CLI. It does not depend on the prompt
content: it reads artifacts/system_prompt.md + artifacts/tools.yaml at the start
of each conversation, so whatever version TV1 merges is what the UI runs.

Every turn is written to transcripts/<version>_<provider>_<timestamp>.transcript.json
with the same schema as chat.py (plus "interface": "streamlit").
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from eval_dashboard import (
    COMPARE_PROMPTS,
    available_versions,
    case_calls,
    case_matrix,
    load_runs,
    load_version_log,
    version_note,
    version_paths,
)
import ui_parts as ui

CURRENT = "current (artifacts/)"
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = Path(os.getenv("AGENT_TRANSCRIPTS_DIR") or ROOT / "transcripts")

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
PROVIDER_KEY_ENV = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "ollama": None,
}
TOOL_KEY_ENV = {
    "lookup": "TAVILY_API_KEY",
    "fetch": "FIRECRAWL_API_KEY",
    "timeline / social_search": "RAPIDAPI_KEY",
    "send": "TELEGRAM_BOT_TOKEN",
}
SAMPLE_QUESTIONS = [
    "Tweet mới nhất của Sam Altman là gì?",
    "Mọi người đang bàn gì về GPT-5 trên Twitter?",
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tóm tắt giúp mình bài này",
    "Tìm vài paper mới về AI agent evaluation",
    "Dân Hacker News đang bàn gì về Rust?",
    "Paper 2106.09685 được cite bao nhiêu lần?",
    "Repo langchain-ai/langgraph có bao nhiêu sao?",
    "Đăng bản tin AI hôm nay lên Telegram",
]
RESULT_PREVIEW_CHARS = 6000


# ---------------------------------------------------------------- helpers

def env_status(name: str | None) -> str:
    if name is None:
        return "không cần key"
    return "✅ đã có" if os.getenv(name) else "❌ thiếu"


def display_path(path: Path) -> str:
    path = Path(path)
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def json_preview(value: Any, max_chars: int = RESULT_PREVIEW_CHARS) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) > max_chars:
        return text[:max_chars] + "\n...<truncated>"
    return text


def format_args(args: dict[str, Any]) -> str:
    return ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in args.items())


def result_badge(result: Any) -> str:
    if isinstance(result, dict):
        if result.get("error"):
            return "⚠️ lỗi"
        if result.get("awaiting_user"):
            return "❓ chờ người dùng"
        items = result.get("items")
        if isinstance(items, list):
            return f"✅ {len(items)} item"
    return "✅ xong"


def new_session(config: dict[str, Any]) -> None:
    """Start a fresh conversation: reload prompt/tools and open a new transcript."""
    system_prompt_path = Path(config["system_prompt"])
    tools_path = Path(config["tools"])
    artifact_version = build_artifact_version(config["version"], system_prompt_path, tools_path)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(config["version"]), safe_slug(config["provider"]), timestamp])

    st.session_state.update({
        "config": dict(config),
        "system_prompt_text": system_prompt_path.read_text(encoding="utf-8"),
        "openai_tools": to_openai_tools(load_tool_declarations(tools_path)),
        "artifact_version": artifact_version,
        "history": [],
        "turns": [],
        "pending": None,
        "transcript_path": TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json",
        "transcript": {
            "transcript_id": transcript_id,
            **artifact_version_dict(artifact_version),
            "interface": "streamlit",
            "provider": config["provider"],
            "model": config["model"] or None,
            "system_prompt": display_path(system_prompt_path),
            "tools": display_path(tools_path),
            "history_window": config["history_window"],
            "max_tool_rounds": config["max_tool_rounds"],
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        },
    })


def run_turn(user_text: str) -> None:
    """One user turn: same message building + tool loop + transcript as chat.py."""
    config = st.session_state.config
    turn_record: dict[str, Any] = {
        "turn_index": len(st.session_state.turns) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    messages = [
        {"role": "system", "content": st.session_state.system_prompt_text},
        *trim_history(st.session_state.history, config["history_window"]),
        {"role": "user", "content": user_text},
    ]
    try:
        provider = make_provider(config["provider"])
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=st.session_state.openai_tools,
            model=config["model"] or None,
            max_tool_rounds=config["max_tool_rounds"],
        )
        turn_record.update(result)
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
    except Exception as exc:  # provider/network errors are shown, not raised
        turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})

    turn_record["ended_at"] = now_iso()
    st.session_state.turns.append(turn_record)
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)


# ---------------------------------------------------------------- rendering

def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def render_tool_event(event: dict[str, Any]) -> None:
    result = event.get("result")
    st.markdown(f"**`{event.get('tool')}`**({format_args(event.get('args') or {})}) · {result_badge(result)}")
    if isinstance(result, dict) and isinstance(result.get("markdown"), str):
        with st.container(border=True):
            st.markdown(result["markdown"])
    elif isinstance(result, dict) and isinstance(result.get("items"), list) and result["items"]:
        for item in result["items"][:10]:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("url") or "(không có tiêu đề)"
            url = item.get("url")
            line = f"- [{title}]({url})" if url else f"- {title}"
            if item.get("source"):
                line += f" · _{item['source']}_"
            st.markdown(line)
    with st.popover("JSON kết quả", use_container_width=False):
        st.code(json_preview(result), language="json")


def render_turn(turn: dict[str, Any], *, is_last: bool) -> None:
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(turn["user"])
    with st.chat_message("assistant", avatar=":material/auto_awesome:"):
        rounds = turn.get("rounds") or []
        n_calls = sum(len(r.get("tool_calls") or []) for r in rounds)
        if n_calls:
            label = f"Đã nghiên cứu · {n_calls} tool · {len(rounds)} vòng"
            with st.expander(label, expanded=False, icon=":material/radio_button_checked:"):
                for rnd in rounds:
                    st.caption(f"Vòng {rnd['round']}")
                    if rnd.get("assistant_text"):
                        st.markdown(f"> {rnd['assistant_text']}")
                    if not rnd.get("tool_calls"):
                        st.markdown("_Không gọi tool, trả lời trực tiếp._")
                    for event in rnd.get("tool_results") or []:
                        render_tool_event(event)
        else:
            st.caption("Trả lời trực tiếp, không gọi tool")

        status = turn.get("status")
        if status == "provider_error":
            st.error(f"Lỗi provider: {turn.get('error')}")
            return
        if status == "waiting_for_user":
            st.info("Agent đang hỏi lại bạn:")
        elif status == "max_tool_rounds":
            st.warning("Agent dừng vì chạm giới hạn số vòng tool.")
        st.markdown(turn.get("assistant_text") or "_(trống)_")

        # Quick-reply buttons when clarify asks a yes/no or choice question.
        if is_last and status == "waiting_for_user":
            last_result = (turn.get("tool_events") or [{}])[-1].get("result") or {}
            options = list(last_result.get("options") or [])
            if not options and last_result.get("response_type") == "yes_no":
                options = ["Có", "Không"]
            if options:
                cols = st.columns(min(len(options), 4))
                for i, option in enumerate(options):
                    if cols[i % len(cols)].button(str(option), key=f"opt_{turn['turn_index']}_{i}"):
                        st.session_state.pending = str(option)
                        st.rerun()


# ---------------------------------------------------------------- config + sidebar

def version_choices() -> list[str]:
    return [*available_versions(), CURRENT]


def version_label(choice: str) -> str:
    if choice == CURRENT:
        return "current · artifacts/"
    return f"{choice} · {version_note(choice)['name']}"


def build_config() -> dict[str, Any]:
    """Read settings from session state. The version is chosen next to the chat
    box, stored in a plain key so it survives pages where that widget is hidden."""
    choices = version_choices()
    st.session_state.setdefault("version_choice", choices[-2] if len(choices) > 1 else CURRENT)
    choice = st.session_state.version_choice
    if choice not in choices:
        choice = st.session_state.version_choice = choices[-1]
    if choice == CURRENT:
        prompt, tools, label = ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml", "current"
    else:
        prompt, tools = version_paths(choice)
        label = choice
    provider = st.session_state.get("provider", PROVIDERS[0])
    return {
        "provider": provider,
        "model": (st.session_state.get("model") or default_model(provider)).strip(),
        "version": label,
        "system_prompt": str(prompt),
        "tools": str(tools),
        "history_window": int(st.session_state.get("history_window", 5)),
        "max_tool_rounds": int(st.session_state.get("max_tool_rounds", 4)),
    }


def default_model(provider: str) -> str:
    # <PROVIDER>_MODEL in .env overrides the code default.
    return os.getenv(f"{provider.upper()}_MODEL") or getattr(make_provider(provider), "default_model", "")


def recent_threads(limit: int = 5) -> list[dict[str, str]]:
    if not TRANSCRIPTS_DIR.is_dir():
        return []
    files = sorted(TRANSCRIPTS_DIR.glob("*.transcript.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    current = st.session_state.get("transcript", {}).get("transcript_id")
    out = []
    for path in files[: limit * 2]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        turns = data.get("turns") or []
        if not turns:
            continue
        tid = data.get("transcript_id") or path.stem
        when = "Now" if tid == current else datetime.fromtimestamp(path.stat().st_mtime).strftime("%b %d · %H:%M")
        out.append({"id": tid, "title": str(turns[0].get("user") or "(trống)"),
                    "when": f"{data.get('artifact_version', '').split('+')[0] or '?'} · {when}"})
        if len(out) >= limit:
            break
    return out


def nav_button(label: str, page: str, icon: str) -> None:
    on = st.session_state.get("page", "chat") == page
    with st.container(key=f"{'navon' if on else 'navoff'}_{page}"):
        if st.button(label, key=f"nav_{page}", icon=icon, use_container_width=True):
            st.session_state.page = page
            st.rerun()


def sidebar(config: dict[str, Any]) -> None:
    with st.sidebar:
        html(ui.brand_html("Research", "Agent"))
        st.write("")
        if st.button("New research", key="new_research", icon=":material/add:", use_container_width=True):
            new_session(config)
            st.session_state.page = "chat"
            st.rerun()
        st.write("")
        nav_button("Research chat", "chat", ":material/chat:")
        nav_button("Version evals", "evals", ":material/science:")

        html('<div class="side-label">RECENT</div>')
        current = st.session_state.get("transcript", {}).get("transcript_id")
        html(ui.recent_html(recent_threads(), current))

        html('<div class="side-label">SETTINGS</div>')
        with st.expander("Provider, model, key", icon=":material/tune:"):
            st.selectbox("Provider", PROVIDERS, key="provider")
            provider = st.session_state.get("provider", PROVIDERS[0])
            st.text_input("Model", key="model", placeholder=default_model(provider),
                          help="Để trống để dùng model mặc định của provider.")
            st.number_input("History window (cặp lượt)", 0, 20, 5, key="history_window")
            st.number_input("Max tool rounds", 1, 10, 4, key="max_tool_rounds")
            st.markdown("**API key**")
            st.markdown(f"- {PROVIDER_KEY_ENV[provider] or provider}: {env_status(PROVIDER_KEY_ENV[provider])}")
            for tool_name, env in TOOL_KEY_ENV.items():
                st.markdown(f"- `{tool_name}`: {env_status(env)}")

        if "artifact_version" in st.session_state:
            with st.expander("Phiên hiện tại", icon=":material/receipt_long:"):
                st.code(st.session_state.artifact_version.artifact_version, language=None)
                st.caption(f"{len(st.session_state.openai_tools)} tool được khai báo")
                st.code(st.session_state.system_prompt_text, language="markdown")
                if st.session_state.transcript_path.exists():
                    st.download_button(
                        "Tải transcript JSON",
                        st.session_state.transcript_path.read_bytes(),
                        file_name=st.session_state.transcript_path.name,
                        mime="application/json",
                        use_container_width=True,
                    )
        cfg = st.session_state.get("config", config)
        choice = st.session_state.get("version_choice", "")
        html(ui.status_html(cfg["version"], version_note(choice)["name"] if choice != CURRENT else "artifacts/"))


# ---------------------------------------------------------------- chat page

def on_version_change() -> None:
    picked = st.session_state.get("version_widget")
    if picked:  # segmented control returns None when the active button is clicked again
        st.session_state.version_choice = picked


def render_version_switch() -> None:
    """One button per version. Switching starts a new conversation (see main)."""
    choices = version_choices()
    current = st.session_state.version_choice
    st.session_state.version_widget = current  # keep the active button in sync
    label_col, buttons_col = st.columns([0.55, 5], vertical_alignment="center")
    label_col.markdown('<div class="eyebrow">Version</div>', unsafe_allow_html=True)
    with buttons_col, st.container(key="version_switch"):
        st.segmented_control(
            "Version", choices, key="version_widget", on_change=on_version_change,
            format_func=lambda c: "current" if c == CURRENT else c,
            label_visibility="collapsed",
        )
    note = version_note(current) if current != CURRENT else {"name": "artifacts/", "summary": "File đang sửa trong artifacts/."}
    st.markdown(
        f'<div class="watch"><b>{ui.esc(note["name"])}</b> · {ui.esc(note["summary"])} '
        f'<span class="meta">· {ui.esc(st.session_state.artifact_version.artifact_version)}</span></div>',
        unsafe_allow_html=True,
    )


def render_try_asking(questions: list[str], key: str) -> None:
    html('<div class="eyebrow" style="margin:22px 0 10px">Try asking</div>')
    with st.container(key=f"try_{key}"):
        for question in questions:
            i = SAMPLE_QUESTIONS.index(question)
            if st.button(question, key=f"sample_{i}"):
                st.session_state.pending = question
                st.rerun()


def render_chat_page() -> None:
    turns = st.session_state.turns
    sources = ui.collect_sources(turns)
    title = turns[0]["user"] if turns else "Nghiên cứu mới"
    html(ui.thread_head_html(title if len(title) <= 70 else title[:67] + "…", len(turns), len(sources)))

    left, right = st.columns([2.2, 1], gap="large")
    with left:
        render_version_switch()
        if not turns:
            st.markdown(
                "Agent tự chọn tool (tìm tin, đọc tweet, đọc URL, tìm paper, tra Hacker News, policy…), "
                "gọi tool thật rồi trả lời. Mở dòng **Đã nghiên cứu** dưới mỗi câu trả lời để xem agent đã gọi gì."
            )
            render_try_asking(SAMPLE_QUESTIONS, "all")
        for i, turn in enumerate(turns):
            render_turn(turn, is_last=i == len(turns) - 1)
        live = st.container()
        if turns and turns[-1].get("status") != "waiting_for_user":
            asked = {t["user"] for t in turns}
            render_try_asking([q for q in SAMPLE_QUESTIONS if q not in asked][:3], "more")

    with right:
        html(ui.sources_html(sources))

    typed = st.chat_input("Hỏi một câu research…")
    user_text = typed or st.session_state.pop("pending", None)
    if user_text:
        with live:
            with st.chat_message("user", avatar=":material/person:"):
                st.markdown(user_text)
            with st.chat_message("assistant", avatar=":material/auto_awesome:"):
                with st.spinner("Agent đang nghiên cứu và gọi tool…"):
                    run_turn(user_text)
        st.rerun()


# ---------------------------------------------------------------- evals page

TREND_METRICS = {
    "Case accuracy": ("base", "case_accuracy"),
    "Routing": ("base", "tool_routing_accuracy"),
    "Args": ("base", "argument_accuracy"),
    "Multi-turn": ("base", "multiturn_accuracy"),
    "Group suite": ("group", "case_accuracy"),
}


def _metric(runs: dict, version: str, suite: str, key: str) -> float | None:
    run = runs.get((version, suite))
    return None if run is None else run["summary"].get(key)


def _passed(runs: dict, version: str) -> tuple[int, int]:
    passed = total = 0
    for suite in ("base", "group"):
        run = runs.get((version, suite))
        if run:
            passed += run["summary"].get("passed_cases", 0)
            total += run["summary"].get("total_cases", 0)
    return passed, total


def render_evals_page() -> None:
    runs = load_runs()
    versions = sorted({v for (v, _s) in runs}, key=lambda v: (len(v), v))
    if not versions:
        st.info("Chưa có run nào trong `runs/`. Chạy `python run_eval.py ...` trước.")
        return
    latest = versions[-1]
    latest_run = runs.get((latest, "base")) or next(r for (v, _s), r in runs.items() if v == latest)
    n_cases = sum(_passed(runs, latest)[1:])
    when = str(latest_run.get("generated_at", ""))[:10]

    head, pick = st.columns([2.3, 1.5], vertical_alignment="bottom")
    with head:
        html(ui.hero_html(n_cases, latest_run.get("model") or "", when, len(versions)))
    with pick:
        a, b = st.columns(2)
        start = a.selectbox("Từ", versions, index=0, format_func=version_label, key="cmp_from")
        end = b.selectbox("Đến", versions, index=len(versions) - 1, format_func=version_label, key="cmp_to")

    timeline = []
    for v in versions:
        run = runs.get((v, "base")) or {}
        stamp = str(run.get("generated_at", ""))
        timeline.append({"version": v, "name": version_note(v)["name"], "when": stamp[11:16]})
    html(ui.timeline_html(timeline, start, end))

    p_new, t_new = _passed(runs, end)
    p_old, t_old = _passed(runs, start)
    cards = [
        {"label": label, "new": _metric(runs, end, suite, key), "old": _metric(runs, start, suite, key)}
        for label, (suite, key) in TREND_METRICS.items()
    ]
    cards.append({"label": "Case pass (base + group)",
                  "new": p_new / t_new if t_new else None, "old": p_old / t_old if t_old else None,
                  "display": f"{p_new}/{t_new}", "was": f"{p_old}/{t_old}"})
    html(ui.metric_cards_html(cards))
    st.write("")

    trend_col, change_col = st.columns([1.5, 1], gap="large")
    with trend_col:
        with st.container(border=True, key="trend_panel"):
            html('<h3 style="font-size:30px;margin:0">Trend across versions</h3>'
                 '<div class="eyebrow" style="margin:2px 0 8px">↑ higher is better · trục y từ 50%</div>')
            choice = st.segmented_control("Metric", list(TREND_METRICS), default="Case accuracy",
                                          key="trend_metric", label_visibility="collapsed") or "Case accuracy"
            suite, key = TREND_METRICS[choice]
            points = [(v, _metric(runs, v, suite, key)) for v in versions]
            html(ui.trend_svg(points, start=start, end=end))
    with change_col:
        log = {row["version"]: row for row in load_version_log()}
        lo, hi = sorted((versions.index(start), versions.index(end)))
        releases = []
        for i in range(lo + 1, hi + 1):
            v = versions[i]
            note = version_note(v)
            releases.append({
                "version": v, "name": note["name"], "summary": note["summary"], "chips": note["chips"],
                "before": _metric(runs, versions[i - 1], "base", "case_accuracy"),
                "after": _metric(runs, v, "base", "case_accuracy"),
                "hypothesis": (log.get(v) or {}).get("hypothesis", ""),
            })
        html(ui.releases_html(releases, versions[lo], versions[hi]))

    st.write("")
    with st.container(border=True, key="matrix_panel"):
        html('<h3 style="font-size:30px;margin:0 0 8px">Case pass/fail qua các version</h3>')
        suites = sorted({s for (_, s) in runs})
        c1, c2 = st.columns([1, 2])
        suite = c1.selectbox("Bộ eval", suites, index=suites.index("base") if "base" in suites else 0)
        only_changed = c2.toggle("Chỉ hiện case từng fail", value=True)
        html(ui.matrix_html(case_matrix(runs, suite, only_changed=only_changed)))

    st.write("")
    html('<h3 style="font-size:30px;margin:8px 0 2px">Thử để thấy khác biệt</h3>'
         '<div class="watch">Chọn version cạnh ô chat, bấm <b>Gửi</b>, rồi đổi version và hỏi lại đúng câu đó. '
         'Bảng dưới mỗi câu là tool call thật của từng version lúc chạy eval.</div>')
    cols = st.columns(2, gap="medium")
    for i, item in enumerate(COMPARE_PROMPTS):
        with cols[i % 2], st.container(border=True):
            html(f'<div class="eyebrow">{ui.esc(item["case"])}</div>')
            for j, turn in enumerate(item["turns"]):
                q, b = st.columns([5, 1], vertical_alignment="center")
                prefix = f"Lượt {j + 1}: " if len(item["turns"]) > 1 else ""
                q.markdown(f'<div class="prompt-q">{prefix}{ui.esc(turn)}</div>', unsafe_allow_html=True)
                if b.button("Gửi", key=f"cmp_{i}_{j}", use_container_width=True):
                    st.session_state.pending = turn
                    st.session_state.page = "chat"
                    st.rerun()
            html(f'<div class="watch">{ui.esc(item["watch"]).replace("`", "")}</div>')
            html(ui.calls_html(case_calls(runs, item["case"])))


# ---------------------------------------------------------------- main

def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")
    html(ui.CSS)
    # ?page=evals opens the eval dashboard directly (handy for demo links).
    st.session_state.setdefault("page", "evals" if st.query_params.get("page") == "evals" else "chat")
    config = build_config()
    if "config" not in st.session_state:
        try:
            new_session(config)
        except Exception as exc:
            st.error(f"Không đọc được prompt/tools: {type(exc).__name__}: {exc}")
            st.stop()
    elif st.session_state.config != config:
        had_turns = bool(st.session_state.turns)
        try:
            new_session(config)
        except Exception as exc:
            st.error(f"Không đọc được prompt/tools: {type(exc).__name__}: {exc}")
            st.stop()
        if had_turns:
            st.toast(f"Đã chuyển sang {config['version']}: bắt đầu cuộc trò chuyện mới.")

    sidebar(config)
    if st.session_state.page == "evals":
        render_evals_page()
    else:
        render_chat_page()


main()
