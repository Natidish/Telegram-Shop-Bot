
"""
bot.py
Multi-Tenant Telegram Shop Bot
==============================
ብዙ ነጋዴዎች በ1 ቦት እንዲጠቀሙ የተዘጋጀ።
 
እንዴት ይሰራል፡
1. ነጋዴ /register ብሎ የራሱን ስቶር (ስም፣ ስልክ፣ ቦታ፣ ምርቶች) ይከፍታል
2. ቦቱ ለነጋዴው unique link ይሰጠዋል፡ https://t.me/BotUsername?start=store_XXXX
3. ነጋዴው ይህን link ለደንበኞቹ ያጋራል (Telegram channel/Facebook/WhatsApp)
4. ደንበኛ link ሲጫን ቀጥታ ወደ እርሱ ስቶር menu ይገባል፣ ምርት ይመርጣል፣ ያዛል
5. ትዕዛዙ ለነጋዴው (owner_id) በቀጥታ Telegram notification ይደርሰዋል
 
Deploy (Render Web Service - Free):
- Build Command : pip install -r requirements.txt
- Start Command : python bot.py
- Environment   : BOT_TOKEN = <ከ @BotFather የተገኘው token>
(RENDER_EXTERNAL_URL ራሱ Render በራስ-ሰር ይሞላዋል - እጅ መንካት አያስፈልግም)
 
Local ሙከራ ላይ (RENDER_EXTERNAL_URL ስለሌለ) ቦቱ በራሱ ወደ polling mode ይቀየራል።
"""
 
import logging
import os
from datetime import datetime
 
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
 
import storage
 
# ====================== CONFIG ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
 
# Conversation states — እያንዳንዱ ConversationHandler የራሱ የተለየ ቁጥር አለው
SELECT_PRODUCT, GET_NAME, GET_PHONE, GET_ADDRESS, CONFIRM = range(5)
REG_NAME, REG_PHONE, REG_LOCATION, REG_PRODUCT_NAME, REG_PRODUCT_PRICE, REG_MORE = range(10, 16)
ADDPROD_NAME, ADDPROD_PRICE = range(20, 22)
 
 
# ====================== KEYBOARDS ======================
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 ዋጋ ዝርዝር", callback_data="menu_price")],
        [InlineKeyboardButton("🛒 ትዕዛዝ ማድረግ", callback_data="menu_order")],
        [InlineKeyboardButton("ℹ️ መረጃ", callback_data="menu_info")],
    ]
    return InlineKeyboardMarkup(keyboard)
 
 
def products_keyboard(products: dict):
    keyboard = [
        [InlineKeyboardButton(f"{p['name']} - {p['price']} ብር", callback_data=f"prod_{key}")]
        for key, p in products.items()
    ]
    keyboard.append([InlineKeyboardButton("⬅️ ተመለስ", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)
 
 
# ====================== /start (ለነጋዴ እና ለደንበኛ) ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # ?start=store_xxx ላይ ያለው ክፍል
 
    # CASE 1: ደንበኛ ከነጋዴው unique link በመጫን የመጣ
    if args:
        store_id = args[0]
        store = storage.get_store(store_id)
        if not store:
            await update.message.reply_text("⚠️ ይህ የስቶር ማስፈንጠሪያ (link) ትክክል አይደለም።")
            return
        context.user_data["store_id"] = store_id
        text = f"👋 እንኳን ወደ *{store['store_name']}* በደህና መጡ!\n\nከታች ካሉት አማራጮች ይምረጡ 👇"
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        return
 
    # CASE 2: ቦቱን በቀጥታ የከፈተ ነጋዴ (የራሱ ስቶር ካለው)
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if owner_store:
        _, store = owner_store
        await update.message.reply_text(
            f"👋 እንደገና በደህና መጡ፣ የ*{store['store_name']}* አስተዳዳሪ!\n\n"
            "🏪 /mystore — የስቶርዎ መረጃ + link\n"
            "➕ /addproduct — ምርት ለመጨመር\n"
            "➖ /removeproduct — ምርት ለማስወገድ\n"
            "🧾 /myorders — የቅርብ ጊዜ ትዕዛዞች",
            parse_mode="Markdown",
        )
        return
 
    # CASE 3: ሙሉ ለሙሉ አዲስ ሰው (ነጋዴም ደንበኛም ያልሆነ)
    text = (
        "👋 *ሰላም!*\n\n"
        "ይህ ቦት ለብዙ ነጋዴዎች የተዘጋጀ ራስ-ሰር የሽያጭ ረዳት ነው።\n\n"
        "🛍️ ደንበኛ ከሆኑ የነጋዴው ማስፈንጠሪያ (link) ይጫኑ።\n"
        "🏪 ነጋዴ ከሆኑ /register ብለው የራስዎን ስቶር በደቂቃዎች ይክፈቱ።"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
 
 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ ተቋርጧል። /start ብለው እንደገና ይጀምሩ።")
    return ConversationHandler.END
 
 
# ====================== ነጋዴ REGISTRATION FLOW ======================
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if storage.get_store_by_owner(update.effective_user.id):
        await update.message.reply_text("⚠️ የተመዘገበ ስቶር አለዎት። /mystore ብለው ይመልከቱ።")
        return ConversationHandler.END
 
    context.user_data["new_store"] = {"products": {}}
    await update.message.reply_text(
        "🏪 *ስቶርዎን እንክፍት!*\n\nየስቶርዎን ስም ይፃፉ (ለምሳሌ፡ ሀበሻ ስቶር):", parse_mode="Markdown"
    )
    return REG_NAME
 
 
async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["store_name"] = update.message.text
    await update.message.reply_text("📞 የስልክ ቁጥርዎን ይፃፉ:")
    return REG_PHONE
 
 
async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["phone"] = update.message.text
    await update.message.reply_text("📍 ስቶርዎ የሚገኝበት ቦታ ይፃፉ:")
    return REG_LOCATION
 
 
async def reg_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["location"] = update.message.text
    await update.message.reply_text(
        "📦 *የመጀመሪያ ምርትዎን ይጨምሩ*\n\nየምርቱን ስም ይፃፉ (ለምሳሌ፡ 👟 ጫማ):", parse_mode="Markdown"
    )
    return REG_PRODUCT_NAME
 
 
async def reg_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["temp_product_name"] = update.message.text
    await update.message.reply_text("💵 ዋጋውን በቁጥር ብቻ ይፃፉ (ለምሳሌ፡ 1200):")
    return REG_PRODUCT_PRICE
 
 
async def reg_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ በቁጥር ብቻ ይፃፉ፣ እንደገና ይሞክሩ:")
        return REG_PRODUCT_PRICE
 
    name = context.user_data.pop("temp_product_name")
    products = context.user_data["new_store"]["products"]
    key = f"p{len(products) + 1}"
    products[key] = {"name": name, "price": price}
 
    keyboard = [
        [InlineKeyboardButton("➕ ሌላ ምርት ጨምር", callback_data="reg_more_yes")],
        [InlineKeyboardButton("✅ ጨርሻለሁ", callback_data="reg_more_no")],
    ]
    await update.message.reply_text(
        f"✅ {name} - {price} ብር ተጨምሯል። ሌላ ይጨምራሉ?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return REG_MORE
 
 
async def reg_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
 
    if query.data == "reg_more_yes":
        await query.edit_message_text("የምርቱን ስም ይፃፉ:")
        return REG_PRODUCT_NAME
 
    # ጨርሷል → ስቶር ይፈጠራል
    owner_id = query.from_user.id
    store_id = f"store_{owner_id}"
    store_data = context.user_data.pop("new_store")
    store_data["owner_id"] = owner_id
    storage.save_store(store_id, store_data)
 
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={store_id}"
 
    text = (
        "🎉 *ስቶርዎ በተሳካ ሁኔታ ተከፍቷል!*\n\n"
        f"🏪 ስም: {store_data['store_name']}\n"
        f"📦 ምርቶች: {len(store_data['products'])}\n\n"
        "ይህን ማስፈንጠሪያ (link) ለደንበኞችዎ ያጋሩ፡\n"
        f"`{link}`\n\n"
        "ተጨማሪ ትዕዛዞች፡\n"
        "➕ /addproduct — ምርት ለመጨመር\n"
        "🧾 /myorders — ትዕዛዞችን ለማየት\n"
        "🏪 /mystore — የስቶር መረጃ ለማየት"
    )
    await query.edit_message_text(text, parse_mode="Markdown")
    return ConversationHandler.END
 
 
# ====================== ምርት መጨመር (ለነባር ስቶር) ======================
async def addproduct_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("⚠️ የተመዘገበ ስቶር የለዎትም። /register ብለው ይክፈቱ።")
        return ConversationHandler.END
 
    context.user_data["addprod_store_id"] = owner_store[0]
    await update.message.reply_text("📦 የምርቱን ስም ይፃፉ:")
    return ADDPROD_NAME
 
 
async def addproduct_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["addprod_name"] = update.message.text
    await update.message.reply_text("💵 ዋጋውን በቁጥር ብቻ ይፃፉ:")
    return ADDPROD_PRICE
 
 
async def addproduct_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ በቁጥር ብቻ ይፃፉ:")
        return ADDPROD_PRICE
 
    store_id = context.user_data.pop("addprod_store_id")
    name = context.user_data.pop("addprod_name")
    store = storage.get_store(store_id)
    key = f"p{len(store.get('products', {})) + 1}"
    storage.add_product(store_id, key, name, price)
    await update.message.reply_text(f"✅ {name} - {price} ብር ተጨምሯል!")
    return ConversationHandler.END
 
 
# ====================== ምርት ማስወገድ ======================
async def removeproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("⚠️ የተመዘገበ ስቶር የለዎትም።")
        return
 
    store_id, store = owner_store
    products = store.get("products", {})
    if not products:
        await update.message.reply_text("📭 የሚያስወግዱት ምርት የለም።")
        return
 
    keyboard = [
        [InlineKeyboardButton(f"❌ {p['name']}", callback_data=f"delprod|{store_id}|{key}")]
        for key, p in products.items()
    ]
    await update.message.reply_text("የሚያስወግዱትን ምርት ይምረጡ:", reply_markup=InlineKeyboardMarkup(keyboard))
 
 
async def removeproduct_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
 
    _, store_id, key = query.data.split("|")
    store = storage.get_store(store_id)
 
    # ደህንነት: ራሱ የስቶሩ ባለቤት ብቻ ምርት ማስወገድ እንዲችል
    if not store or store.get("owner_id") != query.from_user.id:
        await query.edit_message_text("⚠️ ይህን ማድረግ አይፈቀድልዎትም።")
        return
 
    storage.remove_product(store_id, key)
    await query.edit_message_text("✅ ምርቱ ተወግዷል።")
 
 
# ====================== የስቶር መረጃ + ትዕዛዞች ======================
async def mystore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("⚠️ የተመዘገበ ስቶር የለዎትም። /register ብለው ይክፈቱ።")
        return
 
    store_id, store = owner_store
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={store_id}"
    products = store.get("products", {})
    products_text = "\n".join(f"  • {p['name']} - {p['price']} ብር" for p in products.values()) or "  (ምርት የለም)"
 
    text = (
        f"🏪 *{store['store_name']}*\n"
        f"📞 {store['phone']}\n"
        f"📍 {store['location']}\n\n"
        f"📦 *ምርቶች ({len(products)})*\n{products_text}\n\n"
        f"🔗 ማስፈንጠሪያ (ለደንበኞች ያጋሩ)፡\n`{link}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
 
 
async def myorders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("⚠️ የተመዘገበ ስቶር የለዎትም። /register ብለው ይክፈቱ።")
        return
 
    store_id, _ = owner_store
    orders = storage.get_orders_for_store(store_id, limit=10)
    if not orders:
        await update.message.reply_text("📭 እስካሁን ምንም ትዕዛዝ የለም።")
        return
 
    lines = ["🧾 *የቅርብ ጊዜ ትዕዛዞች*\n"]
    for o in reversed(orders):
        lines.append(
            f"🛍️ {o['product']} — {o['price']} ብር\n"
            f"👤 {o['name']} | 📞 {o['phone']}\n"
            f"📍 {o['address']}\n🕒 {o['timestamp']}\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
 
 
# ====================== ደንበኛ MENU (ዋጋ/መረጃ) ======================
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
 
    store_id = context.user_data.get("store_id")
    store = storage.get_store(store_id) if store_id else None
    if not store:
        await query.edit_message_text("⚠️ ክፍለ-ጊዜዎ አልቋል። ከነጋዴው ማስፈንጠሪያ (link) /start እንደገና ይጀምሩ።")
        return
 
    if query.data == "menu_price":
        await query.edit_message_text(
            "📋 *የምርት ዝርዝር*\n\nከታች ካሉት ምረጡ 👇",
            reply_markup=products_keyboard(store.get("products", {})),
            parse_mode="Markdown",
        )
    elif query.data == "menu_info":
        text = f"ℹ️ *{store['store_name']}*\n\n📍 {store['location']}\n📞 {store['phone']}"
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    elif query.data == "menu_back":
        await query.edit_message_text("ከታች ካሉት አማራጮች ይምረጡ 👇", reply_markup=main_menu_keyboard())
 
 
# ====================== ደንበኛ ORDER FLOW ======================
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
 
    store_id = context.user_data.get("store_id")
    store = storage.get_store(store_id) if store_id else None
    if not store:
        await query.edit_message_text("⚠️ ክፍለ-ጊዜዎ አልቋል። ከነጋዴው link /start እንደገና ይጀምሩ።")
        return ConversationHandler.END
 
    await query.edit_message_text("🛒 የትኛውን ምርት ይፈልጋሉ?", reply_markup=products_keyboard(store.get("products", {})))
    return SELECT_PRODUCT
 
 
async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
 
    if query.data == "menu_back":
        await query.edit_message_text("ከታች ካሉት አማራጮች ይምረጡ 👇", reply_markup=main_menu_keyboard())
        return ConversationHandler.END
 
    store_id = context.user_data.get("store_id")
    store = storage.get_store(store_id)
    product_key = query.data.replace("prod_", "")
    product = store.get("products", {}).get(product_key) if store else None
 
    if not product:
        await query.edit_message_text("⚠️ ምርቱ አልተገኘም፣ እንደገና ይሞክሩ።")
        return ConversationHandler.END
 
    context.user_data["order"] = {
        "store_id": store_id,
        "product": product["name"],
        "price": product["price"],
    }
    await query.edit_message_text(f"✅ {product['name']} ተመርጧል።\n\nእስኪ ስምዎን ይፃፉ:")
    return GET_NAME
 
 
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["name"] = update.message.text
    await update.message.reply_text("📞 ስልክ ቁጥርዎን ይፃፉ:")
    return GET_PHONE
 
 
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["phone"] = update.message.text
    await update.message.reply_text("📍 አድራሻዎን/የመረክቢያ ቦታ ይፃፉ:")
    return GET_ADDRESS
 
 
async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order = context.user_data["order"]
    order["address"] = update.message.text
 
    summary = (
        "📦 *ትዕዛዝ ማረጋገጫ*\n\n"
        f"🛍️ ምርት: {order['product']}\n"
        f"💵 ዋጋ: {order['price']} ብር\n"
        f"👤 ስም: {order['name']}\n"
        f"📞 ስልክ: {order['phone']}\n"
        f"📍 አድራሻ: {order['address']}\n\n"
        "ትክክል ነው?"
    )
    keyboard = [
        [InlineKeyboardButton("✅ አረጋግጥ", callback_data="confirm_yes")],
        [InlineKeyboardButton("❌ ሰርዝ", callback_data="confirm_no")],
    ]
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CONFIRM
 
 
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
 
    if query.data == "confirm_no":
        await query.edit_message_text("❌ ትዕዛዙ ተሰርዟል። /start ብለው እንደገና መሞከር ይችላሉ።")
        context.user_data.pop("order", None)
        return ConversationHandler.END
 
    order = context.user_data["order"]
    order["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    order["customer_chat_id"] = query.from_user.id
    storage.save_order(order)
 
    await query.edit_message_text("✅ ትዕዛዝዎ ተመዝግቧል! በቅርቡ እንገናኝዎታለን። 🙏")
 
    # ለስቶሩ ባለቤት (ነጋዴ) notification መላክ
    store = storage.get_store(order["store_id"])
    if store:
        owner_text = (
            "🔔 *አዲስ ትዕዛዝ መጣ!*\n\n"
            f"🛍️ ምርት: {order['product']}\n"
            f"💵 ዋጋ: {order['price']} ብር\n"
            f"👤 ስም: {order['name']}\n"
            f"📞 ስልክ: {order['phone']}\n"
            f"📍 አድራሻ: {order['address']}\n"
            f"🕒 ጊዜ: {order['timestamp']}"
        )
        await context.bot.send_message(chat_id=store["owner_id"], text=owner_text, parse_mode="Markdown")
 
    context.user_data.pop("order", None)
    return ConversationHandler.END
 
 
# ====================== MAIN ======================
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("⚠️ BOT_TOKEN environment variable አልተቀመጠም! Render Environment ላይ ይጨምሩ።")
 
    app = Application.builder().token(BOT_TOKEN).build()
 
    register_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_location)],
            REG_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_product_name)],
            REG_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_product_price)],
            REG_MORE: [CallbackQueryHandler(reg_more, pattern="^reg_more_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,  # states ውስጥ MessageHandler እና CallbackQueryHandler ስላሉ ሆን ተብሎ የተደረገ
    )
 
    addproduct_conv = ConversationHandler(
        entry_points=[CommandHandler("addproduct", addproduct_start)],
        states={
            ADDPROD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_name)],
            ADDPROD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproduct_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
 
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_start, pattern="^menu_order$")],
        states={
            SELECT_PRODUCT: [CallbackQueryHandler(select_product, pattern="^(prod_|menu_back)")],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            CONFIRM: [CallbackQueryHandler(confirm_order, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,  # states ውስጥ MessageHandler እና CallbackQueryHandler ስላሉ ሆን ተብሎ የተደረገ
    )
 
    app.add_handler(CommandHandler("start", start))
    app.add_handler(register_conv)
    app.add_handler(addproduct_conv)
    app.add_handler(order_conv)
    app.add_handler(CommandHandler("mystore", mystore))
    app.add_handler(CommandHandler("myorders", myorders))
    app.add_handler(CommandHandler("removeproduct", removeproduct))
    app.add_handler(CallbackQueryHandler(removeproduct_callback, pattern=r"^delprod\|"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_(price|info|back)$"))
 
    port = int(os.environ.get("PORT", 10000))
    render_url = os.environ.get("RENDER_EXTERNAL_URL")  # Render ራሱ በራስ-ሰር የሚሞላው
 
    if render_url:
        # ====== WEBHOOK MODE (Render Web Service ላይ) ======
        logger.info("🌐 Webhook mode ላይ በ Render እየጀመረ ነው → %s", render_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"{render_url}/{BOT_TOKEN}",
        )
    else:
        # ====== POLLING MODE (Local ሙከራ) ======
        logger.info("💻 Polling mode ላይ Local እየጀመረ ነው...")
        app.run_polling()
 
 
if __name__ == "__main__":
    main()
