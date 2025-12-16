import telebot
from telebot import types
import requests
import re
import time
import random
import os
import threading
import traceback

# ==================== ⚙️ إعدادات البوت ====================
BOT_TOKEN = '7863811209:AAGGDjpHR9WpP795lFXILs5QSzhZMTknrXA'
MY_TRACK_ID = 'zakbot'
ADMIN_ID = 5010090193

# ==================== 📁 إعداد الملفات ====================
if not os.path.exists("cookies.txt"):
    with open("cookies.txt", "w", encoding="utf-8") as f: f.write("")

if not os.path.exists("bot.log"):
    with open("bot.log", "w", encoding="utf-8") as f: f.write("Bot Started Log\n")

# ==================== 🔐 تحميل الكوكيز ====================
def load_cookies():
    try:
        with open("cookies.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return ""

CURRENT_COOKIES = load_cookies()

# ==================== 🛡️ متغيرات النظام ====================
USER_LIMIT = {}
LIMIT_SECONDS = 20
RECENT_PRODUCTS = {}
COOKIE_DEAD = False

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

# إحصائيات البوت
STATS = {
    "total_requests": 0,
    "success_requests": 0,
    "failed_requests": 0,
    "unique_users": set(),
    "start_time": time.time()
}

bot = telebot.TeleBot(BOT_TOKEN)
session = requests.Session() # تسريع الاتصال

# ==================== 🧾 Logging ====================
def log_event(text):
    with open("bot.log", "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} | {text}\n")

def log_exception(e):
    log_event(f"EXCEPTION:\n{traceback.format_exc()}")

# ==================== 🛠️ أدوات مساعدة ====================
def unshorten_url(url):
    try:
        r = session.head(url, allow_redirects=True, timeout=5)
        return r.url
    except:
        return url

def extract_item_id(url):
    m = re.search(r'item/(\d+)\.html', url)
    if not m: m = re.search(r'(\d{10,})', url)
    return m.group(1) if m else None

def get_product_title(url):
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS), 'Cookie': CURRENT_COOKIES}
        r = session.get(url, headers=headers, timeout=5)
        m = re.search(r'<title>(.*?)</title>', r.text)
        if m: return m.group(1).replace(' - AliExpress', '').replace('| AliExpress', '').strip()
    except: pass
    return "AliExpress Product"

# ==================== 🧠 محرك التوليد ====================
def generate_link_with_cookie(target_url):
    global COOKIE_DEAD
    if COOKIE_DEAD: return None

    api_url = "https://portals.aliexpress.com/tools/linkGenerate/generatePromotionLinkV2.htm"
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://portals.aliexpress.com/link_generator.htm',
        'Cookie': CURRENT_COOKIES,
        'Content-Type': 'application/json;charset=UTF-8'
    }
    params = {'shipTos': 'DZ', 'trackId': MY_TRACK_ID, 'targetUrl': target_url}

    try:
        r = session.get(api_url, headers=headers, params=params, timeout=10)
        j = r.json()
        if (j.get('code') == "00" or j.get('success') is True) and j.get('data'):
            return j['data']['shortLink']
    except: pass
    return None

# ==================== 🩺 الفحص التلقائي (Background Thread) ====================
def check_cookie_health():
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS), 'Cookie': CURRENT_COOKIES}
        r = session.get("https://portals.aliexpress.com", headers=headers, timeout=10)
        if "login" in r.url or "login" in r.text.lower():
            return "⚠️ الكوكيز ماتت (Redirected to Login)"
        return "✅ الكوكيز تعمل"
    except Exception as e:
        return f"❌ خطأ اتصال: {str(e)}"

def auto_health_check():
    global COOKIE_DEAD
    while True:
        try:
            if CURRENT_COOKIES and len(CURRENT_COOKIES) > 50:
                status = check_cookie_health()
                if "⚠️" in status:
                    COOKIE_DEAD = True
                    # تنبيه صامت للأدمن في اللوج أو الخاص
                    log_event("AUTO CHECK: Cookie Dead")
                    try: bot.send_message(ADMIN_ID, f"🚨 **إنذار تلقائي:** الكوكيز توقفت عن العمل!")
                    except: pass
        except: pass
        time.sleep(1800) # كل 30 دقيقة

# تشغيل الفحص في الخلفية
threading.Thread(target=auto_health_check, daemon=True).start()

# ==================== 🎹 القوائم ====================
def main_menu_keyboard():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("⭐️ ألعاب العملات ⭐️", callback_data="games"),
        types.InlineKeyboardButton("🛒 سلة العملات", callback_data="cart_discount"),
        types.InlineKeyboardButton("❤️ قناتنا", url="https://t.me/zakideals")
    )
    return m

def games_menu_keyboard():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("⭐️ Daily Coins", url="https://s.click.aliexpress.com/e/_on0MwkF"),
        types.InlineKeyboardButton("⭐️ Merge Boss", url="https://s.click.aliexpress.com/e/_DlCyg5Z"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
    )
    return m

# ==================== 🎮 أوامر الأدمن والمستخدم ====================
@bot.message_handler(commands=['start'])
def start(message):
    STATS["unique_users"].add(message.from_user.id)
    bot.reply_to(message, "👋 أرسل رابط المنتج لاستخراج العروض.", reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['update'])
def update_cookies(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "🔐 أرسل الكوكيز الجديدة:")
    bot.register_next_step_handler(msg, save_cookies)

def save_cookies(message):
    global CURRENT_COOKIES, COOKIE_DEAD
    if len(message.text) < 50: return
    CURRENT_COOKIES = message.text.strip()
    COOKIE_DEAD = False
    with open("cookies.txt", "w", encoding="utf-8") as f: f.write(CURRENT_COOKIES)
    bot.reply_to(message, "✅ تم التحديث")

@bot.message_handler(commands=['status'])
def status_command(message):
    if message.from_user.id != ADMIN_ID: return
    uptime = int((time.time() - STATS["start_time"]) / 60)
    msg = (
        f"📊 **Bot Statistics**\n"
        f"👥 مستخدمون: {len(STATS['unique_users'])}\n"
        f"📦 إجمالي الطلبات: {STATS['total_requests']}\n"
        f"✅ نجاح: {STATS['success_requests']}\n"
        f"❌ فشل: {STATS['failed_requests']}\n"
        f"⏱️ تشغيل منذ: {uptime} دقيقة"
    )
    bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['health'])
def health_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    bot.reply_to(message, check_cookie_health())

# ==================== 🕹️ Callbacks ====================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    if call.data == "games":
        bot.edit_message_text("🎮 الألعاب:", call.message.chat.id, call.message.message_id, reply_markup=games_menu_keyboard())
    elif call.data == "main_menu":
        bot.edit_message_text("🏠 القائمة الرئيسية:", call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard())
    elif call.data == "cart_discount":
        link = generate_link_with_cookie("https://www.aliexpress.com/p/coin-index/index.html")
        if link:
            bot.send_message(call.message.chat.id, f"🛒 **رابط سلة العملات:**\n{link}")
        else:
            bot.answer_callback_query(call.id, "⚠️ غير متوفر")

# ==================== 🔗 معالجة الروابط (تمت إعادتها وربطها بالإحصائيات) ====================
@bot.message_handler(func=lambda m: True)
def handle_links(message):
    global COOKIE_DEAD
    
    # فلترة الروابط فقط
    urls = re.findall(r'https?://\S+', message.text)
    if not urls: return

    # تسجيل المستخدم
    uid = message.from_user.id
    STATS["unique_users"].add(uid)
    STATS["total_requests"] += 1

    # حماية من السبام
    now = time.time()
    if uid in USER_LIMIT and now - USER_LIMIT[uid] < LIMIT_SECONDS:
        bot.reply_to(message, "⏳ انتظر قليلاً...")
        return
    USER_LIMIT[uid] = now

    if COOKIE_DEAD:
        STATS["failed_requests"] += 1
        bot.reply_to(message, "⚠️ البوت تحت الصيانة.")
        return

    wait = bot.reply_to(message, "⏳ جاري التحليل...")

    # معالجة الرابط
    try:
        long_url = unshorten_url(urls[0])
        item_id = extract_item_id(long_url)
        
        if not item_id:
            bot.delete_message(message.chat.id, wait.message_id)
            return

        # منع التكرار لنفس المنتج في وقت قصير
        if item_id in RECENT_PRODUCTS and time.time() - RECENT_PRODUCTS[item_id] < 300:
            bot.delete_message(message.chat.id, wait.message_id)
            bot.reply_to(message, "🔁 تم إرسال هذا الرابط للتو.")
            return
        RECENT_PRODUCTS[item_id] = time.time()

        # جلب البيانات والتوليد
        title = get_product_title(long_url)
        base = f"https://www.aliexpress.com/item/{item_id}.html"
        pvid = str(random.randint(100, 999))
        
        links_map = {
            "coins": f"{base}?sourceType=620&channel=coin&pvid={pvid}",
            "super": f"{base}?sourceType=562&pvid={pvid}",
            "limit": f"{base}?sourceType=561&pvid={pvid}",
            "bundle": f"https://www.aliexpress.com/ssr/300000512/BundleDeals2?productIds={item_id}&pvid={pvid}"
        }

        results = {}
        for k, u in links_map.items():
            results[k] = generate_link_with_cookie(u)
            time.sleep(random.uniform(0.2, 0.5))

        # التحقق النهائي
        if not results["coins"] and not results["super"]:
            COOKIE_DEAD = True
            STATS["failed_requests"] += 1
            log_event(f"FAILED: {item_id}")
            bot.delete_message(message.chat.id, wait.message_id)
            bot.send_message(message.chat.id, "⚠️ حدث خطأ، يرجى المحاولة لاحقاً.")
            try: bot.send_message(ADMIN_ID, "🚨 الكوكيز انتهت أثناء التشغيل!")
            except: pass
            return

        # نجاح!
        STATS["success_requests"] += 1
        log_event(f"SUCCESS: {item_id}")
        
        best = results["coins"] or results["super"]
        text = (
            f"🔥 **أفضل سعر (AliExpress):**\n🔗 {best}\n\n"
            f"📦 **{title}**\n\n"
            f"🪙 Coins:\n{results['coins'] or '❌'}\n\n"
            f"🛒 Super Deals:\n{results['super'] or '❌'}\n\n"
            f"🏅 Limited:\n{results['limit'] or '❌'}\n\n"
            f"📌 Bundle:\n{results['bundle'] or results['super']}"
        )

        bot.delete_message(message.chat.id, wait.message_id)
        bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard(), disable_web_page_preview=True)

    except Exception as e:
        log_exception(e)
        bot.delete_message(message.chat.id, wait.message_id)

# ==================== ▶️ تشغيل ====================
try:
except: pass

print("Bot Started (Diamond Version) 🚀")

bot.infinity_polling()
