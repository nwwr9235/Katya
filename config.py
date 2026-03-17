"""
⚙️ ملف الإعدادات
"""
import os


class Config:
    # ══════════════════════════════════════════
    #   تيليجرام - من @BotFather
    # ══════════════════════════════════════════
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")

    # ══════════════════════════════════════════
    #   Webhook - يُعبأ تلقائياً من Railway
    # ══════════════════════════════════════════
    WEBHOOK_URL: str = os.environ.get("WEBHOOK_URL", "")
    PORT: int = int(os.environ.get("PORT", 8080))

    # ══════════════════════════════════════════
    #   المطور
    # ══════════════════════════════════════════
    DEVELOPER_NAME: str     = os.environ.get("DEVELOPER_NAME", "المطور")
    DEVELOPER_USERNAME: str = os.environ.get("DEVELOPER_USERNAME", "username")
    DEVELOPER_LINK: str     = os.environ.get("DEVELOPER_LINK", "https://t.me/username")

    # ══════════════════════════════════════════
    #   MongoDB
    # ══════════════════════════════════════════
    MONGO_URI: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str   = os.environ.get("DB_NAME", "telegram_bot_db")

    # ══════════════════════════════════════════
    #   قوانين المجموعة
    # ══════════════════════════════════════════
    GROUP_RULES: str = """
📋 **قوانين المجموعة:**

1️⃣ الاحترام المتبادل بين الأعضاء
2️⃣ عدم نشر الإعلانات أو السبام
3️⃣ عدم نشر محتوى مسيء أو غير لائق
4️⃣ الالتزام بموضوع المجموعة
5️⃣ عدم مشاركة روابط خارجية دون إذن

⚠️ مخالفة القوانين تؤدي إلى الحظر الفوري!
"""
