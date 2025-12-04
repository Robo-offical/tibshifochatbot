import logging
from telegram import ChatMember
import config

logger = logging.getLogger(__name__)

async def check_channel_subscription(bot, user_id):
    """
    Foydalanuvchi BARCHA kanallarga obuna bo'lganligini tekshiradi
    """
    try:
        # Admin uchun tekshiruv o'tkazilmaydi
        if user_id == config.ADMIN_ID:
            return True
            
        # HAR BIR KANALNI TEKSHIRAMIZ
        for channel in config.CHANNEL_USERNAMES:
            try:
                chat_member = await bot.get_chat_member(
                    chat_id=f"@{channel}",
                    user_id=user_id
                )
                
                if chat_member.status in [
                    ChatMember.MEMBER,
                    ChatMember.ADMINISTRATOR,
                    ChatMember.OWNER
                ]:
                    continue  # Bu kanalga obuna bo'lgan, keyingisiga o't
                else:
                    logger.info(f"User {user_id} {channel} kanaliga obuna emas. Status: {chat_member.status}")
                    return False  # Obuna emas
                    
            except Exception as e:
                logger.error(f"Error checking channel {channel} for user {user_id}: {e}")
                return False  # Xatolik bo'lsa ham obuna deb hisoblamaymiz
        
        # Agar barcha kanallarga obuna bo'lsa
        return True
        
    except Exception as e:
        logger.error(f"Error checking channel subscription for user {user_id}: {e}")
        return False