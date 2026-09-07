"""
🎊 TELEGRAM SHOP BOT — v4 (Supabase storage)
========================================================
በዚህ ስሪት ላይ የተጨመሩ/የተስተካከሉ ነገሮች:

1. ✅ የነጋዴ ሱቅ ሊንክ ትክክል ነው የሚሰራው (deep-link fix)
2. ✅ ፎቶ (screenshot) መቀበል ስራ ላይ ውሏል
3. ✅ ትዕዛዝ ከተረጋገጠ በኋላ የክፍያ screenshot ይጠየቃል
4. ✅ /received - ደንበኛው እቃው እንደደረሰው ያረጋግጣል
5. ✅ /dispute እና /rate ሙሉ በሙሉ ተተግብረዋል
6. ✅ Admin/Owner ትዕዛዝ (/admin_merchants, /admin_orders)
------------------------ አዲስ (v3) ------------------------
7. 🆕 ነጋዴ ለእያንዳንዱ ምርት ፎቶ መጨመር ይችላል (/register እና /addproduct)
    ደንበኞችም የምርቱን ፎቶ አይተው ነው የሚመርጡት
8. 🆕 /help የበለጠ ሰፊ እና ግልጽ ማብራሪያ ይሰጣል
9. 🆕 /contact - ስለ ቦቱ ችግር ካለ በቀጥታ ወደ bot owner መልእክት ይልካል
10. 🆕 ትዕዛዝ ከተረጋገጠ በኋላ ደንበኛው የመክፈያ አይነት ይመርጣል:
    🏦 የሞባይል ባንክ / ቴሌብር (screenshot በመላክ)
    💵 እቃው ሲደርስ ብር (Cash on Delivery)
    ⭐ Telegram Stars
------------------------ አዲስ (v4) ------------------------
11. 🆕 ዳታ ከJSON ፋይል ወደ Supabase (Postgres) ተቀይሯል — ስለዚህ ቦቱ
    ሲሪስታርት (ለምሳሌ Render free tier ላይ) ዳታ አይጠፋም

⚠️ ከመጀመርዎ በፊት:
    1. schema.sql ውስጥ ያለውን SQL በ Supabase → SQL Editor ውስጥ ያስሩ
    2. SUPABASE_URL እና SUPABASE_KEY የተባሉ environment variable ያዘጋጁ
    3. requirements.txt ውስጥ ያለውን `supabase` ፓኬጅ ይጫኑ
"""

import logging
import os
import asyncio
from datetime import datetime
from uuid import uuid4

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    ContextTypes,
    filters,
)
from supabase import create_client, Client

# ====================== SETUP ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not set!")

PORT = int(os.environ.get("PORT", 10000))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
# Simple Birr -> Telegram Stars conversion. Adjust in your environment
# variables if you want a different rate (e.g. STARS_RATE=0.5).
STARS_RATE = float(os.environ.get("STARS_RATE", "1"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL / SUPABASE_KEY not set!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logger.info("✅ Bot initialized - All systems ready (Supabase storage)")

# ====================== CONVERSATION STATES ======================
# REGISTRATION (also reused by the /addproduct flow)
REG_STORE_NAME, REG_PHONE, REG_LOCATION, REG_PAYMENT, REG_PRODUCT, REG_PRICE, REG_PHOTO = range(7)

# ORDER FLOW
ORDER_GET_NAME = 11
ORDER_GET_PHONE = 12
ORDER_GET_ADDRESS = 13
ORDER_CONFIRM = 14
ORDER_PAYMENT_METHOD = 15
ORDER_PAYMENT_PROOF = 16

# DISPUTE FLOW
DISPUTE_SELECT_ORDER = 19
DISPUTE_REASON = 20
DISPUTE_PROOF = 21

# RATING FLOW
RATING_SELECT_ORDER = 29
RATING_SCORE = 30

# CONTACT ADMIN FLOW
CONTACT_MESSAGE = 40

# ====================== TEXTS - AMHARIC ======================
TEXTS = {
    "am": {
        "start": "👋 ሰላም! ቴሌግራም ሱቅ ቦት ውስጥ እንኳን ወደ ደህና መጡ!\n\n🏪 ሱቅ ለመክፈት: /register\n📚 ስለ ቦቱ ለማወቅ: /help",
        "help": """📚 ይህ ቦት ምን ያደርጋል?

ይህ ቦት ማንኛውም ነጋዴ የራሱን ትንሽ ሱቅ ከፍቶ በቴሌግራም በኩል እቃ እንዲሸጥ፣ እና ደንበኞች በቀላሉ አይተው እንዲያዙ የሚያግዝ ነው።

━━━━━━━━━━━━━━━━
👨‍🏪 ለነጋዴዎች:
/register - አዲስ ሱቅ ክፈት (ስም፣ ስልክ፣ ቦታ፣ ክፍያ መንገድ እና 1ኛ ምርት ከፎቶ ጋር ይመዘገባል)
/addproduct - ተጨማሪ ምርት (ከፎቶ ጋር) ጨምር
/mystore - የሱቅዎን ሊንክ ያግኙ፣ ለደንበኞች ያጋሩ
/myorders - የደረሱ ትዕዛዞችን ይመልከቱ
/dashboard - አጠቃላይ ስታቲስቲክስ (ገቢ፣ ደረጃ፣ ወዘተ)

━━━━━━━━━━━━━━━━
👥 ለደንበኞች:
1️⃣ ነጋዴው የላከልዎትን ሊንክ ይንኩ
2️⃣ የምርቶቹን ፎቶ እያዩ የፈለጉትን ይምረጡ
3️⃣ ስም፣ ስልክ፣ አድራሻ ይሙሉ
4️⃣ የመክፈያ አይነት ይምረጡ (ሞባይል ባንክ / እቃው ሲደርስ / Telegram Stars)
5️⃣ እቃው ሲደርስዎት → /received
6️⃣ ተሞክሮዎን ደረጃ ለመስጠት → /rate

━━━━━━━━━━━━━━━━
📞 ችግር ካጋጠመዎት:
/dispute - ስለ አንድ የተወሰነ ትዕዛዝ ቅሬታ ለማቅረብ
/contact - ስለ ቦቱ አጠቃላይ ችግር ካለ በቀጥታ ለቦቱ ባለቤት ለመላክ

/cancel - በማንኛውም ሂደት ውስጥ ከሆኑ ለማቋረጥ""",
        "no_store_found": "❌ ሱቅ አልተገኘም። ሊንኩን እንደገና ይሞክሩ።",
        "no_products": "❌ ይህ ሱቅ ገና ምርት የለውም።",
        "already_merchant": "❌ አስቀድመው ሱቅ ከፍተዋል!",
        "register_name": "🏪 ሱቅ ስም?",
        "register_phone": "📞 ስልክ ቁጥር?",
        "register_location": "📍 ቦታ?",
        "register_payment": "💳 የሞባይል ባንክ/ቴሌብር ክፍያ ዝርዝርዎ? (ለምሳሌ: CBE Birr - 1000123456 - አበበ በቀለ)",
        "register_product": "📦 የመጀመሪያ ምርት ስም?",
        "register_price": "💵 የ{product} ዋጋ (በብር)?",
        "register_photo": "📸 የ{product} ፎቶ ይላኩ (ደንበኞች እያዩ ይመርጣሉ)።\n\nፎቶ ከሌልዎት 'ዝለል' ብለው ይጻፉ።",
        "register_success": "🎉 ሱቅ ተከፍቷል!\n\n🔗 ይህን ሊንክ ለደንበኞችዎ ያጋሩ:\n{link}\n\n/addproduct - ተጨማሪ ምርት ለመጨመር\n/mystore - ሊንኩን መልሶ ለማየት",
        "invalid_price": "❌ እባክዎ ቁጥር ብቻ ያስገቡ (ለምሳሌ 250)",
        "addproduct_name": "📦 አዲስ ምርት ስም?",
        "addproduct_price": "💵 ዋጋ (በብር)?",
        "addproduct_photo": "📸 የምርቱ ፎቶ ይላኩ።\n\nፎቶ ከሌልዎት 'ዝለል' ብለው ይጻፉ።",
        "addproduct_success": "✅ ምርት ተጨምሯል: {product} - {price} ብር",

        "order_select": "🛒 ከ«{store}» የፈለጉትን ምርት ፎቶ እያዩ ይምረጡ:",
        "select_this": "🛒 ይህን ይምረጡ",
        "order_name": "👤 ሙሉ ስምዎ ማን ነው?",
        "order_phone": "📞 ስልክ ቁጥርዎ?",
        "order_address": "📍 አድራሻዎ (ለማድረስ)?",
        "order_confirm": """📋 የትዕዛዝ ማጠቃለያ

📦 ምርት: {product}
💵 ዋጋ: {price} ብር
👤 ስም: {name}
📞 ስልክ: {phone}
📍 አድራሻ: {address}

ትክክል ነው?""",
        "choose_payment_method": "💳 እንዴት መክፈል ይፈልጋሉ?",
        "order_confirmed": """✅ ትዕዛዝ ተረጋግጧል!

━━━━━━━━━━━━━━━━
💳 እባክዎ ይህን ብር ይላኩ:
{payment}
━━━━━━━━━━━━━━━━

📸 ክፍያ ከፈጸሙ በኋላ የክፍያ screenshot እዚሁ ይላኩ 👇""",
        "order_id": "🆔 የትዕዛዝ ቁጥር: {order_id}",
        "need_photo": "📸 እባክዎ የክፍያ screenshot (ፎቶ) ብቻ ይላኩ።",
        "payment_proof_received": """✅ የክፍያ ማረጋገጫ ደርሶናል! ነጋዴው አረጋግጦ እቃዎን ይልክልዎታል።

📦 እቃው ሲደርስዎት:
/received ብለው ይጻፉ

❌ ችግር ካጋጠመዎት:
/dispute ብለው ይጻፉ""",
        "merchant_payment_notify": "💳 ደንበኛ {name} ({phone}) ለትዕዛዝ {order_id} የክፍያ screenshot ልኳል። እባክዎ ያረጋግጡና እቃውን ይላኩ።",

        "pay_cod_confirmed": """✅ ትዕዛዝዎ ተመዝግቧል!

💵 እቃው ሲደርስዎት ብር ይከፍላሉ (Cash on Delivery)።
🆔 {order_id}

📦 እቃው ሲደርስዎት:
/received ብለው ይጻፉ""",
        "merchant_cod_notify": "💵 ይህ ደንበኛ 'እቃው ሲደርስ ብር' (COD) መርጦዋል። ገንዘብ ያለ screenshot ስለሚሆን፣ እቃውን ሲያደርሱ ገንዘቡን በቀጥታ ይቀበሉ።",

        "stars_invoice_desc": "ከ{store} ግዢ",
        "stars_invoice_sent": "⭐ የ Telegram Stars ክፍያ ተልኳል! እባክዎ ከላይ ያለውን መልእክት ተጫነው ይክፈሉ።",
        "stars_payment_success": "🎉 በ Telegram Stars ክፍያዎ ተሳክቷል!\n\n🆔 {order_id}\n\n📦 እቃው ሲደርስዎት:\n/received ብለው ይጻፉ",
        "merchant_stars_notify": "⭐ ደንበኛው በ Telegram Stars ({stars} ⭐) ከፍሏል። እቃውን መላክ ይችላሉ።",

        "merchant_notify": """🔔 አዲስ ትዕዛዝ!

🆔 {order_id}
📦 ምርት: {product}
💵 ዋጋ: {price} ብር
👤 ደንበኛ: {name}
📞 {phone}
📍 {address}""",

        "no_orders_for_user": "❌ የተመዘገበ ትዕዛዝ አላገኘንልዎትም።",
        "select_order": "🛒 የትኛውን ትዕዛዝ ነው?",
        "received_confirmed": "🎉 አመሰግናለሁ! እቃው እንደደረሰዎት ተመዝግቧል።\n\n⭐ የገዙትን ልምድ ደረጃ ይስጡ: /rate",
        "merchant_received_notify": "📦 ደንበኛ {name} ትዕዛዝ {order_id} እንደደረሰው አረጋግጧል።",

        "dispute_reason": "❌ ምን ችግር አጋጠመዎት? (በዝርዝር ይግለጹ)",
        "dispute_proof": "📸 ካለ ማስረጃ (ፎቶ) ይላኩ፣ ከሌለ 'የለም' ብለው ይጻፉ",
        "dispute_filed": "⚠️ ቅሬታዎ ደርሷል!\n\n🆔 የቅሬታ ቁጥር: {dispute_id}\n👨‍⚖️ አስተዳዳሪው በቅርቡ ያነጋግርዎታል።",
        "admin_dispute_notify": """🚨 አዲስ ቅሬታ!

🆔 {dispute_id}
📦 ትዕዛዝ: {order_id}
👤 ደንበኛ: {name} ({phone})
🏪 ነጋዴ: {store}

❌ ምክንያት:
{reason}""",

        "rating_prompt": "⭐ ከ1 እስከ 5 ደረጃ ይስጡ:",
        "rating_saved": "✅ ደረጃ ተመዝግቧል! አመሰግናለሁ 🙏\n\n📊 የሱቁ አማካይ ደረጃ: {avg} ⭐ ({count} ደረጃዎች)",
        "invalid_rating": "❌ ከ1 እስከ 5 ያለ ቁጥር ብቻ ይላኩ",

        "contact_prompt": "✍️ ስለ ቦቱ ያለዎትን ችግር ወይም አስተያየት ይጻፉ (ፎቶ ማያያዝም ይችላሉ)፣ በቀጥታ ለቦቱ ባለቤት ይደርሳል።",
        "contact_admin_notify": "📩 አዲስ መልእክት ከተጠቃሚ\n👤 {name} (@{username}, id: {user_id})",
        "contact_sent": "✅ መልእክትዎ ደርሷል! ቦቱ ባለቤት በቅርቡ ያገኙዎታል።",
        "contact_unavailable": "⚠️ ይቅርታ፣ ይህ አገልግሎት አሁን አልተዋቀረም። ቆይተው ይሞክሩ።",

        "dashboard": """📊 {store}

🛍️ ትዕዛዞች: {orders}
💰 ገቢ: {revenue} ብር
📦 ምርቶች: {products}
⭐ ደረጃ: {rating} ({rating_count} ደረጃዎች)""",

        "no_orders": "📭 ትዕዛዝ የለም",
        "no_store": "❌ እርስዎ ገና ሱቅ አልከፈቱም። /register ይጠቀሙ።",
        "success": "✅ ስኬታማ!",
        "error": "❌ ስህተት ተፈጥሯል!",
        "cancelled": "❌ ተቋርጧል",
    },
}


def t(lang, key, **kwargs):
    text = TEXTS.get(lang, TEXTS["am"]).get(key, f"[{key}]")
    return text.format(**kwargs) if kwargs else text


def is_skip(update: Update) -> bool:
    """True if the user typed something like 'skip' instead of sending a photo."""
    if update.message.photo:
        return False
    txt = (update.message.text or "").strip().lower()
    return txt in ("ዝለል", "skip", "/skip", "የለም", "none", "no")


# ====================== STORAGE (Supabase) ======================
# Tables expected (see schema.sql): merchants, orders, disputes, ratings
def _safe_execute(query, default=None):
    try:
        res = query.execute()
        return res.data
    except Exception as e:
        logger.error(f"❌ Supabase error: {e}")
        return default


def get_merchant_store(user_id):
    data = _safe_execute(
        supabase.table("merchants").select("*").eq("user_id", user_id), default=[]
    )
    return data[0] if data else None


def save_merchant_store(user_id, store_data):
    row = dict(store_data)
    row["user_id"] = user_id
    _safe_execute(supabase.table("merchants").upsert(row, on_conflict="user_id"))


def get_store(store_id):
    if not store_id:
        return None
    data = _safe_execute(
        supabase.table("merchants").select("*").eq("store_id", store_id), default=[]
    )
    return data[0] if data else None


def get_all_merchants():
    return _safe_execute(supabase.table("merchants").select("*"), default=[]) or []


def get_all_orders():
    return _safe_execute(
        supabase.table("orders").select("*").order("timestamp"), default=[]
    ) or []


def get_orders_for_store(store_id):
    return [o for o in get_all_orders() if o.get("store", {}).get("store_id") == store_id]


def get_orders_for_customer(user_id):
    return _safe_execute(
        supabase.table("orders").select("*").eq("customer_id", user_id), default=[]
    ) or []


def save_order(order):
    row = dict(order)
    _safe_execute(supabase.table("orders").upsert(row, on_conflict="order_id"))


def get_order(order_id):
    data = _safe_execute(
        supabase.table("orders").select("*").eq("order_id", order_id), default=[]
    )
    return data[0] if data else None


def save_dispute(dispute):
    _safe_execute(supabase.table("disputes").insert(dict(dispute)))


def save_rating(store_id, score):
    data = _safe_execute(
        supabase.table("ratings").select("*").eq("store_id", store_id), default=[]
    )
    if data:
        scores = data[0].get("scores") or []
        scores.append(score)
        _safe_execute(supabase.table("ratings").update({"scores": scores}).eq("store_id", store_id))
    else:
        _safe_execute(supabase.table("ratings").insert({"store_id": store_id, "scores": [score]}))


def get_rating_stats(store_id):
    data = _safe_execute(
        supabase.table("ratings").select("*").eq("store_id", store_id), default=[]
    )
    if not data:
        return 0.0, 0
    scores = data[0].get("scores") or []
    if not scores:
        return 0.0, 0
    return round(sum(scores) / len(scores), 1), len(scores)


# ====================== KEYBOARDS ======================
def confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="order_confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="order_cancel")],
    ])


def payment_method_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏦 የሞባይል ባንክ / ቴሌብር", callback_data="pay_mobile")],
        [InlineKeyboardButton("💵 እቃው ሲደርስ ብር (COD)", callback_data="pay_cod")],
        [InlineKeyboardButton("⭐ Telegram Stars", callback_data="pay_stars")],
    ])


def orders_keyboard(orders, prefix):
    buttons = []
    for o in orders[:10]:
        label = f"{o['order_id'][-8:]} - {o.get('product', {}).get('name', '')}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"{prefix}_{o['order_id']}")])
    return InlineKeyboardMarkup(buttons)


# ====================== START / DEEP LINK ======================
async def show_store_products(update: Update, context: ContextTypes.DEFAULT_TYPE, store):
    """Show a merchant's products (with photos) to a visiting customer."""
    lang = context.user_data.get("lang", "am")
    products = store.get("products", [])
    if not products:
        await update.message.reply_text(t(lang, "no_products"))
        return

    context.user_data["current_store"] = store
    await update.message.reply_text(t(lang, "order_select", store=store.get("store_name", "")))

    for i, prod in enumerate(products):
        caption = f"📦 {prod['name']}\n💵 {prod['price']} ብር"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(lang, "select_this"), callback_data=f"prod_{i}")]])
        photo_id = prod.get("photo_file_id")
        if photo_id:
            await update.message.reply_photo(photo=photo_id, caption=caption, reply_markup=kb)
        else:
            await update.message.reply_text(caption, reply_markup=kb)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """START command — correctly handles store deep-links (/start <store_id>)."""
    user = update.effective_user
    lang = context.user_data.setdefault("lang", "am")

    # 1. Parameter ካለ (ደንበኛው በሱቅ ሊንክ ከመጣ)
    if context.args:
        store_id = context.args[0].strip()
        store = get_store(store_id)

        if store:
            if store["user_id"] == user.id:
                await update.message.reply_text("😊 ይሄ የራስዎ ሱቅ ነው።")
            else:
                await show_store_products(update, context, store)
            return
        else:
            await update.message.reply_text(t(lang, "no_store_found"))
            return

    # 2. ነጋዴ ከሆነ የሱቁን ዳሽቦርድ ማውጫ ያሳየዋል
    merchant_store = get_merchant_store(user.id)
    if merchant_store:
        await update.message.reply_text(
            f"👨‍🏪 እንኳን ደህና መጡ {user.first_name}!\n\n"
            f"🏪 ሱቅ: {merchant_store['store_name']}\n\n"
            f"/dashboard - ስታቲስቲክስ\n"
            f"/myorders - ትዕዛዞች\n"
            f"/mystore - ሊንክ ያጋሩ\n"
            f"/addproduct - ምርት ጨምር"
        )
        return

    # 3. Parameter ከሌለውና አዲስ ተጠቃሚ ከሆነ ሰላምታ መልእክት ይልካል
    await update.message.reply_text(t(lang, "start"))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text(t(lang, "help"))


# ====================== REGISTRATION ======================
async def reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")

    if get_merchant_store(user.id):
        await update.message.reply_text(t(lang, "already_merchant"))
        return ConversationHandler.END

    context.user_data["reg_data"] = {
        "user_id": user.id,
        "username": user.username or "merchant",
        "store_id": f"store_{user.id}_{uuid4().hex[:8]}",
        "created": datetime.now().isoformat(),
        "products": [],
    }

    await update.message.reply_text(t(lang, "register_name"))
    return REG_STORE_NAME


async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_data"]["store_name"] = update.message.text
    await update.message.reply_text(t(context.user_data.get("lang", "am"), "register_phone"))
    return REG_PHONE


async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_data"]["phone"] = update.message.text
    await update.message.reply_text(t(context.user_data.get("lang", "am"), "register_location"))
    return REG_LOCATION


async def reg_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_data"]["location"] = update.message.text
    await update.message.reply_text(t(context.user_data.get("lang", "am"), "register_payment"))
    return REG_PAYMENT


async def reg_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_data"]["payment_method"] = update.message.text
    await update.message.reply_text(t(context.user_data.get("lang", "am"), "register_product"))
    return REG_PRODUCT


async def reg_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    context.user_data["reg_data"]["_pending_product_name"] = update.message.text
    await update.message.reply_text(t(lang, "register_price", product=update.message.text))
    return REG_PRICE


async def reg_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    try:
        price = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(t(lang, "invalid_price"))
        return REG_PRICE

    reg_data = context.user_data["reg_data"]
    product_name = reg_data.pop("_pending_product_name")
    reg_data["_pending_product"] = {"name": product_name, "price": price}

    await update.message.reply_text(t(lang, "register_photo", product=product_name))
    return REG_PHOTO


# FIX (new): accept a product photo (or 'skip') to finish registration
async def reg_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    reg_data = context.user_data["reg_data"]
    pending = reg_data.pop("_pending_product")

    if update.message.photo:
        pending["photo_file_id"] = update.message.photo[-1].file_id
    elif not is_skip(update):
        # not a photo and not a recognized "skip" — nudge them, stay in state
        reg_data["_pending_product"] = pending
        await update.message.reply_text(t(lang, "register_photo", product=pending["name"]))
        return REG_PHOTO

    reg_data["products"].append(pending)

    store_data = context.user_data.pop("reg_data")
    save_merchant_store(store_data["user_id"], store_data)

    bot = await context.bot.get_me()
    link = f"https://t.me/{bot.username}?start={store_data['store_id']}"

    logger.info(f"✅ Store created: {store_data['store_name']}")

    await update.message.reply_text(t(lang, "register_success", link=link))
    return ConversationHandler.END


# ====================== ADD PRODUCT (merchant, outside registration) ======================
async def addproduct_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")
    merchant = get_merchant_store(user.id)
    if not merchant:
        await update.message.reply_text(t(lang, "no_store"))
        return ConversationHandler.END
    await update.message.reply_text(t(lang, "addproduct_name"))
    return REG_PRODUCT


async def addproduct_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    context.user_data["_new_product_name"] = update.message.text
    await update.message.reply_text(t(lang, "addproduct_price"))
    return REG_PRICE


async def addproduct_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    try:
        price = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(t(lang, "invalid_price"))
        return REG_PRICE

    product_name = context.user_data.pop("_new_product_name")
    context.user_data["_new_product_pending"] = {"name": product_name, "price": price}
    await update.message.reply_text(t(lang, "addproduct_photo"))
    return REG_PHOTO


async def addproduct_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    pending = context.user_data.get("_new_product_pending")

    if update.message.photo:
        pending["photo_file_id"] = update.message.photo[-1].file_id
    elif not is_skip(update):
        await update.message.reply_text(t(lang, "addproduct_photo"))
        return REG_PHOTO

    context.user_data.pop("_new_product_pending", None)

    user = update.effective_user
    merchant = get_merchant_store(user.id)
    merchant["products"].append(pending)
    save_merchant_store(user.id, merchant)

    await update.message.reply_text(t(lang, "addproduct_success", product=pending["name"], price=pending["price"]))
    return ConversationHandler.END


# ====================== CUSTOMER ORDER FLOW ======================
async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")

    store = context.user_data.get("current_store")
    if not store:
        await query.message.reply_text(t(lang, "error"))
        return ConversationHandler.END

    try:
        prod_idx = int(query.data.replace("prod_", ""))
        product = store["products"][prod_idx]
    except (ValueError, IndexError):
        await query.message.reply_text(t(lang, "error"))
        return ConversationHandler.END

    context.user_data["order_data"] = {
        "store": store,
        "product": product,
    }

    text = f"📦 {product['name']}\n💵 {product['price']} ብር\n\n{t(lang, 'order_name')}"
    # the button may be attached to a photo message or a text message
    if query.message.photo:
        await query.edit_message_caption(caption=text)
    else:
        await query.edit_message_text(text)
    return ORDER_GET_NAME


async def order_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_data"]["name"] = update.message.text
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text(t(lang, "order_phone"))
    return ORDER_GET_PHONE


async def order_get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_data"]["phone"] = update.message.text
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text(t(lang, "order_address"))
    return ORDER_GET_ADDRESS


async def order_get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_data"]["address"] = update.message.text
    lang = context.user_data.get("lang", "am")

    order = context.user_data["order_data"]
    product = order["product"]

    text = t(lang, "order_confirm",
             product=product["name"],
             price=product["price"],
             name=order["name"],
             phone=order["phone"],
             address=order["address"])

    await update.message.reply_text(text, reply_markup=confirm_keyboard())
    return ORDER_CONFIRM


async def order_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")

    if query.data == "order_cancel":
        await query.edit_message_text(t(lang, "cancelled"))
        context.user_data.pop("order_data", None)
        context.user_data.pop("current_store", None)
        return ConversationHandler.END

    user = update.effective_user
    order = context.user_data["order_data"]
    order["timestamp"] = datetime.now().isoformat()
    order["order_id"] = f"order_{uuid4().hex[:8]}"
    order["customer_id"] = user.id
    order["status"] = "awaiting_payment_method"
    save_order(order)

    await query.edit_message_text(t(lang, "choose_payment_method"), reply_markup=payment_method_keyboard())
    return ORDER_PAYMENT_METHOD


# NEW: let the customer choose HOW to pay
async def order_payment_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")

    order = context.user_data.get("order_data")
    if not order:
        await query.edit_message_text(t(lang, "error"))
        return ConversationHandler.END

    choice = query.data  # pay_mobile | pay_cod | pay_stars

    if choice == "pay_mobile":
        order["payment_choice"] = "mobile"
        order["status"] = "awaiting_payment_proof"
        save_order(order)
        store = order["store"]
        text = t(lang, "order_confirmed", payment=store.get("payment_method", "N/A"))
        text += "\n\n" + t(lang, "order_id", order_id=order["order_id"])
        await query.edit_message_text(text)
        return ORDER_PAYMENT_PROOF

    if choice == "pay_cod":
        order["payment_choice"] = "cod"
        order["status"] = "cod_confirmed"
        save_order(order)

        store = order["store"]
        product = order["product"]
        notify_text = t(lang, "merchant_notify",
                         order_id=order["order_id"], product=product["name"], price=product["price"],
                         name=order["name"], phone=order["phone"], address=order["address"])
        try:
            await context.bot.send_message(store["user_id"], notify_text)
            await context.bot.send_message(store["user_id"], t(lang, "merchant_cod_notify"))
        except Exception as e:
            logger.error(f"❌ Notify error: {e}")

        await query.edit_message_text(t(lang, "pay_cod_confirmed", order_id=order["order_id"]))
        context.user_data.pop("order_data", None)
        context.user_data.pop("current_store", None)
        return ConversationHandler.END

    if choice == "pay_stars":
        order["payment_choice"] = "stars"
        order["status"] = "awaiting_stars_payment"
        save_order(order)

        product = order["product"]
        stars_amount = max(1, round(product["price"] * STARS_RATE))
        prices = [LabeledPrice(product["name"], stars_amount)]

        try:
            await context.bot.send_invoice(
                chat_id=update.effective_user.id,
                title=product["name"],
                description=t(lang, "stars_invoice_desc", store=order["store"].get("store_name", "")),
                payload=order["order_id"],
                provider_token="",  # empty for Telegram Stars (XTR)
                currency="XTR",
                prices=prices,
            )
            await query.edit_message_text(t(lang, "stars_invoice_sent"))
        except Exception as e:
            logger.error(f"❌ Stars invoice error: {e}")
            await query.edit_message_text(t(lang, "error"))

        context.user_data.pop("order_data", None)
        context.user_data.pop("current_store", None)
        return ConversationHandler.END

    await query.edit_message_text(t(lang, "error"))
    return ConversationHandler.END


# accept the mobile-bank payment screenshot and forward it to the merchant
async def order_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")

    if not update.message.photo:
        await update.message.reply_text(t(lang, "need_photo"))
        return ORDER_PAYMENT_PROOF

    order = context.user_data.get("order_data")
    if not order:
        await update.message.reply_text(t(lang, "error"))
        return ConversationHandler.END

    file_id = update.message.photo[-1].file_id
    order["payment_proof_file_id"] = file_id
    order["status"] = "paid_pending_confirmation"
    save_order(order)

    store = order["store"]
    product = order["product"]

    notify_text = t(lang, "merchant_notify",
                     order_id=order["order_id"],
                     product=product["name"],
                     price=product["price"],
                     name=order["name"],
                     phone=order["phone"],
                     address=order["address"])
    try:
        await context.bot.send_message(store["user_id"], notify_text)
        await context.bot.send_photo(
            store["user_id"],
            photo=file_id,
            caption=t(lang, "merchant_payment_notify",
                      name=order["name"], phone=order["phone"], order_id=order["order_id"])
        )
    except Exception as e:
        logger.error(f"❌ Notify error: {e}")

    await update.message.reply_text(t(lang, "payment_proof_received"))

    context.user_data.pop("order_data", None)
    context.user_data.pop("current_store", None)
    return ConversationHandler.END


# /received — customer confirms delivery
async def cmd_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")

    orders = [o for o in get_orders_for_customer(user.id)
              if o.get("status") in ("paid_pending_confirmation", "cod_confirmed", "stars_paid", "shipped")]

    if not orders:
        await update.message.reply_text(t(lang, "no_orders_for_user"))
        return

    if len(orders) == 1:
        await _mark_received(update, context, orders[0])
        return

    await update.message.reply_text(
        t(lang, "select_order"),
        reply_markup=orders_keyboard(orders, "received")
    )


async def received_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = query.data.replace("received_", "")
    order = get_order(order_id)
    if not order:
        await query.edit_message_text(t(context.user_data.get("lang", "am"), "error"))
        return
    await _mark_received(update, context, order, from_callback=True)


async def _mark_received(update, context, order, from_callback=False):
    lang = context.user_data.get("lang", "am")
    order["status"] = "delivered"
    save_order(order)

    store = order["store"]
    try:
        await context.bot.send_message(
            store["user_id"],
            t(lang, "merchant_received_notify", name=order["name"], order_id=order["order_id"])
        )
    except Exception as e:
        logger.error(f"❌ Notify error: {e}")

    text = t(lang, "received_confirmed")
    if from_callback:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)


# ====================== TELEGRAM STARS PAYMENT HANDLERS ======================
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Must answer within 10s. We approve every pre-checkout for now."""
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    payment = update.message.successful_payment
    order_id = payment.invoice_payload
    order = get_order(order_id)
    if not order:
        logger.error(f"❌ Successful payment for unknown order {order_id}")
        return

    order["status"] = "stars_paid"
    order["stars_amount"] = payment.total_amount
    save_order(order)

    store = order["store"]
    product = order["product"]
    try:
        notify_text = t(lang, "merchant_notify",
                         order_id=order["order_id"], product=product["name"], price=product["price"],
                         name=order["name"], phone=order["phone"], address=order["address"])
        await context.bot.send_message(store["user_id"], notify_text)
        await context.bot.send_message(store["user_id"], t(lang, "merchant_stars_notify", stars=payment.total_amount))
    except Exception as e:
        logger.error(f"❌ Notify error: {e}")

    await update.message.reply_text(t(lang, "stars_payment_success", order_id=order["order_id"]))


# ====================== DISPUTE FLOW ======================
async def dispute_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")
    orders = get_orders_for_customer(user.id)

    if not orders:
        await update.message.reply_text(t(lang, "no_orders_for_user"))
        return ConversationHandler.END

    if len(orders) == 1:
        context.user_data["dispute_order"] = orders[0]
        await update.message.reply_text(t(lang, "dispute_reason"))
        return DISPUTE_REASON

    await update.message.reply_text(t(lang, "select_order"), reply_markup=orders_keyboard(orders, "dispute"))
    return DISPUTE_SELECT_ORDER
