import requests

class API:
    def __init__(self, ip_server):
        self.API_BASE = ip_server.rstrip('/')
        self.name_conv = None

    def receive_answer(self):
        try:
            response = requests.get(f"{self.API_BASE}/receive_answer")

            self.name_conv = response.json()["conversation_name"]
            message = response.json()["message"]
            return message, self.name_conv
        except Exception as e:
            print("❌ Lỗi khi gọi receive_answer:", e)
            return None

    def ask_model(self, message, name_conversation=None):
        try:
            response = requests.post(f"{self.API_BASE}/ask_model", json={
                "message": message,
                "name_conversation": name_conversation
            })

            self.name_conv = response.json()["conversation_name"]
            return self.name_conv
        except Exception as e:
            print("❌ Lỗi khi gọi ask_model:", e)
            return None

    def add_message(self, message, sender, name_conversation=None):
        try:
            response = requests.post(f"{self.API_BASE}/add_message", json={
                "sender": sender,
                "message": message,
                "name_conversation": name_conversation
            })
            response.raise_for_status()
            self.name_conv = response.json()["conversation_name"]
            return self.name_conv
        except Exception as e:
            print("❌ Lỗi khi gọi add_message:", e)
            return None

    def get_history_conversations(self, name_conversation):
        try:
            response = requests.post(f"{self.API_BASE}/get_history_conversation", json={
                "name_conversation": name_conversation
            })
            response.raise_for_status()
            return response.json()['history']
        except Exception as e:
            print("❌ Lỗi khi gọi get_history_conversations:", e)
            return []

    def get_last_context(self, name_conversation, num_turns=1):
        try:
            response = requests.post(f"{self.API_BASE}/get_context", json={
                "name_conversation": name_conversation,
                "num_turns": num_turns
            })
            response.raise_for_status()
            return response.json()['context']
        except Exception as e:
            print("❌ Lỗi khi gọi get_last_context:", e)
            return []
        
    def get_all_name_conversations(self):
        try:
            response = requests.post(f"{self.API_BASE}/get_all_name_conversations")
            names = response.json()['conversations']

            return names
        except Exception as e:
            print("❌ Lỗi khi gọi get_all_name_conversations:", e)
            return []