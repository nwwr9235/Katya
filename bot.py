"""
🤖 بوت تيليجرام متكامل
"""
import logging
import sys
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters
)
from config import Config
from database import db
from handlers import welcome, interactive, calls
from handlers.admin import arabic_commands_handler
from handlers.replies import (
    add_my_reply_start, save_user_name, cancel_registration,
    add_image_reply_start, receive_keyword, receive_photo, receive_caption,
    group_message_listener,
    WAITING_NAME, WAITING_KEYWORD, WAITING_PHOTO, WAITING_CAPTION,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def register_handlers(app: Application):

    # ══════════════════════════════════════════
    #   محادثة "اضف ردي" — حفظ الاسم والصورة
    # ══════════════════════════════════════════
    add_profile_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^اضف ردي$"), add_my_reply_start),
            MessageHandler(filters.Regex(r"^اضف_ردي$"), add_my_reply_start),
        ],
        states={
            WAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_user_name)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex(r"^الغاء$"), cancel_registration)
        ],
    )

    # ══════════════════════════════════════════
    #   محادثة "اضف رد صورة" — للمشرفين
    # ══════════════════════════════════════════
    add_image_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^اضف رد صورة$"), add_image_reply_start),
        ],
        states={
            WAITING_KEYWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_keyword)
            ],
            WAITING_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_photo),
            ],
            WAITING_CAPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_caption)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex(r"^الغاء$"), cancel_registration)
        ],
    )

    # تسجيل محادثات ConversationHandler أولاً
    app.add_handler(add_profile_conv)
    app.add_handler(add_image_conv)

    # ── الأوامر العربية للإدارة ──
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & filters.Regex(
            r"^(حظر|فك حظر|فك_حظر|الغاء حظر|كتم|فك كتم|فك_كتم|الغاء كتم|رفع|تنزيل|تحذير|تثبيت|حذف|حظر_مؤقت)"
        ),
        arabic_commands_handler
    ))

    # ── الأوامر العامة ──
    app.add_handler(CommandHandler("start",       interactive.start_handler))
    app.add_handler(CommandHandler("help",        interactive.help_handler))
    app.add_handler(CommandHandler("ping",        interactive.ping_handler))
    app.add_handler(CommandHandler("info",        interactive.info_handler))
    app.add_handler(CommandHandler("id",          interactive.id_handler))
    app.add_handler(CommandHandler("rules",       welcome.rules_handler))
    app.add_handler(CommandHandler("joincall",    calls.join_call_handler))
    app.add_handler(CommandHandler("leavecall",   calls.leave_call_handler))

    # ── الترحيب والوداع ──
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome.welcome_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, welcome.farewell_handler))

    # ── الأزرار ──
    app.add_handler(CallbackQueryHandler(welcome.callback_handler))

    # ── الردود الذكية الثابتة ──
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"(?i)المطور"), interactive.reply_developer
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"(?i)مساعدة"), interactive.reply_help
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"(?i)القوانين|الرولز"), welcome.rules_text_handler
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"(?i)^(السلام|سلام|هلا|مرحبا|صباح|مساء)"), interactive.reply_greeting
    ))

    # ── مستمع الردود المخصصة وبروفايلات المستخدمين ──
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS, group_message_listener
    ))

    logger.info("✅ تم تسجيل جميع المعالجات")


async def post_init(app: Application):
    await db.connect()
    await calls.initialize_calls()
    logger.info("🤖 البوت جاهز!")


async def post_shutdown(app: Application):
    await db.close()


def main():
    if not Config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN مفقود!")
        sys.exit(1)

    app = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    register_handlers(app)

    logger.info(f"🚀 تشغيل Webhook على المنفذ {Config.PORT}")
    app.run_webhook(
        listen      = "0.0.0.0",
        port        = Config.PORT,
        webhook_url = f"{Config.WEBHOOK_URL}/webhook",
        url_path    = "/webhook",
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
