import os
from datetime import datetime

# Bot tokeni
BOT_TOKEN = "5842293465:AAEasAFWH-bDGme7Ul08rGjK80lHrwf7zUw"

# Admin va guruh IDlari
ADMIN_ID = 5796033703
GROUP_ID = -1003204703868

# Kanal sozlamalari - IKKITA KANAL QO'SHING
CHANNEL_USERNAMES = ["tibshifouz", "pulsecare"]  # 🔥 YANGILANDI - array formatda

# Ma'lumotlar bazasi
DATABASE_NAME = "tibshifo_support.db"

# Keep alive sozlamalari
KEEP_ALIVE_URL = os.getenv("RENDER_EXTERNAL_URL", "")
HEALTH_CHECK_INTERVAL = 180
POLLING_INTERVAL = 270
PORT = int(os.getenv("PORT", 10000))

# Vaqt zonasi
TIMEZONE = "Asia/Tashkent"

# Javob berish vaqti (soat)
WORKING_HOURS = {
    "start": 9,
    "end": 18
}