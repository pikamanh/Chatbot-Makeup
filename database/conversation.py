import re

from load_database import *

class Conversation:
    def __init__(self):
        self.db = load_database('chatbot')
        self.cursor = self.db.cursor()
    
    def get_name_conversation(self, text):
        # Lấy 10 từ đầu làm tên conversation
        words = re.findall(r'\w+', text)
        print(' '.join(words[:10]))
        return ' '.join(words[:10])

    def get_or_create_conversation(self, name_conversation):
        self.cursor.execute("""
            SELECT id FROM conversations WHERE name = (%s)""", (name_conversation,))

        result = self.cursor.fetchone()

        if result is None:
            self.cursor.execute("INSERT INTO conversations (name) VALUES (%s)", (name_conversation,))
            self.db.commit()

            return self.cursor.lastrowid
        
        return result[0]
    
    def add_message(self, sender, message, name_conversation=None):
        if name_conversation is None:
            name_conversation = self.get_name_conversation(message)

        conversation_id = self.get_or_create_conversation(name_conversation)

        try:
            self.cursor.execute("INSERT INTO messages (conversation_id, sender, message) VALUES (%s, %s, %s)", (conversation_id, sender, message,))
            self.db.commit()

            print(f"✅Đã thêm thành công tin nhắn của {sender} vào messages.")
            return name_conversation
        except Exception as e:
            print("❌Thêm tin nhắn thất bại.")
            print(e)

    def get_history(self, name_conversation):
        self.cursor.execute("""
            SELECT messages.sender, messages.message FROM messages 
            JOIN conversations ON messages.conversation_id = conversations.id
            WHERE conversations.name = %s
            ORDER BY messages.id ASC
        """, (name_conversation,))
        return self.cursor.fetchall()
    
    def kaggle_history(self, name_conversation):
        self.cursor.execute("""
            SELECT messages.sender, messages.message FROM messages 
            JOIN conversations ON messages.conversation_id = conversations.id
            WHERE conversations.name = %s
            ORDER BY messages.id DESC
            LIMIT 9
        """, (name_conversation,))
        result = self.cursor.fetchall()
        return result[::-1]

    def get_last_context(self, name_conversation, num_turns=1):
        # Lấy n lượt gần nhất: mỗi lượt = user + bot
        limit = num_turns * 2
        self.cursor.execute("""
            SELECT messages.sender, messages.message FROM messages 
            JOIN conversations ON messages.conversation_id = conversations.id
            WHERE conversations.name = %s
            ORDER BY messages.id DESC LIMIT %s
        """, (name_conversation, limit))
        rows = self.cursor.fetchall()
        return list(reversed(rows))  # Đảo ngược để đúng thứ tự
    
    def get_all_conversation_names(self):
        self.cursor.execute("SELECT name FROM conversations ORDER BY id DESC")
        return [row[0] for row in self.cursor.fetchall()]