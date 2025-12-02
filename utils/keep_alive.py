import threading
import time
import requests
import logging
from flask import Flask
import config

logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def home():
    return "Tib Shifo Support Bot ishlamoqda  ✅"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/status')
def status():
    return {
        "status": "online",
        "service": "tibshifo-support-bot",
        "port": config.PORT,
        "timestamp": time.time()
    }

def run_flask():
    """Flask serverini ishga tushirish"""
    logger.info(f"Flask server {config.PORT} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=config.PORT, debug=False, use_reloader=False)

def keep_alive_ping():
    """Keep alive so'rovlarni yuborish"""
    if not config.KEEP_ALIVE_URL:
        logger.warning("KEEP_ALIVE_URL sozlanmagan")
        return
    
    while True:
        try:
            response = requests.get(config.KEEP_ALIVE_URL, timeout=10)
            logger.info(f"Keep alive so'rovi: {response.status_code}")
        except Exception as e:
            logger.error(f"Keep alive xatosi: {e}")
        
        time.sleep(config.POLLING_INTERVAL)

def start_keep_alive():
    """Keep aliveni ishga tushirish"""
    # Flask serverini background threadda ishga tushirish
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"Flask server {config.PORT} portda ishga tushdi")
    
    # Keep alive ping thread
    if config.KEEP_ALIVE_URL:
        ping_thread = threading.Thread(target=keep_alive_ping, daemon=True)
        ping_thread.start()
        logger.info("Keep alive ishga tushdi")