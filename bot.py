"""
🤖 بوت تيليجرام متكامل لإدارة المجموعات
المكتبة: python-telegram-bot v20 (Webhook + Asyncio)
قاعدة البيانات: Motor (MongoDB)
"""

import asyncio
import logging
import sys
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
)

from config import Config
from database import db
from handlers import admin, welcome, interactive, calls

# ══════════════════════════════════════════
#           إعداد التسجيل
# ══════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
#           تسجيل جميع المعالجات
# ══════════════════════════════════════════
def register_handlers(app: Application):
    # ── الإدارة ──
    app.add_handler(CommandHandler("ban",    admin.ban_handler))
    app.add_handler(CommandHandler("unban",  admin.unban_handler))
    app.add_handler(CommandHandler("mute",   admin.mute_handler))
    app.add_handler(CommandHandler("unmute", admin.unmute_handler))
    app.add_handler(CommandHandler("banlist",admin.banlist_handler))

    # ── عامة ──
    app.add_handler(CommandHandler("start",  interactive.start_handler))
    app.add_handler(CommandHandler("help",   interactive.help_handler))
    app.add_handler(CommandHandler("ping",   interactive.ping_handler))
    app.add_handler(CommandHandler("info",   interactive.info_handler))
    app.add_handler(CommandHandler("id",     interactive.id_handler))
    app.add_handler(CommandHandler("rules",  welcome.rules_handler))

    # ── المكالمات ──
    app.add_handler(CommandHandler("joincall",   calls.join_call_handler))
    app.add_handler(CommandHandler("leavecall",  calls.leave_call_handler))

    # ── الترحيب بالأعضاء الجدد ──
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome.welcome_handler
    ))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER, welcome.farewell_handler
    ))

    # ── الأزرار ──
    app.add_handler(CallbackQueryHandler(welcome.callback_handler))

    # ── الردود الذكية على الكلمات ──
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"(?i)المطور|developer"), interactive.reply_developer
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"(?i)مساعدة|help me"), interactive.reply_help
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"(?i)القوانين|الرولز|rules"), welcome.rules_text_handler
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"(?i)السلام|سلام|هلا|مرحبا|مرحباً|صباح|مساء"), interactive.reply_greeting
    ))

    logger.info("✅ تم تسجيل جميع المعالجات")


# ══════════════════════════════════════════
#           الدالة الرئيسية
# ══════════════════════════════════════════
async def post_init(app: Application):
    """تُشغَّل بعد تهيئة التطبيق"""
    await db.connect()
    logger.info("✅ تم الاتصال بـ MongoDB")
    await calls.initialize_calls()
    logger.info("🤖 البوت جاهز ويستقبل الرسائل عبر Webhook")


async def post_shutdown(app: Application):
    """تُشغَّل عند الإيقاف"""
    await db.close()
    logger.info("🛑 تم إيقاف البوت")


def main():
    # التحقق من المتغيرات
    if not Config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN مفقود!")
        sys.exit(1)

    # بناء التطبيق
    app = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # تسجيل المعالجات
    register_handlers(app)

    # تشغيل عبر Webhook
    logger.info(f"🚀 تشغيل Webhook على المنفذ {Config.PORT}")
    app.run_webhook(
        listen="0.0.0.0",
        port=Config.PORT,
        webhook_url=f"{Config.WEBHOOK_URL}/webhook",
        url_path="/webhook",
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
