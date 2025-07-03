from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import random
from filelock import FileLock
from datetime import datetime
from langchain_model import process_question

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# URL ngrok (nên chuyển vào biến môi trường trong sản xuất)
def load_ngrok_url():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('NGROK_URL', 'http://localhost:5001') 
    except Exception as e:
        print(f"⚠️ Error loading NGROK_URL from config.json: {e}")
        return 'http://localhost:5001'  # Fallback URL

NGROK_URL = load_ngrok_url()

# File paths
chat_history_file = 'chat_history.json'
questions_file = 'questions.json'

# Hàm đọc lịch sử hội thoại từ file JSON
def load_chat_history():
    if not os.path.exists(chat_history_file):
        print(f"⚠️ File {chat_history_file} không tồn tại, khởi tạo dictionary rỗng")
        return {}
    try:
        with open(chat_history_file, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                print(f"⚠️ File {chat_history_file} rỗng, khởi tạo dictionary rỗng")
                return {}
            data = json.loads(content)
            print(f"✅ Đọc thành công chat_history.json: {len(data)} hội thoại")
            return data
    except json.JSONDecodeError as e:
        print(f"⚠️ Lỗi JSON trong {chat_history_file}: {e}. Khởi tạo dictionary rỗng")
        return {}
    except Exception as e:
        print(f"⚠️ Lỗi khi đọc {chat_history_file}: {e}")
        return {}

# Hàm lưu lịch sử hội thoại vào file JSON
def save_chat_history(chat_history):
    try:
        with FileLock(chat_history_file + '.lock'):
            with open(chat_history_file, 'w', encoding='utf-8') as file:
                json.dump(chat_history, file, indent=2, ensure_ascii=False)
        print(f"✅ Lưu thành công chat_history.json: {len(chat_history)} hội thoại")
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu lịch sử trò chuyện: {e}")

# Hàm đọc danh sách câu hỏi từ file JSON
def load_questions():
    if not os.path.exists(questions_file):
        print(f"⚠️ File {questions_file} không tồn tại, khởi tạo danh sách rỗng")
        return []
    try:
        with open(questions_file, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                print(f"⚠️ File {questions_file} rỗng, khởi tạo danh sách rỗng")
                return []
            data = json.loads(content)
            print(f"✅ Đọc thành công questions.json: {len(data)} câu hỏi")
            return data
    except json.JSONDecodeError as e:
        print(f"⚠️ Lỗi JSON trong {questions_file}: {e}. Khởi tạo danh sách rỗng")
        return []
    except Exception as e:
        print(f"⚠️ Lỗi khi đọc {questions_file}: {e}")
        return []

# Hàm lưu câu hỏi vào file JSON
def save_question(question_data):
    questions = load_questions()
    if not any(q['message'] == question_data['message'] and q['name_conversation'] == question_data['name_conversation'] for q in questions):
        questions.append(question_data)
        try:
            with open(questions_file, 'w', encoding='utf-8') as file:
                json.dump(questions, file, indent=2, ensure_ascii=False)
            print(f"✅ Đã lưu câu hỏi: {question_data}")
        except Exception as e:
            print(f"⚠️ Lỗi khi lưu câu hỏi: {e}")
    else:
        print(f"⏩ Câu hỏi đã tồn tại: {question_data}")

# Hàm thêm tin nhắn vào lịch sử trò chuyện
def add_message_to_history(sender, message, name_conversation):
    chat_history = load_chat_history()
    if name_conversation not in chat_history:
        chat_history[name_conversation] = {
            "title": f"Chat {len(chat_history) + 1}",
            "messages": []
        }
    class_name = "user-message" if sender == "user" else "model-message"
    if not any(msg['text'] == message and msg['className'] == class_name for msg in chat_history[name_conversation]["messages"]):
        chat_history[name_conversation]["messages"].append({"text": message, "className": class_name})
        save_chat_history(chat_history)
        print(f"✅ Nhận từ {sender}: {message} (chatId: {name_conversation})")
    else:
        print(f"⏩ Tin nhắn trùng lặp: {message} (chatId: {name_conversation})")

# Hàm tạo UUID
def generate_uuid():
    def uuid_char(c):
        r = random.randint(0, 15)
        if c == 'x':
            return hex(r)[2:]
        elif c == 'y':
            return hex((r & 0x3 | 0x8))[2:]
        return c
    uuid = ''.join(uuid_char(c) for c in 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx')
    print(f"📎 Tạo UUID mới: {uuid}")
    return uuid

# Route kiểm tra trạng thái server
@app.route('/', methods=['GET'])
def index():
    print(f"📖 [GET /] Yêu cầu từ {request.remote_addr} tại {datetime.now().isoformat()}")
    return jsonify({"status": "Server is running", "version": "1.0", "timestamp": datetime.now().isoformat()})

# Route kiểm tra sức khỏe server
@app.route('/health', methods=['GET'])
def health_check():
    print(f"📖 [GET /health] Yêu cầu từ {request.remote_addr} tại {datetime.now().isoformat()}")
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# API để lưu câu hỏi từ frontend
@app.route('/get_kaggle_question', methods=['GET'])
def get_kaggle_question():
    data = request.args
    message = data.get('message')
    chat_id = data.get('chat_id')
    print(f"📖 [GET /get_kaggle_question] Yêu cầu từ {request.remote_addr}: message={message}, chat_id={chat_id}")

    if not message or not chat_id:
        print(f"⚠️ Thiếu message hoặc chat_id: message={message}, chat_id={chat_id}")
        return jsonify({"error": "Thiếu message hoặc chat_id"}), 400

    add_message_to_history('user', message, chat_id)
    question_data = {"message": message, "name_conversation": chat_id}
    save_question(question_data)
    print(f"✅ Đã lưu câu hỏi cho Kaggle: {question_data}")

    return jsonify({"message": "Câu hỏi đã được lưu cho Kaggle", "name_conversation": chat_id})

# API để Kaggle tải file questions.json
@app.route('/questions', methods=['GET'])
def get_questions_file():
    print(f"📖 [GET /questions] Yêu cầu từ {request.remote_addr} tại {datetime.now().isoformat()}")
    if os.path.exists(questions_file):
        print(f"📤 Gửi file questions.json")
        return send_file(questions_file, mimetype='application/json')
    print(f"⚠️ File questions.json không tồn tại")
    return jsonify({"error": "Không tìm thấy file câu hỏi"}), 404

# API để nhận câu trả lời từ Kaggle
@app.route('/receive_answer', methods=['POST'])
def receive_answer():
    try:
        data = request.json
        sender = data.get('sender', 'bot')
        message = data.get('message')
        name_conversation = data.get('name_conversation')
        print(f"📖 [POST /receive_answer] Yêu cầu từ {request.remote_addr}: {data}")

        if not message or not name_conversation:
            print(f"⚠️ Thiếu message hoặc name_conversation: message={message}, name_conversation={name_conversation}")
            return jsonify({"error": "Thiếu message hoặc name_conversation"}), 400
       
        chat_history = load_chat_history()
      
        if name_conversation not in chat_history:
            questions = load_questions()
            questions = [q for q in questions if q["name_conversation"] != name_conversation]
            try:
                with open(questions_file, 'w', encoding='utf-8') as file:
                    json.dump(questions, file, indent=2, ensure_ascii=False)
                print(f"✅ Đã xóa câu hỏi với name_conversation: {name_conversation}")
            except Exception as e:
                print(f"⚠️ Lỗi khi xóa câu hỏi: {e}")
            return jsonify({
                "status": "ok",
                "message": "Cuộc trò chuyện không tồn tại và đã được xóa."
            })
       
        chat_history[name_conversation]['messages'] = [
            msg for msg in chat_history[name_conversation]['messages']
            if msg['text'] != 'Đang chờ phản hồi từ Kaggle...'
        ]
        if not any(msg['text'] == message and msg['className'] == 'user-message' for msg in chat_history[name_conversation]['messages']):
            add_message_to_history(sender, message, name_conversation)
        else:
            print(f"⏩ Bỏ qua tin nhắn trùng lặp từ Kaggle: {message}")
       
        questions = load_questions()
        questions = [q for q in questions if q["name_conversation"] != name_conversation]
        try:
            with open(questions_file, 'w', encoding='utf-8') as file:
                json.dump(questions, file, indent=2, ensure_ascii=False)
            print(f"✅ Đã xóa câu hỏi với name_conversation: {name_conversation}")
        except Exception as e:
            print(f"⚠️ Lỗi khi xóa câu hỏi: {e}")

        return jsonify({
            "status": "ok",
            "message": message,
            "conversation_name": name_conversation
        })
    except Exception as e:
        print(f"⚠️ Lỗi khi nhận câu trả lời: {str(e)}")
        return jsonify({"error": f"Đã xảy ra lỗi: {str(e)}"}), 500


# API để nhận tin nhắn từ frontend
@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.json
        message = data.get('message')
        chat_id = data.get('chatId', generate_uuid())
        print(f"📖 [POST /chatbot] Yêu cầu từ {request.remote_addr}: message={message}, chatId={chat_id}")

        if not message:
            print(f"⚠️ Không có message được cung cấp")
            return jsonify({"error": "Không có message được cung cấp"}), 400

        chat_history = load_chat_history()
        if chat_id in chat_history and any(msg['text'] == message and msg['className'] == 'user-message' for msg in chat_history[chat_id]["messages"]):
            print(f"⏩ Câu hỏi trùng lặp: {message} (chatId: {chat_id})")
            return jsonify({"reply": "Đang chờ phản hồi từ..."})
        prompt, error = process_question(message, chat_id)
        if error:
            print(f"⚠️ Lỗi từ process_question: {error}")
            return jsonify({"error": error}), 500
        
        add_message_to_history('user', message, chat_id)
        question_data = {"message": prompt, "name_conversation": chat_id}
        save_question(question_data)
        print(f"✅ Đã lưu câu hỏi cho Kaggle: {message} (chatId: {chat_id})")
        return jsonify({"reply": "Đang chờ phản hồi từ ..."})
    except Exception as e:
        print(f"⚠️ Lỗi khi xử lý /chatbot: {str(e)}")
        return jsonify({"error": f"Yêu cầu đến Kaggle thất bại: {str(e)}"}), 500

# API để lấy tất cả các đoạn hội thoại
@app.route('/chats', methods=['GET'])
def get_chats():
    print(f"📖 [GET /chats] Yêu cầu từ {request.remote_addr} tại {datetime.now().isoformat()}")
    chat_history = load_chat_history()
    chats = [
        {"chatId": chat_id, "title": chat["title"], "messages": chat["messages"]}
        for chat_id, chat in chat_history.items()
    ]
    print(f"📤 Trả về {len(chats)} hội thoại")
    return jsonify(chats)

# API để lấy tin nhắn của một đoạn hội thoại cụ thể
@app.route('/chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    print(f"📖 [GET /chat/{chat_id}] Yêu cầu từ {request.remote_addr} tại {datetime.now().isoformat()}")
    chat_history = load_chat_history()
    if chat_id not in chat_history:
        print(f"⚠️ Chat ID {chat_id} không tồn tại trong chat_history.json")
        return jsonify({"error": "Không tìm thấy hội thoại"}), 404
    print(f"📤 Trả về dữ liệu cho chatId {chat_id}: {chat_history[chat_id]}")
    return jsonify(chat_history[chat_id])

# API để tạo đoạn hội thoại mới
@app.route('/chat/new', methods=['POST'])
def new_chat():
    chat_id = generate_uuid()
    chat_history = load_chat_history()
    chat_history[chat_id] = {
        "title": f"Chat {len(chat_history) + 1}",
        "messages": []
    }
    save_chat_history(chat_history)
    print(f"✅ Tạo hội thoại mới: chatId={chat_id}")
    return jsonify({"chatId": chat_id})

# API để xóa một đoạn hội thoại
@app.route('/chat/delete', methods=['POST'])
def delete_chat():
    try:
        data = request.json
        chat_id = data.get('chatId')
        print(f"📖 [POST /chat/delete] Yêu cầu từ {request.remote_addr}: chatId={chat_id}")
        if not chat_id:
            print(f"⚠️ Yêu cầu chatId không được cung cấp")
            return jsonify({"error": "Yêu cầu chatId"}), 400

        chat_history = load_chat_history()
        if chat_id not in chat_history:
            print(f"⚠️ Chat ID {chat_id} không tồn tại")
            return jsonify({"error": "Không tìm thấy hội thoại"}), 404

        del chat_history[chat_id]
        save_chat_history(chat_history)
        print(f"✅ Đã xóa hội thoại: chatId={chat_id}")
        return jsonify({"message": "Hội thoại đã được xóa thành công"})
    except Exception as e:
        print(f"⚠️ Lỗi khi xóa hội thoại: {str(e)}")
        return jsonify({"error": f"Đã xảy ra lỗi: {str(e)}"}), 500

@app.route('/config.json')
def serve_config():
    return send_file('config.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)