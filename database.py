"""
🗄️ قاعدة البيانات - Motor (MongoDB غير متزامن)
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
            logger.error(f"❌ فشل الاتصال بـ MongoDB: {e}")

    async def close(self):
        if self.client:
            self.client.close()

    # ── المحظورون ──
    async def ban_user(self, user_id: int, chat_id: int, banned_by: int, reason: str = "لم يُحدد") -> bool:
        try:
            await self.db.banned_users.update_one(
                {"user_id": user_id, "chat_id": chat_id},
                {"$set": {
                    "user_id": user_id, "chat_id": chat_id,
                    "banned_by": banned_by, "reason": reason,
                    "banned_at": datetime.utcnow()
                }},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"خطأ ban_user: {e}")
            return False

    async def unban_user(self, user_id: int, chat_id: int) -> bool:
        try:
            result = await self.db.banned_users.delete_one({"user_id": user_id, "chat_id": chat_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"خطأ unban_user: {e}")
            return False

    async def get_banned_list(self, chat_id: int) -> list:
        try:
            cursor = self.db.banned_users.find({"chat_id": chat_id})
            return await cursor.to_list(length=100)
        except Exception:
            return []

    # ── المكتومون ──
    async def mute_user(self, user_id: int, chat_id: int, muted_by: int) -> bool:
        try:
            await self.db.muted_users.update_one(
                {"user_id": user_id, "chat_id": chat_id},
                {"$set": {
                    "user_id": user_id, "chat_id": chat_id,
                    "muted_by": muted_by, "muted_at": datetime.utcnow()
                }},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"خطأ mute_user: {e}")
            return False

    async def unmute_user(self, user_id: int, chat_id: int) -> bool:
        try:
            result = await self.db.muted_users.delete_one({"user_id": user_id, "chat_id": chat_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"خطأ unmute_user: {e}")
            return False

    # ── السجل ──
    async def log_action(self, chat_id: int, action: str, by_user: int, on_user: int, reason: str):
        try:
            await self.db.admin_logs.insert_one({
                "chat_id": chat_id, "action": action,
                "by_user": by_user, "on_user": on_user,
                "reason": reason, "timestamp": datetime.utcnow(),
            })
        except Exception as e:
            logger.error(f"خطأ log_action: {e}")


db = Database()
