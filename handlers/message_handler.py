from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, MessageHandler, filters
import config
import logging
from utils.database import update_user_activity, add_request, get_user_requests
from utils.time_utils import get_current_time, format_time, get_response_time_estimate, get_working_hours_message
from utils.channel_check import check_channel_subscription
from handlers.user_handlers import USER_KEYBOARD
from handlers.admin_handlers import ADMIN_KEYBOARD, handle_admin_messages as admin_handle_messages

logger = logging.getLogger(__name__)

async def route_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xabarlarni admin/user ga yo'naltiradi"""
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"📩 Yangi xabar: {user.id} - {message_text}")
    
    # Foydalanuvchi faolligini yangilash
    update_user_activity(user.id)
    
    # 1. AVVAL context.user_data ni tekshirish (BARCHA HOLATLAR UCHUN)
    if 'waiting_for_request' in context.user_data:
        await handle_user_request(update, context, user, message_text)
        return
    
    # Admin holatlarini tekshirish
    if user.id == config.ADMIN_ID:
        if any(key in context.user_data for key in [
            'waiting_for_broadcast', 'waiting_for_search', 
            'waiting_for_reply_id', 'waiting_for_reply_text'
        ]):
            await admin_handle_messages(update, context)
            return
    
    # 2. KEYIN admin/user tugmalarini tekshirish
    if user.id == config.ADMIN_ID:
        await admin_handle_messages(update, context)
    else:
        await handle_user_message(update, context, user, message_text)

async def handle_user_request(update: Update, context: ContextTypes.DEFAULT_TYPE, user, message_text):
    """Foydalanuvchi so'rovini qayta ishlash"""
    logger.info(f"📝 So'rov yuborilmoqda: {user.id}")
    
    # Kanalga obuna bo'lishni tekshirish
    is_subscribed = await check_channel_subscription(context.bot, user.id)
    
    if not is_subscribed:
        await update.message.reply_text(
            f"❌ {user.first_name}, kanalga obuna bo'lmagansiz!\n\n"
            f"Botdan foydalanish uchun quyidagi kanallarning BARCHASIGA obuna bo'ling:\n"
            f"• @{config.CHANNEL_USERNAMES[0]}\n"
            f"• @{config.CHANNEL_USERNAMES[1]}\n\n"
            f"✅ Ikkala kanalga ham obuna bo'lgach, qayta urining.",
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
        del context.user_data['waiting_for_request']
        return
    
    # Xabar uzunligini tekshirish
    if len(message_text) < 5:
        await update.message.reply_text(
            "❌ Xabar juda qisqa! Iltimos, kamida 5 ta belgidan iborat bo'lsin.\n"
            "Qaytadan yozing:"
        )
        return
    
    if len(message_text) > 2000:
        await update.message.reply_text(
            "❌ Xabar juda uzun! Iltimos, 2000 ta belgidan oshmasligi kerak.\n"
            "Qaytadan qisqaroq yozing:"
        )
        return
    
    try:
        # So'rovni bazaga saqlash
        from utils.database import add_request
        request_id = add_request(user.id, message_text)
        logger.info(f"✅ So'rov saqlandi: #{request_id}")
        
        # Guruhga yuborish
        await context.bot.send_message(
            chat_id=config.GROUP_ID,
            text=f"🆕 YANGI SO'ROV #{request_id}\n\n"
                 f"👤 Foydalanuvchi: @{user.username or user.first_name}\n"
                 f"🆔 User ID: {user.id}\n"
                 f"📱 Username: @{user.username or 'Yoq'}\n"
                 f"📅 Vaqt: {format_time(get_current_time())}\n\n"
                 f"📝 XABAR:\n{message_text}\n\n"
                 f"✏️ JAVOB BERISH:\n"
                 f"/reply {request_id} [javob matni]\n\n"
                 f"📄 SO'ROV MA'LUMOTI:\n"
                 f"/requestinfo {request_id}\n\n"
                 f"📋 BARCHA SO'ROVLAR:\n"
                 f"/allrequests",
            disable_web_page_preview=True
        )
        logger.info(f"✅ Guruhga yuborildi: #{request_id}")
        
    except Exception as e:
        logger.error(f"❌ Guruhga xabar yuborishda xatolik: {e}")
    
    # Foydalanuvchiga tasdiqlash
    response_time = get_response_time_estimate()
    
    keyboard = ADMIN_KEYBOARD if user.id == config.ADMIN_ID else USER_KEYBOARD
    
    await update.message.reply_text(
        f"✅ {user.first_name}, murojaatingiz qabul qilindi!\n\n"
        f"📨 So'rov raqami: #{request_id}\n"
        f"⏰ {response_time}\n"
        f"📊 Holat: ⏳ Kutayotgan\n\n"
        f"📌 So'rov holatini '📋 Mening so'rovlarim' tugmasi orqali kuzatishingiz mumkin.\n"
        f"📞 Adminlar tez orada siz bilan bog'lanishadi.",
        reply_markup=keyboard
    )
    
    # Rejimni tozalash
    del context.user_data['waiting_for_request']
    logger.info(f"✅ So'rov tugatildi: #{request_id}")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user, message_text):
    """Oddiy foydalanuvchi xabarlarini qayta ishlash"""
    logger.info(f"👤 Foydalanuvchi xabari: {user.id} - {message_text}")
    
    # Kanalga obuna bo'lishni tekshirish
    is_subscribed = await check_channel_subscription(context.bot, user.id)
    
    if not is_subscribed:
        await update.message.reply_text(
            f"❌ {user.first_name}, kanalga obuna bo'lmagansiz!\n\n"
            f"Botdan foydalanish uchun quyidagi kanallarning BARCHASIGA obuna bo'ling:\n"
            f"• @{config.CHANNEL_USERNAMES[0]}\n"
            f"• @{config.CHANNEL_USERNAMES[1]}\n\n"
            f"✅ Ikkala kanalga ham obuna bo'lgach, /start buyrug'ini yuboring.\n"
            f"🔗 Linklar:\n"
            f"• https://t.me/{config.CHANNEL_USERNAMES[0]}\n"
            f"• https://t.me/{config.CHANNEL_USERNAMES[1]}",
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
        return
    
    # Reply keyboard orqali tanlov - ASOSIY TUGMALAR
    if message_text == "📨 Murojaat yuborish":
        context.user_data['waiting_for_request'] = True
        response_time = get_response_time_estimate()
        
        await update.message.reply_text(
            f"✍️ {user.first_name}, murojaatingiz matnini yozing:\n\n"
            f"📌 Masalan:\n"
            f"• 'murojat yuboruvchini qiziqtirgan savollar'\n"
            f"• 'Kanal qanday materiallar beradi?'\n"
            f"• 'boshqa tibbiyotga oid savollar'\n\n"
            f"⏰ {response_time}\n"
            f"🕐 Ish vaqtlari: 08:00 - 23:00\n\n"
            f"📝 Yorqin va aniq yozishingiz javob tezligini oshiradi!",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"📝 So'rov rejimi: {user.id}")
    
    elif message_text == "📋 Mening so'rovlarim":
        await show_user_requests(update, context, user)
    
    elif message_text == "🕐 Ish vaqtlari":
        await show_working_hours(update, context, user)
    
    elif message_text == "ℹ️ Yordam":
        await show_help(update, context, user)
    
    else:
        # Agar hech qaysi holatga to'g'ri kelmasa
        if len(message_text) > 1000:
            await update.message.reply_text(
                "📝 Iltimos, xabaringizni qisqaroq qilib yozing.\n"
                "Yoki '📨 Murojaat yuborish' tugmasi orqali so'rov yuboring.",
                reply_markup=USER_KEYBOARD
            )
        else:
            await update.message.reply_text(
                f"👋 {user.first_name}! Pastdagi tugmalardan foydalaning:\n\n"
                f"• 📨 Murojaat yuborish - Yangi so'rov\n"
                f"• 📋 Mening so'rovlarim - Oldingi so'rovlar\n"
                f"• 🕐 Ish vaqtlari - Adminlar ish vaqtlari\n"
                f"• ℹ️ Yordam - Bot haqida ma'lumot\n\n"
                f"📝 Yordam kerak bo'lsa /help buyrug'idan foydalaning.",
                reply_markup=USER_KEYBOARD
            )

async def show_user_requests(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """Foydalanuvchining so'rovlarini ko'rsatish"""
    from utils.database import get_user_requests
    
    requests = get_user_requests(user.id)
    
    if not requests:
        text = (
            f"📭 {user.first_name}, sizning hozircha so'rovlaringiz yo'q.\n\n"
            f"➕ Yangi so'rov yuborish uchun '📨 Murojaat yuborish' tugmasini bosing."
        )
    else:
        text = f"📋 {user.first_name}, sizning so'rovlaringiz ({len(requests)} ta):\n\n"
        
        for req in requests:
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅'
            }.get(req[3], '❓')
            
            text += f"{status_emoji} So'rov #{req[0]}:\n"
            text += f"📝 {req[2][:100]}...\n"
            text += f"📊 Holat: {req[3]}\n"
            text += f"📅 Sana: {req[5]}\n"
            
            # Agar javob berilgan bo'lsa
            if req[3] == 'completed' and req[6]:  # admin_reply maydoni
                text += f"📩 Admin javobi: {req[6][:150]}...\n"
            
            text += "─" * 25 + "\n"
        
        # Statistik ma'lumot
        pending = sum(1 for r in requests if r[3] == 'pending')
        completed = sum(1 for r in requests if r[3] == 'completed')
        
        text += f"\n📊 Statistikangiz:\n"
        text += f"• ⏳ Kutayotgan: {pending}\n"
        text += f"• ✅ Yakunlangan: {completed}\n"
        text += f"• 📨 Umumiy: {len(requests)}\n\n"
        text += f"➕ Yangi so'rov: '📨 Murojaat yuborish'"
    
    await update.message.reply_text(text, reply_markup=USER_KEYBOARD)
    logger.info(f"📋 So'rovlar ko'rsatildi: {user.id}")

async def show_working_hours(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """Ish vaqtlari haqida ma'lumot"""
    current_time = get_current_time()
    time_str = format_time(current_time)
    
    text = (
        f"🕐 Vaqt ma'lumotlari:\n\n"
        f"📅 Joriy vaqt: {time_str}\n"
        f"🌏 Vaqt zonasi: {config.TIMEZONE}\n"
        f"⏰ Ish vaqtlari: 09:00 - 18:00\n"
        f"⏰ 18:00 dan keyin ham soat 23:00gacha yozishingiz mumkin."
        f"📢 Kanallar: @{config.CHANNEL_USERNAMES[0]}, @{config.CHANNEL_USERNAMES[1]}\n\n"
        f"{get_working_hours_message()}\n"
        f"{get_response_time_estimate()}\n\n"
        f"ℹ️ Eslatma: Adminlar ish vaqtlarida tezroq javob beradi."
    )
    
    keyboard = ADMIN_KEYBOARD if user.id == config.ADMIN_ID else USER_KEYBOARD
    await update.message.reply_text(text, reply_markup=keyboard)
    logger.info(f"🕐 Ish vaqtlari ko'rsatildi: {user.id}")

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """Yordam ma'lumotlari"""
    text = (
        f"ℹ️ {user.first_name}, @aisroilov support bot yordami:\n\n"
        
        f"📌 ASOSIY FUNKSIYALAR:\n"
        f"1. '📨 Murojaat yuborish' - Kanallar haqida yoki boshqa masalada so'rov yuborish\n"
        f"2. '📋 Mening so'rovlarim' - Yuborgan so'rovlaringiz holati\n"
        f"3. '🕐 Ish vaqtlari' - Adminlar ish vaqtlari\n\n"
        
        f"📌 KOMANDALAR:\n"
        f"• /start - Botni qayta ishga tushirish\n"
        f"• /myrequests - So'rovlaringizni ko'rish\n"
        f"• /time - Joriy vaqtni bilish\n"
        f"• /help - Yordam\n"
        
        f"{'• /admin - Admin panel' if user.id == config.ADMIN_ID else ''}\n\n"
        
        f"📌 QO'LLANMA:\n"
        f"1. Avval @{config.CHANNEL_USERNAMES[0]} va @{config.CHANNEL_USERNAMES[1]} kanallariga obuna bo'ling\n"
        f"2. '📨 Murojaat yuborish' tugmasini bosing\n"
        f"3. kanal yoki boshqa masaladagi so'rovingizni yozing\n"
        f"4. Adminlar so'rovingizni ko'rib chiqib javob beradi\n\n"
        
        f"📌 ESLATMALAR:\n"
        f"• Adminlar 09:00-18:00 orasida javob beradi\n"
        f"• Har bir so'rovga alohida javob beriladi\n"
        f"• So'rov holatini '📋 Mening so'rovlarim' dan kuzating\n"
        f"• Takroriy so'rov yubormaslikka harakat qiling"
    )
    
    keyboard = ADMIN_KEYBOARD if user.id == config.ADMIN_ID else USER_KEYBOARD
    await update.message.reply_text(text, reply_markup=keyboard)
    logger.info(f"ℹ️ Yordam ko'rsatildi: {user.id}")

# setup_message_handlers funksiyasini O'CHIRAMIZ - endi asosiy main.py da