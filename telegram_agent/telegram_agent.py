"""
=============================================================================
فِرا آنالیز - Agent هوشمند تلگرام (Telegram Agent)
=============================================================================
قابلیت‌ها:
۱. ارسال خودکار ۵ پیش‌بینی برتر روز به چت مشخص‌شده
۲. پاسخ به پیام کاربر: کاربر نام تیم می‌نویسد، Agent تحلیل کامل می‌فرستد
۳. کامندهای تلگرام: /start، /today، /help
=============================================================================
"""

import os
import sys
import time
import json
import datetime
import requests
import urllib.parse

from analysis_engine import get_daily_top_picks, get_match_analysis_by_name

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()  # چت پیش‌فرض برای ارسال روزانه

TEHRAN_TZ = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
API_BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
OFFSET_FILE = "tg_offset.json"  # ذخیره offset پیام‌های خوانده‌شده

# ==================== ارسال پیام به تلگرام ====================
def send_message(chat_id: str, text: str, disable_web_preview: bool = True):
    """ارسال پیام متنی به تلگرام با پارسی HTML"""
    url = f"{API_BASE}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_web_preview
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code != 200:
            print(f"خطای تلگرام ({chat_id}): {r.status_code} — {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"خطای شبکه تلگرام: {e}")
        return False


def load_offset() -> int:
    try:
        with open(OFFSET_FILE, "r") as f:
            return json.load(f).get("offset", 0)
    except Exception:
        return 0


def save_offset(offset: int):
    try:
        with open(OFFSET_FILE, "w") as f:
            json.dump({"offset": offset}, f)
    except Exception as e:
        print(f"خطا در ذخیره offset: {e}")


# ==================== قالب‌بندی پیام‌ها ====================
def format_daily_digest(picks: list) -> str:
    """قالب پیام روزانه ۵ پیش‌بینی برتر"""
    if not picks:
        return (
            "🔍 <b>فِرا آنالیز</b>\n\n"
            "امروز مسابقه ارزشمندی در لیگ‌های اصلی پیدا نشد.\n"
            "روز دیگری چک کنید! ⚽"
        )

    now = datetime.datetime.now(TEHRAN_TZ)
    date_fa = now.strftime("%Y-%m-%d")

    lines = [
        f"🎯 <b>فِرا آنالیز — برترین فرصت‌های امروز</b>",
        f"📅 {date_fa} | سقف ریسک: ۲٪ موجودی\n"
    ]

    for i, m in enumerate(picks, 1):
        lines.append(f"<b>{i}. {m['home']} vs {m['away']}</b>")
        lines.append(f"   🏆 {m['league']} | شروع: {format_kickoff(m.get('kickoff', ''))}")
        lines.append(f"   📈 احتمال: {m['p_home']}٪ / {m['p_draw']}٪ / {m['p_away']}٪")
        lines.append(f"   ⭐ تیم برگزیده: <b>{m['fav']}</b>")

        # نمایش بهترین پیشنهاد شرطی
        if m["bets"]:
            top = m["bets"][0]
            lines.append(f"   💰 شرط پیشنهادی: <b>{top['label']}</b> (ضریب ~{top['odds_est']})")
            lines.append(f"   {top['safety']}")

        lines.append("")

    lines.append("💡 برای تحلیل کامل: نام تیم را بنویسید (مثلاً «رئال مادرید»)")
    lines.append("🛡️ مسئولیت شرط‌بندی با خودتان است. فقط مبلغی که از دست دادنش مشکلی ایجاد نمی‌کند.")
    return "\n".join(lines)


def format_match_analysis(m: dict) -> str:
    """قالب تحلیل کامل یک بازی"""
    lines = [
        f"⚽ <b>{m['home']} vs {m['away']}</b>",
        f"🏆 {m.get('league', 'لیگ')} | شروع: {format_kickoff(m.get('kickoff', ''))}\n",
        f"📊 <b>احتمالات مدل هوش مصنوعی:</b>",
        f"   🏠 {m['home']}: <b>{m['p_home']}٪</b>",
        f"   ⚖️ مساوی: <b>{m['p_draw']}٪</b>",
        f"   ✈️ {m['away']}: <b>{m['p_away']}٪</b>\n",
        f"⭐ <b>تیم برگزیده مدل:</b> {m['fav']}\n",
    ]

    if m.get("advice"):
        lines.append(f"🤖 <b>تحلیل AI:</b> {m['advice']}\n")

    # پیشنهادهای شرطی
    if m["bets"]:
        lines.append("💰 <b>پیشنهادهای شرطی (به ترتیب اطمینان):</b>")
        for i, b in enumerate(m["bets"], 1):
            conf_emoji = {"بالا": "🟢", "متوسط": "🟡", "پایین": "🔴"}.get(b["confidence"], "⚪")
            lines.append(f"   {i}. {conf_emoji} <b>{b['label']}</b> — ضریب ~{b['odds_est']}")
            lines.append(f"      {b['safety']}")
        lines.append("")

    # رکوردهای سریالی
    if m.get("streaks"):
        lines.append("🔥 <b>رکوردهای سریالی:</b>")
        for s in m["streaks"]:
            lines.append(f"   {s}")
        lines.append("")

    lines.append("💼 قانون طلایی: حداکثر ۲٪ بانک‌رول در هر شرط.")
    return "\n".join(lines)


def format_kickoff(iso_str: str) -> str:
    """تبدیل زمان ISO به ساعت تهران"""
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        tehran = dt.astimezone(TEHRAN_TZ)
        return tehran.strftime("%H:%M")
    except Exception:
        return iso_str or "نامشخص"


# ==================== پردازش پیام کاربر ====================
def handle_user_message(chat_id: str, text: str):
    """پاسخ به پیام کاربر بر اساس محتوا"""
    text = text.strip()

    if text.startswith("/start"):
        send_message(chat_id, (
            "👋 <b>سلام! به فِرا آنالیز خوش آمدید</b>\n\n"
            "🤖 من دستیار هوشمند تحلیل ورزشی هستم.\n\n"
            "<b>امکانات:</b>\n"
            "• نام تیم بنویسید → تحلیل کامل بازی\n"
            "• <code>/today</code> → ۵ فرصت برتر امروز\n"
            "• <code>/help</code> → راهنما\n\n"
            "مثال: <code>رئال مادرید</code> یا <code>Liverpool</code>"
        ))

    elif text.startswith("/today"):
        send_message(chat_id, "⏳ در حال تحلیل بازی‌های امروز...")
        picks = get_daily_top_picks(5)
        send_message(chat_id, format_daily_digest(picks))

    elif text.startswith("/help"):
        send_message(chat_id, (
            "📖 <b>راهنمای فِرا آنالیز</b>\n\n"
            "• نام تیم را بنویسید → تحلیل کامل بازی\n"
            "• <code>/today</code> → ۵ پیش‌بینی برتر امروز\n"
            "• <code>/start</code> → شروع ربات\n\n"
            "💡 نمونه: «بارسا»، «Manchester City»، «یوونتوس»"
        ))

    else:
        # جستجوی تیم
        send_message(chat_id, f"🔍 در حال جستجوی «{text}»...")
        result = get_match_analysis_by_name(text)
        if result:
            send_message(chat_id, format_match_analysis(result))
        else:
            send_message(chat_id, (
                f"❌ بازی‌ای برای «{text}» پیدا نشد.\n"
                "فقط لیگ‌های اصلی اروپا پوشش داده می‌شوند (لیگ برتر، لالیگا، سری آ، بوندسلیگا، لیگ ۱ و UCL)."
            ))


# ==================== Polling پیام‌ها ====================
def poll_updates(duration_seconds: int = 60):
    """دریافت و پاسخ به پیام‌های جدید برای مدت مشخص"""
    offset = load_offset()
    deadline = time.time() + duration_seconds

    while time.time() < deadline:
        try:
            r = requests.get(
                f"{API_BASE}/getUpdates",
                params={"offset": offset, "timeout": 25, "allowed_updates": ["message"]},
                timeout=30
            )
            if r.status_code != 200:
                time.sleep(5)
                continue

            updates = r.json().get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                msg = u.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "")

                if chat_id and text:
                    print(f"📩 پیام از {chat_id}: {text[:50]}")
                    handle_user_message(chat_id, text)

            save_offset(offset)

        except requests.exceptions.Timeout:
            continue  # Long polling طبیعی است
        except Exception as e:
            print(f"خطا در polling: {e}")
            time.sleep(5)


# ==================== نقطه ورود اصلی ====================
def main():
    if not TELEGRAM_TOKEN:
        print("❌ خطا: TELEGRAM_TOKEN تنظیم نشده است.")
        sys.exit(1)

    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"

    if mode == "daily":
        # ارسال روزانه به چت پیش‌فرض
        if not TELEGRAM_CHAT_ID:
            print("❌ خطا: TELEGRAM_CHAT_ID تنظیم نشده است.")
            sys.exit(1)
        print("🚀 ارسال خلاصه روزانه...")
        picks = get_daily_top_picks(5)
        send_message(TELEGRAM_CHAT_ID, format_daily_digest(picks))
        print("✅ ارسال شد.")

    elif mode == "interact":
        # پاسخ به پیام‌های کاربران
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 120
        print(f"🤖 حالت تعاملی برای {duration} ثانیه...")
        poll_updates(duration)

    else:
        print(f"نامشخص: {mode}. گزینه‌ها: daily | interact")


if __name__ == "__main__":
    main()
