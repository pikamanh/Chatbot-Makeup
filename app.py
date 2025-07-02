import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from utils.api import API

api = API('https://69e7-171-253-191-127.ngrok-free.app')  # 🔁 Đặt đúng địa chỉ server bạn đang dùng

st.set_page_config(page_title="Chatbot for Makeup", page_icon="💄")
st.title("💄 Chatbot for Makeup")

# Sidebar chọn hội thoại
st.sidebar.title("🧠 Quản lý hội thoại")
all_convs = api.get_all_name_conversations()
selected = st.sidebar.selectbox("Chọn hội thoại", ["🆕 Tạo mới"] + all_convs)

# Lưu lựa chọn hiện tại
if "last_selected_conv" not in st.session_state:
    st.session_state["last_selected_conv"] = None

# Nếu người dùng chọn một hội thoại mới (khác hội thoại cũ), thì reset messages
if selected != st.session_state["last_selected_conv"]:
    if selected == "🆕 Tạo mới":
        st.session_state["conv_name"] = None
        st.session_state.messages = []
    else:
        st.session_state["conv_name"] = selected
        history = api.get_history_conversations(selected)
        st.session_state.messages = [{'role': s, 'content': m} for s, m in history]

    st.session_state["last_selected_conv"] = selected

if "conv_name" not in st.session_state:
    st.session_state["conv_name"] = None

# Hiển thị lại lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# Giao diện chat
prompt = st.chat_input("Type your message...")
if prompt:
    # Hiển thị user
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    # Gửi prompt đến server để xử lý Kaggle
    conv_name = api.ask_model(prompt, st.session_state["conv_name"])
    st.session_state["conv_name"] = conv_name  # Cập nhật nếu là mới

    # Chờ phản hồi từ Kaggle
    with st.spinner("🤖 Loading..."):
        max_wait = 60  # Giây
        interval = 2
        waited = 0
        bot_reply = None

        while waited < max_wait:
            context = api.get_last_context(conv_name)
            for (sender_1, msg_1), (sender_2, msg_2) in context:
                if sender_2 == 'assistant':
                    bot_reply = msg_2

            if bot_reply:
                break

            time.sleep(interval)
            waited += interval

    # Hiển thị phản hồi
    if bot_reply:
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        st.session_state.messages.append({'role': 'assistant', 'content': bot_reply})
    else:
        st.warning("⏰ Xin lỗi bạn. Hiện tại server đang lỗi.")