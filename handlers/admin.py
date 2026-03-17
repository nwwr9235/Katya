"""
🛡️ أوامر الإدارة بالعربية بدون / أو .
حظر - كتم - رفع - تنزيل - تحذير - تثبيت - حذف
"""
import logging
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from database import db

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
#              دوال مساعدة
# ══════════════════════════════════════════

async def is_admin(update: Update, user_id: int) -> bool:
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def bot_is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        bot_member = await update.effective_chat.get_member(context.bot.id)
        return bot_member.status in ("administrator", "creator")
    except Exception:
        return False


def get_target(update: Update, args: list):
    """استخراج المستخدم المستهدف والسبب"""
    target_id = None
    reason    = "لم يُحدد سبب"

    # إذا كان رداً على رسالة
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        if args:
            reason = " ".join(args)
    elif args:
        target_id = args[0].lstrip("@")
        if len(args) > 1:
            reason = " ".join(args[1:])

    return target_id, reason


def parse_duration(text: str) -> int:
    """تحويل النص لثواني: 1d يوم 1h ساعة 1m دقيقة"""
    if not text:
        return 0
    units = {"d": 86400, "h": 3600, "m": 60}
    unit  = text[-1].lower()
    if unit in units:
        try:
            return int(text[:-1]) * units[unit]
        except ValueError:
            return 0
    return 0


# ══════════════════════════════════════════
#    معالج الرسائل النصية للأوامر العربية
# ══════════════════════════════════════════

async def arabic_commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يستمع لجميع رسائل المجموعة ويكشف الأوامر العربية:
    حظر - فك حظر - كتم - فك كتم - رفع - تنزيل
    تحذير - تثبيت - حذف - حظر مؤقت
    """
    if not update.message or not update.message.text:
        return

    text      = update.message.text.strip()
    parts     = text.split()
    command   = parts[0].lower() if parts else ""
    args      = parts[1:] if len(parts) > 1 else []
    chat_id   = update.effective_chat.id
    caller_id = update.effective_user.id

    # ── حظر ──
    if command == "حظر":
        await _ban(update, context, chat_id, caller_id, args)

    # ── فك حظر ──
    elif command in ("فك حظر", "فك_حظر", "الغاء حظر", "الغاء_حظر"):
        await _unban(update, context, chat_id, caller_id, args)

    # ── كتم ──
    elif command == "كتم":
        await _mute(update, context, chat_id, caller_id, args)

    # ── فك كتم ──
    elif command in ("فك كتم", "فك_كتم", "الغاء كتم"):
        await _unmute(update, context, chat_id, caller_id, args)

    # ── رفع مشرف ──
    elif command == "رفع":
        await _promote(update, context, chat_id, caller_id, args)

    # ── تنزيل مشرف ──
    elif command == "تنزيل":
        await _demote(update, context, chat_id, caller_id, args)

    # ── تحذير ──
    elif command == "تحذير":
        await _warn(update, context, chat_id, caller_id, args)

    # ── تثبيت ──
    elif command == "تثبيت":
        await _pin(update, context, chat_id, caller_id)

    # ── حذف ──
    elif command == "حذف":
        await _delete(update, context, caller_id)

    # ── حظر مؤقت ──
    elif command == "حظر_مؤقت" or command == "حظر مؤقت":
        await _tban(update, context, chat_id, caller_id, args)


# ══════════════════════════════════════════
#                  حظر
# ══════════════════════════════════════════

async def _ban(update, context, chat_id, caller_id, args):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return
    if not await bot_is_admin(update, context):
        await update.message.reply_text("⚠️ البوت ليس مشرفاً!")
        return

    target_id, reason = get_target(update, args)
    if not target_id:
        await update.message.reply_text(
            "❓ **الاستخدام:**\n"
            "رد على رسالة المستخدم واكتب: `حظر [السبب]`\n"
            "أو: `حظر @username [السبب]`",
            parse_mode="Markdown"
        )
        return

    try:
        await context.bot.ban_chat_member(chat_id, target_id)
        await db.ban_user(target_id, chat_id, caller_id, reason)
        await db.log_action(chat_id, "ban", caller_id, target_id, reason)
        await update.message.reply_text(
            f"🚫 **تم الحظر**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}\n"
            f"📝 السبب: {reason}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")


# ══════════════════════════════════════════
#               فك الحظر
# ══════════════════════════════════════════

async def _unban(update, context, chat_id, caller_id, args):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    target_id, _ = get_target(update, args)
    if not target_id:
        await update.message.reply_text("❓ الاستخدام: `فك حظر @username`", parse_mode="Markdown")
        return

    try:
        await context.bot.unban_chat_member(chat_id, target_id)
        await db.unban_user(target_id, chat_id)
        await update.message.reply_text(
            f"✅ **تم فك الحظر**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")


# ══════════════════════════════════════════
#                  كتم
# ══════════════════════════════════════════

async def _mute(update, context, chat_id, caller_id, args):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return
    if not await bot_is_admin(update, context):
        await update.message.reply_text("⚠️ البوت ليس مشرفاً!")
        return

    target_id, reason = get_target(update, args)
    if not target_id:
        await update.message.reply_text(
            "❓ رد على رسالة المستخدم واكتب: `كتم [السبب]`",
            parse_mode="Markdown"
        )
        return

    try:
        await context.bot.restrict_chat_member(
            chat_id, target_id,
            ChatPermissions(can_send_messages=False)
        )
        await db.mute_user(target_id, chat_id, caller_id)
        await update.message.reply_text(
            f"🔇 **تم الكتم**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}\n"
            f"📝 السبب: {reason}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")


# ══════════════════════════════════════════
#                فك الكتم
# ══════════════════════════════════════════

async def _unmute(update, context, chat_id, caller_id, args):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    target_id, _ = get_target(update, args)
    if not target_id:
        await update.message.reply_text("❓ رد على رسالة المستخدم واكتب: `فك كتم`", parse_mode="Markdown")
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
        await update.message.reply_text(
            f"🔊 **تم فك الكتم**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")


# ══════════════════════════════════════════
#               رفع مشرف
# ══════════════════════════════════════════

async def _promote(update, context, chat_id, caller_id, args):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return
    if not await bot_is_admin(update, context):
        await update.message.reply_text("⚠️ البوت ليس مشرفاً أو لا يملك صلاحية رفع المشرفين!")
        return

    target_id, title = get_target(update, args)
    if not target_id:
        await update.message.reply_text(
            "❓ رد على رسالة المستخدم واكتب: `رفع [اللقب]`",
            parse_mode="Markdown"
        )
        return

    try:
        await context.bot.promote_chat_member(
            chat_id, target_id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_invite_users=True,
        )
        if title and title != "لم يُحدد سبب":
            try:
                await context.bot.set_chat_administrator_custom_title(chat_id, target_id, title[:16])
            except Exception:
                pass

        await db.log_action(chat_id, "promote", caller_id, target_id, title)
        await update.message.reply_text(
            f"⬆️ **تم رفع العضو لمشرف**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"🏷️ اللقب: {title if title != 'لم يُحدد سبب' else '—'}\n"
            f"👮 بواسطة: {update.effective_user.first_name}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")


# ══════════════════════════════════════════
#               تنزيل مشرف
# ══════════════════════════════════════════

async def _demote(update, context, chat_id, caller_id, args):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return
    if not await bot_is_admin(update, context):
        await update.message.reply_text("⚠️ البوت ليس مشرفاً!")
        return

    target_id, _ = get_target(update, args)
    if not target_id:
        await update.message.reply_text("❓ رد على رسالة المستخدم واكتب: `تنزيل`", parse_mode="Markdown")
        return

    try:
        await context.bot.promote_chat_member(
            chat_id, target_id,
            can_delete_messages=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_invite_users=False,
            can_manage_chat=False,
        )
        await db.log_action(chat_id, "demote", caller_id, target_id, "")
        await update.message.reply_text(
            f"⬇️ **تم تنزيل المشرف**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"👮 بواسطة: {update.effective_user.first_name}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")


# ══════════════════════════════════════════
#                 تحذير
# ══════════════════════════════════════════

async def _warn(update, context, chat_id, caller_id, args):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    target_id, reason = get_target(update, args)
    if not target_id:
        await update.message.reply_text("❓ رد على رسالة المستخدم واكتب: `تحذير [السبب]`", parse_mode="Markdown")
        return

    warns = await db.add_warn(target_id, chat_id, caller_id, reason)

    if warns >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, target_id)
            await db.reset_warns(target_id, chat_id)
            await db.ban_user(target_id, chat_id, caller_id, "تجاوز 3 تحذيرات")
            await update.message.reply_text(
                f"🚫 **تم الحظر تلقائياً!**\n\n"
                f"👤 المستخدم: `{target_id}`\n"
                f"⚠️ وصل إلى **3 تحذيرات**",
                parse_mode="Markdown"
            )
        except BadRequest as e:
            await update.message.reply_text(f"❌ {e.message}")
    else:
        await update.message.reply_text(
            f"⚠️ **تحذير!**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"📝 السبب: {reason}\n"
            f"🔢 التحذيرات: **{warns}/3**\n\n"
            f"{'⛔ تحذير أخير قبل الحظر!' if warns == 2 else ''}",
            parse_mode="Markdown"
        )


# ══════════════════════════════════════════
#                 تثبيت
# ══════════════════════════════════════════

async def _pin(update, context, chat_id, caller_id):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❓ رد على الرسالة التي تريد تثبيتها واكتب: `تثبيت`")
        return

    try:
        await context.bot.pin_chat_message(chat_id, update.message.reply_to_message.message_id)
        await update.message.reply_text("📌 **تم تثبيت الرسالة!**", parse_mode="Markdown")
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")


# ══════════════════════════════════════════
#                  حذف
# ══════════════════════════════════════════

async def _delete(update, context, caller_id):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❓ رد على الرسالة التي تريد حذفها واكتب: `حذف`")
        return

    try:
        await update.message.reply_to_message.delete()
        await update.message.delete()
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")


# ══════════════════════════════════════════
#               حظر مؤقت
# ══════════════════════════════════════════

async def _tban(update, context, chat_id, caller_id, args):
    if not await is_admin(update, caller_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط!")
        return

    target_id, _ = get_target(update, args)
    duration_str  = args[1] if len(args) > 1 else (args[0] if args else "")
    duration_secs = parse_duration(duration_str)

    if not target_id or not duration_secs:
        await update.message.reply_text(
            "❓ رد على رسالة المستخدم واكتب:\n"
            "`حظر_مؤقت 2h [السبب]`\n\n"
            "الوحدات: `m` دقيقة | `h` ساعة | `d` يوم",
            parse_mode="Markdown"
        )
        return

    until = datetime.utcnow() + timedelta(seconds=duration_secs)
    try:
        await context.bot.ban_chat_member(chat_id, target_id, until_date=until)
        await db.ban_user(target_id, chat_id, caller_id, f"حظر مؤقت {duration_str}")
        await update.message.reply_text(
            f"⏱ **تم الحظر المؤقت**\n\n"
            f"👤 المستخدم: `{target_id}`\n"
            f"⏳ المدة: **{duration_str}**\n"
            f"👮 بواسطة: {update.effective_user.first_name}",
            parse_mode="Markdown"
        )
    except BadRequest as e:
        await update.message.reply_text(f"❌ {e.message}")
