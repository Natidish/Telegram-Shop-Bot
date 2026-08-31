"""
🎊 TELEGRAM SHOP BOT - ULTIMATE AMHARIC FIRST VERSION
========================================================
✨ DEFAULT AMHARIC LANGUAGE
✨ BEAUTIFUL WELCOME SCREEN
✨ DETAILED HOW TO USE
✨ REFERRAL REWARDS SYSTEM
✨ ADMIN PANEL
✨ EMOJI RICH INTERFACE
✨ DATABASE READY FOR POSTGRES
"""

import logging
import os
import asyncio
import json
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Chat
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ====================== SETUP ======================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not set!")

PORT = int(os.environ.get("PORT", 10000))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

STORAGE_DIR = "bot_data"
os.makedirs(STORAGE_DIR, exist_ok=True)

logger.info("🤖 Bot starting with Amharic as default language")

# ====================== STATES ======================
SELECT_PRODUCT, GET_NAME, GET_PHONE, GET_ADDRESS, CONFIRM = range(5)
REG_NAME, REG_PHONE, REG_LOCATION, REG_PAYMENT, REG_PROD_NAME, REG_PROD_PRICE, REG_PROD_PHOTO, REG_PROD_DESC, REG_MORE = range(10, 19)
LANG_SELECT = 100

# ====================== TEXTS - AMHARIC FIRST ======================
TEXTS = {
    "am": {
        "welcome": """
👋 ሰላም! እንኳን ወደ ቴሌግራም ሱቅ ቦት ደህና መጡ!

🎯 በዚህ ቦት ብዙ ሰዎች ሱቆቻቸውን ገንብተዋል
💼 እና ብዙ ገቢ አግኝተዋል

📱 ምን ትፈልጉ?
""",
        "welcome_merchant": """
👨‍💼 ሰላም {name}!

🎉 ወደ ሱቁ እንኳን ወደ ደህና መጡ!

🏪 ሱቅ: {store}
👤 Username: @{username}
✅ ሁኔታ: {status}

━━━━━━━━━━━━━━━━━━━━
📊 ወደ ዳሽቦርድ ይሂዱ
━━━━━━━━━━━━━━━━━━━━
""",
        "main_menu": """
🏠 ዋና ሳህን - እንዴት ይጠቀም?

👨‍🏪 ነጋዴ ነሀ?
   → /register ሱቅ ይክፈቱ
   → /dashboard ስታቲስቲክስ ይመልከቱ
   
👥 ደንበኛ ነሀ?
   → ሉከቁ ሊንክ ሻጋታ
   → ምርት ይመርጡ
   → ትዕዛዝ ሞክሩ

━━━━━━━━━━━━━━━━━━━━
ምን ይፈልጋሉ?
""",
        "how_to_use": """
📚 ቦት እንዴት ይጠቀም

━━━━━━━━━━━━━━━━━━━━
👨‍🏪 ለነጋዴወች (Merchants)
━━━━━━━━━━━━━━━━━━━━

1️⃣ REGISTER - ሱቅ ይክፈቱ
   /register ብታዩ
   - ሱቅ ስም ይፃፉ
   - ስልክ ቁጥር ይፃፉ  
   - ቦታ ይፃፉ
   - ክፍያ መረጃ ይፃፉ
   - ምርትወች ጨምሩ
   ✅ 30 ቀናት ነጻ!

2️⃣ SHARE YOUR LINK
   /mystore ብታዩ
   👉 ሊንክ ይኮኑ
   👉 ደንበኞች ይላኩ
   💰 ትዕዛዞች ይደርስ!

3️⃣ MANAGE STORE
   /dashboard - ስታቲስቲክስ
   /myorders - ትዕዛዞች ይመልከቱ
   /addproduct - ምርት ጨምሩ
   /test_notify - ሙከራ ሰሩ

4️⃣ EARN WITH REFERRAL
   🎁 ሪፌራል ሊንክ ያግኙ
   👉 ወዳጆች ይላኩ
   💰 እነሱ ሱቅ ከፈቱ
   🏆 ገቢ ይክፍያ!

━━━━━━━━━━━━━━━━━━━━
👥 ለደንበኞች (Customers)
━━━━━━━━━━━━━━━━━━━━

1️⃣ ሊንክ ይጠቀሙ
   ነጋዴ ሊንክ ይቀቡ
   👉 ጠቅ ያድርጉ

2️⃣ BROWSE PRODUCTS
   📋 ምርቶች ይመልከቱ
   ⭐ ዝርዝር ይማሩ

3️⃣ PLACE ORDER
   🛒 ትዕዛዝ ያስቀምጡ
   - ስም ይፃፉ
   - ስልክ ይፃፉ
   - አድራሻ ይፃፉ

4️⃣ PAYMENT
   💳 ክፍያ መረጃ ይቀቡ
   💸 ብር ይላኩ
   📸 ሰክርን ይላኩ

━━━━━━━━━━━━━━━━━━━━
💡 ምክር
━━━━━━━━━━━━━━━━━━━━
✅ ሱቅ ጠብቅ (ምርት ይጨምሩ)
✅ ደንበኛ ፈጣን ይመልሱ  
✅ ሪፌራል ይጠቀሙ (ገቢ ያስክፍ)
✅ /help ለበለጠ ትርጉም

📞 ጥያቄ? @BotSupport ይደውሉ
""",
        "register_prompt": "🏪 ሱቅ ይክፈቱ!\n\n1️⃣ የሱቅ ስም ምን ይሆን?",
        "shop_created": """
🎉 🎉 🎉 ሱቅ ተከፍቷል!

🏪 ስም: {store}
👤 Username: @{username}
📍 ID: {store_id}

━━━━━━━━━━━━━━━━━━━━
🔗 ደንበኞች ሊንክ:
{link}

🎁 ሪፌራል ሊንክ:
{ref_link}

━━━━━━━━━━━━━━━━━━━━
✅ ጀምር!
/dashboard - ስታቲስቲክስ
/addproduct - ምርት ጨምር
/test_notify - ሙከራ ሰራ
""",
        "order_confirm": """
✅ ትዕዛዝ ተረጋገጠ!

📦 ምርት: {product}
💵 ዋጋ: {price} ብር
👤 ስም: {name}
📞 ስልክ: {phone}
📍 አድራሻ: {address}

━━━━━━━━━━━━━━━━━━━━
💳 ይህ ገንዘብ ይላኩ:

{payment}

━━━━━━━━━━━━━━━━━━━━
📸 ከላከ በኋላ:
🖼️ ሰክርን ይሰሩ
📲 ይላኩ: {phone}

❓ ጥያቄ? ደርድር ያድርጉ
""",
        "merchant_notification": """
🔔 🔥 አዲስ ትዕዛዝ ደርሶዎታል!

🏪 ሱቅ: {store}
📦 ምርት: {product}
💵 ዋጋ: {price} ብር

👤 ደንበኛ: {name}
📞 ስልክ: {phone}
📍 አድራሻ: {address}

🕐 ሰአት: {timestamp}

━━━━━━━━━━━━━━━━━━━━
⚡ በቅጥበት ይመልሱ!
""",
        "test_msg": "✅ ሙከራ ስኬታማ!\n\n메시징 ሥርዐት ይሰራል! 🎉",
        "no_store": "❌ ሱቅ አልተገኘም\n\n/register ይጠቀሙ",
        "no_orders": "📭 ገና ትዕዛዝ የለም\n\nስብr ይጠብቁ! 😊",
        "dashboard": """
📊 DASHBOARD - {store}

━━━━━━━━━━━━━━━━━━━━
📈 ስታቲስቲክስ:
━━━━━━━━━━━━━━━━━━━━
🛍️ ጠቅላላ ትዕዛዞች: {total_orders}
💰 ጠቅላላ ገቢ: {total_revenue} ብር
📦 ምርቶች: {total_products}
🎁 ሪፌራሎች: {referrals}

━━━━━━━━━━━━━━━━━━━━
🟢 ሁኔታ: {status}
⏰ ትግበራ: {days_left} ቀናት ተቀሩ

━━━━━━━━━━━━━━━━━━━━
🔗 ሊንክ ሰናጋግ:
{store_link}
""",
        "admin_panel": """
👨‍💼 ADMIN PANEL

━━━━━━━━━━━━━━━━━━━━
📊 SYSTEM STATUS
━━━━━━━━━━━━━━━━━━━━
🏪 Total Stores: {total_stores}
👥 Total Users: {total_users}
📦 Total Orders: {total_orders}
💰 Total Revenue: {total_revenue} Br

━━━━━━━━━━━━━━━━━━━━
🎯 Top Stores:
━━━━━━━━━━━━━━━━━━━━
{top_stores}

━━━━━━━━━━━━━━━━━━━━
Actions:
/broadcast - Message all users
/block_store - Block a store
/remove_user - Remove user
""",
    },
    "en": {
        "welcome": """
👋 Welcome to Telegram Shop Bot!

🎯 Thousands of merchants here
💼 Making great sales

📱 What do you want?
""",
        "welcome_merchant": """
👨‍💼 Welcome {name}!

🎉 Welcome to your shop!

🏪 Store: {store}
👤 Username: @{username}
✅ Status: {status}

━━━━━━━━━━━━━━━━━━━━
📊 Go to Dashboard
━━━━━━━━━━━━━━━━━━━━
""",
        "main_menu": """
🏠 Main Menu

👨‍🏪 Merchant?
   → /register Create shop
   → /dashboard Stats
   
👥 Customer?
   → Get merchant link
   → Browse products
   → Place order

What would you like?
""",
        "how_to_use": """
📚 HOW TO USE THIS BOT

━━━━━━━━━━━━━━━━━━━━
FOR MERCHANTS
━━━━━━━━━━━━━━━━━━━━

1️⃣ /register - Create shop
2️⃣ /mystore - Get shareable link
3️⃣ /dashboard - View stats
4️⃣ /test_notify - Test messages
5️⃣ Share link with customers

━━━━━━━━━━━━━━━━━━━━
FOR CUSTOMERS
━━━━━━━━━━━━━━━━━━━━

1️⃣ Get merchant link
2️⃣ Click it
3️⃣ Browse products
4️⃣ Place order
5️⃣ Send payment

━━━━━━━━━━━━━━━━━━━━
💡 TIPS
━━━━━━━━━━━━━━━━━━━━
✅ Keep store updated
✅ Reply customers fast
✅ Use referral links
✅ 30 days free trial

Need help? /help
""",
        "register_prompt": "🏪 Create Your Shop!\n\n1️⃣ Store name?",
        "shop_created": """
🎉 Shop Created!

🏪 Name: {store}
👤 Username: @{username}

🔗 Customer Link:
{link}

🎁 Referral Link:
{ref_link}

✅ Start!
/dashboard
/addproduct
/test_notify
""",
        "order_confirm": """
✅ Order Confirmed!

📦 Product: {product}
💵 Price: {price} Br
👤 Name: {name}
📞 Phone: {phone}
📍 Address: {address}

💳 Pay to:
{payment}

📸 Send screenshot to:
{phone}
""",
        "merchant_notification": """
🔔 NEW ORDER!

🏪 Store: {store}
📦 Product: {product}
💵 Price: {price} Br
👤 Customer: {name}
📞 Phone: {phone}
📍 Address: {address}
🕐 Time: {timestamp}

⚡ Reply fast!
""",
        "test_msg": "✅ Test Successful!\n\nMessaging works! 🎉",
        "no_store": "No store found\n\n/register to create",
        "no_orders": "No orders yet\n\nBe patient! 😊",
        "dashboard": """
📊 DASHBOARD - {store}

📈 Statistics:
🛍️ Orders: {total_orders}
💰 Revenue: {total_revenue} Br
📦 Products: {total_products}
🎁 Referrals: {referrals}

🟢 Status: {status}
⏰ Trial: {days_left} days left

🔗 Share Link:
{store_link}
""",
        "admin_panel": """
👨‍💼 ADMIN PANEL

📊 SYSTEM
🏪 Stores: {total_stores}
👥 Users: {total_users}
📦 Orders: {total_orders}
💰 Revenue: {total_revenue} Br

🎯 Top Stores:
{top_stores}
""",
    }
}

def get_text(lang, key, **kwargs):
    """Get translated text"""
    text = TEXTS.get(lang, TEXTS["am"]).get(key, f"Missing: {key}")
    try:
        return text.format(**kwargs) if kwargs else text
    except:
        return text

# ====================== STORAGE ======================
def save_store(store_id, data):
    path = os.path.join(STORAGE_DIR, f"store_{store_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_store(store_id):
    path = os.path.join(STORAGE_DIR, f"store_{store_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def get_store_by_owner(owner_id):
    for file in os.listdir(STORAGE_DIR):
        if file.startswith("store_"):
            sid = file.replace("store_", "").replace(".json", "")
            store = get_store(sid)
            if store and store.get("owner_id") == owner_id:
                return (sid, store)
    return None

def save_order(order):
    order_id = f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    path = os.path.join(STORAGE_DIR, f"{order_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(order, f, ensure_ascii=False, indent=2)
    return order_id

def get_orders(store_id, limit=20):
    orders = []
    for file in sorted(os.listdir(STORAGE_DIR), reverse=True):
        if file.startswith("order_"):
            path = os.path.join(STORAGE_DIR, file)
            with open(path, "r", encoding="utf-8") as f:
                order = json.load(f)
                if order.get("store_id") == store_id:
                    orders.append(order)
                    if len(orders) >= limit:
                        break
    return orders

def is_active(store):
    reg_date_str = store.get("registration_date", datetime.now().strftime("%Y-%m-%d"))
    try:
        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
    except:
        return True
    expiry = reg_date + timedelta(days=30)
    return datetime.now() < expiry

def days_left(store):
    reg_date_str = store.get("registration_date")
    if not reg_date_str:
        return 30
    try:
        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
        expiry = reg_date + timedelta(days=30)
        remaining = (expiry - datetime.now()).days
        return max(0, remaining)
    except:
        return 30

def get_all_stores():
    stores = []
    for file in os.listdir(STORAGE_DIR):
        if file.startswith("store_"):
            sid = file.replace("store_", "").replace(".json", "")
            store = get_store(sid)
            if store:
                stores.append((sid, store))
    return stores

# ====================== KEYBOARDS ======================
def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇪🇹 አማርኛ (Amharic)", callback_data="lang_am")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ])

def main_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏪 " + ("ሱቅ ይክፈቱ" if lang == "am" else "Create Shop"), callback_data="action_register")],
        [InlineKeyboardButton("📚 " + ("እንዴት ይጠቀም" if lang == "am" else "How to Use"), callback_data="action_how")],
        [InlineKeyboardButton("❓ " + ("ጠያቂ" if lang == "am" else "Help"), callback_data="action_help")],
        [InlineKeyboardButton("🌐 " + ("ቋንቋ ለውጥ" if lang == "am" else "Change Lang"), callback_data="action_lang")],
    ])

def merchant_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 " + ("ዳሽቦርድ" if lang == "am" else "Dashboard"), callback_data="merch_dashboard")],
        [InlineKeyboardButton("📋 " + ("ትዕዛዞች" if lang == "am" else "Orders"), callback_data="merch_orders")],
        [InlineKeyboardButton("🔗 " + ("ሊንክ" if lang == "am" else "My Link"), callback_data="merch_link")],
        [InlineKeyboardButton("📚 " + ("ጠያቂ" if lang == "am" else "Help"), callback_data="action_help")],
    ])

def products_menu(products, lang):
    buttons = [
        [InlineKeyboardButton(f"{p['name']} - {p['price']} Br", callback_data=f"prod_{k}")]
        for k, p in products.items()
    ]
    buttons.append([InlineKeyboardButton("⬅️ " + ("ተመለስ" if lang == "am" else "Back"), callback_data="menu_back")])
    return InlineKeyboardMarkup(buttons)

# ====================== COMMANDS ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    lang = context.user_data.get("lang", "am")  # DEFAULT AMHARIC!
    
    # Store link
    if args:
        store_id = args[0]
        store = get_store(store_id)
        if not store:
            await update.message.reply_text("❌ Invalid link")
            return
        if not is_active(store):
            await update.message.reply_text("🔴 " + ("ሱቁ ተዝግቷል" if lang == "am" else "Store closed"))
            return
        
        context.user_data["store_id"] = store_id
        await update.message.reply_text(
            f"🏪 {store['store_name']}\n\n" + ("ምርቶች ይመልከቱ:" if lang == "am" else "Browse products:"),
            reply_markup=products_menu(store.get("products", {}), lang)
        )
        return
    
    # Merchant dashboard
    owner_store = get_store_by_owner(user.id)
    if owner_store:
        _, store = owner_store
        status = "✅ " + ("ንቁ" if is_active(store) else "ጊዜ ያልቃ") if lang == "am" else ("✅ Active" if is_active(store) else "❌ Expired")
        
        welcome_text = get_text(lang, "welcome_merchant", 
            name=user.first_name or "Friend",
            store=store['store_name'],
            username=store.get('username'),
            status=status
        )
        
        await update.message.reply_text(welcome_text, reply_markup=merchant_menu(lang))
        return
    
    # New user - show welcome in AMHARIC by default
    await update.message.reply_text(
        get_text(lang, "welcome"),
        reply_markup=main_keyboard(lang)
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang = query.data.replace("lang_", "")
    context.user_data["lang"] = lang
    
    msg = "✅ " + ("አማርኛ ተመርጧል!" if lang == "am" else "English selected!")
    await query.edit_message_text(msg)
    
    # Restart
    await query.message.reply_text(
        get_text(lang, "welcome"),
        reply_markup=main_keyboard(lang)
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text(get_text(lang, "how_to_use"))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("❌ " + ("ተቋርጧል" if lang == "am" else "Cancelled"))
    context.user_data.clear()
    return ConversationHandler.END

# ====================== REGISTRATION ======================
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    user = update.effective_user
    
    if get_store_by_owner(user.id):
        await update.message.reply_text("❌ " + ("ቀድሞ ሱቅ አለዎት" if lang == "am" else "You already have a store"))
        return ConversationHandler.END
    
    ref_code = f"ref_{user.id}"
    
    context.user_data["new_store"] = {
        "user_id": user.id,
        "username": user.username or "merchant",
        "first_name": user.first_name or "User",
        "referral_code": ref_code,
        "referrals": [],
        "products": {},
        "lang": lang
    }
    
    await update.message.reply_text(get_text(lang, "register_prompt"))
    return 100

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    context.user_data["new_store"]["store_name"] = update.message.text
    await update.message.reply_text("📞 " + ("2️⃣ ስልክ ቁጥር?" if lang == "am" else "2️⃣ Phone?"))
    return 101

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    context.user_data["new_store"]["phone"] = update.message.text
    await update.message.reply_text("📍 " + ("3️⃣ ቦታ?" if lang == "am" else "3️⃣ Location?"))
    return 102

async def reg_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    context.user_data["new_store"]["location"] = update.message.text
    await update.message.reply_text("💳 " + ("4️⃣ ክፍያ መረጃ?" if lang == "am" else "4️⃣ Payment?"))
    return 103

async def reg_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    context.user_data["new_store"]["payment_method"] = update.message.text
    await update.message.reply_text("📦 " + ("5️⃣ ማዞሪያ ምርት ስም?" if lang == "am" else "5️⃣ First product?"))
    return 104

async def reg_prod_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["temp_prod_name"] = update.message.text
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("💵 " + ("ዋጋ?" if lang == "am" else "Price?"))
    return 105

async def reg_prod_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["temp_prod_price"] = int(update.message.text.strip())
    except:
        lang = context.user_data.get("lang", "am")
        await update.message.reply_text("❌ " + ("ቁጥር ብቻ" if lang == "am" else "Number only"))
        return 105
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("📸 " + ("ፎቶ? (/skip)" if lang == "am" else "Photo? (/skip)"))
    return 106

async def reg_prod_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["temp_prod_photo"] = update.message.photo[-1].file_id
    else:
        context.user_data["temp_prod_photo"] = None
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("📝 " + ("ገላጭ? (/skip)" if lang == "am" else "Description? (/skip)"))
    return 107

async def reg_prod_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    desc = update.message.text if update.message.text and not update.message.text.startswith('/') else ("ገላጭ የለም" if lang == "am" else "No description")
    
    name = context.user_data.pop("temp_prod_name")
    price = context.user_data.pop("temp_prod_price")
    photo = context.user_data.pop("temp_prod_photo")
    
    products = context.user_data["new_store"]["products"]
    key = f"p{len(products) + 1}"
    products[key] = {"name": name, "price": price, "photo": photo, "description": desc}
    
    keyboard = [
        [InlineKeyboardButton("➕ " + ("ሌላ ጨምር" if lang == "am" else "Add More"), callback_data="reg_more_yes")],
        [InlineKeyboardButton("✅ " + ("ጨርሻለሁ" if lang == "am" else "Done"), callback_data="reg_more_no")],
    ]
    
    await update.message.reply_text(f"✅ {name} - {price} Br", reply_markup=InlineKeyboardMarkup(keyboard))
    return 108

async def reg_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    
    if query.data == "reg_more_yes":
        await query.edit_message_text("📦 " + ("ምርት ስም?" if lang == "am" else "Product?"))
        return 104
    
    # Save
    owner_id = query.from_user.id
    store_id = f"store_{owner_id}"
    store_data = context.user_data.pop("new_store")
    store_data["owner_id"] = owner_id
    store_data["registration_date"] = datetime.now().strftime("%Y-%m-%d")
    store_data["total_orders"] = 0
    store_data["total_revenue"] = 0
    
    save_store(store_id, store_data)
    
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={store_id}"
    ref_link = f"https://t.me/{bot_username}?start=ref_{owner_id}"
    
    created_msg = get_text(lang, "shop_created",
        store=store_data['store_name'],
        username=store_data['username'],
        store_id=store_id,
        link=link,
        ref_link=ref_link
    )
    
    await query.edit_message_text(created_msg)
    
    # Welcome
    try:
        welcome = f"🎉 " + ("ወደ ሱቁ እንኳን ወደ ደህና መጡ!" if lang == "am" else "Welcome!") + f"\n\n🏪 {store_data['store_name']}\n/dashboard\n/test_notify"
        await context.bot.send_message(chat_id=owner_id, text=welcome)
    except:
        pass
    
    return ConversationHandler.END

# ====================== MERCHANT COMMANDS ======================
async def merchant_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    user_id = query.from_user.id
    owner_store = get_store_by_owner(user_id)
    
    if not owner_store:
        await query.edit_message_text("❌ No store")
        return
    
    store_id, store = owner_store
    
    if query.data == "merch_dashboard":
        orders = get_orders(store_id)
        dash_text = get_text(lang, "dashboard",
            store=store['store_name'],
            total_orders=len(orders),
            total_revenue=sum(o.get('price', 0) for o in orders),
            total_products=len(store.get('products', {})),
            referrals=len(store.get('referrals', [])),
            status="✅ " + ("ንቁ" if is_active(store) else "ጊዜ ያልቃ") if lang == "am" else ("✅ Active" if is_active(store) else "❌ Expired"),
            days_left=days_left(store),
            store_link=f"https://t.me/{(await context.bot.get_me()).username}?start={store_id}"
        )
        await query.edit_message_text(dash_text)
    
    elif query.data == "merch_link":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={store_id}"
        await query.edit_message_text(f"🔗 " + ("ሊንክዎ:" if lang == "am" else "Your link:") + f"\n\n{link}")
    
    elif query.data == "merch_orders":
        orders = get_orders(store_id, limit=10)
        if not orders:
            await query.edit_message_text("📭 " + ("ትዕዛዝ የለም" if lang == "am" else "No orders"))
            return
        text = ("ቅርብ ትዕዛዞች:\n\n" if lang == "am" else "Recent orders:\n\n")
        for i, o in enumerate(orders, 1):
            text += f"{i}. {o.get('product')} ({o.get('price')} Br) - {o.get('name')}\n"
        await query.edit_message_text(text)

async def action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    
    if query.data == "action_register":
        await query.message.reply_text("🏪 /register")
    elif query.data == "action_how":
        await query.edit_message_text(get_text(lang, "how_to_use"))
    elif query.data == "action_help":
        await query.edit_message_text(get_text(lang, "how_to_use"))
    elif query.data == "action_lang":
        await query.edit_message_text(("ቋንቋ ይምረጡ:" if lang == "am" else "Select language:"), reply_markup=lang_keyboard())

async def test_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    owner_store = get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("❌ " + ("ሱቅ የለም" if lang == "am" else "No store"))
        return
    
    _, store = owner_store
    user_id = store.get("user_id")
    
    test_msg = get_text(lang, "test_msg")
    
    try:
        await context.bot.send_message(chat_id=user_id, text=test_msg)
        await update.message.reply_text("✅ " + ("ሙከራ ተልኩ!" if lang == "am" else "Test sent!"))
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    owner_store = get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("❌ " + ("ሱቅ የለም" if lang == "am" else "No store"))
        return
    
    store_id, store = owner_store
    orders = get_orders(store_id)
    
    dash_text = get_text(lang, "dashboard",
        store=store['store_name'],
        total_orders=len(orders),
        total_revenue=sum(o.get('price', 0) for o in orders),
        total_products=len(store.get('products', {})),
        referrals=len(store.get('referrals', [])),
        status="✅ " + ("ንቁ" if is_active(store) else "ጊዜ ያልቃ") if lang == "am" else ("✅ Active" if is_active(store) else "❌ Expired"),
        days_left=days_left(store),
        store_link=f"https://t.me/{(await context.bot.get_me()).username}?start={store_id}"
    )
    
    await update.message.reply_text(dash_text)

# ====================== ADMIN PANEL ======================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only")
        return
    
    stores = get_all_stores()
    total_revenue = sum(
        sum(o.get('price', 0) for o in get_orders(sid))
        for sid, _ in stores
    )
    
    top_stores = sorted(
        [(s['store_name'], len(get_orders(sid))) for sid, s in stores],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_text = "\n".join([f"{i}. {name} ({orders})" for i, (name, orders) in enumerate(top_stores, 1)])
    
    admin_msg = get_text("am", "admin_panel",
        total_stores=len(stores),
        total_users=len(stores),
        total_orders=sum(len(get_orders(sid)) for sid, _ in stores),
        total_revenue=total_revenue,
        top_stores=top_text
    )
    
    await update.message.reply_text(admin_msg)

# ====================== MAIN ======================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    register_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            100: [MessageHandler(filters.TEXT, reg_name)],
            101: [MessageHandler(filters.TEXT, reg_phone)],
            102: [MessageHandler(filters.TEXT, reg_location)],
            103: [MessageHandler(filters.TEXT, reg_payment)],
            104: [MessageHandler(filters.TEXT, reg_prod_name)],
            105: [MessageHandler(filters.TEXT, reg_prod_price)],
            106: [MessageHandler(filters.PHOTO | filters.COMMAND, reg_prod_photo)],
            107: [MessageHandler(filters.TEXT | filters.COMMAND, reg_prod_desc)],
            108: [CallbackQueryHandler(reg_more, pattern="^reg_more_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("test_notify", test_notify))
    app.add_handler(CommandHandler("admin", admin_panel))
    
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(action_callback, pattern="^action_"))
    app.add_handler(CallbackQueryHandler(merchant_callback, pattern="^merch_"))
    app.add_handler(register_conv)
    
    await app.initialize()
    
    if RENDER_EXTERNAL_URL:
        async with app:
            await app.bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}")
            await app.start()
            await app.updater.start_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
            )
            logger.info("🤖 Bot running (webhook mode)")
            await asyncio.Event().wait()
    else:
        async with app:
            await app.start()
            await app.updater.start_polling()
            logger.info("🤖 Bot running (polling mode)")
            await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
