"""Research Agent - Streamlit UI.

Provides an interactive web interface for testing the agent, inspecting tool calls,
managing multi-round interactions, and exporting session transcripts.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# Setup paths
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import run_model_tool_loop, write_transcript, trim_history

load_lab_env(ROOT)
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"

st.set_page_config(
    page_title="Research Agent - Tool Eval UI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling
st.markdown(
    """
    <style>
    .stChatMessage { margin-bottom: 0.8rem; }
    .tool-badge {
        display: inline-block;
        padding: 2px 8px;
        background-color: #2b313e;
        color: #58a6ff;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.85em;
        margin-right: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []  # list of {role, content}
    if "turns_record" not in st.session_state:
        st.session_state.turns_record = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")


init_session()

# --- Sidebar Configuration ---
with st.sidebar:
    st.title("⚙️ Agent Controls")

    provider_name = st.selectbox(
        "Provider",
        options=["openrouter", "gemini", "openai", "anthropic", "ollama"],
        index=0,
        help="Chọn nhà cung cấp LLM",
    )

    model_override = st.text_input(
        "Model Override (để trống nếu dùng mặc định)",
        value="",
        placeholder="e.g. meta-llama/llama-3.3-70b-instruct",
    )

    version_label = st.text_input(
        "Artifact Version",
        value="v0",
        help="Version tag cho log và transcript (v0, v1, v2, v3...)",
    )

    st.divider()

    # Artifact inspection
    st.subheader("📁 Artifacts Status")
    prompt_file = ARTIFACTS_DIR / "system_prompt.md"
    tools_file = ARTIFACTS_DIR / "tools.yaml"

    try:
        art_ver = build_artifact_version(system_prompt_path=prompt_file, tools_path=tools_file)
        st.caption(f"Prompt hash: `{art_ver.prompt_hash[:10]}...`")
        st.caption(f"Tools hash: `{art_ver.tools_hash[:10]}...`")
    except Exception as e:
        st.warning(f"Không thể đọc artifact: {e}")
        art_ver = None

    with st.expander("📝 Xem System Prompt"):
        if prompt_file.exists():
            st.code(prompt_file.read_text(encoding="utf-8"), language="markdown")
        else:
            st.error("system_prompt.md not found")

    with st.expander("🛠️ Danh sách Tools đã nạp"):
        if tools_file.exists():
            decls = load_tool_declarations(tools_file)
            for t in decls:
                st.markdown(f"**`{t.get('name')}`**: {t.get('description', '')}")
        else:
            st.error("tools.yaml not found")

    st.divider()

    # Session Management
    col_clear, col_save = st.columns(2)
    with col_clear:
        if st.button("🗑️ Xoá chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.history = []
            st.session_state.turns_record = []
            st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()

    with col_save:
        if st.session_state.turns_record:
            transcript_data = {
                "session_id": st.session_state.session_id,
                "version": version_label,
                "provider": provider_name,
                "model": model_override or "default",
                "artifact": artifact_version_dict(art_ver) if art_ver else {},
                "turns": st.session_state.turns_record,
            }
            st.download_button(
                "💾 Tải Transcript",
                data=json.dumps(transcript_data, ensure_ascii=False, indent=2),
                file_name=f"transcript_{st.session_state.session_id}.json",
                mime="application/json",
                use_container_width=True,
            )

# --- Main App Header ---
st.title("🔍 Research Agent - Live Test & Demo")
st.caption(
    "Agent thực hiện research đa nguồn (Web, Twitter, Hacker News, OpenAlex Citations, Policy, arXiv), tự động chọn tool và trả lời kèm bằng chứng."
)

# Suggested queries
st.markdown("**💡 Câu hỏi mẫu để thử:**")
sample_cols = st.columns(3)
sample_queries = [
    "Dân Hacker News đang bàn gì về Rust?",
    "Paper 2106.09685 được cite bao nhiêu lần?",
    "Tweet mới nhất của Sam Altman là gì?",
]
for idx, q in enumerate(sample_queries):
    if sample_cols[idx].button(q, key=f"sample_{idx}", use_container_width=True):
        st.session_state.pending_query = q
        st.rerun()

# --- Render Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "tool_rounds" in msg and msg["tool_rounds"]:
            with st.expander(f"🛠️ Tool Execution Log ({len(msg['tool_rounds'])} round)", expanded=False):
                for r in msg["tool_rounds"]:
                    st.markdown(f"**Round {r.get('round', 1)}:**")
                    for tc in r.get("tool_calls", []):
                        st.markdown(f"<span class='tool-badge'>🔧 {tc.get('name')}</span>", unsafe_allow_html=True)
                        st.json(tc.get("args", {}), expanded=False)
                    for tr in r.get("tool_results", []):
                        st.markdown(f"**Kết quả từ `{tr.get('tool')}`:**")
                        st.json(tr.get("result", {}), expanded=False)

# --- Handle User Input ---
query_input = st.chat_input("Nhập câu hỏi nghiên cứu của bạn...")
if "pending_query" in st.session_state and st.session_state.pending_query:
    query_input = st.session_state.pending_query
    st.session_state.pending_query = None

if query_input:
    # Append user turn to visual chat
    st.session_state.messages.append({"role": "user", "content": query_input})
    with st.chat_message("user"):
        st.markdown(query_input)

    # Prepare agent run
    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ và thực thi tools..."):
            try:
                provider = make_provider(provider_name)
                tools_decl = load_tool_declarations(tools_file)
                tools_schema = to_openai_tools(tools_decl)
                system_prompt_text = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""

                # Build context messages with history
                history_window = 5
                trimmed = trim_history(st.session_state.history, history_window)
                messages = [
                    {"role": "system", "content": system_prompt_text},
                    *trimmed,
                    {"role": "user", "content": query_input},
                ]

                # Run tool loop
                model_arg = model_override.strip() or None
                outcome = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=tools_schema,
                    model=model_arg,
                    max_tool_rounds=4,
                )

                assistant_text = outcome.get("assistant_text", "")
                rounds = outcome.get("rounds", [])

                # Display response
                st.markdown(assistant_text)

                if rounds:
                    with st.expander(f"🛠️ Tool Execution Log ({len(rounds)} round)", expanded=True):
                        for r in rounds:
                            st.markdown(f"**Round {r.get('round', 1)}:**")
                            for tc in r.get("tool_calls", []):
                                st.markdown(f"<span class='tool-badge'>🔧 {tc.get('name')}</span>", unsafe_allow_html=True)
                                st.json(tc.get("args", {}), expanded=False)
                            for tr in r.get("tool_results", []):
                                st.markdown(f"**Kết quả từ `{tr.get('tool')}`:**")
                                st.json(tr.get("result", {}), expanded=False)

                # Update history & records
                st.session_state.history.append({"role": "user", "content": query_input})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "tool_rounds": rounds,
                })

                turn_record = {
                    "turn_index": len(st.session_state.turns_record) + 1,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "user_query": query_input,
                    "status": outcome.get("status"),
                    "assistant_text": assistant_text,
                    "rounds": rounds,
                }
                st.session_state.turns_record.append(turn_record)

                # Auto-save transcript to disk
                transcript_path = TRANSCRIPTS_DIR / f"streamlit_{st.session_state.session_id}.transcript.json"
                transcript_payload = {
                    "session_id": st.session_state.session_id,
                    "version": version_label,
                    "provider": provider_name,
                    "model": model_arg or getattr(provider, "default_model", "unknown"),
                    "artifact": artifact_version_dict(art_ver) if art_ver else {},
                    "turns": st.session_state.turns_record,
                }
                write_transcript(transcript_path, transcript_payload)

            except Exception as exc:
                st.error(f"Đã xảy ra lỗi khi chạy agent: {exc}")
                import traceback
                st.code(traceback.format_exc(), language="python")

