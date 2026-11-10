from __future__ import annotations

import os
from hmac import compare_digest
from re import sub
from sqlite3 import Error as SQLiteError
from typing import Any

import streamlit as st

from chat import ARTIFACTS_DIR, run_model_tool_loop, trim_history
from chat_history import HISTORY_PATH, ChatHistory
from providers import OpenRouterProvider, make_provider
from tools import load_tool_declarations, to_openai_tools


SNAPSHOTS_DIR = ARTIFACTS_DIR / "eval_versions"
BASE_ARTIFACTS = {
    "v0": ("system_prompt_v0.md", "tools_v0_v1.yaml"),
    "v1": ("system_prompt_v1.md", "tools_v0_v1.yaml"),
    "v2": ("system_prompt_v1.md", "tools_v2_v3_base.yaml"),
    "v3": ("system_prompt_v3_base.md", "tools_v2_v3_base.yaml"),
}


st.set_page_config(page_title="Research Agent", page_icon="🔎")
st.title("Research Agent")
st.caption("Tìm nguồn, đọc bài viết và tổng hợp kết quả. Bản demo chỉ hỗ trợ thao tác đọc.")

demo_access_code = os.getenv("RESEARCH_DEMO_ACCESS_CODE")
if demo_access_code and not st.session_state.get("demo_access_granted"):
    with st.form("demo_access"):
        entered_code = st.text_input("Mã truy cập demo", type="password")
        submitted = st.form_submit_button("Mở demo")
    if submitted:
        if compare_digest(entered_code.encode(), demo_access_code.encode()):
            st.session_state.demo_access_granted = True
            st.rerun()
        st.error("Mã truy cập chưa đúng.")
    st.stop()

def open_conversation(chat_id: str = "") -> None:
    st.session_state.messages = []
    if not demo_access_code and not st.session_state.get("history_unavailable"):
        st.query_params["chat"] = chat_id


def render_chat_message(message: dict[str, Any]) -> None:
    st.markdown(message["content"])
    if message.get("image") is not None:
        st.image(message["image"])
    if message.get("tools"):
        st.caption("Tool đã gọi · " + ", ".join(message["tools"]))


history_store = None
if not demo_access_code and not st.session_state.get("history_unavailable"):
    try:
        history_store = ChatHistory(HISTORY_PATH)
        conversations = history_store.list_conversations()
        conversation_id = st.query_params.get("chat", next(iter(conversations), ""))
        if conversation_id not in conversations:
            conversation_id = ""
        history = history_store.read_messages(conversation_id)
        st.session_state.messages = history
    except (OSError, SQLiteError):
        history_store = None
        st.session_state.history_unavailable = True

if history_store is None:
    history = st.session_state.setdefault("messages", [])

with st.sidebar:
    st.button("Cuộc trò chuyện mới", icon=":material/edit_square:", width="stretch", on_click=open_conversation)
    if history_store is not None:
        st.markdown("""
            <style>
            .st-key-chat_threads .stButton button {
                justify-content: flex-start;
                text-align: left;
                min-height: 2rem;
            }
            .st-key-chat_threads .stButton button[kind="secondary"] {
                background: color-mix(in srgb, currentColor 10%, transparent);
                border-color: transparent;
            }
            </style>
        """, unsafe_allow_html=True)
        st.markdown("**Các cuộc trò chuyện**")
        if not conversations:
            st.caption("Các cuộc chat đã lưu sẽ xuất hiện ở đây.")
        with st.container(key="chat_threads", gap=None):
            for chat_id, question in conversations.items():
                title = " ".join(question.split())
                label = title[:47] + "…" if len(title) > 48 else title
                label = sub(r"([\\`*_{}\[\]<>!])", r"\\\1", label)
                st.button(
                    label, key=f"chat_{chat_id}", width="stretch",
                    type="secondary" if chat_id == conversation_id else "tertiary",
                    on_click=open_conversation, args=(chat_id,),
                )
    elif not demo_access_code:
        st.warning("Lịch sử hiện chỉ lưu trong phiên. Tải lại trang để thử mở lại tệp lưu trên máy.")

    model = None
    version = "v3"
    use_base_v3 = False
    if demo_access_code:
        provider_name = "openrouter"
        provider = OpenRouterProvider(max_tokens=2048)
        st.caption(f"Demo v3 · {provider.default_model}")
    else:
        with st.expander("Cài đặt model"):
            version = st.selectbox("Phiên bản lab", list(BASE_ARTIFACTS), index=3, key="lab_version")
            if version == "v3":
                use_base_v3 = st.checkbox(
                    "Dùng cấu hình v3 của eval base",
                    help="Mặc định v3 dùng cấu hình demo có tool source_inventory.",
                )
            provider_name = st.selectbox("Model provider", ["openrouter", "gemini", "anthropic", "openai", "ollama"])
            provider = OpenRouterProvider(max_tokens=2048) if provider_name == "openrouter" else make_provider(provider_name)
            model = st.text_input(
                "Model (để trống để dùng mặc định)",
                key=f"model_{provider_name}",
                placeholder=provider.default_model,
            ).strip() or None
    missing_key = provider_name != "ollama" and not os.getenv(provider.api_key_env, "").strip()
    if missing_key:
        st.warning(f"Thiếu {provider.api_key_env}. Thêm key vào .env rồi khởi động lại app.")
    with st.expander("Thử hỏi"):
        st.markdown("- Tin về robot trong tuần này có gì?\n- Tóm tắt bài tại https://example.com/\n- Tóm tắt 3 tweet mới nhất giúp mình.")

for message in history:
    with st.chat_message(message["role"]):
        render_chat_message(message)

query = st.chat_input("Nhập câu hỏi nghiên cứu", disabled=missing_key)
if query and query.strip():
    query = query.strip()
    with st.chat_message("user"):
        st.markdown(query)

    if version == "v3" and not use_base_v3:
        prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"
    else:
        prompt_name, tools_name = BASE_ARTIFACTS[version]
        prompt_path = SNAPSHOTS_DIR / prompt_name
        tools_path = SNAPSHOTS_DIR / tools_name
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt += "\n\nThe Streamlit demo is read-only. Telegram sending is unavailable here."
    declarations = load_tool_declarations(tools_path)
    tools = to_openai_tools([tool for tool in declarations if tool["name"] != "send"])
    recent = trim_history(history, 5)
    messages = [
        {"role": "system", "content": prompt},
        *[{"role": item["role"], "content": item["content"]} for item in recent],
        {"role": "user", "content": query},
    ]

    with st.chat_message("assistant"), st.spinner("Agent đang xử lý…"):
        try:
            result = run_model_tool_loop(
                provider=provider, messages=messages, tools=tools,
                model=model, max_tool_rounds=4,
            )
        except Exception as exc:
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            error = f"HTTP {status}" if isinstance(status, int) else type(exc).__name__
            st.error(f"Không gọi được `{model or provider.default_model}` qua `{provider_name}` ({error}).")
        else:
            answer = result["assistant_text"] or "Model chưa trả về nội dung."
            tool_names = list(dict.fromkeys(event["tool"] for event in result["tool_events"]))
            reply = {"role": "assistant", "content": answer, "tools": tool_names}
            render_chat_message(reply)
            history.extend([
                {"role": "user", "content": query},
                reply,
            ])
            if history_store is not None:
                try:
                    saved_id = history_store.save_turn(
                        conversation_id, query, answer, tool_names,
                    )
                except SQLiteError:
                    st.session_state.history_unavailable = True
                    st.warning("Lượt chat này đang giữ trong phiên và chưa được lưu xuống máy.")
                else:
                    st.query_params["chat"] = saved_id
                    st.rerun()
