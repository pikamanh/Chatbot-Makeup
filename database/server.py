from flask import Flask, request, jsonify
from flask_cors import CORS
from  conversation import Conversation
import json
import os

app = Flask(__name__)
cors = CORS(app)

conv = Conversation()
INPUT_FILE = "pending_question.json"
INPUT_HISTORY = "pending_history.json"

# Nhận câu trả lời từ model
@app.route("/receive_answer", methods=["POST"])
def receive_answer():
    data = request.json
    sender = data.get("sender", 'assistant')
    message = data["message"]
    name_conversation = data["name_conversation"]

    conv.add_message(sender, message, name_conversation)
    print(f"✅ Nhận từ Kaggle: {message}")

    # Xóa file pending nếu tồn tại
    if os.path.exists(INPUT_FILE):
        os.remove(INPUT_FILE)
        print("🧹 Đã xóa file pending_question.json")

    return jsonify({"status": "ok", "message": message, "conversation_name": name_conversation})

# Gửi câu hỏi cho model
@app.route("/ask_model", methods=["POST"])
def ask_model():
    data = request.json
    message = data["message"]
    name = data.get("name_conversation")

    conv_name = conv.add_message("user", message, name)

    # Ghi câu hỏi vào file để Kaggle xử lý
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "message": message,
            "name_conversation": conv_name
        }, f, ensure_ascii=False)

    return jsonify({"status": "sent_to_kaggle", "conversation_name": conv_name})

# Kaggle nhận câu hỏi
@app.route("/get_kaggle_question", methods=["GET"])
def get_kaggle_question():
    try:
        with open("pending_question.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify({})

@app.route("/kaggle_get_history", methods=["POST"])

# Kaggle lấy lịch sử conversation
@app.route("/kaggle_get_history_conversation", methods=['POST'])
def kaggle_get_history():
    data = request.json
    name_conv = data['name_conversation']

    history = conv.kaggle_history(name_conv)

    return jsonify({'history': history})

# Thêm tin nhắn vào database
@app.route("/add_message", methods=['POST'])
def add_message():
    data = request.json
    sender = data['sender']
    message = data['message']
    name_conv = data['name_conversation']

    name_conv = conv.add_message(sender, message, name_conv)
    return jsonify({"conversation_name": name_conv})

# Lấy toàn bộ tên conversation
@app.route("/get_all_name_conversations", methods=['POST'])
def get_conversations():
    names = conv.get_all_conversation_names()
    return jsonify({"conversations": names})

# Lấy lịch sử conversation
@app.route("/get_history_conversation", methods=['POST'])
def get_history():
    data = request.json
    name_conv = data['name_conversation']

    history = conv.get_history(name_conv)

    return jsonify({'history': history})

# Lấy câu hỏi hoặc câu trả lời cuối cùng
@app.route("/get_context", methods=['POST'])
def get_context():
    data = request.json
    name_conv = data['name_conversation']

    context = conv.get_last_context(name_conv)
    return jsonify({'sender': context[0], 'message': context[1]})

if __name__ == '__main__':
    app.run(port=5000, debug=True)