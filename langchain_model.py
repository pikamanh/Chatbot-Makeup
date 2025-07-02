import json
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# File paths
CHAT_HISTORY_FILE = 'chat_history.json'
CONFIG_FILE = 'config.json'
# Hỗ trợ cả máy cục bộ và Kaggle
PDF_PATH = os.getenv('PDF_PATH', '/kaggle/working/Makeup.pdf' if os.path.exists('/kaggle/working/') else '/Users/nguyenvokhang/Downloads/Webchatbot/Trang_diem_tiep_vien_hang_khong.pdf')
print(f"PDF Path: {PDF_PATH}")

def load_ngrok_url():
    """Đọc NGROK_URL từ config.json."""
    try:
        if not os.path.exists(CONFIG_FILE):
            print(f"⚠️ File {CONFIG_FILE} does not exist, using default URL")
            return 'http://localhost:5001'
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        ngrok_url = config.get('NGROK_URL', 'http://localhost:5001')
        print(f"✅ Loaded NGROK_URL: {ngrok_url}")
        return ngrok_url
    except Exception as e:
        print(f"⚠️ Error loading NGROK_URL from {CONFIG_FILE}: {e}")
        return 'http://localhost:5001'

def load_conversation_history(chat_id):
    """Đọc lịch sử hội thoại cho chat_id từ chat_history.json."""
    try:
        if not os.path.exists(CHAT_HISTORY_FILE):
            print(f"⚠️ File {CHAT_HISTORY_FILE} does not exist, returning empty history")
            return []
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        if chat_id not in history:
            print(f"⚠️ Chat ID {chat_id} not found in {CHAT_HISTORY_FILE}")
            return []
        # Chuyển đổi lịch sử thành định dạng LangChain: list of (question, answer)
        chat_history = []
        user_messages = [msg for msg in history[chat_id]['messages'] if msg['className'] == 'user-message']
        model_messages = [msg for msg in history[chat_id]['messages'] if msg['className'] == 'model-message']
        for i, user_msg in enumerate(user_messages):
            answer = model_messages[i]['text'] if i < len(model_messages) else ''
            chat_history.append((user_msg['text'], answer))
        print(f"✅ Loaded {len(chat_history)} messages for chat_id: {chat_id}")
        return chat_history
    except Exception as e:
        print(f"⚠️ Error loading conversation history: {e}")
        return []

def load_pdf(pdf_path=PDF_PATH):
    """Tải và trích xuất nội dung từ file PDF."""
    try:
        if not os.path.exists(pdf_path):
            print(f"⚠️ PDF file {pdf_path} does not exist")
            return []
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        if not documents:
            print(f"⚠️ No content extracted from {pdf_path}")
            return []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)
        print(f"✅ Loaded {len(split_docs)} chunks from {pdf_path}")
        return split_docs
    except Exception as e:
        print(f"⚠️ Error loading PDF: {e}")
        return []

def create_vector_store(documents):
    """Tạo vector store từ nội dung PDF."""
    try:
        if not documents:
            print("⚠️ No documents provided for vector store")
            return None
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")
        vector_store = FAISS.from_documents(documents, embeddings)
        print("✅ Created FAISS vector store")
        return vector_store
    except Exception as e:
        print(f"⚠️ Error creating vector store: {e}")
        return None

def process_question(question, chat_id, pdf_path=PDF_PATH):
    """Tạo prompt với ngữ cảnh từ PDF và lịch sử hội thoại."""
    try:
        chat_history = load_conversation_history(chat_id)
        documents = load_pdf(pdf_path)
        if not documents:
            print("⚠️ Returning error due to failed PDF loading")
            return "Error: Could not load PDF content.", None

        vector_store = create_vector_store(documents)
        if not vector_store:
            print("⚠️ Returning error due to failed vector store creation")
            return "Error: Could not create vector store.", None

        # Tạo prompt với ngữ cảnh từ lịch sử và PDF
        history_text = ""
        for q, a in chat_history:
            history_text += f"User: {q}\nBot: {a}\n"
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        relevant_docs = retriever.get_relevant_documents(question)
        context = "\n".join([doc.page_content for doc in relevant_docs])
        
        prompt = f"<s>[INST] Context from PDF:\n{context}\n\nConversation history:\n{history_text}\nUser: {question}\n[/INST]"
        print(f"✅ Created prompt for question: {question}")
        return prompt, None
    except Exception as e:
        print(f"⚠️ Error processing question: {e}")
        return f"Error: {str(e)}", None