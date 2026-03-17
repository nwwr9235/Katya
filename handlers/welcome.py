"""
👋 معالجات الترحيب مع Inline Buttons
"""
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import Config

logger = logging.getLogger(__name__)


def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 القوانين",     callback_data="show_rules"),
            InlineKeyboardButton("👨‍💻 المطور",      url=Config.DEVELOPER_LINK),
        ],
        [
            InlineKeyboardButton("✅ قرأت القوانين وأوافق", callback_data="accept_rules"),
        ],
        [
            InlineKeyboardButton("🆘 مساعدة",       callback_data="get_help"),
            InlineKeyboardButton("📊 إحصائيات",     callback_data="stats"),
        ],
    ])


# ══════════════════════════════════════════
#           ترحيب بالعضو الجديد
# ══════════════════════════════════════════

async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        name    = member.first_name
        mention = f"[{name}](tg://user?id={member.id})"
        chat    = update.effective_chat

        try:
            count = await chat.get_member_count()
        except Exception:
            count = "؟"

        text = (
            f"🎉 **أهلاً وسهلاً {mention} في {chat.title}!**\n\n"
            f"🌟 يسعدنا انضمامك إلينا\n"
            f"📌 يرجى قراءة القوانين قبل المشاركة\n\n"
            f"👥 عدد الأعضاء الآن: **{count}**"
        )

        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=welcome_keyboard(),
        )


# ══════════════════════════════════════════
#              وداع العضو
# ══════════════════════════════════════════

async def farewell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.message.left_chat_member
    if member and not member.is_bot:
        await update.message.reply_text(
            f"👋 وداعاً **{member.first_name}**، نتمنى أن نراك مجدداً! 🌹",
            parse_mode="Markdown"
        )


# ══════════════════════════════════════════
#              أمر /rules
# ══════════════════════════════════════════

async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        Config.GROUP_RULES,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ أوافق على القوانين", callback_data="accept_rules")
        ]])
    )


async def rules_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد عند ذكر كلمة القوانين في المجموعة"""
    await rules_handler(update, context)


# ══════════════════════════════════════════
#           معالجات الأزرار
# ══════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data
    user  = query.from_user.first_name
    chat  = update.effective_chat

    if data == "show_rules":
        await query.message.reply_text(
            Config.GROUP_RULES,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ أوافق", callback_data="accept_rules")
            ]])
        )

    elif data == "accept_rules":
        await query.answer(f"✅ شكراً {user}! تم تسجيل موافقتك.", show_alert=True)

    elif data == "get_help":
        await query.message.reply_text(
            "🆘 **المساعدة**\n\n"
            "• `/start` — تشغيل البوت\n"
            "• `/help`  — قائمة الأوامر\n"
            "• `/rules` — القوانين\n"
            "• `/ping`  — اختبار السرعة\n\n"
            "**للمشرفين:**\n"
            "• `/ban` `/unban` `/mute` `/unmute`\n"
            "• `/banlist` — قائمة المحظورين",
            parse_mode="Markdown"
        )

    elif data == "stats":
        try:
            count = await chat.get_member_count()
        except Exception:
            count = "؟"
        await query.message.reply_text(
            f"📊 **إحصائيات {chat.title}**\n\n"
            f"👥 الأعضاء: `{count}`\n"
            f"🤖 البوت: نشط ✅",
            parse_mode="Markdown"
        )
