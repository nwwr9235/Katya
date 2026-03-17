"""
🛡️ معالجات الإدارة: Ban, Unban, Mute, Unmute
"""
import logging
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from database import db

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
#              دوال مساعدة
# ══════════════════════════════════════════

async def is_admin(update: Update, user_id: int) -> bool:
    """التحقق من كون المستخدم مشرفاً"""
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def bot_is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق من صلاحيات البوت"""
    try:
        bot_member = await update.effective_chat.get_member(context.bot.id)
        return bot_member.status in ("administrator", "creator")
    except Exception:
        return False


def get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استخراج المستخدم المستهدف والسبب"""
    target_id = None
    reason = "لم يُحدد سبب"

    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        if context.args:
            reason = " ".join(context.args)
    elif context.args:
        try:
            target_id = int(context.args[0])
            if len(context.args) > 1:
                reason = " ".join(context.args[1:])
        except ValueError:
            target_id = context.args[0].lstrip("@")
            if len(context.args) > 1:
                reason = " ".join(context.args[1:])

    return target_id, reason


# ══════════════════════════════════════════
#                  /ban
# ══════════════════════════════════════════

async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id   = update.effective_chat.id
    caller_id = update.effective_user.id

    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    if not await bot_is_admin(update, context):
        await update.message.reply_text("⚠️ البوت ليس مشرفاً! أعطه صلاحية تقييد الأعضاء.")
        return

    target_id, reason = get_target(update, context)
    if not target_id:
        await update.message.reply_text(
            "❓ **طريقة الاستخدام:**\n"
            "• رد على رسالة المستخدم: `/ban [السبب]`\n"
            "• أو: `/ban @username [السبب]`",
            parse_mode="Markdown"
        )
        return

    try:
        await context.bot.ban_chat_member(chat_id, target_id)
        await db.ban_user(target_id, chat_id, caller_id, reason)
        await db.log_action(chat_id, "ban", caller_id, target_id, reason)

        await update.message.reply_text(
            f"🚫 **تم الحظر بنجاح**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}\n"
            f"📝 السبب: {reason}\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ خطأ: {e.message}")


# ══════════════════════════════════════════
#                 /unban
# ══════════════════════════════════════════

async def unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    chat_id   = update.effective_chat.id

    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    target_id, _ = get_target(update, context)
    if not target_id:
        await update.message.reply_text("❓ استخدام: `/unban @username`", parse_mode="Markdown")
        return

    try:
        await context.bot.unban_chat_member(chat_id, target_id)
        await db.unban_user(target_id, chat_id)
        await db.log_action(chat_id, "unban", caller_id, target_id, "")

        await update.message.reply_text(
            f"✅ **تم إلغاء الحظر**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ خطأ: {e.message}")


# ══════════════════════════════════════════
#                  /mute
# ══════════════════════════════════════════

async def mute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    chat_id   = update.effective_chat.id

    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    if not await bot_is_admin(update, context):
        await update.message.reply_text("⚠️ البوت ليس مشرفاً!")
        return

    target_id, reason = get_target(update, context)
    if not target_id:
        await update.message.reply_text("❓ استخدام: `/mute @username [السبب]`", parse_mode="Markdown")
        return

    try:
        await context.bot.restrict_chat_member(
            chat_id, target_id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
            )
        )
        await db.mute_user(target_id, chat_id, caller_id)
        await db.log_action(chat_id, "mute", caller_id, target_id, reason)

        await update.message.reply_text(
            f"🔇 **تم الكتم بنجاح**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}\n"
            f"📝 السبب: {reason}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ خطأ: {e.message}")


# ══════════════════════════════════════════
#                 /unmute
# ══════════════════════════════════════════

async def unmute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    chat_id   = update.effective_chat.id

    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    target_id, _ = get_target(update, context)
    if not target_id:
        await update.message.reply_text("❓ استخدام: `/unmute @username`", parse_mode="Markdown")
        return

    try:
        await context.bot.restrict_chat_member(
            chat_id, target_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        await db.unmute_user(target_id, chat_id)
        await db.log_action(chat_id, "unmute", caller_id, target_id, "")

        await update.message.reply_text(
            f"🔊 **تم إلغاء الكتم**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ خطأ: {e.message}")


# ══════════════════════════════════════════
#                /banlist
# ══════════════════════════════════════════

async def banlist_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    banned = await db.get_banned_list(update.effective_chat.id)
    if not banned:
        await update.message.reply_text("✅ لا يوجد أعضاء محظورون!")
        return

    text = "🚫 **قائمة المحظورين:**\n\n"
    for i, u in enumerate(banned[:20], 1):
        text += f"{i}. `{u['user_id']}` — {u.get('reason','—')}\n"

    await update.message.reply_text(text, parse_mode="Markdown")
