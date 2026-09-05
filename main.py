"""
🎊 TELEGRAM SHOP BOT — FIXED VERSION
========================================================
ማስተካከያዎች (Fixes in this version):
1. ✅ የነጋዴ ሱቅ ሊንክ ተስተካክሏል - ደንበኛ ሊንኩን ሲነካ የነጋዴውን ምርቶች ያሳየዋል
   (Fixed store deep-link — clicking a merchant's link now shows THAT
   merchant's products instead of pushing the visitor into /register)
2. ✅ ፎቶ (screenshot) መቀበል ተጨምሯል - ትዕዛዝ ከተረጋገጠ በኋላ የክፍያ screenshot ይጠየቃል
   (Photo/screenshot handling added — after confirming an order, the
   customer is asked to send a payment screenshot, which is forwarded
   to the merchant)
3. ✅ /received ትዕዛዝ ተጨምሯል - ደንበኛው እቃው እንደደረሰው ሲያረጋግጥ ነጋዴውን ያሳውቃል
   (New /received command — customer confirms delivery, merchant is
   notified, customer is invited to rate)
4. ✅ /dispute እና /rate ሙሉ በሙሉ ተተግብረዋል (proof photo ጨምሮ)
   (Full /dispute and /rate conversations implemented, including
   photo proof for disputes)
5. ✅ Admin/Owner ትእዛዝ ተጨምሯል - ሁሉንም ነጋዴዎችና ትዕዛዞች ለማየት
   (New admin commands so the bot owner can see all merchants,
   products, and orders)
"""

import logging
import os
import asyncio
import json
from datetime import datetime
from uuid import uuid4

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

STORAGE_DIR = "bot_data"
os.makedirs(STORAGE_DIR, exist_ok=True)

logger.info("✅ Bot initialized - All systems ready")

# ====================== CONVERSATION STATES ======================
# REGISTRATION
REG_STORE_NAME, REG_PHONE, REG_LOCATION, REG_PAYMENT, REG_PRODUCT, REG_PRICE = range(6)

# ORDER FLOW
ORDER_GET_NAME = 11
ORDER_GET_PHONE = 12
ORDER_GET_ADDRESS = 13
ORDER_CONFIRM = 14
ORDER_PAYMENT_PROOF = 15

# DISPUTE FLOW
DISPUTE_SELECT_ORDER = 19
DISPUTE_REASON = 20
DISPUTE_PROOF = 21

# RATING FLOW
RATING_SELECT_ORDER = 29
RATING_SCORE = 30

# ====================== TEXTS - AMHARIC FIRST ======================
TEXTS = {
    "am": {
        "start": "👋 ሰላም! ቴሌግራም ሱቅ ቦት ውስጥ እንኳን ወደ ደህና መጡ!\n\n🏪 ሱቅ ለመክፈት: /register\n📚 እርዳታ: /help",
        "help": """📚 ቦት እንዴት ይጠቀም

👨‍🏪 ለነጋዴዎች:
/register - ሱቅ ክፈት
/addproduct - ምርት ጨምር
/dashboard - ስታቲስቲክስ
/myorders - ትዕዛዞች
/mystore - የሱቅ ሊንክ

👥 ለደንበኞች:
🔗 የነጋዴ ሊንክ ጠቅ በማድረግ ይግዙ
/received - እቃው እንደደረሰዎት ያረጋግጡ
/rate - ትዕዛዝ ደረጃ ይስጡ

📞 ችግር ካለ?
/dispute - ተከሳሽ (ቅሬታ) ያቅርቡ""",
        "no_store_found": "❌ ሱቅ አልተገኘም። ሊንኩን እንደገና ይሞክሩ።",
        "no_products": "❌ ይህ ሱቅ ገና ምርት የለውም።",
        "already_merchant": "❌ አስቀድመው ሱቅ ከፍተዋል!",
        "register_name": "🏪 ሱቅ ስም?",
        "register_phone": "📞 ስልክ ቁጥር?",
        "register_location": "📍 ቦታ?",
        "register_payment": "💳 ክፍያ ዝርዝር? (ንግድ ባንክ/ቴሌብር/ወዘተ)",
        "register_product": "📦 የመጀመሪያ ምርት ስም?",
        "register_price": "💵 የ{product} ዋጋ (በብር)?",
        "register_success": "🎉 ሱቅ ተከፍቷል!\n\n🔗 ይህን ሊንክ ለደንበኞችዎ ያጋሩ:\n{link}\n\n/addproduct - ተጨማሪ ምርት ለመጨመር\n/mystore - ሊንኩን መልሶ ለማየት",
        "invalid_price": "❌ እባክዎ ቁጥር ብቻ ያስገቡ (ለምሳሌ 250)",
        "addproduct_name": "📦 አዲስ ምርት ስም?",
        "addproduct_price": "💵 ዋጋ (በብር)?",
        "addproduct_success": "✅ ምርት ተጨምሯል: {product} - {price} ብር",

        "order_select": "🛒 ከ{store} ምርት ይምረጡ:",
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


# ====================== STORAGE ======================
def save_json(filename, data):
    path = os.path.join(STORAGE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filename):
    path = os.path.join(STORAGE_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_merchant_store(user_id):
    return load_json(f"merchant_{user_id}.json")


def save_merchant_store(user_id, store_data):
    save_json(f"merchant_{user_id}.json", store_data)


def get_store(store_id):
    if not store_id:
        return None
    for file in os.listdir(STORAGE_DIR):
        if file.startswith("merchant_") and file.endswith(".json"):
            store = load_json(file)
            if store and store.get("store_id") == store_id:
                return store
    return None


def get_all_merchants():
    merchants = []
    for file in os.listdir(STORAGE_DIR):
        if file.startswith("merchant_") and file.endswith(".json"):
            store = load_json(file)
            if store:
                merchants.append(store)
    return merchants


def get_all_orders():
    orders = []
    for file in os.listdir(STORAGE_DIR):
        if file.startswith("order_") and file.endswith(".json"):
            order = load_json(file)
            if order:
                orders.append(order)
    return orders


def get_orders_for_store(store_id):
    return [o for o in get_all_orders() if o.get("store", {}).get("store_id") == store_id]


def get_orders_for_customer(user_id):
    return [o for o in get_all_orders() if o.get("customer_id") == user_id]


def save_order(order):
    save_json(f"{order['order_id']}.json", order)


def get_order(order_id):
    return load_json(f"{order_id}.json")


def save_rating(store_id, score):
    ratings = load_json(f"ratings_{store_id}.json") or {"scores": []}
    ratings["scores"].append(score)
    save_json(f"ratings_{store_id}.json", ratings)
    return ratings


def get_rating_stats(store_id):
    ratings = load_json(f"ratings_{store_id}.json") or {"scores": []}
    scores = ratings.get("scores", [])
    if not scores:
        return 0.0, 0
    return round(sum(scores) / len(scores), 1), len(scores)


# ====================== KEYBOARDS ======================
def products_keyboard(products):
    buttons = []
    for i, prod in enumerate(products):
        buttons.append([InlineKeyboardButton(
            f"{prod['name']} - {prod['price']} ብር",
            callback_data=f"prod_{i}"
        )])
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="order_confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="order_cancel")],
    ])


def orders_keyboard(orders, prefix):
    buttons = []
    for o in orders[:10]:
        label = f"{o['order_id'][-8:]} - {o.get('product', {}).get('name', '')}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"{prefix}_{o['order_id']}")])
    return InlineKeyboardMarkup(buttons)


# ====================== START / DEEP LINK (FIX #1) ======================
async def show_store_products(update: Update, context: ContextTypes.DEFAULT_TYPE, store):
    """Show a specific merchant's products to a visiting customer."""
    lang = context.user_data.get("lang", "am")
    products = store.get("products", [])
    if not products:
        await update.message.reply_text(t(lang, "no_products"))
        return
    context.user_data["current_store"] = store
    await update.message.reply_text(
        t(lang, "order_select", store=store.get("store_name", "")),
        reply_markup=products_keyboard(products)
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """START command — now correctly handles store deep-links."""
    user = update.effective_user
    lang = context.user_data.setdefault("lang", "am")

    # If a merchant, greet as merchant regardless of args
    merchant_store = get_merchant_store(user.id)

    # FIX: check the deep-link payload (/start <store_id>)
    if context.args:
        store_id = context.args[0]
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

    if merchant_store:
        await update.message.reply_text(
            f"👨‍🏪 እንኳን ደህና መጡ {user.first_name}!\n\n"
            f"🏪 ሱቅ: {merchant_store['store_name']}\n\n"
            f"/dashboard - ስታቲስቲክስ\n"
            f"/myorders - ትዕዛዞች\n"
            f"/mystore - ሊንክ ያጋሩ"
        )
        return

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
    reg_data["products"].append({"name": product_name, "price": price})

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

    user = update.effective_user
    merchant = get_merchant_store(user.id)
    product_name = context.user_data.pop("_new_product_name")
    merchant["products"].append({"name": product_name, "price": price})
    save_merchant_store(user.id, merchant)

    await update.message.reply_text(t(lang, "addproduct_success", product=product_name, price=price))
    return ConversationHandler.END


# ====================== CUSTOMER ORDER FLOW ======================
async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")

    store = context.user_data.get("current_store")
    if not store:
        await query.edit_message_text(t(lang, "error"))
        return ConversationHandler.END

    try:
        prod_idx = int(query.data.replace("prod_", ""))
        product = store["products"][prod_idx]
    except (ValueError, IndexError):
        await query.edit_message_text(t(lang, "error"))
        return ConversationHandler.END

    context.user_data["order_data"] = {
        "store": store,
        "product": product,
    }

    text = f"📦 {product['name']}\n💵 {product['price']} ብር\n\n{t(lang, 'order_name')}"
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
    order["status"] = "awaiting_payment_proof"
    save_order(order)

    store = order["store"]
    text = t(lang, "order_confirmed", payment=store.get("payment_method", "N/A"))
    text += "\n\n" + t(lang, "order_id", order_id=order["order_id"])

    await query.edit_message_text(text)
    return ORDER_PAYMENT_PROOF


# FIX #2/#3: accept the payment screenshot and forward it to the merchant
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

    # notify merchant with order details
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


# FIX #4: /received — customer confirms delivery
async def cmd_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")

    orders = [o for o in get_orders_for_customer(user.id)
              if o.get("status") in ("paid_pending_confirmation", "shipped")]

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


# ====================== DISPUTE FLOW (FIX #4/#2 photo) ======================
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

    await update.message.reply_text(
        t(lang, "select_order"),
        reply_markup=orders_keyboard(orders, "disp")
    )
    return DISPUTE_SELECT_ORDER


async def dispute_select_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    order_id = query.data.replace("disp_", "")
    order = get_order(order_id)
    if not order:
        await query.edit_message_text(t(lang, "error"))
        return ConversationHandler.END
    context.user_data["dispute_order"] = order
    await query.edit_message_text(t(lang, "dispute_reason"))
    return DISPUTE_REASON


async def dispute_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dispute_reason_text"] = update.message.text
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text(t(lang, "dispute_proof"))
    return DISPUTE_PROOF


async def dispute_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    user = update.effective_user
    order = context.user_data.get("dispute_order")
    reason = context.user_data.get("dispute_reason_text", "")

    proof_file_id = None
    if update.message.photo:
        proof_file_id = update.message.photo[-1].file_id

    dispute = {
        "dispute_id": f"disp_{uuid4().hex[:8]}",
        "order_id": order["order_id"],
        "customer_id": user.id,
        "name": order.get("name"),
        "phone": order.get("phone"),
        "store": order.get("store", {}).get("store_name"),
        "store_user_id": order.get("store", {}).get("user_id"),
        "reason": reason,
        "proof_file_id": proof_file_id,
        "timestamp": datetime.now().isoformat(),
    }
    save_json(f"{dispute['dispute_id']}.json", dispute)

    if ADMIN_ID:
        try:
            admin_text = t(lang, "admin_dispute_notify",
                            dispute_id=dispute["dispute_id"],
                            order_id=dispute["order_id"],
                            name=dispute["name"],
                            phone=dispute["phone"],
                            store=dispute["store"],
                            reason=dispute["reason"])
            await context.bot.send_message(ADMIN_ID, admin_text)
            if proof_file_id:
                await context.bot.send_photo(ADMIN_ID, photo=proof_file_id)
        except Exception as e:
            logger.error(f"❌ Admin notify error: {e}")

    await update.message.reply_text(t(lang, "dispute_filed", dispute_id=dispute["dispute_id"]))

    context.user_data.pop("dispute_order", None)
    context.user_data.pop("dispute_reason_text", None)
    return ConversationHandler.END


# ====================== RATING FLOW ======================
async def rate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")
    orders = get_orders_for_customer(user.id)

    if not orders:
        await update.message.reply_text(t(lang, "no_orders_for_user"))
        return ConversationHandler.END

    if len(orders) == 1:
        context.user_data["rating_order"] = orders[0]
        await update.message.reply_text(t(lang, "rating_prompt"))
        return RATING_SCORE

    await update.message.reply_text(
        t(lang, "select_order"),
        reply_markup=orders_keyboard(orders, "rate")
    )
    return RATING_SELECT_ORDER


async def rate_select_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "am")
    order_id = query.data.replace("rate_", "")
    order = get_order(order_id)
    if not order:
        await query.edit_message_text(t(lang, "error"))
        return ConversationHandler.END
    context.user_data["rating_order"] = order
    await query.edit_message_text(t(lang, "rating_prompt"))
    return RATING_SCORE


async def rate_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    try:
        score = int(update.message.text.strip())
        if score < 1 or score > 5:
            raise ValueError
    except ValueError:
        await update.message.reply_text(t(lang, "invalid_rating"))
        return RATING_SCORE

    order = context.user_data.pop("rating_order")
    store_id = order.get("store", {}).get("store_id")
    save_rating(store_id, score)
    avg, count = get_rating_stats(store_id)

    await update.message.reply_text(t(lang, "rating_saved", avg=avg, count=count))
    return ConversationHandler.END


# ====================== MERCHANT COMMANDS ======================
async def cmd_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")

    merchant = get_merchant_store(user.id)
    if not merchant:
        await update.message.reply_text(t(lang, "no_store"))
        return

    orders = get_orders_for_store(merchant["store_id"])
    revenue = sum(o.get("product", {}).get("price", 0) for o in orders
                  if o.get("status") in ("paid_pending_confirmation", "delivered"))
    avg, count = get_rating_stats(merchant["store_id"])

    text = t(lang, "dashboard",
             store=merchant["store_name"],
             orders=len(orders),
             revenue=revenue,
             products=len(merchant.get("products", [])),
             rating=avg,
             rating_count=count)

    await update.message.reply_text(text)


async def cmd_mystore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")

    merchant = get_merchant_store(user.id)
    if not merchant:
        await update.message.reply_text(t(lang, "no_store"))
        return

    bot = await context.bot.get_me()
    link = f"https://t.me/{bot.username}?start={merchant['store_id']}"
    await update.message.reply_text(f"🔗 {link}")


async def cmd_myorders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "am")

    merchant = get_merchant_store(user.id)
    if not merchant:
        await update.message.reply_text(t(lang, "no_store"))
        return

    orders = get_orders_for_store(merchant["store_id"])
    if not orders:
        await update.message.reply_text(t(lang, "no_orders"))
        return

    text = "📦 የቅርብ ጊዜ ትዕዛዞች:\n\n"
    for i, order in enumerate(orders[-10:], 1):
        text += (f"{i}. {order['product']['name']} ({order['product']['price']} ብር) "
                 f"[{order.get('status', '')}]\n"
                 f"   👤 {order['name']} 📞 {order['phone']}\n\n")

    await update.message.reply_text(text)


# ====================== ADMIN (FIX #5) ======================
def _is_admin(user_id):
    return ADMIN_ID and user_id == ADMIN_ID


async def cmd_admin_merchants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        return

    merchants = get_all_merchants()
    if not merchants:
        await update.message.reply_text("📭 ነጋዴ የለም")
        return

    text = f"🏪 ጠቅላላ ነጋዴዎች: {len(merchants)}\n\n"
    for m in merchants:
        orders = get_orders_for_store(m["store_id"])
        avg, count = get_rating_stats(m["store_id"])
        text += (
            f"🏪 {m['store_name']}\n"
            f"   👤 @{m.get('username','')} (id: {m['user_id']})\n"
            f"   📞 {m.get('phone','')}\n"
            f"   📍 {m.get('location','')}\n"
            f"   💳 {m.get('payment_method','')}\n"
            f"   📦 ምርቶች: {len(m.get('products', []))}\n"
            f"   🛍️ ትዕዛዞች: {len(orders)}\n"
            f"   ⭐ {avg} ({count})\n\n"
        )
        if len(text) > 3500:
            await update.message.reply_text(text)
            text = ""
    if text:
        await update.message.reply_text(text)


async def cmd_admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        return

    orders = get_all_orders()
    if not orders:
        await update.message.reply_text("📭 ትዕዛዝ የለም")
        return

    text = f"🛍️ ጠቅላላ ትዕዛዞች: {len(orders)}\n\n"
    for o in orders[-20:]:
        text += (
            f"🆔 {o['order_id']}  [{o.get('status','')}]\n"
            f"   🏪 {o.get('store', {}).get('store_name','')}\n"
            f"   👤 ደንበኛ: {o.get('name','')} 📞 {o.get('phone','')} (id: {o.get('customer_id','')})\n"
            f"   📦 {o.get('product', {}).get('name','')} - {o.get('product', {}).get('price','')} ብር\n\n"
        )
        if len(text) > 3500:
            await update.message.reply_text(text)
            text = ""
    if text:
        await update.message.reply_text(text)


async def cmd_admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        return
    await update.message.reply_text(
        "👨‍⚖️ Admin Commands:\n\n"
        "/admin_merchants - ሁሉንም ነጋዴዎች አሳይ\n"
        "/admin_orders - ሁሉንም ትዕዛዞች አሳይ"
    )


# ====================== CANCEL FALLBACK ======================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "am")
    await update.message.reply_text(t(lang, "cancelled"))
    return ConversationHandler.END


# ====================== MAIN ======================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    register_conv = ConversationHandler(
        entry_points=[CommandHandler("register", reg_start)],
        states={
            REG_STORE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_location)],
            REG_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_payment)],
            REG_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_product)],
            REG_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    addproduct_conv = ConversationHandler(
        entry_points=[CommandHandler("addproduct", addproduct_start)],
        states={
            REG_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_name)],
            REG_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_product, pattern="^prod_")],
        states={
            ORDER_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_get_name)],
            ORDER_GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_get_phone)],
            ORDER_GET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_get_address)],
            ORDER_CONFIRM: [CallbackQueryHandler(order_confirm_callback, pattern="^order_")],
            ORDER_PAYMENT_PROOF: [
                MessageHandler(filters.PHOTO, order_payment_proof),
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_payment_proof),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    dispute_conv = ConversationHandler(
        entry_points=[CommandHandler("dispute", dispute_start)],
        states={
            DISPUTE_SELECT_ORDER: [CallbackQueryHandler(dispute_select_order, pattern="^disp_")],
            DISPUTE_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, dispute_reason)],
            DISPUTE_PROOF: [
                MessageHandler(filters.PHOTO, dispute_proof),
                MessageHandler(filters.TEXT & ~filters.COMMAND, dispute_proof),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    rate_conv = ConversationHandler(
        entry_points=[CommandHandler("rate", rate_start)],
        states={
            RATING_SELECT_ORDER: [CallbackQueryHandler(rate_select_order, pattern="^rate_")],
            RATING_SCORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, rate_score)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    # Core commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))
    app.add_handler(CommandHandler("mystore", cmd_mystore))
    app.add_handler(CommandHandler("myorders", cmd_myorders))
    app.add_handler(CommandHandler("received", cmd_received))

    # Admin
    app.add_handler(CommandHandler("admin_merchants", cmd_admin_merchants))
    app.add_handler(CommandHandler("admin_orders", cmd_admin_orders))
    app.add_handler(CommandHandler("admin_help", cmd_admin_help))

    # Conversations
    app.add_handler(register_conv)
    app.add_handler(addproduct_conv)
    app.add_handler(order_conv)
    app.add_handler(dispute_conv)
    app.add_handler(rate_conv)

    # Standalone callback for /received selection list
    app.add_handler(CallbackQueryHandler(received_callback, pattern="^received_"))

    await app.initialize()

    if RENDER_EXTERNAL_URL:
        logger.info("🌐 Starting webhook mode")
        async with app:
            await app.bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}")
            await app.start()
            await app.updater.start_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
            )
            logger.info("✅ Bot running (webhook mode)")
            await asyncio.Event().wait()
    else:
        logger.info("📱 Starting polling mode")
        async with app:
            await app.start()
            await app.updater.start_polling()
            logger.info("✅ Bot running (polling mode)")
            await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        raise
