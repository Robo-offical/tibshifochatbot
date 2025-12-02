from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import config
import logging
from utils.database import (
    add_user, add_request, get_user_requests, 
    update_user_activity, get_user_by_id
)
from utils.channel_check import check_channel_subscription
from utils.time_utils import (
    get_current_time, format_time, 
    get_working_hours_message, get_response_time_estimate
)
from handlers.admin_handlers import ADMIN_KEYBOARD

logger = logging.getLogger(__name__)

# REPLY KEYBOARD tugmalari
USER_KEYBOARD = ReplyKeyboardMarkup([
    ["📨 Murojaat yuborish"],
    ["📋 Mening so'rovlarim"],
    ["🕐 Ish vaqtlari", "ℹ️ Yordam"]
], resize_keyboard=True, one_time_keyboard=False)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi - kanalga obuna bo'lishni tekshiradi"""
    user = update.effective_user
    
    # Foydalanuvchi faolligini yangilash
    update_user_activity(user.id)
    
    # Kanalga obuna bo'lishni tekshirish
    is_subscribed = await check_channel_subscription(context.bot, user.id)
    
    if not is_subscribed:
        await update.message.reply_text(
            f"👋 Salom {user.first_name}!\n\n"
            f"❌ Botdan foydalanish uchun quyidagi kanalga obuna bo'lishingiz kerak:\n"
            f"👉 @{config.CHANNEL_USERNAME}\n\n"
            f"✅ Obuna bo'lgach, /start buyrug'ini qayta yuboring.\n\n"
            f"📢 Kanal linki: https://t.me/{config.CHANNEL_USERNAME}",
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
        return
    
    # Foydalanuvchini bazaga qo'shish yoki yangilash
    add_user(user.id, user.username, user.first_name, user.last_name)
    
    current_time = get_current_time()
    time_str = format_time(current_time)
    
    # Admin yoki oddiy foydalanuvchi uchun keyboard
    if user.id == config.ADMIN_ID:
        await update.message.reply_text(
            f"👑 Salom {user.first_name}! Admin paneliga xush kelibsiz!\n\n"
            f"📅 Joriy vaqt: {time_str}\n"
            f"⏰ {get_working_hours_message()}\n\n"
            f"🛠️ Pastdagi tugmalardan foydalaning yoki komandalar:\n"
            f"• /admin - Admin panel\n"
            f"• /myrequests - So'rovlarim\n"
            f"• /time - Vaqt va ish soatlari",
            reply_markup=ADMIN_KEYBOARD
        )
    else:
        # Oddiy foydalanuvchining oldingi so'rovlari soni
        user_requests = get_user_requests(user.id)
        request_count = len(user_requests) if user_requests else 0
        
        welcome_text = (
            f"👋 Salom {user.first_name}! Manga support botiga xush kelibsiz!\n\n"
            f"📅 Joriy vaqt: {time_str}\n"
            f"⏰ {get_working_hours_message()}\n\n"
        )
        
        if request_count > 0:
            # So'rovlari bor foydalanuvchi uchun
            pending_count = sum(1 for req in user_requests if req[3] == 'pending')
            completed_count = sum(1 for req in user_requests if req[3] == 'completed')
            
            welcome_text += (
                f"📊 Sizning statistikangiz:\n"
                f"• 📨 Umumiy so'rovlar: {request_count}\n"
                f"• ⏳ Kutayotgan: {pending_count}\n"
                f"• ✅ Yakunlangan: {completed_count}\n\n"
            )
        else:
            # Yangi foydalanuvchi uchun
            welcome_text += (
                f"🎉 Siz yangi foydalanuvchisiz!\n"
                f"Birinchi so'rovingizni yuborish uchun pastdagi tugmani bosing.\n\n"
            )
        
        welcome_text += (
            f"🛠️ Pastdagi tugmalardan foydalaning yoki komandalar:\n"
            f"• /myrequests - So'rovlarim\n"
            f"• /time - Vaqt va ish soatlari\n"
            f"• /help - Yordam"
        )
        
        await update.message.reply_text(welcome_text, reply_markup=USER_KEYBOARD)

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vaqt va ish soatlari haqida ma'lumot"""
    user = update.effective_user
    
    # Foydalanuvchi faolligini yangilash
    update_user_activity(user.id)
    
    current_time = get_current_time()
    time_str = format_time(current_time)
    
    text = (
        f"🕐 Vaqt ma'lumotlari:\n\n"
        f"📅 Joriy vaqt: {time_str}\n"
        f"🌏 Vaqt zonasi: {config.TIMEZONE}\n"
        f"⏰ Ish vaqtlari: 09:00 - 18:00\n"
        f"📢 Kanal: @{config.CHANNEL_USERNAME}\n\n"
        f"{get_working_hours_message()}\n"
        f"{get_response_time_estimate()}\n\n"
        f"ℹ️ Eslatma: Adminlar ish vaqtlarida tezroq javob beradi."
    )
    
    keyboard = ADMIN_KEYBOARD if user.id == config.ADMIN_ID else USER_KEYBOARD
    await update.message.reply_text(text, reply_markup=keyboard)

async def myrequests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchining so'rovlari"""
    user = update.effective_user
    
    # Foydalanuvchi faolligini yangilash
    update_user_activity(user.id)
    
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
    
    keyboard = ADMIN_KEYBOARD if user.id == config.ADMIN_ID else USER_KEYBOARD
    await update.message.reply_text(text, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam komandasi"""
    user = update.effective_user
    
    # Foydalanuvchi faolligini yangilash
    update_user_activity(user.id)
    
    text = (
        f"ℹ️ {user.first_name}, bot yordami:\n\n"
        
        f"📌 ASOSIY FUNKSIYALAR:\n"
        f"1. '📨 Murojaat yuborish' - Manga haqida so'rov yuborish\n"
        f"2. '📋 Mening so'rovlarim' - Yuborgan so'rovlaringiz holati\n"
        f"3. '🕐 Ish vaqtlari' - Adminlar ish vaqtlari\n\n"
        
        f"📌 KOMANDALAR:\n"
        f"• /start - Botni qayta ishga tushirish\n"
        f"• /myrequests - So'rovlaringizni ko'rish\n"
        f"• /time - Joriy vaqtni bilish\n"
        f"• /help - Yordam\n"
        
        f"{'• /admin - Admin panel' if user.id == config.ADMIN_ID else ''}\n\n"
        
        f"📌 QO'LLANMA:\n"
        f"1. Avval @{config.CHANNEL_USERNAME} kanaliga obuna bo'ling\n"
        f"2. '📨 Murojaat yuborish' tugmasini bosing\n"
        f"3. Manga nomi, qism raqami yoki muammoingizni yozing\n"
        f"4. Adminlar so'rovingizni ko'rib chiqib javob beradi\n\n"
        
        f"📌 ESLATMALAR:\n"
        f"• Adminlar 09:00-18:00 orasida javob beradi\n"
        f"• Har bir so'rovga alohida javob beriladi\n"
        f"• So'rov holatini '📋 Mening so'rovlarim' dan kuzating\n"
        f"• Takroriy so'rov yubormaslikka harakat qiling"
    )
    
    keyboard = ADMIN_KEYBOARD if user.id == config.ADMIN_ID else USER_KEYBOARD
    await update.message.reply_text(text, reply_markup=keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi xabarlarini qayta ishlash"""
    user = update.effective_user
    message_text = update.message.text
    
    # Foydalanuvchi faolligini yangilash
    update_user_activity(user.id)
    
    # Kanalga obuna bo'lishni tekshirish
    is_subscribed = await check_channel_subscription(context.bot, user.id)
    
    if not is_subscribed:
        await update.message.reply_text(
            f"❌ {user.first_name}, kanalga obuna bo'lmagansiz!\n\n"
            f"Botdan foydalanish uchun quyidagi kanalga obuna bo'ling:\n"
            f"👉 @{config.CHANNEL_USERNAME}\n\n"
            f"✅ Obuna bo'lgach, /start buyrug'ini yuboring.\n"
            f"🔗 Link: https://t.me/{config.CHANNEL_USERNAME}",
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
        return
    
    # Reply keyboard orqali tanlov
    if message_text == "📨 Murojaat yuborish":
        context.user_data['waiting_for_request'] = True
        response_time = get_response_time_estimate()
        
        await update.message.reply_text(
            f"✍️ {user.first_name}, murojaatingiz matnini yozing:\n\n"
            f"📌 Masalan:\n"
            f"• 'One Piece manga 1050-qismi kerak'\n"
            f"• 'Naruto manga ingliz tilida'\n"
            f"• 'Attack on Titan oxirgi qismi'\n\n"
            f"⏰ {response_time}\n"
            f"🕐 Ish vaqtlari: 09:00 - 18:00\n\n"
            f"📝 Yorqin va aniq yozishingiz javob tezligini oshiradi!",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif message_text == "📋 Mening so'rovlarim":
        await myrequests_command(update, context)
    
    elif message_text == "🕐 Ish vaqtlari":
        await time_command(update, context)
    
    elif message_text == "ℹ️ Yordam":
        await help_command(update, context)
    
    # Admin funksiyalari (user_handlers.py da admin_handlers ni import qilmasdan)
    elif user.id == config.ADMIN_ID and message_text in [
        "📊 Statistika", "📢 Broadcast", "📋 Support", "🔍 Qidirish"
    ]:
        # Admin funksiyalari uchun alohida import
        from handlers.admin_handlers import (
            handle_support_panel, handle_admin_messages
        )
        
        if message_text == "📋 Support":
            await handle_support_panel(update, context)
        else:
            await handle_admin_messages(update, context)
    
    # Agar foydalanuvchi so'rov yuborish rejimida bo'lsa
    elif 'waiting_for_request' in context.user_data:
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
        
        # So'rovni bazaga saqlash
        request_id = add_request(user.id, message_text)
        
        # Guruhga yaxshiroq formatda xabar yuborish
        try:
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
        except Exception as e:
            logger.error(f"❌ Guruhga xabar yuborishda xatolik: {e}")
            # Guruhga yuborishda xatolik bo'lsa ham foydalanuvchiga xabar beramiz
        
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
    
    # Agar hech qaysi holatga to'g'ri kelmasa
    else:
        # Spam yoki notanish xabarlarga javob
        if len(message_text) > 1000:  # Uzun xabarlar
            await update.message.reply_text(
                "📝 Iltimos, xabaringizni qisqaroq qilib yozing.\n"
                "Yoki '📨 Murojaat yuborish' tugmasi orqali so'rov yuboring.",
                reply_markup=USER_KEYBOARD if user.id != config.ADMIN_ID else ADMIN_KEYBOARD
            )
        else:
            # Oddiy xabarlar uchun yordam berish
            keyboard = ADMIN_KEYBOARD if user.id == config.ADMIN_ID else USER_KEYBOARD
            
            await update.message.reply_text(
                f"👋 {user.first_name}! Pastdagi tugmalardan foydalaning:\n\n"
                f"• 📨 Murojaat yuborish - Yangi so'rov\n"
                f"• 📋 Mening so'rovlarim - Oldingi so'rovlar\n"
                f"• 🕐 Ish vaqtlari - Adminlar ish vaqtlari\n"
                f"• ℹ️ Yordam - Bot haqida ma'lumot\n\n"
                f"📝 Yordam kerak bo'lsa /help buyrug'idan foydalaning.",
                reply_markup=keyboard
            )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bekor qilish komandasi"""
    user = update.effective_user
    
    # Barcha rejimlarni tozalash
    for key in ['waiting_for_request', 'waiting_for_reply_id', 
                'waiting_for_reply_text', 'waiting_for_broadcast', 
                'waiting_for_search']:
        if key in context.user_data:
            del context.user_data[key]
    
    keyboard = ADMIN_KEYBOARD if user.id == config.ADMIN_ID else USER_KEYBOARD
    
    await update.message.reply_text(
        "✅ Barcha amallar bekor qilindi.\n"
        "Asosiy menyuga qaytdingiz.",
        reply_markup=keyboard
    )

def setup_user_handlers(application):
    """Foydalanuvchi handlerlarini sozlash"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("time", time_command))
    application.add_handler(CommandHandler("myrequests", myrequests_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))