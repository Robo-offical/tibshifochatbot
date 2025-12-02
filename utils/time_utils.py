from datetime import datetime, timedelta
import pytz
import logging
import config

logger = logging.getLogger(__name__)

def get_current_time(timezone="Asia/Tashkent"):
    """Joriy vaqtni olish"""
    tz = pytz.timezone(timezone)
    return datetime.now(tz)

def format_time(date_time, format_str="%Y-%m-%d %H:%M:%S"):
    """Vaqtni formatlash"""
    return date_time.strftime(format_str)

def is_working_hours(start_hour=9, end_hour=18):
    """Ish vaqtida ekanligini tekshirish"""
    current_time = get_current_time()
    current_hour = current_time.hour
    return start_hour <= current_hour < end_hour

def get_working_hours_message():
    """Ish vaqtlari haqida xabar"""
    if is_working_hours():
        return "✅ Hozir ish vaqti. Tez orada javob olasiz."
    else:
        return "⚠️ Hozir ish vaqti emas. Adminlar 09:00 dan 18:00 gacha javob beradi."

def get_response_time_estimate():
    """Javob berish vaqtini taxmin qilish"""
    if is_working_hours():
        return "⏰ Taxminiy javob vaqti: 1 soat ichida"
    else:
        return "⏰ Taxminiy javob vaqti: Ertaga 09:00 dan keyin"