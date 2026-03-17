# 🤖 بوت إدارة المجموعات - Telegram Group Manager Bot

بوت تيليجرام متكامل لإدارة المجموعات مبني بـ Python 3.10 و Pyrogram 2.0

---

## 🗂️ هيكل المشروع

```
telegram_bot/
│
├── bot.py                    # ← نقطة الدخول الرئيسية
├── config.py                 # ← الإعدادات والمتغيرات
├── database.py               # ← قاعدة البيانات (Motor/MongoDB)
├── requirements.txt          # ← المتطلبات
├── .env.example              # ← نموذج ملف الإعدادات
│
└── handlers/                 # ← مجلد المعالجات
    ├── __init__.py
    ├── admin_handlers.py     # ← Ban, Unban, Mute, Unmute
    ├── welcome_handlers.py   # ← الترحيب + Inline Buttons
    ├── interactive_handlers.py # ← الردود الذكية
    └── calls_handlers.py     # ← هيكل PyGalls للمكالمات
```

---

## 📦 التثبيت

### 1. استنساخ المشروع
```bash
git clone <repo_url>
cd telegram_bot
```

### 2. إنشاء بيئة افتراضية
```bash
python3.10 -m venv venv
source venv/bin/activate   # Linux/Mac
# أو: venv\Scripts\activate  # Windows
```

### 3. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 4. إعداد المتغيرات البيئية
```bash
cp .env.example .env
nano .env   # أو أي محرر نصوص
```

### 5. الحصول على بيانات تيليجرام
- `API_ID` و `API_HASH`: من [my.telegram.org](https://my.telegram.org)
- `BOT_TOKEN`: من [@BotFather](https://t.me/BotFather)

### 6. تشغيل البوت
```bash
python bot.py
```

---

## 🔧 الميزات

### 🛡️ نظام الإدارة
| الأمر | الوصف | المستخدم |
|-------|-------|---------|
| `/ban [مستخدم] [سبب]` | حظر عضو | مشرف |
| `/unban [مستخدم]` | إلغاء الحظر | مشرف |
| `/mute [مستخدم] [سبب]` | كتم عضو | مشرف |
| `/unmute [مستخدم]` | إلغاء الكتم | مشرف |
| `/banlist` | قائمة المحظورين | مشرف |

### 👋 نظام الترحيب
- رسالة ترحيب تلقائية عند دخول أعضاء جدد
- أزرار Inline: القوانين، الموافقة، المساعدة، الإحصائيات

### 💬 الردود الذكية
- ذكر "المطور" ← معلومات المطور ورابطه
- ذكر "مساعدة" ← إرشادات المساعدة
- ذكر "القوانين" ← عرض قوانين المجموعة
- التحيات ← رد تلقائي

### 🗄️ قاعدة البيانات (MongoDB)
- تخزين المحظورين مع الأسباب والتواريخ
- تخزين المكتومين
- إعدادات المجموعة
- سجل إجراءات الإدارة

### 🔊 المكالمات (PyGalls - هيكل أساسي)
```bash
# لتفعيل المكالمات:
pip install py-tgcalls

# ثم قم بإلغاء التعليقات في:
# handlers/calls_handlers.py
```

---

## ⚙️ التخصيص

### تغيير قوانين المجموعة
في `config.py`، عدّل متغير `GROUP_RULES`.

### إضافة ردود ذكية جديدة
في `handlers/interactive_handlers.py`:
```python
app.on_message(
    keyword_filter("كلمة_جديدة") & filters.group
)(دالة_المعالج)
```

---

## 🐳 تشغيل بـ Docker (اختياري)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t group-manager-bot .
docker run --env-file .env group-manager-bot
```

---

## 📋 المتطلبات التقنية
- Python 3.10+
- MongoDB 5.0+
- Pyrogram 2.0.106
- Motor 3.3.2

---

## 👨‍💻 ملاحظات للمطور
- جميع العمليات **غير متزامنة (Async)**
- يستخدم نمط **Singleton** لقاعدة البيانات
- الفلاتر مخصصة باستخدام `filters.create()`
- سجلات مفصلة في كل عملية
