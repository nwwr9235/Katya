"""
🛡️ معالجات أوامر الإدارة: Ban, Unban, Mute, Unmute
"""

import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import (
    UserAdminInvalid,
    ChatAdminRequired,
    PeerIdInvalid,
    UserNotParticipant,
)
from database import db

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
#         دوال المساعدة (Helpers)
# ══════════════════════════════════════════

async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """التحقق من كون المستخدم مشرفاً"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status.value in ("administrator", "owner")
    except Exception:
        return False


async def bot_has_permission(client: Client, chat_id: int, permission: str) -> bool:
    """التحقق من صلاحيات البوت في المجموعة"""
    try:
        me = await client.get_me()
        bot_member = await client.get_chat_member(chat_id, me.id)
        if permission == "ban":
            return bot_member.privileges.can_restrict_members
        elif permission == "delete":
            return bot_member.privileges.can_delete_messages
        return False
    except Exception:
        return False


def extract_target(message: Message):
    """استخراج المستخدم المستهدف من الرسالة أو الرد"""
    target_id = None
    reason = "لم يُحدد سبب"

    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        if len(message.command) > 1:
            reason = " ".join(message.command[1:])
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
            if len(message.command) > 2:
                reason = " ".join(message.command[2:])
        except ValueError:
            target_id = message.command[1].lstrip("@")
            if len(message.command) > 2:
                reason = " ".join(message.command[2:])

    return target_id, reason


# ══════════════════════════════════════════
#              أمر الحظر /ban
# ══════════════════════════════════════════

async def ban_user_handler(client: Client, message: Message):
    """معالج أمر الحظر"""
    chat_id = message.chat.id
    executor_id = message.from_user.id

    # التحقق من صلاحيات المشرف
    if not await is_admin(client, chat_id, executor_id):
        await message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط!")
        return

    # التحقق من صلاحيات البوت
    if not await bot_has_permission(client, chat_id, "ban"):
        await message.reply_text(
            "⚠️ البوت لا يملك صلاحية حظر الأعضاء!\n"
            "يرجى منح البوت صلاحية **تقييد الأعضاء**."
        )
        return

    target_id, reason = extract_target(message)

    if not target_id:
        await message.reply_text(
            "❓ **طريقة الاستخدام:**\n"
            "• رد على رسالة المستخدم: `/ban [السبب]`\n"
            "• أو: `/ban @username [السبب]`"
        )
        return

    try:
        # تنفيذ الحظر
        await client.ban_chat_member(chat_id, target_id)

        # حفظ في قاعدة البيانات
        await db.ban_user(target_id, chat_id, executor_id, reason)

        # تسجيل الإجراء
        await db.log_action(chat_id, "ban", executor_id, target_id, reason)

        executor_name = message.from_user.first_name
        await message.reply_text(
            f"🚫 **تم حظر المستخدم بنجاح**\n\n"
            f"👤 **المستخدم:** `{target_id}`\n"
            f"👮 **بواسطة:** {executor_name}\n"
            f"📝 **السبب:** {reason}\n"
            f"🕐 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        logger.info(f"تم حظر المستخدم {target_id} في المجموعة {chat_id}")

    except UserAdminInvalid:
        await message.reply_text("❌ لا يمكن حظر مشرف آخر!")
    except PeerIdInvalid:
        await message.reply_text("❌ المستخدم غير موجود أو معرّف غير صحيح!")
    except Exception as e:
        logger.error(f"خطأ في الحظر: {e}")
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")


# ══════════════════════════════════════════
#           أمر إلغاء الحظر /unban
# ══════════════════════════════════════════

async def unban_user_handler(client: Client, message: Message):
    """معالج أمر إلغاء الحظر"""
    chat_id = message.chat.id
    executor_id = message.from_user.id

    if not await is_admin(client, chat_id, executor_id):
        await message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط!")
        return

    if not await bot_has_permission(client, chat_id, "ban"):
        await message.reply_text("⚠️ البوت لا يملك الصلاحيات الكافية!")
        return

    target_id, reason = extract_target(message)

    if not target_id:
        await message.reply_text(
            "❓ **طريقة الاستخدام:**\n"
            "• `/unban @username`\n"
            "• `/unban [معرف المستخدم]`"
        )
        return

    try:
        await client.unban_chat_member(chat_id, target_id)
        await db.unban_user(target_id, chat_id)
        await db.log_action(chat_id, "unban", executor_id, target_id, "")

        executor_name = message.from_user.first_name
        await message.reply_text(
            f"✅ **تم إلغاء حظر المستخدم بنجاح**\n\n"
            f"👤 **المستخدم:** `{target_id}`\n"
            f"👮 **بواسطة:** {executor_name}\n"
            f"🕐 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        logger.info(f"تم إلغاء حظر المستخدم {target_id} في المجموعة {chat_id}")

    except Exception as e:
        logger.error(f"خطأ في إلغاء الحظر: {e}")
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")


# ══════════════════════════════════════════
#             أمر الكتم /mute
# ══════════════════════════════════════════

async def mute_user_handler(client: Client, message: Message):
    """معالج أمر الكتم"""
    chat_id = message.chat.id
    executor_id = message.from_user.id

    if not await is_admin(client, chat_id, executor_id):
        await message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط!")
        return

    if not await bot_has_permission(client, chat_id, "ban"):
        await message.reply_text("⚠️ البوت لا يملك صلاحية تقييد الأعضاء!")
        return

    target_id, reason = extract_target(message)

    if not target_id:
        await message.reply_text(
            "❓ **طريقة الاستخدام:**\n"
            "• رد على رسالة المستخدم: `/mute [السبب]`\n"
            "• `/mute @username [السبب]`"
        )
        return

    try:
        # كتم المستخدم (منع إرسال الرسائل)
        await client.restrict_chat_member(
            chat_id,
            target_id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
        )
        await db.mute_user(target_id, chat_id, executor_id)
        await db.log_action(chat_id, "mute", executor_id, target_id, reason)

        executor_name = message.from_user.first_name
        await message.reply_text(
            f"🔇 **تم كتم المستخدم بنجاح**\n\n"
            f"👤 **المستخدم:** `{target_id}`\n"
            f"👮 **بواسطة:** {executor_name}\n"
            f"📝 **السبب:** {reason}\n"
            f"🕐 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        logger.info(f"تم كتم المستخدم {target_id} في المجموعة {chat_id}")

    except UserAdminInvalid:
        await message.reply_text("❌ لا يمكن كتم مشرف آخر!")
    except Exception as e:
        logger.error(f"خطأ في الكتم: {e}")
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")


# ══════════════════════════════════════════
#           أمر إلغاء الكتم /unmute
# ══════════════════════════════════════════

async def unmute_user_handler(client: Client, message: Message):
    """معالج أمر إلغاء الكتم"""
    chat_id = message.chat.id
    executor_id = message.from_user.id

    if not await is_admin(client, chat_id, executor_id):
        await message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط!")
        return

    target_id, reason = extract_target(message)

    if not target_id:
        await message.reply_text(
            "❓ **طريقة الاستخدام:**\n"
            "• رد على رسالة المستخدم: `/unmute`\n"
            "• `/unmute @username`"
        )
        return

    try:
        # إعادة صلاحيات المستخدم
        await client.restrict_chat_member(
            chat_id,
            target_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await db.unmute_user(target_id, chat_id)
        await db.log_action(chat_id, "unmute", executor_id, target_id, "")

        executor_name = message.from_user.first_name
        await message.reply_text(
            f"🔊 **تم إلغاء كتم المستخدم بنجاح**\n\n"
            f"👤 **المستخدم:** `{target_id}`\n"
            f"👮 **بواسطة:** {executor_name}\n"
            f"🕐 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

    except Exception as e:
        logger.error(f"خطأ في إلغاء الكتم: {e}")
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")


# ══════════════════════════════════════════
#        أمر قائمة المحظورين /banlist
# ══════════════════════════════════════════

async def banlist_handler(client: Client, message: Message):
    """عرض قائمة المحظورين"""
    chat_id = message.chat.id
    executor_id = message.from_user.id

    if not await is_admin(client, chat_id, executor_id):
        await message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط!")
        return

    banned = await db.get_banned_list(chat_id)

    if not banned:
        await message.reply_text("✅ لا يوجد أعضاء محظورون في هذه المجموعة!")
        return

    text = "🚫 **قائمة الأعضاء المحظورين:**\n\n"
    for i, user in enumerate(banned[:20], 1):
        text += (
            f"{i}. `{user['user_id']}` — {user.get('reason', 'لا سبب')}\n"
        )

    if len(banned) > 20:
        text += f"\n...و {len(banned) - 20} آخرين"

    await message.reply_text(text)


# ══════════════════════════════════════════
#         تسجيل المعالجات
# ══════════════════════════════════════════

def register(app: Client):
    """تسجيل جميع معالجات الإدارة"""
    app.on_message(
        filters.command("ban") & filters.group
    )(ban_user_handler)

    app.on_message(
        filters.command("unban") & filters.group
    )(unban_user_handler)

    app.on_message(
        filters.command("mute") & filters.group
    )(mute_user_handler)

    app.on_message(
        filters.command("unmute") & filters.group
    )(unmute_user_handler)

    app.on_message(
        filters.command("banlist") & filters.group
    )(banlist_handler)

    logger.info("✅ تم تسجيل معالجات الإدارة")
