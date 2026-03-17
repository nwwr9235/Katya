"""
🔊 معالجات المكالمات الجماعية - هيكل أساسي باستخدام PyGalls
ملاحظة: PyGalls (أو pytgcalls) مكتبة للمكالمات الجماعية في تيليجرام
"""

import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
#    تهيئة PyGalls (pytgcalls)
# ══════════════════════════════════════════

class CallsManager:
    """
    مدير المكالمات الجماعية باستخدام PyGalls (pytgcalls).
    
    📦 لتفعيل هذه الميزة، قم بتثبيت:
        pip install py-tgcalls
    
    ثم قم بإلغاء تعليق الكود أدناه.
    """

    def __init__(self):
        self.pytgcalls_client = None
        self.active_calls: dict = {}  # {chat_id: call_info}
        self.is_initialized = False

    async def initialize(self, pyrogram_client: Client):
        """تهيئة مكتبة PyGalls"""
        try:
            # ══════════════════════════════════════
            # قم بإلغاء التعليق عند تثبيت pytgcalls:
            # ══════════════════════════════════════
            #
            # from pytgcalls import PyTgCalls
            # from pytgcalls.types import MediaStream
            # from pytgcalls.types.stream import AudioPiped
            #
            # self.pytgcalls_client = PyTgCalls(pyrogram_client)
            # await self.pytgcalls_client.start()
            # self.is_initialized = True
            # logger.info("✅ تم تهيئة PyGalls بنجاح")

            logger.info(
                "⚠️  PyGalls: الهيكل جاهز - قم بتثبيت py-tgcalls لتفعيل المكالمات"
            )
        except ImportError:
            logger.warning("⚠️  مكتبة py-tgcalls غير مثبتة. المكالمات غير متاحة.")
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة PyGalls: {e}")

    async def join_voice_chat(self, chat_id: int, audio_file: str = None):
        """
        الانضمام لمكالمة جماعية وتشغيل ملف صوتي
        
        المعاملات:
            chat_id: معرف المجموعة
            audio_file: مسار الملف الصوتي (اختياري)
        """
        if not self.is_initialized:
            return False, "❌ PyGalls غير مهيأ"

        try:
            # ══════════════════════════════════════
            # قم بإلغاء التعليق عند تثبيت pytgcalls:
            # ══════════════════════════════════════
            #
            # if audio_file:
            #     await self.pytgcalls_client.join_group_call(
            #         chat_id,
            #         AudioPiped(audio_file),
            #     )
            # else:
            #     await self.pytgcalls_client.join_group_call(
            #         chat_id,
            #         MediaStream("https://example.com/audio.mp3"),
            #     )
            # self.active_calls[chat_id] = {"status": "playing", "file": audio_file}
            # return True, "✅ تم الانضمام للمكالمة"

            return False, "⚠️  يرجى تثبيت py-tgcalls أولاً"
        except Exception as e:
            return False, f"❌ خطأ: {e}"

    async def leave_voice_chat(self, chat_id: int):
        """مغادرة المكالمة الجماعية"""
        if not self.is_initialized:
            return False, "❌ PyGalls غير مهيأ"

        try:
            # await self.pytgcalls_client.leave_group_call(chat_id)
            # self.active_calls.pop(chat_id, None)
            # return True, "✅ تم مغادرة المكالمة"
            return False, "⚠️  يرجى تثبيت py-tgcalls أولاً"
        except Exception as e:
            return False, f"❌ خطأ: {e}"

    async def pause_playback(self, chat_id: int):
        """إيقاف مؤقت للتشغيل"""
        try:
            # await self.pytgcalls_client.pause_stream(chat_id)
            return True, "⏸ تم الإيقاف المؤقت"
        except Exception as e:
            return False, f"❌ خطأ: {e}"

    async def resume_playback(self, chat_id: int):
        """استئناف التشغيل"""
        try:
            # await self.pytgcalls_client.resume_stream(chat_id)
            return True, "▶️ تم استئناف التشغيل"
        except Exception as e:
            return False, f"❌ خطأ: {e}"

    def get_active_calls(self) -> dict:
        """جلب المكالمات النشطة"""
        return self.active_calls.copy()


# نسخة واحدة من مدير المكالمات
calls_manager = CallsManager()


# ══════════════════════════════════════════
#     دالة التهيئة الخارجية
# ══════════════════════════════════════════

async def initialize_calls(client: Client):
    """تهيئة نظام المكالمات"""
    await calls_manager.initialize(client)


# ══════════════════════════════════════════
#        معالجات أوامر المكالمات
# ══════════════════════════════════════════

async def join_call_command(client: Client, message: Message):
    """أمر الانضمام للمكالمة /joincall"""
    chat_id = message.chat.id

    # التحقق من المشرف
    from handlers.admin_handlers import is_admin
    if not await is_admin(client, chat_id, message.from_user.id):
        await message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط!")
        return

    processing_msg = await message.reply_text("⏳ جاري الانضمام للمكالمة...")

    audio_file = None
    if len(message.command) > 1:
        audio_file = message.command[1]

    success, result_msg = await calls_manager.join_voice_chat(chat_id, audio_file)

    await processing_msg.edit_text(
        f"🎵 **حالة المكالمة**\n\n{result_msg}\n\n"
        f"💡 **ملاحظة:** لتفعيل المكالمات الحقيقية،\n"
        f"قم بتثبيت: `pip install py-tgcalls`",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏸ إيقاف مؤقت", callback_data=f"pause_call_{chat_id}"),
                    InlineKeyboardButton("⏹ إنهاء", callback_data=f"leave_call_{chat_id}"),
                ]
            ]
        ),
    )


async def leave_call_command(client: Client, message: Message):
    """أمر مغادرة المكالمة /leavecall"""
    chat_id = message.chat.id

    from handlers.admin_handlers import is_admin
    if not await is_admin(client, chat_id, message.from_user.id):
        await message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط!")
        return

    success, result_msg = await calls_manager.leave_voice_chat(chat_id)
    await message.reply_text(f"🔇 **المكالمة**\n\n{result_msg}")


async def call_status_command(client: Client, message: Message):
    """عرض حالة المكالمات /callstatus"""
    active = calls_manager.get_active_calls()

    if not active:
        await message.reply_text(
            "📵 **لا توجد مكالمات نشطة حالياً**\n\n"
            "💡 استخدم `/joincall` للانضمام لمكالمة"
        )
        return

    status_text = "📞 **المكالمات النشطة:**\n\n"
    for chat_id, info in active.items():
        status_text += f"• المجموعة `{chat_id}`: {info.get('status', 'غير معروف')}\n"

    await message.reply_text(status_text)


# ══════════════════════════════════════════
#         تسجيل المعالجات
# ══════════════════════════════════════════

def register(app: Client):
    """تسجيل معالجات المكالمات"""
    app.on_message(
        filters.command("joincall") & filters.group
    )(join_call_command)

    app.on_message(
        filters.command("leavecall") & filters.group
    )(leave_call_command)

    app.on_message(
        filters.command("callstatus") & filters.group
    )(call_status_command)

    logger.info("✅ تم تسجيل معالجات المكالمات (هيكل PyGalls جاهز)")
