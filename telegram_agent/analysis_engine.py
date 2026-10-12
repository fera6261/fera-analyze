"""
=============================================================================
فِرا آنالیز - موتور تحلیل پیش‌بینی (Analysis Engine)
=============================================================================
وظیفه: واکشی مسابقات، محاسبه احتمالات و تولید بهترین پیش‌بینی‌ها
منابع: API-Football (v3.football.api-sports.io)
=============================================================================
"""

import os
import re
import requests
import datetime
import random

# سیستم چرخشی API Keys - 5 کلید = 500 درخواست روزانه
API_KEYS = [
    "b6da7d3ae058e193ddfa7d5899118c25",
    "823d3e56dd0ec2a4f540f34d6af10109",
    "04dd219f140d04a059f5b26dc90b4787",
    "95f257bda61369aec43315933cac8278",
    "feec2f3f3a506e5e54ca4bca3945749b"
]

# اگر متغیر محیطی وجود داشت، به لیست اضافه کن
env_key = os.environ.get("RAPIDAPI_KEY", os.environ.get("API_FOOTBALL_KEY", "")).strip()
if env_key and env_key not in API_KEYS:
    API_KEYS.insert(0, env_key)

TEHRAN_TZ = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
_call_counter = 0  # شمارنده تعداد فراخوانی‌ها


def _get_api_key():
    """انتخاب هوشمند API key با الگوریتم Round-Robin"""
    global _call_counter
    key = API_KEYS[_call_counter % len(API_KEYS)]
    _call_counter += 1
    return key


def _headers():
    """تنظیم هدرها بر اساس نوع کلید (مستقیم یا RapidAPI)"""
    api_key = _get_api_key()
    is_direct = (len(api_key) == 32 and "-" not in api_key)
    if is_direct:
        return "https://v3.football.api-sports.io", {"x-apisports-key": api_key}
    return "https://api-football-v1.p.rapidapi.com/v3", {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }


def call_api(endpoint: str, retry_count: int = 0):
    """فراخوانی امن API-Football با چرخش خودکار کلیدها در صورت خطا"""
    base, headers = _headers()
    try:
        r = requests.get(f"{base}/{endpoint}", headers=headers, timeout=12)
        if r.status_code == 200:
            return r.json().get("response", [])
        elif r.status_code == 429 and retry_count < len(API_KEYS):
            # اگر کلید به محدودیت رسید، کلید بعدی را امتحان کن
            print(f"⚠️ کلید به محدودیت رسید، تلاش با کلید بعدی...")
            return call_api(endpoint, retry_count + 1)
    except Exception as e:
        print(f"خطای شبکه در {endpoint}: {e}")
    return None


def get_today_tehran() -> str:
    """تاریخ امروز به وقت تهران"""
    return datetime.datetime.now(TEHRAN_TZ).strftime("%Y-%m-%d")


# ==================== لیگ‌های پوشش داده‌شده ====================
PRIORITY_LEAGUES = {
    39: "لیگ برتر انگلیس", 140: "لالیگا اسپانیا", 135: "سری آ ایتالیا",
    78: "بوندسلیگا آلمان", 61: "لیگ ۱ فرانسه", 2: "لیگ قهرمانان اروپا",
    3: "لیگ اروپا", 12: "کاپ ایتالیا", 45: "کاپ FA انگلیس",
}


# ==================== واکشی مسابقات امروز ====================
def fetch_today_fixtures() -> list:
    """دریافت مسابقات امروز از لیگ‌های اولویت‌دار"""
    today = get_today_tehran()
    fixtures = call_api(f"fixtures?date={today}")
    if not fixtures:
        return []

    result = []
    for fx in fixtures:
        league_id = fx.get("league", {}).get("id", 0)
        if league_id not in PRIORITY_LEAGUES:
            continue
        # فقط بازی‌های شروع‌نشده یا در جریان
        status = fx.get("fixture", {}).get("status", {}).get("short", "NS")
        if status in ["FT", "AET", "PEN", "PST", "CANC", "ABD", "SUSP", "POST"]:
            continue

        result.append({
            "fixture_id": fx["fixture"]["id"],
            "date_iso": fx["fixture"]["date"],
            "kickoff": fx["fixture"]["date"],
            "league_id": league_id,
            "league": PRIORITY_LEAGUES[league_id],
            "home": fx["teams"]["home"]["name"],
            "away": fx["teams"]["away"]["name"],
            "status": status,
        })
    return result


# ==================== تحلیل عمیق یک مسابقه ====================
def analyze_fixture(fixture_id: int) -> dict | None:
    """تحلیل کامل یک مسابقه با اندپوینت /predictions"""
    data = call_api(f"predictions?fixture={fixture_id}")
    if not data:
        return None

    resp = data[0]
    pred = resp.get("predictions", {})
    teams = resp.get("teams", {})
    comparison = resp.get("comparison", {})
    h2h = resp.get("h2h", [])

    # درصد احتمالات مدل
    pct = pred.get("percent", {})
    p_home = int(pct.get("home", "45%").replace("%", "") or 45)
    p_draw = int(pct.get("draw", "25%").replace("%", "") or 25)
    p_away = int(pct.get("away", "30%").replace("%", "") or 30)

    # پیشنهاد رسمی API
    advice = pred.get("advice", "")
    under_over = pred.get("under_over", "")
    winner_pred = pred.get("winner", {})
    goals_pred = pred.get("goals", {})

    home_name = teams.get("home", {}).get("name", "میزبان")
    away_name = teams.get("away", {}).get("name", "میهمان")
    home_logo = teams.get("home", {}).get("logo", "")
    away_logo = teams.get("away", {}).get("logo", "")

    # ساخت رکوردهای سریالی از H2H
    streaks = []
    if h2h and len(h2h) >= 3:
        high_scoring = sum(
            1 for g in h2h[:5]
            if (g.get("goals", {}).get("home", 0) or 0) + (g.get("goals", {}).get("away", 0) or 0) >= 3
        )
        if high_scoring >= 3:
            streaks.append(f"⚡ در {high_scoring} از ۵ تقابل مستقیم اخیر، حداقل ۳ گل ثبت شده است.")

    att_home = comparison.get("att", {}).get("home", "50%")
    att_away = comparison.get("att", {}).get("away", "50%")
    streaks.append(f"📊 توان تهاجمی: {home_name} ({att_home}) در برابر {away_name} ({att_away}).")

    # مشخص کردن تیم برگزیده
    fav = home_name if p_home >= p_away else away_name
    is_home_fav = p_home >= p_away
    fav_pct = max(p_home, p_away)

    # ساخت پیشنهاد شرط بر اساس احتمالات
    bets = build_bet_suggestions(
        p_home, p_draw, p_away, fav, is_home_fav, under_over, advice
    )

    return {
        "fixture_id": fixture_id,
        "home": home_name,
        "away": away_name,
        "home_logo": home_logo,
        "away_logo": away_logo,
        "p_home": p_home, "p_draw": p_draw, "p_away": p_away,
        "fav": fav,
        "advice": advice,
        "under_over": under_over,
        "winner_hint": winner_pred.get("advice", ""),
        "goals_home_hint": goals_pred.get("home", ""),
        "goals_away_hint": goals_pred.get("away", ""),
        "streaks": streaks,
        "bets": bets,
        "league": PRIORITY_LEAGUES.get(
            resp.get("league", {}).get("id", 0),
            resp.get("league", {}).get("name", "لیگ")
        ),
        "kickoff": resp.get("fixture", {}).get("date", ""),
    }


# ==================== ساخت پیشنهادهای شرطی ====================
def build_bet_suggestions(p_home, p_draw, p_away, fav, is_home_fav, under_over, advice) -> list:
    """تولید لیست پیشنهادهای شرطی بر اساس احتمالات مدل"""
    bets = []
    fav_pct = max(p_home, p_away)
    fav_prob = fav_pct / 100.0

    # ۱. مساوی فسخ (DNB) - پیشنهاد اصلی
    dnb_prob = fav_prob / (1 - (p_draw / 100.0))  # احتمال برند در DNB
    if dnb_prob >= 0.60:
        bets.append({
            "type": "DNB",
            "label": f"{fav} مساوی فسخ",
            "probability": dnb_prob,
            "odds_est": round(1.0 / dnb_prob, 2),
            "safety": "🛡️ تساوی = بازگشت کامل وجه",
            "confidence": "بالا" if dnb_prob >= 0.70 else "متوسط"
        })

    # ۲. هندیکپ آسیایی -1.0 اگر اختلاف قوی است
    if fav_pct >= 62:
        bets.append({
            "type": "AH",
            "label": f"{fav} هندیکپ -۱.۰",
            "probability": fav_prob * 0.72,
            "odds_est": round(1.80, 2),
            "safety": "🛡️ برد با ۱ اختلاف = بازگشت وجه",
            "confidence": "متوسط"
        })

    # ۳. اور ۱.۵ گل - اگر مدل روی خط بالا تمرکز دارد
    if under_over and ("+" in under_over or "Over" in under_over or "بالا" in under_over):
        bets.append({
            "type": "OU",
            "label": f"مجموع گل {under_over}",
            "probability": 0.68,
            "odds_est": 1.50,
            "safety": "⚽ گزینه امن گل‌محور",
            "confidence": "بالا"
        })

    # ۴. برد مستقیم فقط در صورت اطمینان بالا
    if fav_pct >= 70:
        bets.append({
            "type": "1X2",
            "label": f"{fav} برد مستقیم",
            "probability": fav_prob,
            "odds_est": round(1.0 / fav_prob, 2),
            "safety": "⚠️ بدون چتر حمایتی",
            "confidence": "متوسط"
        })

    return bets


# ==================== امتیازدهی و رتبه‌بندی ====================
def rank_fixtures(fixtures: list, limit: int = 5) -> list:
    """مرتب‌سازی بازی‌ها بر اساس قدرت سیگنال و رتبه‌بندی برترین‌ها"""
    ranked = []
    for fx in fixtures:
        analysis = analyze_fixture(fx["fixture_id"])
        if not analysis:
            continue
        # امتیاز: حداکثر احتمال تیم برگزیده × تعداد پیشنهادهای قوی
        strong_bets = sum(1 for b in analysis["bets"] if b["confidence"] == "بالا")
        score = analysis["p_home"] + analysis["p_away"] + (strong_bets * 10)
        analysis["score"] = score
        analysis["league"] = fx["league"]
        ranked.append(analysis)
        ranked.sort(key=lambda x: -x["score"])

    return ranked[:limit]


# ==================== تابع اصلی: بهترین‌های روز ====================
def get_daily_top_picks(limit: int = 5) -> list:
    """استخراج برترین پیش‌بینی‌های امروز برای ارسال به تلگرام"""
    fixtures = fetch_today_fixtures()
    if not fixtures:
        return []
    return rank_fixtures(fixtures, limit)


# ==================== تابع اصلی: تحلیل یک بازی خاص ====================
def get_match_analysis_by_name(team_name: str) -> dict | None:
    """
    جستجوی بازی بر اساس نام تیم (فارسی یا انگلیسی، fuzzy matching)
    خروجی: تحلیل کامل بازی یا None
    """
    fixtures = fetch_today_fixtures()
    query = normalize_team_name(team_name)

    best_match = None
    best_score = 0

    for fx in fixtures:
        h_norm = normalize_team_name(fx["home"])
        a_norm = normalize_team_name(fx["away"])
        score = 0
        if query == h_norm or query == a_norm:
            score = 100
        elif query in h_norm or query in a_norm:
            score = 80
        elif h_norm in query or a_norm in query:
            score = 70

        if score > best_score:
            best_match = fx
            best_score = score

    if not best_match:
        return None

    return analyze_fixture(best_match["fixture_id"])


# ==================== نرمال‌سازی نام تیم ====================
TEAM_NAME_MAP = {
    # انگلیسی -> استاندارد
    "real madrid": "real madrid", "barcelona": "barcelona", "fc barcelona": "barcelona",
    "liverpool": "liverpool", "manchester united": "man utd", "man utd": "man utd",
    "manchester city": "man city", "man city": "man city", "arsenal": "arsenal",
    "chelsea": "chelsea", "tottenham": "tottenham", "tottenham hotspur": "tottenham",
    "juventus": "juventus", "inter": "inter", "inter milan": "inter",
    "ac milan": "milan", "milan": "milan", "napoli": "napoli", "roma": "roma",
    "as roma": "roma", "lazio": "lazio", "atletico madrid": "atletico",
    "bayern": "bayern", "bayern munich": "bayern", "borussia dortmund": "dortmund",
    "psg": "psg", "paris": "psg", "paris saint-germain": "psg",
    # فارسی -> انگلیسی استاندارد
    "رئال مادرید": "real madrid", "بارسلونا": "barcelona", "بارسا": "barcelona",
    "لیورپول": "liverpool", "منچستر یونایتد": "man utd", "منچسترسیتی": "man city",
    "ارسنال": "arsenal", "چلسی": "chelsea", "تاتنهام": "tottenham",
    "یوونتوس": "juventus", "اینتر": "inter", "میلان": "milan", "ناپولی": "napoli",
    "رم": "roma", "لاتزیو": "lazio", "اتلتیکو مادرید": "atletico",
    "بایرن": "bayern", "دورتموند": "dortmund", "پاری سن ژرمن": "psg",
}


def normalize_team_name(name: str) -> str:
    """نرمال‌سازی نام تیم به انگلیسی استاندارد"""
    if not name:
        return ""
    name = name.lower().strip()
    # تبدیل فارسی به انگلیسی
    for fa, en in TEAM_NAME_MAP.items():
        if fa in name:
            return en
    # حذف کلمات اضافی
    name = re.sub(r'\b(fc|club|sc|ac|afc|cf)\b', '', name)
    return re.sub(r'\s+', ' ', name).strip()
