from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import execute_tool_call, run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import load_tool_declarations, to_openai_tools


ROOT = Path(__file__).resolve().parent
PROVIDER_NAMES = ["openai", "openrouter", "anthropic", "gemini", "ollama"]
PROVIDER_KEYS = {
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
SUGGESTIONS = [
    ("🗞️ Bài đăng mới của sama", "Lấy 5 bài đăng mới nhất của tài khoản sama trên X."),
    ("🔎 Tìm bài đăng về AI", "Tìm các bài đăng mới nhất trên X về AI."),
    ("🌐 Tin AI hôm nay", "Tìm tin tức AI nổi bật hôm nay trên web."),
    ("📄 Tìm nghiên cứu arXiv", "Tìm các bài nghiên cứu arXiv mới về AI agents."),
]


def load_css() -> None:
    """Nạp CSS tĩnh cho giao diện; không đưa nội dung động vào HTML."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        :root { --blue: #4f8bf9; --ink: #17233b; --muted: #6e7b91; --panel: #ffffff; }
        html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
        .stApp { background: #f5f8fd; color: var(--ink); }
        [data-testid="stSidebar"] { background: #fff; border-right: 1px solid #e7edf5; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { color: var(--ink); }
        .hero { padding: 1.25rem 1.4rem; margin: .4rem 0 1.2rem; border-radius: 20px;
                background: linear-gradient(120deg, #e7f0ff, #f4f8ff 65%, #eef7ff);
                border: 1px solid #dce9ff; box-shadow: 0 8px 24px rgba(36, 74, 130, .07); }
        .hero-title { font-size: clamp(1.35rem, 4vw, 1.9rem); font-weight: 700; margin: 0; color: #18345f; }
        .hero-subtitle { margin: .45rem 0 0; color: #5c6d88; font-size: .96rem; }
        [data-testid="stChatMessage"] { border: 1px solid #e7edf5; border-radius: 18px;
                padding: .85rem 1rem; margin-bottom: .7rem; background: rgba(255,255,255,.92);
                box-shadow: 0 4px 16px rgba(34, 57, 91, .045); }
        [data-testid="stChatInput"] { border-radius: 16px; }
        .stButton > button { border-radius: 12px; border: 1px solid #d9e5f6; transition: .15s ease; }
        .stButton > button:hover { border-color: var(--blue); color: #245fc5; }
        @media (max-width: 640px) {
            .hero { padding: 1rem; border-radius: 16px; }
            [data-testid="stChatMessage"] { padding: .7rem; border-radius: 15px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    """Khởi tạo dữ liệu phiên chat một lần cho mỗi người dùng."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [{
            "role": "assistant",
            "content": "Xin chào! Mình là Research Agent. Bạn có thể nhờ mình tìm bài đăng X, tin web, đọc URL hoặc tìm nghiên cứu arXiv.",
            "time": datetime.now().strftime("%H:%M"),
            "tool_events": [],
        }]
    st.session_state.setdefault("provider_name", "openai")
    st.session_state.setdefault("model_provider", st.session_state.provider_name)
    st.session_state.setdefault("model_id", None)
    st.session_state.setdefault("agent_runtime", None)
    st.session_state.setdefault("pending_send", None)


def reset_runtime() -> None:
    """Xóa provider/runtime để được tạo mới khi provider hoặc model thay đổi."""
    st.session_state.agent_runtime = None


@st.cache_data
def provider_defaults() -> dict[str, str]:
    """Lấy model mặc định trực tiếp từ các adapter hiện có."""
    return {name: make_provider(name).default_model for name in PROVIDER_NAMES}


def render_sidebar() -> tuple[str, str]:
    """Hiển thị cấu hình provider và giới thiệu bài lab."""
    defaults = provider_defaults()
    with st.sidebar:
        st.markdown("# 🔬 Research Agent")
        st.caption("Trợ lý nghiên cứu có thể gọi các công cụ trong lab.")
        if st.button("🧹 Xóa cuộc trò chuyện", key="clear_conversation", use_container_width=True):
            for key in ("chat_messages", "agent_runtime", "pending_send"):
                st.session_state.pop(key, None)
            st.rerun()

        st.divider()
        provider = st.selectbox(
            "Provider",
            PROVIDER_NAMES,
            format_func=lambda item: {
                "openai": "OpenAI",
                "openrouter": "OpenRouter",
                "anthropic": "Anthropic",
                "gemini": "Gemini",
                "ollama": "Ollama (local)",
            }[item],
            key="provider_name",
        )
        if st.session_state.model_provider != provider:
            st.session_state.model_provider = provider
            st.session_state.model_id = defaults[provider]
            reset_runtime()
        elif st.session_state.model_id is None:
            st.session_state.model_id = defaults[provider]

        model = st.text_input("Model", key="model_id", help="Model ID được truyền tới adapter đã chọn.")
        runtime = st.session_state.agent_runtime
        if runtime and (runtime["provider_name"] != provider or runtime["model"] != model):
            reset_runtime()

        if provider == "ollama":
            st.info("Ollama không cần API key; máy cần chạy endpoint local đã cấu hình.")
            configured = True
        else:
            key_name = PROVIDER_KEYS[provider]
            configured = bool(os.getenv(key_name))
            label = "Đã cấu hình" if configured else "Chưa cấu hình"
            st.caption(f"Trạng thái provider: **{label}** ({key_name})")

        st.caption("Tham số model: temperature cố định ở 0.0 trong luồng chat hiện tại; không có giới hạn token cấu hình từ UI.")
        st.divider()
        st.markdown("### Về bài lab")
        st.write("Xây dựng Research Agent định tuyến yêu cầu tới tool nghiên cứu, đọc kết quả và trả lời có dẫn nguồn khi có thể.")
        st.caption("RapidAPI chỉ được dùng qua tool X đã có trong dự án.")
    return provider, model


def get_runtime(provider_name: str, model: str) -> dict[str, Any]:
    """Tạo provider và nạp prompt/tools một lần rồi giữ trong session state."""
    runtime = st.session_state.agent_runtime
    if runtime and runtime["provider_name"] == provider_name and runtime["model"] == model:
        return runtime

    provider = make_provider(provider_name)
    declarations = load_tool_declarations(ROOT / "artifacts" / "tools.yaml")
    runtime = {
        "provider_name": provider_name,
        "provider": provider,
        "model": model or provider.default_model,
        "system_prompt": (ROOT / "artifacts" / "system_prompt.md").read_text(encoding="utf-8"),
        "tools": to_openai_tools(declarations),
    }
    st.session_state.agent_runtime = runtime
    return runtime


def friendly_error(error: Any) -> str:
    """Chuyển lỗi provider/tool thành thông báo thân thiện, không lộ chi tiết nhạy cảm."""
    message = str(error).lower()
    if any(word in message for word in ("missing api key", "api key env", "unauthorized", "invalid_api_key", "401")):
        return "Chưa cấu hình API key hợp lệ cho provider đang chọn. Hãy kiểm tra biến tương ứng trong `starter_v0/.env`."
    if any(word in message for word in ("429", "quota", "rate limit", "resource_exhausted")):
        return "Provider đang giới hạn lượt gọi hoặc đã hết quota. Hãy chờ một lúc hoặc kiểm tra hạn mức tài khoản."
    if any(word in message for word in ("timeout", "timed out", "deadline exceeded")):
        return "Yêu cầu bị quá thời gian chờ. Hãy thử lại sau."
    if any(word in message for word in ("connection", "network", "name resolution", "unreachable")):
        return "Không kết nối được dịch vụ. Hãy kiểm tra mạng hoặc trạng thái dịch vụ rồi thử lại."
    if "install live provider dependency" in message or "no module named" in message:
        return "Thiếu thư viện provider. Cài các gói trong `starter_v0/requirements.txt` rồi thử lại."
    return "Đã xảy ra lỗi khi xử lý yêu cầu. Hãy kiểm tra cấu hình provider/tool và thử lại."


def safe_value(key: str, value: Any) -> str:
    """Ẩn giá trị nhạy cảm và rút gọn tham số trước khi hiển thị."""
    if re.search(r"key|token|secret|password|authorization|header", key, re.IGNORECASE):
        return "[đã ẩn]"
    if key.lower() == "text" and value:
        return "[nội dung được hiển thị ở bước xác nhận gửi]"
    if isinstance(value, (dict, list)):
        return f"[{type(value).__name__}: {len(value)} mục]"
    text = str(value)
    return text if len(text) <= 240 else text[:237] + "..."


def format_tool_result(result: Any) -> str:
    """Tóm tắt kết quả tool thành nội dung dễ đọc, không đổ JSON thô."""
    if not isinstance(result, dict):
        return "Tool đã hoàn tất." if result is not None else "Không có dữ liệu trả về."
    if result.get("error"):
        return friendly_error(f"{result.get('error')} {result.get('message', '')}")
    if result.get("awaiting_user"):
        return "Đang chờ bạn trả lời câu hỏi làm rõ."
    if result.get("status") == "sent":
        return "Telegram xác nhận đã gửi tin nhắn."
    if result.get("status") == "needs_confirmation":
        return "Chưa gửi. Cần xác nhận rõ ràng trước khi thực hiện."
    items = result.get("items")
    if isinstance(items, list):
        lines = [f"Tìm thấy {len(items)} kết quả."]
        for index, item in enumerate(items[:5], start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "Kết quả")[:180]
            url = str(item.get("url") or "")[:300]
            summary = str(item.get("summary") or "").replace("\n", " ")[:260]
            lines.append(f"{index}. **{title}**")
            if url:
                lines.append(f"   {url}")
            if summary:
                lines.append(f"   {summary}")
        if len(items) > 5:
            lines.append(f"… còn {len(items) - 5} kết quả.")
        return "\n\n".join(lines)
    status = result.get("status")
    if status:
        return f"Trạng thái: {safe_value('status', status)}"
    return "Tool đã chạy xong."


def render_message(message: dict[str, Any]) -> None:
    """Hiển thị một tin nhắn, timestamp và các bước tool trong expander."""
    role = message.get("role", "assistant")
    avatar = "🧑" if role == "user" else "🔬"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.get("content", ""))
        st.caption(message.get("time", ""))
        events = message.get("tool_events") or []
        if events:
            with st.expander(f"🧰 Các bước tool ({len(events)})"):
                for event in events:
                    name = str(event.get("tool") or "tool")
                    with st.container(border=True):
                        st.markdown(f"**{name}**")
                        args = event.get("args") or {}
                        if isinstance(args, dict) and args:
                            st.caption("Tham số")
                            for key, value in args.items():
                                st.write(f"- `{key}`: {safe_value(str(key), value)}")
                        result = event.get("result", event)
                        st.caption("Kết quả")
                        st.write(format_tool_result(result))


def run_agent_turn(user_text: str, provider_name: str, model: str) -> None:
    """Gọi vòng chat hiện có, hoãn mọi tool gửi để chờ xác nhận UI."""
    user_message = {"role": "user", "content": user_text, "time": datetime.now().strftime("%H:%M")}
    st.session_state.chat_messages.append(user_message)
    try:
        runtime = get_runtime(provider_name, model)
        history = [
            {"role": message["role"], "content": message["content"]}
            for message in st.session_state.chat_messages[:-1]
            if message.get("role") in {"user", "assistant"}
        ]
        messages = [
            {"role": "system", "content": runtime["system_prompt"]},
            *trim_history(history, 5),
            {"role": "user", "content": user_text},
        ]
        result = run_model_tool_loop(
            provider=runtime["provider"],
            messages=messages,
            tools=runtime["tools"],
            model=runtime["model"],
            max_tool_rounds=4,
            defer_tool_names={"send"},
            log_tool_calls=False,
        )
        status = result.get("status")
        if status == "confirmation_required":
            action = result.get("pending_action") or {}
            args = action.get("args") or {}
            content = "Agent đề xuất gửi tin nhắn Telegram. Hãy xem nội dung và xác nhận bên dưới."
            events = result.get("tool_events", [])
            events.append({"tool": "send", "args": args, "result": {"status": "needs_confirmation"}})
            assistant_message = {
                "role": "assistant", "content": content,
                "time": datetime.now().strftime("%H:%M"), "tool_events": events,
            }
            st.session_state.chat_messages.append(assistant_message)
            st.session_state.pending_send = {
                "args": args,
                "message_index": len(st.session_state.chat_messages) - 1,
            }
            return

        answer = result.get("assistant_text") or "Mình chưa nhận được câu trả lời từ agent."
        if status == "max_tool_rounds":
            answer = "Mình đã chạm giới hạn số vòng gọi tool. Hãy thử yêu cầu ngắn hoặc cụ thể hơn."
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": answer,
            "time": datetime.now().strftime("%H:%M"),
            "tool_events": result.get("tool_events", []),
        })
    except Exception as exc:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": friendly_error(exc),
            "time": datetime.now().strftime("%H:%M"),
            "tool_events": [],
            "is_error": True,
        })


def handle_pending_send() -> bool:
    """Hiển thị nội dung cần gửi và chỉ thực hiện sau nút xác nhận rõ ràng."""
    pending = st.session_state.pending_send
    if not pending:
        return False

    args = pending.get("args") or {}
    text = args.get("text") if isinstance(args, dict) else ""
    st.warning("Bạn cần xác nhận trước khi gửi nội dung này lên Telegram.")
    st.caption("Nội dung chính xác sẽ gửi:")
    st.code(str(text or "(Nội dung trống)"), language=None)
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        confirm = st.button(
            "✅ Xác nhận gửi", key="confirm_send", type="primary",
            disabled=not bool(text), use_container_width=True,
        )
    with cancel_col:
        cancel = st.button("Hủy", key="cancel_send", use_container_width=True)

    if confirm:
        tool_args = dict(args)
        tool_args["confirmed"] = True
        event = execute_tool_call(ToolCall("send", tool_args))
        message = st.session_state.chat_messages[pending["message_index"]]
        message["tool_events"] = [event]
        result = event.get("result", {})
        message["content"] = (
            "Đã gửi tin nhắn lên Telegram."
            if result.get("status") == "sent"
            else f"Không gửi được: {friendly_error(result.get('message') or result.get('error', ''))}"
        )
        st.session_state.pending_send = None
        st.rerun()
    if cancel:
        message = st.session_state.chat_messages[pending["message_index"]]
        message["content"] = "Đã hủy. Mình không gửi nội dung lên Telegram."
        message["tool_events"] = []
        st.session_state.pending_send = None
        st.rerun()
    return True


def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="🔬", layout="wide")
    load_lab_env(ROOT)
    init_state()
    load_css()
    provider, model = render_sidebar()

    st.markdown(
        "<section class='hero'><p class='hero-title'>🔬 Research Agent</p>"
        "<p class='hero-subtitle'>Tìm kiếm, đọc và tổng hợp thông tin bằng các công cụ nghiên cứu của lab.</p></section>",
        unsafe_allow_html=True,
    )

    for message in st.session_state.chat_messages:
        render_message(message)

    if handle_pending_send():
        return

    selected_prompt: str | None = None
    if len(st.session_state.chat_messages) == 1:
        st.markdown("#### Bắt đầu nhanh")
        columns = st.columns(2)
        for index, (label, prompt) in enumerate(SUGGESTIONS):
            with columns[index % 2]:
                if st.button(label, key=f"suggestion_{index}", use_container_width=True):
                    selected_prompt = prompt

    typed_prompt = st.chat_input("Hỏi Research Agent…", disabled=bool(st.session_state.pending_send))
    user_text = selected_prompt or typed_prompt
    if user_text:
        with st.spinner("Research Agent đang xử lý…"):
            run_agent_turn(user_text, provider, model)
        st.rerun()


if __name__ == "__main__":
    main()
