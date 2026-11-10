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

def render_tool_event(event: dict[str, Any]) -> None:
    result = event.get("result")
    st.markdown(f"**🔧 `{event.get('tool')}`**({format_args(event.get('args') or {})}) · {result_badge(result)}")
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
    st.code(json_preview(result), language="json")


def render_turn(turn: dict[str, Any], *, is_last: bool) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        rounds = turn.get("rounds") or []
        n_calls = sum(len(r.get("tool_calls") or []) for r in rounds)
        if n_calls:
            label = f"Tool calls: {n_calls} lời gọi trong {len(rounds)} vòng"
            with st.expander(label, expanded=is_last):
                for rnd in rounds:
                    st.caption(f"Vòng {rnd['round']}")
                    if rnd.get("assistant_text"):
                        st.markdown(f"> {rnd['assistant_text']}")
                    if not rnd.get("tool_calls"):
                        st.markdown("_Không gọi tool, trả lời trực tiếp._")
                    for event in rnd.get("tool_results") or []:
                        render_tool_event(event)
        else:
            st.caption("Không gọi tool")

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


def sidebar() -> dict[str, Any]:
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        provider = st.selectbox("Provider", PROVIDERS, index=0)
        # <PROVIDER>_MODEL in .env overrides the code default (e.g. OPENROUTER_MODEL when
        # OPENROUTER_BASE_URL points at another OpenAI-compatible host such as Groq).
        default_model = os.getenv(f"{provider.upper()}_MODEL") or getattr(make_provider(provider), "default_model", "")
        model = st.text_input("Model", value=default_model, help="Để trống để dùng model mặc định của provider.")
        version = st.text_input("Version label", value="v2", help="Nhãn ghi vào transcript, ví dụ v2, v3.")
        with st.expander("Nâng cao"):
            system_prompt = st.text_input("System prompt", value=str(ARTIFACTS_DIR / "system_prompt.md"))
            tools = st.text_input("Tools YAML", value=str(ARTIFACTS_DIR / "tools.yaml"))
            history_window = st.number_input("History window (cặp lượt)", 0, 20, 5)
            max_tool_rounds = st.number_input("Max tool rounds", 1, 10, 4)

        config = {
            "provider": provider,
            "model": model.strip(),
            "version": version.strip() or "ui",
            "system_prompt": system_prompt,
            "tools": tools,
            "history_window": int(history_window),
            "max_tool_rounds": int(max_tool_rounds),
        }

        if st.button("🆕 Cuộc trò chuyện mới", use_container_width=True):
            new_session(config)
            st.rerun()

        if "config" in st.session_state and st.session_state.config != config:
            st.warning("Cấu hình đã đổi. Bấm **Cuộc trò chuyện mới** để áp dụng.")

        st.divider()
        st.subheader("🔑 API key")
        st.markdown(f"- {PROVIDER_KEY_ENV[provider] or provider}: {env_status(PROVIDER_KEY_ENV[provider])}")
        for tool_name, env in TOOL_KEY_ENV.items():
            st.markdown(f"- `{tool_name}`: {env_status(env)}")

        if "artifact_version" in st.session_state:
            st.divider()
            st.subheader("🧾 Phiên hiện tại")
            av = st.session_state.artifact_version
            st.code(av.artifact_version, language=None)
            st.caption(f"{len(st.session_state.openai_tools)} tool được khai báo trong tools.yaml")
            with st.expander("📝 System prompt đang dùng"):
                st.code(st.session_state.system_prompt_text, language="markdown")
            with st.expander("🛠️ Tool đang khai báo"):
                for tool in st.session_state.openai_tools:
                    fn = tool["function"]
                    st.markdown(f"**`{fn['name']}`**: {fn.get('description', '')}")
            st.caption(f"Transcript: `{display_path(st.session_state.transcript_path)}`")
            if st.session_state.transcript_path.exists():
                st.download_button(
                    "⬇️ Tải transcript JSON",
                    st.session_state.transcript_path.read_bytes(),
                    file_name=st.session_state.transcript_path.name,
                    mime="application/json",
                    use_container_width=True,
                )
    return config


def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")
    config = sidebar()
    if "config" not in st.session_state:
        try:
            new_session(config)
        except Exception as exc:
            st.error(f"Không đọc được prompt/tools: {type(exc).__name__}: {exc}")
            st.stop()

    st.title("🔎 Research Agent")
    st.caption(
        "Agent tự chọn tool (tìm tin, đọc tweet, đọc URL, tìm paper, tra policy...), "
        "gọi tool thật, rồi trả lời. Mở mục **Tool calls** để xem agent đã gọi gì."
    )

    turns = st.session_state.turns
    if not turns:
        st.markdown("**Thử nhanh một câu hỏi mẫu:**")
        cols = st.columns(2)
        for i, question in enumerate(SAMPLE_QUESTIONS):
            if cols[i % 2].button(question, key=f"sample_{i}", use_container_width=True):
                st.session_state.pending = question
                st.rerun()

    for i, turn in enumerate(turns):
        render_turn(turn, is_last=i == len(turns) - 1)

    typed = st.chat_input("Hỏi agent...")
    user_text = typed or st.session_state.pop("pending", None)
    if user_text:
        with st.chat_message("user"):
            st.markdown(user_text)
        with st.chat_message("assistant"):
            with st.spinner("Agent đang suy nghĩ và gọi tool..."):
                run_turn(user_text)
        st.rerun()


main()
