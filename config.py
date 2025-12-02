import os
from datetime import datetime

# Bot tokeni
BOT_TOKEN = "8235666144:AAH84i_sC-8cWwEor9f_7u4OFn8qApDBfkE"

# Admin va guruh IDlari
ADMIN_ID_1 = 5796033703
ADMIN_ID = 7930827520
GROUP_ID = -1003204703868

# Kanal sozlamalari
CHANNEL_USERNAME = "tibshifouz"

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