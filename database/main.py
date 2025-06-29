import sys
import os
import time

# Thêm đường dẫn cha (Chatbot-Makeup) vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from utils.api import API

api = API('https://c539-116-108-3-127.ngrok-free.app/')

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
    conv_name = api.ask_model(user_input, st.session_state['conv_name'])
    # conv_name = conv.add_message("user", user_input, st.session_state["conv_name"])

    # Hiển thị tạm
    st.markdown(f"**You**: {user_input}")
    with st.spinner("🤖 Bot đang suy nghĩ từ Kaggle..."):
        # Chờ vài giây cho Kaggle trả lời (hoặc polling)
        time.sleep(5)

        context = api.get_last_context(conv_name)
        bot_responses = [msg for sender, msg in context if sender == "bot"]
        st.markdown(f"🤖 **Bot**: {bot_responses[0]}")