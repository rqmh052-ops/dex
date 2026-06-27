# 🔨 Splash DEX Bot

بوت تيليجرام لتخصيص ملف `classes.dex` الخاص بـ SplashActivity في تطبيقات Android.

---

## 🗂 هيكل المشروع

```
splash_dex_bot/
├── bot.py                  ← البوت الرئيسي (منطق FSM)
├── run.py                  ← نقطة التشغيل
├── requirements.txt
├── .env.example            ← نسخه إلى .env
├── smali/                  ← ملفات Smali (القوالب)
│   ├── SplashActivity.smali
│   ├── SplashActivity$4.smali
│   ├── SplashActivity$5.smali
│   └── SplashActivity$6.smali
└── tools/
    ├── README.md
    └── smali.jar           ← نزّله يدوياً (انظر tools/README.md)
```

---

## ⚙️ إعداد البيئة

### 1. المتطلبات
- Python 3.11+
- Java 8+
- `smali.jar` (من https://github.com/JesusFreke/smali/releases)

### 2. تثبيت المكتبات

```bash
pip install -r requirements.txt
```

### 3. إعداد ملف .env

```bash
cp .env.example .env
nano .env   # أدخل BOT_TOKEN و ADMIN_IDS
```

```env
BOT_TOKEN=7123456789:AAFxxxxxxxxxx
ADMIN_IDS=123456789
```

> لمعرفة ID تيليجرام الخاص بك: أرسل `/start` إلى **@userinfobot**

### 4. وضع smali.jar

نزّل آخر إصدار من:  
**https://github.com/JesusFreke/smali/releases**

ثم:
```bash
mv smali-*.jar tools/smali.jar
```

### 5. تشغيل البوت

```bash
python run.py
```

---

## 🤖 أوامر البوت

| الأمر | الوظيفة |
|---|---|
| `/start` | بدء معالج بناء DEX |
| `/cancel` | إلغاء العملية الحالية |
| `/status` | فحص حالة الأدوات (Java + smali.jar) |

---

## 🔄 خطوات المعالج (FSM)

```
/start
  └─▶ [١] اسم القناة
  └─▶ [٢] وصف القناة
  └─▶ [٣] يوزرنيم القناة (بدون @)
  └─▶ [٤] لوغو القناة  (صورة أو ملف)
  └─▶ [٥] AdMob Unit ID  (أو تخطي)
  └─▶ [٦] نص زر الاشتراك  (أو تخطي)
  └─▶ [تأكيد] عرض ملخص
  └─▶ [بناء] تعديل Smali → تجميع DEX → إرسال الملف
```

---

## 📝 ما الذي يُعدَّل تلقائياً؟

| الملف | ما يُغيَّر |
|---|---|
| `SplashActivity.smali` | اسم القناة، الوصف، الرابط، الصورة (base64)، نص الزر، AdMob ID |
| `SplashActivity$4.smali` | رابط القناة في زر الاشتراك (Telegram intent) |
| `SplashActivity$5.smali` | لا تغيير |
| `SplashActivity$6.smali` | لا تغيير |

---

## 🔒 الأمان

- البوت **للأدمن فقط** — أي رسالة من غير الأدمن تُتجاهل تماماً
- لا يوجد أي تسجيل لبيانات المستخدم خارج الجلسة
- لدعم أكثر من أدمن: `ADMIN_IDS=123456789,987654321`

---

## 🐧 تشغيل كـ systemd service (اختياري)

```ini
# /etc/systemd/system/splashbot.service
[Unit]
Description=Splash DEX Bot
After=network.target

[Service]
WorkingDirectory=/path/to/splash_dex_bot
ExecStart=/usr/bin/python3 /path/to/splash_dex_bot/run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable splashbot
systemctl start splashbot
systemctl status splashbot
```

---

## ⚠️ ملاحظات مهمة

1. **لا تستخدم علامات `"` في اسم القناة أو الوصف** — تُحذف تلقائياً
2. **الصورة**: يُفضل إرسالها كـ Document وليس كصورة عادية (تيليجرام يضغط الصور)
3. **حجم الصورة**: تُحوَّل تلقائياً إلى PNG بحجم أقصى 300×300 بكسل
4. **AdMob**: إذا تخطيته، يُستخدم ID معطَّل (لا تظهر إعلانات)
