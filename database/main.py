import sys
import os
import time

# Thêm đường dẫn cha (Chatbot-Makeup) vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from utils.api import API

api = API('https://24b1-116-108-112-166.ngrok-free.app')

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
        max_wait_time = 60  # Giới hạn tối đa chờ 60s
        wait_time = 0
        bot_message = None
        bot_responses = []

        while wait_time < max_wait_time:
            context = api.get_last_context(conv_name)

            for (sender_1, msg_1), (sender_2, msg_2) in context:
                if sender_2 == 'bot':
                    bot_message = msg_2
                    print(bot_message)

            if bot_message:
                break

            time.sleep(2)
            wait_time += 2

        if bot_message:
            st.markdown(f"🤖 **Bot**: {bot_message}")
        else:
            st.warning("⏰ Quá thời gian chờ mà chưa có phản hồi từ Kaggle.")
