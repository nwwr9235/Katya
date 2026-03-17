"""
💬 نظام الردود الذكية
- اضف ردي: يحفظ اسم وصورة المستخدم، عند ذكر الاسم يعرض صورته
- رد على كلمة بصورة
- ردود نصية مخصصة
"""
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from database import db
from handlers.admin import is_admin

logger = logging.getLogger(__name__)

# حالات المحادثة لـ "اضف ردي"
WAITING_NAME = 1


# ══════════════════════════════════════════
#    نظام "اضف ردي" — حفظ الاسم والصورة
# ══════════════════════════════════════════

async def add_my_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    عندما يكتب المستخدم "اضف ردي"
    يطلب منه البوت إرسال اسمه
    """
    user = update.effective_user
    await update.message.reply_text(
        f"👋 أهلاً {user.first_name}!\n\n"
        f"📝 أرسل **اسمك** الذي تريد أن يُعرف به في المجموعة:\n"
        f"_(سيظهر اسمك وصورتك عند ذكرك)_",
        parse_mode="Markdown"
    )
    return WAITING_NAME


async def save_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    استقبال الاسم من المستخدم وحفظه مع صورته
    """
    user      = update.effective_user
    chat_id   = update.effective_chat.id
    user_name = update.message.text.strip()

    if len(user_name) < 2 or len(user_name) > 50:
        await update.message.reply_text("❌ الاسم يجب أن يكون بين 2 و50 حرفاً، حاول مجدداً:")
        return WAITING_NAME

    # جلب صورة المستخدم
    photo_file_id = None
    try:
        photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            photo_file_id = photos.photos[0][0].file_id
    except Exception:
        pass

    # حفظ في قاعدة البيانات
    await db.save_user_profile(
        user_id      = user.id,
        chat_id      = chat_id,
        display_name = user_name,
        photo_id     = photo_file_id,
        username     = user.username or "",
    )

    if photo_file_id:
        await update.message.reply_photo(
            photo   = photo_file_id,
            caption = f"✅ **تم الحفظ بنجاح!**\n\n"
                      f"🏷️ الاسم: **{user_name}**\n"
                      f"🖼️ الصورة: محفوظة\n\n"
                      f"_الآن عند كتابة اسمك في المجموعة سيعرض البوت صورتك!_",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"✅ **تم الحفظ بنجاح!**\n\n"
            f"🏷️ الاسم: **{user_name}**\n"
            f"⚠️ لم يتم العثور على صورة — تأكد من وجود صورة في حسابك\n\n"
            f"_الآن عند كتابة اسمك في المجموعة سيعرض البوت بطاقتك!_",
            parse_mode="Markdown"
        )

    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END


# ══════════════════════════════════════════
#     مستمع المجموعة — يكشف ذكر الأسماء
# ══════════════════════════════════════════

async def group_message_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يستمع لكل رسائل المجموعة:
    1 - يتحقق إذا الرسالة تحتوي على اسم مستخدم مسجل → يعرض بطاقته
    2 - يتحقق من الردود المخصصة بصورة أو نص
    """
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    text    = update.message.text.strip()

    # ── التحقق من أسماء المستخدمين المسجلين ──
    profiles = await db.get_all_profiles(chat_id)
    for profile in profiles:
        if profile["display_name"].lower() in text.lower():
            if profile.get("photo_id"):
                await update.message.reply_photo(
                    photo   = profile["photo_id"],
                    caption = f"👤 **{profile['display_name']}**\n"
                              f"{'@' + profile['username'] if profile.get('username') else ''}\n"
                              f"🆔 `{profile['user_id']}`",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"👤 **{profile['display_name']}**\n"
                    f"{'@' + profile['username'] if profile.get('username') else ''}\n"
                    f"🆔 `{profile['user_id']}`",
                    parse_mode="Markdown"
                )
            return  # نعرض بطاقة واحدة فقط

    # ── التحقق من الردود المخصصة ──
    custom_replies = await db.get_all_replies(chat_id)
    for r in custom_replies:
        if r["keyword"].lower() in text.lower():
            if r.get("photo_id"):
                # رد بصورة
                await update.message.reply_photo(
                    photo   = r["photo_id"],
                    caption = r.get("caption", ""),
                )
            else:
                # رد نصي
                await update.message.reply_text(r["reply"])
            return


# ══════════════════════════════════════════
#     إضافة رد بصورة: اضف رد صورة
# ══════════════════════════════════════════

WAITING_KEYWORD = 1
WAITING_PHOTO   = 2
WAITING_CAPTION = 3


async def add_image_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إضافة رد بصورة — للمشرفين فقط"""
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return ConversationHandler.END

    await update.message.reply_text(
        "🖼️ **إضافة رد بصورة**\n\n"
        "أرسل **الكلمة المفتاحية** التي ستُفعّل هذا الرد:\n"
        "_(اكتب الغاء للإلغاء)_",
        parse_mode="Markdown"
    )
    return WAITING_KEYWORD


async def receive_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() == "الغاء":
        await update.message.reply_text("❌ تم الإلغاء.")
        return ConversationHandler.END

    context.user_data["reply_keyword"] = text.lower()
    await update.message.reply_text(
        f"✅ الكلمة: `{text}`\n\n"
        f"الآن أرسل **الصورة** التي تريد إرسالها كرد:",
        parse_mode="Markdown"
    )
    return WAITING_PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ يرجى إرسال صورة. أو اكتب `الغاء`", parse_mode="Markdown")
        return WAITING_PHOTO

    photo_id = update.message.photo[-1].file_id
    context.user_data["reply_photo_id"] = photo_id

    await update.message.reply_text(
        "✅ تم استقبال الصورة!\n\n"
        "أرسل **تعليق للصورة** (اختياري)، أو اكتب `تخطي` لبدون تعليق:",
        parse_mode="Markdown"
    )
    return WAITING_CAPTION


async def receive_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyword = context.user_data.get("reply_keyword", "")
    photo_id = context.user_data.get("reply_photo_id", "")
    caption = update.message.text.strip()

    if caption.lower() == "تخطي":
        caption = ""

    await db.add_custom_reply(
        chat_id  = chat_id,
        keyword  = keyword,
        reply    = caption,
        added_by = update.effective_user.id,
        photo_id = photo_id,
    )

    await update.message.reply_photo(
        photo   = photo_id,
        caption = f"✅ **تم إضافة الرد بصورة!**\n\n"
                  f"🔑 الكلمة: `{keyword}`\n"
                  f"💬 التعليق: {caption or '—'}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END
