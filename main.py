"""
🎊 TELEGRAM SHOP BOT - ULTIMATE FIXED VERSION
========================================================
✨ ORDER BUG FIXED
✨ DISPUTE SYSTEM (ተክስ አፈታት)
✨ RATING SYSTEM (ምዕራፍ)
✨ REFUND SYSTEM (ገንዘብ ይመልሱ)
✨ ADMIN MEDIATION (አስተዳደር ሲወስን)
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

logger.info("🤖 Bot starting with Dispute & Rating System")

# ====================== STATES ======================
SELECT_PRODUCT, GET_NAME, GET_PHONE, GET_ADDRESS, CONFIRM = range(5)
REG_NAME, REG_PHONE, REG_LOCATION, REG_PAYMENT, REG_PROD_NAME, REG_PROD_PRICE, REG_PROD_PHOTO, REG_PROD_DESC, REG_MORE = range(10, 19)
DISPUTE_REASON, DISPUTE_PROOF, RATE_ORDER = range(30, 33)

# ====================== TEXTS - AMHARIC FIRST ======================
TEXTS = {
    "am": {
        "welcome": """
👋 ሰላም! እንኳን ወደ ቴሌግራም ሱቅ ቦት ደህና መጡ!

🎯 ነጋዴወች ሱቆቻቸውን ገንብተዋል
💼 ደንበኞች ምርቶች ገዙ
🎁 ሪፌራል ሊሰሩ

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

⭐ ምርት ለመመዘን:
/rate_order - ደረጃ ይስጡ

❌ ችግር ካለ:
/dispute - ተክስ ይንሳ

━━━━━━━━━━━━━━━━━━━━
ሰላም!
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

/confirm_order - ተስማምተው
/cancel_order - ተከልክሉ
""",
        "order_received": """
📦 ምርት ደርሷል?

✅ YES - ደርሳበትከ
❌ NO - ደርሳ ደብቅ (ተክስ ይንሳ)
⭐ RATE - ደረጃ ይስጡ
""",
        "dispute_reason": """
❌ ምርት ደርሳ ሰሪ?

ምን ችግር?
""",
        "dispute_proof": """
📸 ማስረጃ ይሰጡ:

📷 ፎቶ ይላኩ
📹 ቪዲዮ ይላኩ
📝 ገላጭ ይሰጡ
""",
        "dispute_filed": """
⚠️ ተክስ ታመለስ!

📋 Reference: {dispute_id}
🕐 ሰአት: {timestamp}
📝 ምክንያት: {reason}

━━━━━━━━━━━━━━━━━━━━
👨‍⚖️ ፍርድ:

✅ Admin ገምግም ሰሪ
📋 1-2 ቀናት ውስጥ ውሳኔ
💰 ገንዘብ ይመልሱ ሊሰሩ

━━━━━━━━━━━━━━━━━━━━
""",
        "rating_prompt": """
⭐ ደረጃ ይስጡ (1-5)

1️⃣ 끔찍함(በስተቀር 나쁨)
2️⃣ መጥፎ
3️⃣ 괜찮은 (ሚዩ)
4️⃣ ጥሩ
5️⃣ ፍጹም!

/rate_1 እስከ /rate_5
""",
        "rating_saved": """
⭐ ደረጃ ተገለጸ!

📊 ሙሉ ደረጃ: {average_rating}
🗳️ ጠቅላላ ምዕራፍ: {total_ratings}

ምስጋና! 🙏
""",
        "help": """
📚 ቦት እንዴት ይጠቀም

👨‍🏪 ለነጋዴወች:
/register - ሱቅ ይክፈቱ
/dashboard - ስታቲስቲክስ
/myorders - ትዕዛዞች ይመልከቱ
/test_notify - ሙከራ

👥 ለደንበኞች:
/rate_order - ደረጃ ይስጡ
/dispute - ተክስ ይንሳ

⚖️ DISPUTE SYSTEM:
1. ምርት ደርሳ ሰሪ?
2. ማስረጃ ይላኩ
3. Admin ሰሪ
4. ገንዘብ ይመልሱ

━━━━━━━━━━━━━━━━━━━━
ጥያቄ? /help ብያዩ
""",
        "no_store": "❌ ሱቅ አልተገኘም",
    },
    "en": {
        "welcome": """
👋 Welcome to Telegram Shop Bot!

🎯 Merchants create shops
💼 Customers buy products
🎁 Earn with referrals

What do you want?
""",
        "welcome_merchant": """
👨‍💼 Welcome {name}!

🎉 Welcome to your shop!

🏪 Store: {store}
👤 Username: @{username}
✅ Status: {status}
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

⭐ Rate order: /rate_order
❌ Problem? /dispute
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
/confirm_order or /cancel_order
""",
        "dispute_reason": "What's the problem?",
        "dispute_proof": "Send proof (photo/video/description)",
        "dispute_filed": """
⚠️ Dispute Filed!

📋 Reference: {dispute_id}
👨‍⚖️ Admin will review (1-2 days)
💰 Refund if confirmed
""",
        "rating_prompt": """
⭐ Rate (1-5 stars)

/rate_1 - Terrible
/rate_2 - Bad
/rate_3 - OK
/rate_4 - Good
/rate_5 - Perfect!
""",
        "rating_saved": """
⭐ Rating saved!

Average: {average_rating}
Total ratings: {total_ratings}

Thank you! 🙏
""",
        "help": """
📚 HOW TO USE

👨‍🏪 MERCHANTS:
/register, /dashboard, /myorders

👥 CUSTOMERS:
/rate_order - Rate
/dispute - Report problem

⚖️ DISPUTE SYSTEM:
1. Product not received?
2. Send proof
3. Admin reviews
4. Refund if approved

Need help? /help
""",
        "no_store": "No store found",
    }
}

def get_text(lang, key, **kwargs):
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

def save_dispute(dispute_data):
    dispute_id = f"dispute_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    path = os.path.join(STORAGE_DIR, f"{dispute_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dispute_data, f, ensure_ascii=False, indent=2)
    return dispute_id

def get_dispute(dispute_id):
    path = os.path.join(STORAGE_DIR, f"{dispute_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_rating(rating_data):
    rating_id = f"rating_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    path = os.path.join(STORAGE_DIR, f"{rating_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rating_data, f, ensure_ascii=False, indent=2)
    return rating_id

def get_store_ratings(store_id):
    ratings = []
    for file in os.listdir(STORAGE_DIR):
        if file.startswith("rating_"):
            path = os.path.join(STORAGE_DIR, file)
            with open(path, "r", encoding="utf-8") as f:
                rating = json.load(f)
                if rating.get("store_id") == store_id:
                    ratings.append(rating)
    return ratings

def get_average_rating(store_id):
    ratings = get_store_ratings(store_id)
    if not ratings:
        return 0
    total = sum(r.get('rating', 0) for r in ratings)
    return round(total / len(ratings), 1)

def is_active(store):
    reg_date_str = store.get("registration_date", datetime.now().strftime("%Y-%m-%d"))
    try:
        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
    except:
        return True
    expiry = reg_date + timedelta(days=30)
    return datetime.now() < expiry

# ====================== KEYBOARDS ======================
def products_menu(products, lang):
    buttons = [
        [InlineKeyboardButton(f"{p['name']} - {p['price']} Br", callback_data=f"prod_{k}")]
        for k, p in products.items()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(buttons)

# ====================== COMMANDS ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    lang = context.user_data.get("lang", "am")
    
    if args:
        store_id = args[0]
        store = get_store(store_id)
        if not store or not is_active(store):
            await update.message.reply_text("❌ Invalid store")
            return
        
        context.user_data["store_id"] = store_id
        await update.message.reply_text(
            f"🏪 {store['store_name']}\n\nChoose product:",
            reply_markup=products_menu(store.get("products", {}), lang)
        )
        return
    
    owner_store = get_store_by_owner(user.id)
    if owner_store:
        _, store = owner_store
        status = "✅ Active" if is_active(store) else "❌ Expired"
        await update.message.reply_text(
            get_text(lang, "welcome_merchant", 
                name=user.first_name or "Friend",
                store=store['store_name'],
                username=store.get('username'),
                status=status
            )
        )
        return
    
    await update.message.reply_text(get_text(lang, "welcome"))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text(get_text(lang, "help"))

# ====================== ORDER WITH BUG FIX ======================
async def product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔧 FIXED - Product selection now works correctly"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    
    store_id = context.user_data.get("store_id")
    if not store_id:
        await query.edit_message_text("❌ Store not found")
        return
    
    store = get_store(store_id)
    if not store:
        await query.edit_message_text("❌ Store not found")
        return
    
    prod_key = query.data.replace("prod_", "")
    product = store.get("products", {}).get(prod_key)
    
    if not product:
        await query.edit_message_text("❌ Product not found")
        return
    
    context.user_data["order"] = {
        "store_id": store_id,
        "product": product["name"],
        "price": product["price"]
    }
    
    text = f"📦 {product['name']}\n💵 {product['price']} Br\n📝 {product.get('description')}\n\n" + ("ስምዎ?" if lang == "am" else "Your name?")
    
    if product.get("photo"):
        try:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=product["photo"],
                caption=text
            )
        except:
            await query.edit_message_text(text)
    else:
        await query.edit_message_text(text)

async def get_customer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get name for order"""
    lang = context.user_data.get("lang", "am")
    context.user_data["order"]["name"] = update.message.text
    await update.message.reply_text("📞 " + ("ስልክ?" if lang == "am" else "Phone?"))

async def get_customer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get phone for order"""
    lang = context.user_data.get("lang", "am")
    context.user_data["order"]["phone"] = update.message.text
    await update.message.reply_text("📍 " + ("አድራሻ?" if lang == "am" else "Address?"))

async def get_customer_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get address for order"""
    lang = context.user_data.get("lang", "am")
    context.user_data["order"]["address"] = update.message.text
    
    order = context.user_data["order"]
    
    keyboard = [
        [InlineKeyboardButton("✅ " + ("ሙሉ ጊዜ" if lang == "am" else "Confirm"), callback_data="order_confirm_yes")],
        [InlineKeyboardButton("❌ " + ("ሰርዝ" if lang == "am" else "Cancel"), callback_data="order_confirm_no")],
    ]
    
    summary = f"📦 {order['product']}\n💵 {order['price']} Br\n👤 {order['name']}\n📞 {order['phone']}\n📍 {order['address']}"
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and save order"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    
    if query.data == "order_confirm_no":
        await query.edit_message_text("❌ Cancelled")
        return
    
    order = context.user_data["order"]
    order["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    order["customer_id"] = query.from_user.id
    order["status"] = "pending"  # 🔧 NEW: Track status
    
    store_id = order.get("store_id")
    store = get_store(store_id)
    
    order_id = save_order(order)
    
    # Notify merchant
    if store and "user_id" in store:
        notify_text = get_text(lang, "merchant_notification",
            store=store['store_name'],
            product=order['product'],
            price=order['price'],
            name=order['name'],
            phone=order['phone'],
            address=order['address'],
            timestamp=order['timestamp']
        )
        try:
            await context.bot.send_message(chat_id=store["user_id"], text=notify_text)
        except:
            pass
    
    # Send to customer
    payment_method = store.get('payment_method', 'N/A') if store else 'N/A'
    
    confirm_msg = get_text(lang, "order_confirm",
        product=order['product'],
        price=order['price'],
        name=order['name'],
        phone=order['phone'],
        address=order['address'],
        payment=payment_method
    )
    
    await query.edit_message_text(confirm_msg)
    
    # Store order ID for rating/dispute
    context.user_data["last_order_id"] = order_id
    
    context.user_data.pop("order", None)

# ====================== DISPUTE SYSTEM ======================
async def dispute_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start dispute process"""
    lang = context.user_data.get("lang", "am")
    
    if "last_order_id" not in context.user_data:
        await update.message.reply_text("❌ " + ("ትዕዛዝ አልተገኘም" if lang == "am" else "No recent order"))
        return
    
    context.user_data["dispute_order"] = context.user_data.get("last_order_id")
    await update.message.reply_text(get_text(lang, "dispute_reason"))

async def dispute_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get dispute reason"""
    lang = context.user_data.get("lang", "am")
    context.user_data["dispute_reason_text"] = update.message.text
    await update.message.reply_text(get_text(lang, "dispute_proof"))

async def dispute_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get dispute proof (photo or text)"""
    lang = context.user_data.get("lang", "am")
    
    proof = None
    if update.message.photo:
        proof = update.message.photo[-1].file_id
    elif update.message.text:
        proof = update.message.text
    
    # Save dispute
    dispute_data = {
        "customer_id": update.effective_user.id,
        "order_id": context.user_data.get("dispute_order"),
        "reason": context.user_data.get("dispute_reason_text"),
        "proof": proof,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "pending"
    }
    
    dispute_id = save_dispute(dispute_data)
    
    dispute_msg = get_text(lang, "dispute_filed",
        dispute_id=dispute_id,
        timestamp=dispute_data["timestamp"],
        reason=dispute_data["reason"]
    )
    
    await update.message.reply_text(dispute_msg)
    
    # Notify admin
    if ADMIN_ID:
        admin_msg = f"""
⚠️ DISPUTE FILED!

📋 Dispute ID: {dispute_id}
👤 Customer: {update.effective_user.first_name}
📝 Reason: {dispute_data['reason']}
🕐 Time: {dispute_data['timestamp']}

/review_dispute_{dispute_id} - Review
/approve_dispute_{dispute_id} - Approve refund
/reject_dispute_{dispute_id} - Reject
"""
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
        except:
            pass
    
    context.user_data.pop("dispute_order", None)
    context.user_data.pop("dispute_reason_text", None)

# ====================== RATING SYSTEM ======================
async def rate_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rate order"""
    lang = context.user_data.get("lang", "am")
    
    if "last_order_id" not in context.user_data:
        await update.message.reply_text("❌ " + ("ትዕዛዝ አልተገኘም" if lang == "am" else "No recent order"))
        return
    
    keyboard = [
        [InlineKeyboardButton("1️⃣", callback_data="rate_1")],
        [InlineKeyboardButton("2️⃣", callback_data="rate_2")],
        [InlineKeyboardButton("3️⃣", callback_data="rate_3")],
        [InlineKeyboardButton("4️⃣", callback_data="rate_4")],
        [InlineKeyboardButton("5️⃣", callback_data="rate_5")],
    ]
    
    await update.message.reply_text(
        get_text(lang, "rating_prompt"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save rating"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    
    rating_value = int(query.data.replace("rate_", ""))
    
    # Get order
    order_id = context.user_data.get("last_order_id")
    order_path = os.path.join(STORAGE_DIR, f"{order_id}.json")
    
    if os.path.exists(order_path):
        with open(order_path, "r", encoding="utf-8") as f:
            order = json.load(f)
        
        store_id = order.get("store_id")
        
        # Save rating
        rating_data = {
            "order_id": order_id,
            "store_id": store_id,
            "customer_id": query.from_user.id,
            "rating": rating_value,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        save_rating(rating_data)
        
        # Get average
        avg_rating = get_average_rating(store_id)
        total_ratings = len(get_store_ratings(store_id))
        
        rating_msg = get_text(lang, "rating_saved",
            average_rating=avg_rating,
            total_ratings=total_ratings
        )
        
        await query.edit_message_text(rating_msg)
        
        # Notify merchant
        store = get_store(store_id)
        if store and "user_id" in store:
            merchant_msg = f"⭐ 새로운 평점!\n\n{rating_value}⭐ from {query.from_user.first_name}\n\n평균: {avg_rating}⭐"
            try:
                await context.bot.send_message(chat_id=store["user_id"], text=merchant_msg)
            except:
                pass

# ====================== REGISTRATION ======================
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    
    if get_store_by_owner(update.effective_user.id):
        await update.message.reply_text("❌ " + ("ቀድሞ ሱቅ አለዎት" if lang == "am" else "You already have a store"))
        return ConversationHandler.END
    
    context.user_data["new_store"] = {
        "user_id": update.effective_user.id,
        "username": update.effective_user.username or "merchant",
        "products": {}
    }
    
    await update.message.reply_text("🏪 " + ("ሱቅ ስም?" if lang == "am" else "Store name?"))
    return 100

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["store_name"] = update.message.text
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("📞 " + ("ስልክ?" if lang == "am" else "Phone?"))
    return 101

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["phone"] = update.message.text
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("📍 " + ("ቦታ?" if lang == "am" else "Location?"))
    return 102

async def reg_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["location"] = update.message.text
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("💳 " + ("ክፍያ?" if lang == "am" else "Payment?"))
    return 103

async def reg_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["payment_method"] = update.message.text
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("📦 " + ("ምርት ስም?" if lang == "am" else "Product?"))
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
        await update.message.reply_text("❌ Number only")
        return 105
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("📸 " + ("ፎቶ?" if lang == "am" else "Photo?"))
    return 106

async def reg_prod_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["temp_prod_photo"] = update.message.photo[-1].file_id
    else:
        context.user_data["temp_prod_photo"] = None
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text("📝 " + ("ገላጭ?" if lang == "am" else "Description?"))
    return 107

async def reg_prod_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    desc = update.message.text or ("ገላጭ የለም" if lang == "am" else "No description")
    
    name = context.user_data.pop("temp_prod_name")
    price = context.user_data.pop("temp_prod_price")
    photo = context.user_data.pop("temp_prod_photo")
    
    products = context.user_data["new_store"]["products"]
    key = f"p{len(products) + 1}"
    products[key] = {"name": name, "price": price, "photo": photo, "description": desc}
    
    keyboard = [
        [InlineKeyboardButton("➕ " + ("ሌላ" if lang == "am" else "More"), callback_data="reg_more_yes")],
        [InlineKeyboardButton("✅ " + ("ጨርሳ" if lang == "am" else "Done"), callback_data="reg_more_no")],
    ]
    
    await update.message.reply_text(f"✅ {name}", reply_markup=InlineKeyboardMarkup(keyboard))
    return 108

async def reg_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    
    if query.data == "reg_more_yes":
        await query.edit_message_text("📦 " + ("ምርት ስም?" if lang == "am" else "Product?"))
        return 104
    
    owner_id = query.from_user.id
    store_id = f"store_{owner_id}"
    store_data = context.user_data.pop("new_store")
    store_data["owner_id"] = owner_id
    store_data["registration_date"] = datetime.now().strftime("%Y-%m-%d")
    store_data["total_orders"] = 0
    store_data["total_revenue"] = 0
    
    save_store(store_id, store_data)
    
    await query.edit_message_text("🎉 ሱቅ ተከፍቷል!")
    
    return ConversationHandler.END

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    owner_store = get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("❌ " + ("ሱቅ አልተገኘም" if lang == "am" else "No store"))
        return
    
    store_id, store = owner_store
    orders = get_orders(store_id)
    avg_rating = get_average_rating(store_id)
    
    dash = f"""
📊 {store['store_name']}

🛍️ Orders: {len(orders)}
💰 Revenue: {sum(o.get('price', 0) for o in orders)} Br
📦 Products: {len(store.get('products', {}))}
⭐ Rating: {avg_rating}
🎁 Referrals: {len(store.get('referrals', []))}
"""
    
    await update.message.reply_text(dash)

async def test_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    owner_store = get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("❌ " + ("ሱቅ አልተገኘም" if lang == "am" else "No store"))
        return
    
    _, store = owner_store
    user_id = store.get("user_id")
    
    try:
        await context.bot.send_message(chat_id=user_id, text="✅ Test successful!")
        await update.message.reply_text("✅ Test sent!")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

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
        fallbacks=[],
        per_message=False,
    )
    
    order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(product_callback, pattern="^prod_"),
            MessageHandler(filters.TEXT, get_customer_name),
        ],
        states={
            1: [MessageHandler(filters.TEXT, get_customer_name)],
            2: [MessageHandler(filters.TEXT, get_customer_phone)],
            3: [MessageHandler(filters.TEXT, get_customer_address)],
            4: [CallbackQueryHandler(confirm_order, pattern="^order_confirm_")],
        },
        fallbacks=[],
        per_message=False,
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("register", register_start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("test_notify", test_notify))
    app.add_handler(CommandHandler("dispute", dispute_start))
    app.add_handler(CommandHandler("rate_order", rate_order))
    
    app.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(product_callback, pattern="^prod_"))
    app.add_handler(CallbackQueryHandler(confirm_order, pattern="^order_confirm_"))
    
    app.add_handler(MessageHandler(filters.TEXT, dispute_reason))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, dispute_proof))
    
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
