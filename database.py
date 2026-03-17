"""
🗄️ وحدة قاعدة البيانات - Motor (MongoDB غير متزامن)
"""

import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

logger = logging.getLogger(__name__)


class Database:
    """كلاس إدارة قاعدة البيانات باستخدام Motor"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        """الاتصال بقاعدة البيانات"""
        try:
            self.client = AsyncIOMotorClient(Config.MONGO_URI)
            self.db = self.client[Config.DB_NAME]
            # اختبار الاتصال
            await self.client.admin.command("ping")
            logger.info("✅ تم الاتصال بـ MongoDB بنجاح")
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بـ MongoDB: {e}")
            raise

    async def close(self):
        """إغلاق الاتصال"""
        if self.client:
            self.client.close()
            logger.info("🔌 تم قطع الاتصال بـ MongoDB")

    # ══════════════════════════════════════════
    #            إدارة المستخدمين المحظورين
    # ══════════════════════════════════════════

    async def ban_user(
        self,
        user_id: int,
        chat_id: int,
        banned_by: int,
        reason: str = "لم يُحدد سبب",
    ) -> bool:
        """حظر مستخدم وحفظه في قاعدة البيانات"""
        try:
            await self.db.banned_users.update_one(
                {"user_id": user_id, "chat_id": chat_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "chat_id": chat_id,
                        "banned_by": banned_by,
                        "reason": reason,
                        "banned_at": datetime.utcnow(),
                    }
                },
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ بيانات الحظر: {e}")
            return False

    async def unban_user(self, user_id: int, chat_id: int) -> bool:
        """إلغاء حظر مستخدم من قاعدة البيانات"""
        try:
            result = await self.db.banned_users.delete_one(
                {"user_id": user_id, "chat_id": chat_id}
            )
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"خطأ في إلغاء الحظر: {e}")
            return False

    async def is_banned(self, user_id: int, chat_id: int) -> bool:
        """التحقق من حظر المستخدم"""
        doc = await self.db.banned_users.find_one(
            {"user_id": user_id, "chat_id": chat_id}
        )
        return doc is not None

    async def get_banned_list(self, chat_id: int) -> list:
        """جلب قائمة المحظورين في مجموعة"""
        cursor = self.db.banned_users.find({"chat_id": chat_id})
        return await cursor.to_list(length=100)

    # ══════════════════════════════════════════
    #            إدارة المكتومين (Muted)
    # ══════════════════════════════════════════

    async def mute_user(
        self,
        user_id: int,
        chat_id: int,
        muted_by: int,
        duration: Optional[int] = None,
    ) -> bool:
        """كتم مستخدم وحفظه في قاعدة البيانات"""
        try:
            await self.db.muted_users.update_one(
                {"user_id": user_id, "chat_id": chat_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "chat_id": chat_id,
                        "muted_by": muted_by,
                        "duration": duration,
                        "muted_at": datetime.utcnow(),
                    }
                },
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ بيانات الكتم: {e}")
            return False

    async def unmute_user(self, user_id: int, chat_id: int) -> bool:
        """إلغاء كتم مستخدم"""
        try:
            result = await self.db.muted_users.delete_one(
                {"user_id": user_id, "chat_id": chat_id}
            )
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"خطأ في إلغاء الكتم: {e}")
            return False

    # ══════════════════════════════════════════
    #            إعدادات المجموعة
    # ══════════════════════════════════════════

    async def get_group_settings(self, chat_id: int) -> dict:
        """جلب إعدادات المجموعة"""
        doc = await self.db.group_settings.find_one({"chat_id": chat_id})
        if not doc:
            # إعدادات افتراضية
            default = {
                "chat_id": chat_id,
                "welcome_enabled": True,
                "anti_spam": True,
                "language": "ar",
                "created_at": datetime.utcnow(),
            }
            await self.db.group_settings.insert_one(default)
            return default
        return doc

    async def update_group_settings(self, chat_id: int, settings: dict) -> bool:
        """تحديث إعدادات المجموعة"""
        try:
            await self.db.group_settings.update_one(
                {"chat_id": chat_id},
                {"$set": settings},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"خطأ في تحديث إعدادات المجموعة: {e}")
            return False

    # ══════════════════════════════════════════
    #            إحصائيات المجموعة
    # ══════════════════════════════════════════

    async def log_action(
        self, chat_id: int, action: str, by_user: int, on_user: int, reason: str
    ):
        """تسجيل إجراءات الإدارة"""
        await self.db.admin_logs.insert_one(
            {
                "chat_id": chat_id,
                "action": action,
                "by_user": by_user,
                "on_user": on_user,
                "reason": reason,
                "timestamp": datetime.utcnow(),
            }
        )


# إنشاء نسخة واحدة من قاعدة البيانات (Singleton)
db = Database()
