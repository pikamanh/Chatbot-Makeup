from flask import Flask, request, jsonify
from flask_cors import CORS
from  conversation import Conversation
from pyngrok import ngrok

app = Flask(__name__)
cors = CORS(app)

conv = Conversation()

@app.route("/add_message", methods=['POST'])
def add_message():
    data = request.json
    sender = data['sender']
    message = data['message']
    name_conv = data['name_conversation']

    name_conv = conv.add_message(sender, message, name_conv)
    return jsonify({"conversation_name": name_conv})

@app.route("/get_all_name_conversations", methods=['POST'])
def get_conversations():
    names = conv.get_all_conversation_names()
    return jsonify({"conversations": names})

@app.route("/get_history_conversation", methods=['POST'])
def get_history():
    data = request.json
    name_conv = data['name_conversation']

    history = conv.get_history(name_conv)

    return jsonify({'history': history})

@app.route("/get_context", methods=['POST'])
def get_context():
    data = request.json
    name_conv = data['name_conversation']

    context = conv.get_last_context(name_conv)
    return jsonify({'context': context})

if __name__ == '__main__':
    app.run(port=5000, debug=True)