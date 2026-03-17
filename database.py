"""
🗄️ قاعدة البيانات الكاملة - Motor (MongoDB)
"""
import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(Config.MONGO_URI)
            self.db = self.client[Config.DB_NAME]
            await self.client.admin.command("ping")
            logger.info("✅ MongoDB متصل")
        except Exception as e:
            logger.error(f"❌ MongoDB: {e}")

    async def close(self):
        if self.client:
            self.client.close()

    # ══════════════════════════════════════════
    #              المحظورون
    # ══════════════════════════════════════════

    async def ban_user(self, user_id, chat_id, banned_by, reason="لم يُحدد"):
        try:
            await self.db.banned_users.update_one(
                {"user_id": user_id, "chat_id": chat_id},
                {"$set": {"user_id": user_id, "chat_id": chat_id,
                          "banned_by": banned_by, "reason": reason,
                          "banned_at": datetime.utcnow()}},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"ban_user: {e}")
            return False

    async def unban_user(self, user_id, chat_id):
        try:
            await self.db.banned_users.delete_one({"user_id": user_id, "chat_id": chat_id})
            return True
        except Exception as e:
            logger.error(f"unban_user: {e}")
            return False

    async def get_banned_list(self, chat_id):
        try:
            return await self.db.banned_users.find({"chat_id": chat_id}).to_list(100)
        except Exception:
            return []

    # ══════════════════════════════════════════
    #              المكتومون
    # ══════════════════════════════════════════

    async def mute_user(self, user_id, chat_id, muted_by):
        try:
            await self.db.muted_users.update_one(
                {"user_id": user_id, "chat_id": chat_id},
                {"$set": {"user_id": user_id, "chat_id": chat_id,
                          "muted_by": muted_by, "muted_at": datetime.utcnow()}},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"mute_user: {e}")
            return False

    async def unmute_user(self, user_id, chat_id):
        try:
            await self.db.muted_users.delete_one({"user_id": user_id, "chat_id": chat_id})
            return True
        except Exception as e:
            logger.error(f"unmute_user: {e}")
            return False

    # ══════════════════════════════════════════
    #              التحذيرات
    # ══════════════════════════════════════════

    async def add_warn(self, user_id, chat_id, warned_by, reason):
        try:
            await self.db.warns.insert_one({
                "user_id": user_id, "chat_id": chat_id,
                "warned_by": warned_by, "reason": reason,
                "warned_at": datetime.utcnow()
            })
            return await self.db.warns.count_documents({"user_id": user_id, "chat_id": chat_id})
        except Exception as e:
            logger.error(f"add_warn: {e}")
            return 0

    async def get_warns(self, user_id, chat_id):
        try:
            return await self.db.warns.count_documents({"user_id": user_id, "chat_id": chat_id})
        except Exception:
            return 0

    async def reset_warns(self, user_id, chat_id):
        try:
            await self.db.warns.delete_many({"user_id": user_id, "chat_id": chat_id})
            return True
        except Exception as e:
            logger.error(f"reset_warns: {e}")
            return False

    # ══════════════════════════════════════════
    #        بروفايلات المستخدمين (اضف ردي)
    # ══════════════════════════════════════════

    async def save_user_profile(self, user_id, chat_id, display_name, photo_id, username):
        """حفظ بروفايل المستخدم (اضف ردي)"""
        try:
            await self.db.user_profiles.update_one(
                {"user_id": user_id, "chat_id": chat_id},
                {"$set": {
                    "user_id": user_id, "chat_id": chat_id,
                    "display_name": display_name,
                    "photo_id": photo_id,
                    "username": username,
                    "saved_at": datetime.utcnow()
                }},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"save_user_profile: {e}")
            return False

    async def get_all_profiles(self, chat_id):
        """جلب جميع البروفايلات المسجلة في مجموعة"""
        try:
            return await self.db.user_profiles.find({"chat_id": chat_id}).to_list(500)
        except Exception:
            return []

    # ══════════════════════════════════════════
    #         الردود التلقائية المخصصة
    # ══════════════════════════════════════════

    async def add_custom_reply(self, chat_id, keyword, reply, added_by, photo_id=None):
        """إضافة رد تلقائي (نص أو صورة)"""
        try:
            await self.db.custom_replies.update_one(
                {"chat_id": chat_id, "keyword": keyword},
                {"$set": {
                    "chat_id": chat_id, "keyword": keyword,
                    "reply": reply, "photo_id": photo_id,
                    "added_by": added_by, "added_at": datetime.utcnow()
                }},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"add_custom_reply: {e}")
            return False

    async def delete_custom_reply(self, chat_id, keyword):
        try:
            result = await self.db.custom_replies.delete_one({"chat_id": chat_id, "keyword": keyword})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"delete_custom_reply: {e}")
            return False

    async def get_all_replies(self, chat_id):
        try:
            return await self.db.custom_replies.find({"chat_id": chat_id}).to_list(200)
        except Exception:
            return []

    # ══════════════════════════════════════════
    #              سجل الإجراءات
    # ══════════════════════════════════════════

    async def log_action(self, chat_id, action, by_user, on_user, reason):
        try:
            await self.db.admin_logs.insert_one({
                "chat_id": chat_id, "action": action,
                "by_user": by_user, "on_user": on_user,
                "reason": reason, "timestamp": datetime.utcnow(),
            })
        except Exception as e:
            logger.error(f"log_action: {e}")


db = Database()
