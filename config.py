"""
⚙️ ملف الإعدادات - قم بتعديل القيم حسب بياناتك
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    # ══════════════════════════════════════════
    #   إعدادات تيليجرام - احصل عليها من my.telegram.org
    # ══════════════════════════════════════════
    API_ID: int = int(os.environ.get("API_ID", 12345678))
    API_HASH: str = os.environ.get("API_HASH", "your_api_hash_here")
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "your_bot_token_here")

    # ══════════════════════════════════════════
    #   إعدادات المطور
    # ══════════════════════════════════════════
    DEVELOPER_NAME: str = os.environ.get("DEVELOPER_NAME", "أحمد المطور")
    DEVELOPER_USERNAME: str = os.environ.get("DEVELOPER_USERNAME", "developer")
    DEVELOPER_LINK: str = os.environ.get(
        "DEVELOPER_LINK", "https://t.me/developer"
    )

    # ══════════════════════════════════════════
    #   إعدادات قاعدة البيانات MongoDB
    # ══════════════════════════════════════════
    MONGO_URI: str = os.environ.get(
        "MONGO_URI", "mongodb://localhost:27017"
    )
    DB_NAME: str = os.environ.get("DB_NAME", "telegram_bot_db")

    # ══════════════════════════════════════════
    #   إعدادات المجموعة
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
