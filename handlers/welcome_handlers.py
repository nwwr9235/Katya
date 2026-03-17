"""
👋 معالجات الترحيب بالأعضاء الجدد مع أزرار Inline
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    ChatMemberUpdated,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from config import Config
from database import db

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
#      بناء أزرار رسالة الترحيب
# ══════════════════════════════════════════

def build_welcome_keyboard() -> InlineKeyboardMarkup:
    """إنشاء لوحة مفاتيح الترحيب"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 قوانين المجموعة", callback_data="show_rules"
                ),
                InlineKeyboardButton(
                    "👨‍💻 المطور", url=Config.DEVELOPER_LINK
                ),
            ],
            [
                InlineKeyboardButton(
                    "✅ قرأت القوانين وأوافق عليها", callback_data="accept_rules"
                )
            ],
            [
                InlineKeyboardButton(
                    "🆘 طلب المساعدة", callback_data="get_help"
                ),
                InlineKeyboardButton(
                    "📊 إحصائيات المجموعة", callback_data="group_stats"
                ),
            ],
        ]
    )


# ══════════════════════════════════════════
#      معالج انضمام عضو جديد
# ══════════════════════════════════════════

async def welcome_new_member(client: Client, message: Message):
    """إرسال رسالة ترحيب عند انضمام عضو جديد"""
    chat = message.chat

    for new_member in message.new_chat_members:
        # تجاهل البوتات
        if new_member.is_bot:
            continue

        # اسم المستخدم
        user_name = new_member.first_name
        if new_member.last_name:
            user_name += f" {new_member.last_name}"

        user_mention = f"[{user_name}](tg://user?id={new_member.id})"

        welcome_text = (
            f"🎉 **مرحباً بك في {chat.title}!**\n\n"
            f"👋 أهلاً وسهلاً بك يا {user_mention}\n\n"
            f"🌟 نحن سعداء بانضمامك إلينا!\n"
            f"📌 يرجى قراءة قوانين المجموعة قبل المشاركة.\n\n"
            f"💡 **معلومات سريعة:**\n"
            f"• عدد الأعضاء: `{await get_member_count(client, chat.id)}`\n"
            f"• المجموعة: **{chat.title}**\n\n"
            f"نتمنى لك وقتاً ممتعاً! 🚀"
        )

        # حفظ بيانات المستخدم الجديد
        await db.update_group_settings(
            chat.id,
            {"last_join": new_member.id}
        )

        await message.reply_text(
            welcome_text,
            reply_markup=build_welcome_keyboard(),
            disable_web_page_preview=True,
        )
        logger.info(f"تم ترحيب بالمستخدم {new_member.id} في {chat.id}")


async def get_member_count(client: Client, chat_id: int) -> int:
    """جلب عدد أعضاء المجموعة"""
    try:
        chat = await client.get_chat(chat_id)
        return chat.members_count or 0
    except Exception:
        return 0


# ══════════════════════════════════════════
#      معالج مغادرة العضو
# ══════════════════════════════════════════

async def farewell_member(client: Client, message: Message):
    """رسالة وداع عند مغادرة عضو"""
    left_member = message.left_chat_member

    if left_member and not left_member.is_bot:
        user_name = left_member.first_name
        await message.reply_text(
            f"👋 وداعاً {user_name}، نتمنى أن نراك مجدداً! 🌹"
        )


# ══════════════════════════════════════════
#      معالجات الأزرار (Callbacks)
# ══════════════════════════════════════════

async def callback_show_rules(client: Client, callback: CallbackQuery):
    """عرض قوانين المجموعة عند الضغط على الزر"""
    await callback.answer()
    await callback.message.reply_text(
        Config.GROUP_RULES,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 رجوع", callback_data="go_back")]]
        ),
    )


async def callback_accept_rules(client: Client, callback: CallbackQuery):
    """عند موافقة المستخدم على القوانين"""
    user_name = callback.from_user.first_name
    await callback.answer(f"✅ شكراً {user_name}! تم تسجيل موافقتك.", show_alert=True)

    # تحديث حالة المستخدم في قاعدة البيانات
    await db.update_group_settings(
        callback.message.chat.id,
        {f"accepted_rules.{callback.from_user.id}": True}
    )


async def callback_get_help(client: Client, callback: CallbackQuery):
    """عرض رسالة المساعدة"""
    await callback.answer()
    help_text = (
        "🆘 **مركز المساعدة**\n\n"
        "**أوامر المستخدمين:**\n"
        "• `/start` - بدء التشغيل\n"
        "• `/help` - عرض المساعدة\n"
        "• `/rules` - قوانين المجموعة\n\n"
        "**أوامر المشرفين:**\n"
        "• `/ban` - حظر عضو\n"
        "• `/unban` - إلغاء الحظر\n"
        "• `/mute` - كتم عضو\n"
        "• `/unmute` - إلغاء الكتم\n"
        "• `/banlist` - قائمة المحظورين\n\n"
        f"📞 للتواصل: {Config.DEVELOPER_LINK}"
    )
    await callback.message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 رجوع", callback_data="go_back")]]
        ),
    )


async def callback_group_stats(client: Client, callback: CallbackQuery):
    """عرض إحصائيات المجموعة"""
    await callback.answer("⏳ جاري جلب الإحصائيات...", show_alert=False)
    chat = callback.message.chat
    member_count = await get_member_count(client, chat.id)
    banned_count = len(await db.get_banned_list(chat.id))

    stats_text = (
        f"📊 **إحصائيات {chat.title}**\n\n"
        f"👥 عدد الأعضاء: `{member_count}`\n"
        f"🚫 المحظورون: `{banned_count}`\n"
        f"🤖 البوت: نشط ✅\n"
        f"🗄️ قاعدة البيانات: متصلة ✅"
    )
    await callback.message.reply_text(stats_text)


async def callback_go_back(client: Client, callback: CallbackQuery):
    """العودة للرسالة الأصلية"""
    await callback.answer()
    await callback.message.delete()


# ══════════════════════════════════════════
#          أمر /rules للمجموعة
# ══════════════════════════════════════════

async def rules_command(client: Client, message: Message):
    """عرض قوانين المجموعة"""
    await message.reply_text(
        Config.GROUP_RULES,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ أوافق على القوانين", callback_data="accept_rules"
                    )
                ]
            ]
        ),
    )


# ══════════════════════════════════════════
#         تسجيل المعالجات
# ══════════════════════════════════════════

def register(app: Client):
    """تسجيل جميع معالجات الترحيب"""
    # معالج الأعضاء الجدد
    app.on_message(
        filters.new_chat_members & filters.group
    )(welcome_new_member)

    # معالج مغادرة الأعضاء
    app.on_message(
        filters.left_chat_member & filters.group
    )(farewell_member)

    # معالج أمر القوانين
    app.on_message(
        filters.command("rules") & filters.group
    )(rules_command)

    # معالجات الأزرار
    app.on_callback_query(filters.regex("^show_rules$"))(callback_show_rules)
    app.on_callback_query(filters.regex("^accept_rules$"))(callback_accept_rules)
    app.on_callback_query(filters.regex("^get_help$"))(callback_get_help)
    app.on_callback_query(filters.regex("^group_stats$"))(callback_group_stats)
    app.on_callback_query(filters.regex("^go_back$"))(callback_go_back)

    logger.info("✅ تم تسجيل معالجات الترحيب")
