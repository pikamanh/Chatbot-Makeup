import os
import json
import sys
from flask_api import app

PORT = 5001
CONFIG_FILE = 'config.json'
PDF_PATH = os.getenv('PDF_PATH', '/kaggle/working/Makeup.pdf' if os.path.exists('/kaggle/working/') else '/Users/nguyenvokhang/Downloads/Webchatbot/Trang_diem_tiep_vien_hang_khong.pdf')

def save_ngrok_url(url):
    config = {'NGROK_URL': url if url else 'http://localhost:5001'}
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved ngrok URL to {CONFIG_FILE}")
    except Exception as e:
        print(f"⚠️ Error saving ngrok URL: {e}")

def load_ngrok_url():
    try:
        if not os.path.exists(CONFIG_FILE):
            print(f"⚠️ {CONFIG_FILE} not found, using default URL")
            return 'http://localhost:5001'
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"⚠️ {CONFIG_FILE} is empty, using default URL")
                return 'http://localhost:5001'
            config = json.loads(content)
        ngrok_url = config.get('NGROK_URL', 'http://localhost:5001')
        print(f"✅ Loaded NGROK_URL: {ngrok_url}")
        return ngrok_url
    except json.JSONDecodeError as e:
        print(f"⚠️ Invalid JSON in {CONFIG_FILE}: {e}, using default URL")
        return 'http://localhost:5001'
    except Exception as e:
        print(f"⚠️ Error loading NGROK_URL from {CONFIG_FILE}: {e}")
        return 'http://localhost:5001'

def main(ngrok_url=None):
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF file {PDF_PATH} not found. Exiting...")
        return

    # Use provided ngrok_url or load from config.json
    if ngrok_url:
        print(f"✅ Using provided ngrok URL: {ngrok_url}")
        save_ngrok_url(ngrok_url)
    else:
        ngrok_url = load_ngrok_url()
        print(f"⚠️ No ngrok URL provided, using URL from config.json: {ngrok_url}")

    print(f"🚀 Starting Flask server on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=True)

if __name__ == '__main__':
    # Get ngrok URL from command-line argument or environment variable
    ngrok_url = "https://a56b-2401-d800-852-830f-8c0c-21d9-95ce-39d9.ngrok-free.app"
    if len(sys.argv) > 1:
        ngrok_url = sys.argv[1]
    elif os.getenv('NGROK_URL'):
        ngrok_url = os.getenv('NGROK_URL')
    main(ngrok_url)