from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop, trim_history
from versioning import build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent - AI Assistant",
    page_icon="🔍",
    layout="wide",
)

# Custom Styling
st.markdown("""
<style>
    .stChatFloatingInputContainer {
        padding-bottom: 20px;
    }
    .tool-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        background: #eef2ff;
        color: #4f46e5;
        font-size: 0.85em;
        font-weight: 600;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)


def init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []


init_session()

# Sidebar
with st.sidebar:
    st.title("⚙️ Cấu hình Agent")
    provider_name = st.selectbox(
        "Model Provider",
        options=["groq", "openrouter", "openai", "gemini", "ollama"],
        index=0,
    )
    
    version_label = st.text_input("Version", value="v0")
    max_rounds = st.slider("Max Tool Rounds", min_value=1, max_value=6, value=4)
    history_window = st.slider("Context History Window", min_value=1, max_value=10, value=5)

    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"

    try:
        artifact_ver = build_artifact_version(version_label, system_prompt_path, tools_path)
        st.caption(f"**Artifact Version:** `{artifact_ver.artifact_version}`")
    except Exception as e:
        st.caption(f"Error computing version: {e}")

    st.divider()
    st.subheader("🛠️ Công cụ khả dụng")
    tool_decls = load_tool_declarations(tools_path)
    for t in tool_decls:
        with st.expander(f"📌 {t['name']}"):
            st.write(t.get("description", "No description"))

    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

st.title("🔍 Research Agent — Interactive UI")
st.caption("Trợ lý nghiên cứu AI với khả năng tự động lựa chọn tool, duyệt web, kiểm tra tin tức & mạng xã hội.")

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "tools" in msg and msg["tools"]:
            with st.expander(f"🛠️ Tool Events ({len(msg['tools'])} tools gọi)", expanded=False):
                for event in msg["tools"]:
                    st.markdown(f"**Tool:** `{event.get('tool')}`")
                    st.json({"args": event.get("args"), "result": event.get("result")})

# User Input
if user_input := st.chat_input("Nhập câu hỏi hoặc yêu cầu nghiên cứu của bạn..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process response
    with st.chat_message("assistant"):
        with st.status("🧠 Agent đang phân tích và tìm kiếm...", expanded=True) as status:
            try:
                system_prompt = system_prompt_path.read_text(encoding="utf-8")
                openai_tools = to_openai_tools(load_tool_declarations(tools_path))
                provider = make_provider(provider_name)
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    *trim_history(st.session_state.history, history_window),
                    {"role": "user", "content": user_input},
                ]

                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=None,
                    max_tool_rounds=max_rounds,
                )

                tool_events = result.get("tool_events", [])
                if tool_events:
                    st.write(f"Đã thực hiện **{len(tool_events)}** lệnh gọi tool:")
                    for ev in tool_events:
                        st.markdown(f"- 🔧 **`{ev.get('tool')}`** với tham số: `{json.dumps(ev.get('args', {}), ensure_ascii=False)}`")

                status.update(label="Hoàn thành!", state="complete", expanded=False)

                assistant_text = result.get("assistant_text", "")
                st.markdown(assistant_text)

                # Save history
                st.session_state.history.append({"role": "user", "content": user_input})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "tools": tool_events,
                })

            except Exception as err:
                status.update(label="Lỗi xử lý!", state="error", expanded=True)
                st.error(f"Đã xảy ra lỗi: {err}")

