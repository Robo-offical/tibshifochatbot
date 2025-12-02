from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import config
import logging
from utils.database import (
    get_requests_by_status, update_request_status, 
    add_reply, get_request_details, get_all_users, search_user,
    is_group_member_admin, add_group_admin, get_group_admins,
    get_statistics, get_all_requests
)
import asyncio

logger = logging.getLogger(__name__)

# Admin reply keyboard
ADMIN_KEYBOARD = ReplyKeyboardMarkup([
    ["📨 Murojaat yuborish"],
    ["📊 Statistika", "📢 Broadcast"],
    ["📋 Support", "🔍 Qidirish"],
    ["📋 Mening so'rovlarim", "🕐 Ish vaqtlari"]
], resize_keyboard=True, one_time_keyboard=False)

# Support panel keyboard
SUPPORT_KEYBOARD = ReplyKeyboardMarkup([
    ["⏳ Kutayotgan so'rovlar", "🔄 Jarayondagilar"],
    ["✅ Yakunlangan so'rovlar", "📝 So'rovga javob berish"],
    ["⬅️ Orqaga"]
], resize_keyboard=True)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin komandasi"""
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    await update.message.reply_text(
        "👑 Admin Panel\nPastdagi tugmalardan foydalaning:",
        reply_markup=ADMIN_KEYBOARD
    )

async def handle_support_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Support panelini ko'rsatish"""
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        return
    
    # So'rovlarni holati bo'yicha olish
    pending = get_requests_by_status('pending')
    in_progress = get_requests_by_status('in_progress')
    completed = get_requests_by_status('completed')
    
    text = "📋 Support Panel\n\n"
    text += f"⏳ Kutayotgan: {len(pending)} ta\n"
    text += f"🔄 Jarayonda: {len(in_progress)} ta\n"
    text += f"✅ Yakunlangan: {len(completed)} ta\n\n"
    text += "Pastdagi tugmalardan foydalaning:"
    
    await update.message.reply_text(text, reply_markup=SUPPORT_KEYBOARD)

async def handle_pending_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kutayotgan so'rovlarni ko'rsatish"""
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        return
    
    pending = get_requests_by_status('pending')
    
    if not pending:
        text = "⏳ Kutayotgan so'rovlar yo'q."
    else:
        text = "⏳ KUTAYOTGAN SO'ROVLAR:\n\n"
        for req in pending[:10]:  # Faqat 10 tasini ko'rsatish
            text += f"🔸 #{req[0]}\n"
            text += f"👤: @{req[7] or req[8] or req[1]}\n"
            text += f"📝: {req[2][:80]}...\n"
            text += f"📅: {req[5]}\n"
            text += f"✏️ Javob: /reply {req[0]} [xabar]\n"
            text += "─" * 30 + "\n"
    
    await update.message.reply_text(text, reply_markup=SUPPORT_KEYBOARD)

async def handle_in_progress_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jarayondagi so'rovlarni ko'rsatish"""
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        return
    
    in_progress = get_requests_by_status('in_progress')
    
    if not in_progress:
        text = "🔄 Jarayondagi so'rovlar yo'q."
    else:
        text = "🔄 JARAYONDAGI SO'ROVLAR:\n\n"
        for req in in_progress[:10]:
            text += f"🔸 #{req[0]}\n"
            text += f"👤: @{req[7] or req[8] or req[1]}\n"
            text += f"📝: {req[2][:80]}...\n"
            text += f"📅: {req[5]}\n"
            text += f"✏️ Javob: /reply {req[0]} [xabar]\n"
            text += "─" * 30 + "\n"
    
    await update.message.reply_text(text, reply_markup=SUPPORT_KEYBOARD)

async def handle_completed_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yakunlangan so'rovlarni ko'rsatish"""
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        return
    
    completed = get_requests_by_status('completed')
    
    if not completed:
        text = "✅ Yakunlangan so'rovlar yo'q."
    else:
        text = "✅ YAKUNLANGAN SO'ROVLAR (oxirgi 10 ta):\n\n"
        for req in completed[:10]:
            text += f"🔸 #{req[0]}\n"
            text += f"👤: @{req[7] or req[8] or req[1]}\n"
            text += f"📝: {req[2][:60]}...\n"
            text += f"📅: {req[5]}\n"
            text += "─" * 25 + "\n"
    
    await update.message.reply_text(text, reply_markup=SUPPORT_KEYBOARD)

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhda har qanday a'zo foydalanuvchiga javob berishi"""
    
    # Faqat guruhda ishlashi kerak
    if update.effective_chat.id != config.GROUP_ID:
        return
    
    user = update.effective_user
    
    # Komanda argumentlarini olish
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n"
            "✅ To'g'ri format: /reply <request_id> <xabar matni>\n"
            "📝 Misol: /reply 15 Salom, manga topildi!\n\n"
            "ℹ️ Request ID ni bot guruhga yuborgan xabardan olishingiz mumkin."
        )
        return
    
    try:
        request_id = int(args[0])
        message_text = ' '.join(args[1:])
        
        # So'rovni bazada mavjudligini tekshirish
        request_details = get_request_details(request_id)
        
        if not request_details:
            await update.message.reply_text(f"❌ #{request_id} IDli so'rov topilmadi!")
            return
        
        # Foydalanuvchi ID sini olish
        user_id = request_details[1]
        request_user_name = request_details[8] or request_details[9] or "Foydalanuvchi"
        
        # Foydalanuvchiga javob yuborish
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📩 Sizning #{request_id} raqamli so'rovingizga javob:\n\n"
                     f"{message_text}\n\n"
                     f"👤 Javob berdi: @{user.username or user.first_name}\n"
                     f"💬 Guruh: {update.effective_chat.title}"
            )
            
            # Bazada yangilash
            add_reply(request_id, user.id, message_text)
            
            # Guruhdagi xabarni yangilash
            await update.message.reply_text(
                f"✅ #{request_id} so'roviga javob yuborildi!\n"
                f"👤 Foydalanuvchi: {request_user_name}\n"
                f"👨‍💼 Javob berdi: @{user.username or user.first_name}\n"
                f"📝 Javob: {message_text[:100]}..."
            )
            
            # Agar foydalanuvchi admin bo'lmasa, admin qilish
            if not is_group_member_admin(user.id):
                add_group_admin(user.id)
                logger.info(f"Yangi guruh admini qo'shildi: {user.id}")
            
        except Exception as e:
            logger.error(f"Foydalanuvchiga javob yuborishda xatolik: {e}")
            await update.message.reply_text(
                f"⚠️ Foydalanuvchiga javob yuborilmadi (bloklagan bo'lishi mumkin).\n"
                f"📌 Biroq javob saqlandi: #{request_id}"
            )
            
    except ValueError:
        await update.message.reply_text("❌ Request ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Reply komandasida xatolik: {e}")
        await update.message.reply_text(f"❌ Xatolik: {str(e)[:100]}")

async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh adminlarini ko'rish"""
    
    if update.effective_chat.id != config.GROUP_ID:
        return
    
    try:
        # Guruh adminlarini Telegram API orqali olish
        chat_admins = await context.bot.get_chat_administrators(config.GROUP_ID)
        
        text = "👑 Guruh Adminlari:\n\n"
        
        for admin in chat_admins:
            user = admin.user
            status = "👑 Bosh admin" if admin.status == "creator" else "🛡️ Admin"
            text += f"{status}: @{user.username or user.first_name} (ID: {user.id})\n"
        
        # Bazadagi adminlar
        db_admins = get_group_admins()
        if db_admins:
            text += "\n📋 Javob bera oladiganlar:\n"
            for admin in db_admins[:10]:  # Faqat 10 tasi
                admin_id = admin[0]
                username = admin[1] or admin[2] or f"ID: {admin_id}"
                text += f"👤 {username}\n"
        
        await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Adminlarni olishda xatolik: {e}")
        await update.message.reply_text("❌ Adminlarni olishda xatolik yuz berdi.")

async def addadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi admin qo'shish (faqat asosiy admin)"""
    
    if update.effective_user.id != config.ADMIN_ID:
        await update.message.reply_text("❌ Sizda bu huquq yo'q!")
        return
    
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "❌ Foydalanuvchi ID sini kiriting!\n"
            "✅ Misol: /addadmin 123456789"
        )
        return
    
    try:
        user_id = int(args[0])
        add_group_admin(user_id)
        
        await update.message.reply_text(f"✅ {user_id} IDli foydalanuvchi admin qilindi!")
        
    except ValueError:
        await update.message.reply_text("❌ ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Admin qo'shishda xatolik: {e}")
        await update.message.reply_text(f"❌ Xatolik: {e}")

async def requestinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """So'rov haqida ma'lumot olish"""
    
    if update.effective_chat.id != config.GROUP_ID:
        return
    
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "❌ So'rov ID sini kiriting!\n"
            "✅ Misol: /requestinfo 15\n"
            "📋 Barcha so'rovlar: /allrequests"
        )
        return
    
    try:
        request_id = int(args[0])
        request_details = get_request_details(request_id)
        
        if not request_details:
            await update.message.reply_text(f"❌ #{request_id} IDli so'rov topilmadi!")
            return
        
        # So'rov ma'lumotlari
        user_id = request_details[1]
        message = request_details[2]
        status = request_details[3]
        created_at = request_details[5]
        username = request_details[8] or "Noma'lum"
        first_name = request_details[9] or "Noma'lum"
        
        status_emoji = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅'
        }.get(status, '❓')
        
        text = (
            f"📄 So'rov #{request_id} ma'lumotlari:\n\n"
            f"{status_emoji} Holat: {status}\n"
            f"👤 Foydalanuvchi: {first_name} (@{username})\n"
            f"🆔 User ID: {user_id}\n"
            f"📅 Yuborilgan: {created_at}\n"
            f"📝 Xabar: {message[:300]}...\n\n"
            f"✏️ Javob berish: /reply {request_id} [xabar]"
        )
        
        await update.message.reply_text(text)
        
    except ValueError:
        await update.message.reply_text("❌ ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Request info xatosi: {e}")
        await update.message.reply_text(f"❌ Xatolik: {e}")

async def allrequests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha so'rovlarni ko'rish"""
    
    if update.effective_chat.id != config.GROUP_ID:
        return
    
    requests = get_all_requests(limit=20)
    
    if not requests:
        await update.message.reply_text("📭 Hozircha so'rovlar yo'q.")
        return
    
    text = "📋 Oxirgi 20 ta so'rov:\n\n"
    
    for req in requests:
        status_emoji = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅'
        }.get(req[1], '❓')
        
        text += f"{status_emoji} #{req[0]}\n"
        text += f"👤 {req[2] or 'Nomalum'} (@{req[3] or 'Nomalum'})\n"
        text += f"📝 {req[4][:50]}...\n"
        text += f"📅 {req[5]}\n"
        text += f"✏️ /reply {req[0]} [xabar]\n"
        text += "─" * 30 + "\n"
    
    await update.message.reply_text(text)

async def handle_admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin xabarlarini qayta ishlash"""
    user = update.effective_user
    message_text = update.message.text
    
    if user.id != config.ADMIN_ID:
        return
    
    # Admin funksiyalari
    if message_text == "📊 Statistika":
        stats = get_statistics()
        
        text = (
            f"📊 Bot Statistikasi:\n\n"
            f"👥 Umumiy foydalanuvchilar: {stats['total_users']}\n"
            f"📨 Umumiy so'rovlar: {stats['total_requests']}\n"
            f"📈 Bugungi so'rovlar: {stats['today_requests']}\n"
            f"⏳ Kutayotgan so'rovlar: {stats['pending_requests']}\n"
            f"🔄 Jarayonda: {stats['in_progress_requests']}\n"
            f"✅ Yakunlangan: {stats['completed_requests']}\n"
        )
        
        await update.message.reply_text(text, reply_markup=ADMIN_KEYBOARD)
    
    elif message_text == "📢 Broadcast":
        context.user_data['waiting_for_broadcast'] = True
        await update.message.reply_text(
            "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing:\n\n"
            "⚠️ Eslatma:\n"
            "1. Xabar yuborish biroz vaqt olishi mumkin\n"
            "2. Faqat kanalga obuna bo'lgan foydalanuvchilarga yuboriladi\n"
            "3. Telegram limitlari tufayli bir vaqtda 30 ta xabar yuboriladi",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif message_text == "📋 Support":
        await handle_support_panel(update, context)
    
    elif message_text == "🔍 Qidirish":
        context.user_data['waiting_for_search'] = True
        await update.message.reply_text(
            "🔍 Qidirmoqchi bo'lgan foydalanuvchi ID, username yoki ismini yozing:",
            reply_markup=ReplyKeyboardRemove()
        )
    
    # Support panel tugmalari
    elif message_text == "⏳ Kutayotgan so'rovlar":
        await handle_pending_requests(update, context)
    
    elif message_text == "🔄 Jarayondagilar":
        await handle_in_progress_requests(update, context)
    
    elif message_text == "✅ Yakunlangan so'rovlar":
        await handle_completed_requests(update, context)
    
    elif message_text == "📝 So'rovga javob berish":
        context.user_data['waiting_for_reply_id'] = True
        await update.message.reply_text(
            "✏️ Javob bermoqchi bo'lgan so'rov ID sini yozing:\n"
            "(Masalan: 15)",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif message_text == "⬅️ Orqaga":
        await update.message.reply_text("👑 Admin Panel", reply_markup=ADMIN_KEYBOARD)
    
    # Broadcast xabarini qayta ishlash
    elif 'waiting_for_broadcast' in context.user_data and user.id == config.ADMIN_ID:
        await update.message.reply_text("⏳ Broadcast bajarilmoqda...", reply_markup=ADMIN_KEYBOARD)
        
        users = get_all_users()
        success = 0
        failed = 0
        
        for user_id in users[:50]:  # Test uchun faqat 50 tasiga
            try:
                # Kanalga obuna bo'lishni tekshirish
                is_subscribed = await check_channel_subscription(context.bot, user_id)
                
                if not is_subscribed:
                    continue
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 Botdan xabar:\n\n{message_text}\n\n"
                         f"📢 @{config.CHANNEL_USERNAME} kanaliga obuna bo'ling!"
                )
                success += 1
                
                # Tezlikni cheklash
                if success % 5 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                failed += 1
                logger.error(f"Xabar yuborishda xatolik {user_id}: {e}")
        
        del context.user_data['waiting_for_broadcast']
        
        await update.message.reply_text(
            f"✅ Broadcast yakunlandi!\n\n"
            f"✅ Muvaffaqiyatli: {success}\n"
            f"❌ Xatolik: {failed}",
            reply_markup=ADMIN_KEYBOARD
        )
    
    # Qidiruvni qayta ishlash
    elif 'waiting_for_search' in context.user_data and user.id == config.ADMIN_ID:
        results = search_user(message_text)
        
        if not results:
            text = "❌ Hech qanday foydalanuvchi topilmadi."
        else:
            text = f"🔍 Natijalar ({len(results)} ta):\n\n"
            for user_data in results[:10]:
                user_id = user_data[1]
                username = user_data[2] if user_data[2] else "Mavjud emas"
                first_name = user_data[3] if user_data[3] else "Mavjud emas"
                last_name = user_data[4] if user_data[4] else "Mavjud emas"
                joined_date = user_data[5]
                
                text += f"👤 ID: {user_id}\n"
                text += f"📱 Username: @{username}\n"
                text += f"👤 Ism: {first_name}\n"
                text += f"👥 Familiya: {last_name}\n"
                text += f"📅 Qo'shilgan: {joined_date}\n"
                text += "─" * 20 + "\n"
        
        del context.user_data['waiting_for_search']
        
        await update.message.reply_text(text, reply_markup=ADMIN_KEYBOARD)
    
    # So'rovga javob berish
    elif 'waiting_for_reply_id' in context.user_data and user.id == config.ADMIN_ID:
        try:
            request_id = int(message_text)
            request_details = get_request_details(request_id)
            
            if not request_details:
                await update.message.reply_text(f"❌ #{request_id} IDli so'rov topilmadi!", reply_markup=SUPPORT_KEYBOARD)
                del context.user_data['waiting_for_reply_id']
                return
            
            context.user_data['reply_request_id'] = request_id
            context.user_data['waiting_for_reply_text'] = True
            del context.user_data['waiting_for_reply_id']
            
            await update.message.reply_text(
                f"✅ So'rov #{request_id} topildi!\n"
                f"👤 Foydalanuvchi: @{request_details[8] or request_details[9] or 'Nomalum'}\n"
                f"📝 So'rov: {request_details[2][:200]}...\n\n"
                f"Endi javobingizni yozing:",
                reply_markup=ReplyKeyboardRemove()
            )
            
        except ValueError:
            await update.message.reply_text("❌ ID raqam bo'lishi kerak!", reply_markup=SUPPORT_KEYBOARD)
            del context.user_data['waiting_for_reply_id']
    
    elif 'waiting_for_reply_text' in context.user_data and user.id == config.ADMIN_ID:
        request_id = context.user_data['reply_request_id']
        reply_text = message_text
        
        # Bazaga saqlash
        add_reply(request_id, user.id, reply_text)
        
        # Foydalanuvchiga yuborish
        request_details = get_request_details(request_id)
        user_id = request_details[1]
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📩 Sizning #{request_id} raqamli so'rovingizga javob:\n\n"
                     f"{reply_text}\n\n"
                     f"✅ Javob berdi: @{user.username or user.first_name}"
            )
            reply_status = "✅ Foydalanuvchiga javob yuborildi"
        except Exception as e:
            logger.error(f"Foydalanuvchiga javob yuborishda xatolik: {e}")
            reply_status = "⚠️ Foydalanuvchiga javob yuborilmadi (bloklagan bo'lishi mumkin)"
        
        # Rejimni tozalash
        del context.user_data['waiting_for_reply_text']
        del context.user_data['reply_request_id']
        
        await update.message.reply_text(
            f"✅ Javob saqlandi!\n"
            f"#{request_id} so'rovi 'completed' holatiga o'zgartirildi.\n"
            f"{reply_status}",
            reply_markup=SUPPORT_KEYBOARD
        )
    
    # Agar hech qaysi holatga to'g'ri kelmasa
    else:
        await update.message.reply_text(
            "👑 Admin Panel\nPastdagi tugmalardan foydalaning:",
            reply_markup=ADMIN_KEYBOARD
        )

# Import qilish uchun kerak
async def check_channel_subscription(bot, user_id):
    """Kanal obunasini tekshirish"""
    from utils.channel_check import check_channel_subscription as check_sub
    return await check_sub(bot, user_id)

def setup_admin_handlers(application):
    """Admin va guruh handlerlarini sozlash"""
    # Guruh komandalari (har kim uchun)
    application.add_handler(CommandHandler("reply", reply_command))
    application.add_handler(CommandHandler("requestinfo", requestinfo_command))
    application.add_handler(CommandHandler("allrequests", allrequests_command))
    application.add_handler(CommandHandler("admins", admins_command))
    
    # Faqat asosiy admin uchun
    application.add_handler(CommandHandler("addadmin", addadmin_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Admin xabarlarini qayta ishlash
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_admin_messages
    ))