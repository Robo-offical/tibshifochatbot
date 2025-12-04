import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import BotCommand
import config
from utils.database import init_db
from utils.keep_alive import start_keep_alive
from handlers.user_handlers import setup_user_handlers
from handlers.admin_handlers import setup_admin_handlers
from handlers.message_handler import route_messages  # ✅ TO'G'RIDAN FUNKSIYANI IMPORT QILISH

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    """Bot ishga tushganda komandalarni sozlaydi"""
    commands = [
        BotCommand("start", "Botni ishga tushurish"),
        BotCommand("admin", "Admin panel (faqat adminlar uchun)"),
        BotCommand("myrequests", "Mening so'rovlarim"),
        BotCommand("time", "Joriy vaqt va ish soatlari"),
        BotCommand("help", "Tib Shifo Bot yordami"),
        BotCommand("cancel", "Bekor qilish"),
        BotCommand("reply", "Foydalanuvchiga javob berish"),
        BotCommand("requestinfo", "So'rov haqida ma'lumot"),
        BotCommand("allrequests", "Barcha so'rovlarni ko'rish"),
        BotCommand("admins", "Guruh adminlarini ko'rish"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    logger.info("Bot ishga tushmoqda...")
    
    try:
        application = Application.builder() \
            .token(config.BOT_TOKEN) \
            .post_init(post_init) \
            .build()

        init_db()
        
        # 🔥 MUHIM: HANDLERLAR TARTIBI
        # 1. BIRINCHI - Message handlerlarni qo'shamiz
        # BU eng BIRINCHI bo'lishi kerak, chunki u barcha xabarlarni qabul qiladi
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            route_messages
        ))
        
        # 2. Command handlerlarni sozlash
        setup_user_handlers(application)     # /start, /time, /myrequests, /help, /cancel
        setup_admin_handlers(application)    # /admin, /reply, /requestinfo, etc.

        start_keep_alive()

        logger.info(f"✅ Bot muvaffaqiyatli ishga tushdi (Port: {config.PORT})")
        logger.info(f"👑 Admin ID: {config.ADMIN_ID}")
        logger.info(f"👥 Guruh ID: {config.GROUP_ID}")
        logger.info(f"📢 Kanallar: {config.CHANNEL_USERNAMES}")
        
        application.run_polling(
            allowed_updates=["message"], 
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Bot ishga tushishda xatolik: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()