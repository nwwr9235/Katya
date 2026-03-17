# ══════════════════════════════════════════
#   Dockerfile لنشر البوت على Railway
# ══════════════════════════════════════════

FROM python:3.10-slim

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات أولاً (للاستفادة من Docker Cache)
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
