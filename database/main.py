import sys
import os

# Thêm đường dẫn cha (Chatbot-Makeup) vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from utils.api import API

api = API('https://b9a2-116-108-3-127.ngrok-free.app/')

# --- Sidebar ---
st.sidebar.title("🧠 Quản lý hội thoại")
all_names = api.get_all_name_conversations()
selected = st.sidebar.selectbox("Chọn hội thoại", ["🆕 Tạo mới"] + all_names)
if selected == "🆕 Tạo mới":
    st.session_state["conv_name"] = None
else:
    st.session_state["conv_name"] = selected
    # Hiển thị lịch sử
    for sender, msg in api.get_history_conversations(selected):
        st.markdown(f"**{sender.capitalize()}**: {msg}")

# --- Giao diện chat ---
user_input = st.text_input("Bạn:", "")

if user_input:
    # Lưu message user, tạo hội thoại nếu chưa có
    conv_name = api.add_message(user_input, "user", st.session_state["conv_name"])
    # conv_name = conv.add_message("user", user_input, st.session_state["conv_name"])

    # Lấy context gần nhất
    context = api.get_last_context(conv_name)
    prompt = "\n".join(f"{s}: {m}" for s, m in context)

    # Gọi model sinh phản hồi (giả lập):
    bot_reply = f"Bot trả lời dựa trên:\n{prompt}"

    # Lưu và hiển thị
    api.add_message(bot_reply, "bot", conv_name)
    # conv.add_message("bot", bot_reply, conv_name)
    st.markdown(f"🤖 **Bot**: {bot_reply}")