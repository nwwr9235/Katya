"""
💬 المعالجات التفاعلية: الردود الذكية والأوامر العامة
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import Config

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
#     فلاتر مخصصة للكلمات المفتاحية
# ══════════════════════════════════════════

# فلتر للكشف عن كلمات مفتاحية في الرسائل
def keyword_filter(*keywords):
    """إنشاء فلتر للكلمات المفتاحية"""
    async def func(flt, client, message):
        if message.text:
            text = message.text.lower()
            return any(kw.lower() in text for kw in flt.data)
        return False

    return filters.create(
        func,
        data=keywords,
        name="KeywordFilter",
    )


# ══════════════════════════════════════════
#         أمر /start
# ══════════════════════════════════════════

async def start_command(client: Client, message: Message):
    """معالج أمر البدء"""
    user_name = message.from_user.first_name

    start_text = (
        f"👋 مرحباً {user_name}!\n\n"
        f"🤖 أنا **بوت إدارة المجموعات**\n"
        f"قادر على مساعدتك في إدارة مجموعتك بكفاءة عالية.\n\n"
        f"**⚡ قدراتي:**\n"
        f"• 🛡️ إدارة الأعضاء (حظر، كتم، إلغاء)\n"
        f"• 👋 ترحيب تلقائي بالأعضاء الجدد\n"
        f"• 📋 عرض قوانين المجموعة\n"
        f"• 🗄️ قاعدة بيانات متكاملة\n"
        f"• 🔊 دعم المكالمات الجماعية (قريباً)\n\n"
        f"اكتب /help لعرض قائمة الأوامر الكاملة 📖"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 الأوامر", callback_data="get_help"),
                InlineKeyboardButton("👨‍💻 المطور", url=Config.DEVELOPER_LINK),
            ],
            [
                InlineKeyboardButton(
                    "➕ أضفني لمجموعتك", url=f"https://t.me/botusername?startgroup=true"
                )
            ],
        ]
    )

    await message.reply_text(start_text, reply_markup=keyboard)


# ══════════════════════════════════════════
#         أمر /help
# ══════════════════════════════════════════

async def help_command(client: Client, message: Message):
    """معالج أمر المساعدة"""
    help_text = (
        "📖 **دليل الأوامر الكامل**\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🔵 **أوامر عامة:**\n"
        "• `/start` - تشغيل البوت\n"
        "• `/help` - هذه القائمة\n"
        "• `/rules` - قوانين المجموعة\n"
        "• `/ping` - اختبار سرعة الاستجابة\n"
        "• `/info` - معلومات عن البوت\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🔴 **أوامر المشرفين:**\n"
        "• `/ban [مستخدم] [سبب]` - حظر عضو\n"
        "• `/unban [مستخدم]` - إلغاء الحظر\n"
        "• `/mute [مستخدم] [سبب]` - كتم عضو\n"
        "• `/unmute [مستخدم]` - إلغاء الكتم\n"
        "• `/banlist` - قائمة المحظورين\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "💡 **تلميح:** يمكنك الرد على رسالة المستخدم\n"
        "واستخدام الأمر مباشرة بدون ذكر اسمه."
    )
    await message.reply_text(help_text)


# ══════════════════════════════════════════
#         أمر /ping
# ══════════════════════════════════════════

async def ping_command(client: Client, message: Message):
    """اختبار سرعة استجابة البوت"""
    import time
    start = time.monotonic()
    sent = await message.reply_text("🏓 جاري القياس...")
    elapsed = (time.monotonic() - start) * 1000
    await sent.edit_text(
        f"🏓 **Pong!**\n\n⚡ زمن الاستجابة: `{elapsed:.2f}ms`"
    )


# ══════════════════════════════════════════
#         أمر /info
# ══════════════════════════════════════════

async def info_command(client: Client, message: Message):
    """معلومات عن البوت"""
    me = await client.get_me()
    info_text = (
        f"🤖 **معلومات البوت**\n\n"
        f"• **الاسم:** {me.first_name}\n"
        f"• **المعرف:** @{me.username}\n"
        f"• **الآي دي:** `{me.id}`\n\n"
        f"⚙️ **التقنيات المستخدمة:**\n"
        f"• Python 3.10 🐍\n"
        f"• Pyrogram 2.0 📡\n"
        f"• MongoDB (Motor) 🗄️\n"
        f"• PyGalls (المكالمات) 🔊\n\n"
        f"👨‍💻 **المطور:** [{Config.DEVELOPER_NAME}]({Config.DEVELOPER_LINK})"
    )
    await message.reply_text(
        info_text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 تواصل مع المطور", url=Config.DEVELOPER_LINK)]]
        ),
    )


# ══════════════════════════════════════════
#      الردود الذكية على الكلمات المفتاحية
# ══════════════════════════════════════════

async def reply_developer(client: Client, message: Message):
    """الرد عند ذكر كلمة 'المطور'"""
    await message.reply_text(
        f"👨‍💻 **معلومات المطور**\n\n"
        f"• **الاسم:** {Config.DEVELOPER_NAME}\n"
        f"• **الحساب:** @{Config.DEVELOPER_USERNAME}\n"
        f"• **التواصل:** {Config.DEVELOPER_LINK}\n\n"
        f"_هو من قام ببرمجة هذا البوت الرائع_ 🚀",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("💬 تواصل معه", url=Config.DEVELOPER_LINK)]]
        ),
        disable_web_page_preview=True,
    )


async def reply_help_request(client: Client, message: Message):
    """الرد على طلبات المساعدة"""
    await message.reply_text(
        "🆘 **يبدو أنك تحتاج مساعدة!**\n\n"
        "اكتب /help لعرض قائمة الأوامر الكاملة\n"
        f"أو تواصل مع المطور: {Config.DEVELOPER_LINK}",
        disable_web_page_preview=True,
    )


async def reply_rules_mention(client: Client, message: Message):
    """الرد عند ذكر كلمة 'القوانين' أو 'الرولز'"""
    from config import Config
    await message.reply_text(
        Config.GROUP_RULES,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ أوافق", callback_data="accept_rules")]]
        ),
    )


async def reply_greeting(client: Client, message: Message):
    """الرد على التحيات"""
    user_name = message.from_user.first_name
    greetings = [
        f"وعليكم السلام ورحمة الله وبركاته يا {user_name}! 👋",
        f"أهلاً وسهلاً بك يا {user_name}! 🌟",
        f"مرحباً {user_name}! كيف حالك؟ 😊",
    ]
    import random
    await message.reply_text(random.choice(greetings))


# ══════════════════════════════════════════
#         معالج /id لمعرفة الآيدي
# ══════════════════════════════════════════

async def id_command(client: Client, message: Message):
    """عرض معرف المستخدم والمجموعة"""
    user = message.from_user
    chat = message.chat

    text = (
        f"🆔 **معلومات المعرفات**\n\n"
        f"👤 **معرّفك:** `{user.id}`\n"
        f"💬 **معرّف المجموعة:** `{chat.id}`\n"
    )

    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        text += f"↪️ **معرّف المستخدم المذكور:** `{replied_user.id}`\n"

    await message.reply_text(text)


# ══════════════════════════════════════════
#         تسجيل المعالجات
# ══════════════════════════════════════════

def register(app: Client):
    """تسجيل جميع المعالجات التفاعلية"""

    # الأوامر العامة
    app.on_message(filters.command("start") & filters.private)(start_command)
    app.on_message(filters.command("help"))(help_command)
    app.on_message(filters.command("ping"))(ping_command)
    app.on_message(filters.command("info"))(info_command)
    app.on_message(filters.command("id"))(id_command)

    # الردود الذكية على الكلمات المفتاحية
    app.on_message(
        keyword_filter("المطور", "developer", "مطور البوت") & filters.group
    )(reply_developer)

    app.on_message(
        keyword_filter("مساعدة", "help me", "محتاج مساعدة") & filters.group
    )(reply_help_request)

    app.on_message(
        keyword_filter("القوانين", "الرولز", "rules") & filters.group
    )(reply_rules_mention)

    app.on_message(
        keyword_filter(
            "السلام عليكم", "سلام", "هلا", "هلو", "مرحبا", "مرحباً", "صباح الخير", "مساء الخير"
        ) & filters.group
    )(reply_greeting)

    logger.info("✅ تم تسجيل المعالجات التفاعلية")
