import logging
from telegram import ChatMember
import config

logger = logging.getLogger(__name__)

async def check_channel_subscription(bot, user_id):
    """
    Foydalanuvchi kanalga obuna bo'lganligini tekshiradi
    """
    try:
        # Admin uchun tekshiruv o'tkazilmaydi
        if user_id == config.ADMIN_ID:
            return True
            
        chat_member = await bot.get_chat_member(
            chat_id=f"@{config.CHANNEL_USERNAME}",
            user_id=user_id
        )
        
        if chat_member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        ]:
            return True
        
        logger.info(f"User {user_id} not subscribed to channel. Status: {chat_member.status}")
        return False
        
    except Exception as e:
        logger.error(f"Error checking channel subscription for user {user_id}: {e}")
        return False