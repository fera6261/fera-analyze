# 🤖 فِرا آنالیز - Telegram Agent

دستیار هوشمند تحلیل و پیش‌بینی ورزشی با قابلیت ارسال خودکار به تلگرام

## ✨ ویژگی‌ها

- ✅ ارسال روزانه 5 پیش‌بینی برتر به تلگرام (ساعت 9 صبح)
- ✅ تحلیل لحظه‌ای بازی با نوشتن نام تیم
- ✅ پشتیبانی از لیگ‌های اصلی اروپا
- ✅ اجرای خودکار با GitHub Actions (رایگان)
- ✅ محاسبه احتمالات با AI

## 🚀 نصب سریع

### گام 1: دریافت API Keys

1. **Telegram Bot Token:**
   - به [@BotFather](https://t.me/BotFather) پیام دهید
   - دستور `/newbot` و مراحل را طی کنید
   - توکن را کپی کنید

2. **Chat ID:**
   - به [@userinfobot](https://t.me/userinfobot) پیام دهید
   - عدد ID خود را یادداشت کنید

3. **API-Football Key:**
   - از [api-football.com](https://www.api-football.com/) بگیرید
   - پلن رایگان: 100 درخواست/روز

### گام 2: تنظیم GitHub Secrets

1. به **Settings** → **Secrets and variables** → **Actions** برید
2. روی **New repository secret** کلیک کنید
3. این 3 secret را اضافه کنید:

| Name | Value |
|------|-------|
| `TELEGRAM_TOKEN` | توکن ربات از BotFather |
| `TELEGRAM_CHAT_ID` | Chat ID شما |
| `RAPIDAPI_KEY` | کلید API-Football |

### گام 3: فعال‌سازی Actions

1. به تب **Actions** برید
2. اگر disabled بود، روی **Enable** کلیک کنید
3. Workflow "Fera Telegram Agent" را انتخاب کنید
4. **Run workflow** را بزنید

✅ **تمام!** پیام در تلگرام دریافت می‌کنید.

## 📱 نحوه استفاده

### کامندهای ربات

| کامند | عملکرد |
|--------|---------|
| `/start` | شروع ربات و راهنما |
| `/today` | دریافت 5 فرصت برتر امروز |
| `/help` | راهنمای کامل |
| **نام تیم** | تحلیل کامل بازی (مثلاً `رئال مادرید` یا `Liverpool`) |

### زمان‌بندی خودکار

| زمان | وظیفه |
|------|-------|
| 09:00 صبح | ارسال 5 پیش‌بینی برتر |
| 12:00 ظهر | پاسخ به پیام‌ها (25 دقیقه) |
| 18:00 عصر | پاسخ به پیام‌ها (25 دقیقه) |
| 22:00 شب | پاسخ به پیام‌ها (25 دقیقه) |

## 🏗️ ساختار پروژه

```
fera-analyze/
├── .github/
│   └── workflows/
│       └── telegram_agent.yml    # GitHub Actions workflow
├── telegram_agent/
│   ├── analysis_engine.py        # موتور تحلیل و رتبه‌بندی
│   ├── telegram_agent.py         # ربات تلگرام
│   └── requirements.txt          # وابستگی‌های Python
└── README.md
```

## 🔧 تست محلی

برای تست قبل از استقرار:

```bash
cd telegram_agent
pip install -r requirements.txt

# تنظیم متغیرهای محیطی
export TELEGRAM_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
export RAPIDAPI_KEY="your-api-key"

# اجرا
python telegram_agent.py daily
```

## 🛠️ عیب‌یابی

### ربات پیام نمی‌فرستد
- Chat ID را چک کنید (باید عددی مثل `123456789` باشد)
- برای کانال، ID منفی است (مثلاً `-1001234567890`)
- ربات باید عضو کانال و Admin باشد

### API Key تمام شد
- پلن رایگان: 100 درخواست/روز
- هر روز نیمه‌شب UTC ریست می‌شود

### Actions اجرا نمی‌شود
- **Settings** → **Actions** → **General**
- "Allow all actions and reusable workflows" را انتخاب کنید

## 📊 لیگ‌های پوشش داده‌شده

- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 لیگ برتر انگلیس (Premier League)
- 🇪🇸 لالیگا اسپانیا (La Liga)
- 🇮🇹 سری آ ایتالیا (Serie A)
- 🇩🇪 بوندسلیگا آلمان (Bundesliga)
- 🇫🇷 لیگ 1 فرانسه (Ligue 1)
- 🏆 لیگ قهرمانان اروپا (Champions League)

## 🚧 محدودیت‌ها

- Agent در بازه‌های زمانی مشخص پیام‌ها را می‌خواند (polling)
- برای پاسخ 24/7 فوری، نیاز به VPS یا webhook دارید
- API رایگان محدودیت 100 درخواست/روز دارد

## 🎯 توسعه آینده

- [ ] Webhook برای پاسخ فوری 24/7
- [ ] پشتیبانی NBA و تنیس
- [ ] دکمه‌های inline برای تعامل سریع‌تر
- [ ] هشدار افت ضریب
- [ ] پایگاه داده تاریخچه کاربران

## ⚖️ توجه قانونی

این نرم‌افزار صرفاً برای تحلیل آماری ارائه شده است. مسئولیت استفاده با خودتان می‌باشد.

## 📞 پشتیبانی

مشکلی پیش آمد؟ [Issue](https://github.com/fera6261/fera-analyze/issues) بسازید!

---

**ساخته شده با ❤️ برای علاقه‌مندان به تحلیل ورزشی**
