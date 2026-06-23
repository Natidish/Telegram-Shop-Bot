"""
bot.py
Multi-Tenant Telegram Shop Bot with Merchant Custom Accounts & Telegram Stars
=============================================================================
"""

import logging
import os
import asyncio
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
    PreCheckoutQueryHandler,
)

import storage

# ====================== CONFIG ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Conversation states
SELECT_PRODUCT, GET_NAME, GET_PHONE, GET_ADDRESS, CONFIRM = range(5)
REG_NAME, REG_PHONE, REG_LOCATION, REG_PAYMENT_METHOD, REG_PRODUCT_NAME, REG_PRODUCT_PRICE, REG_MORE = range(10, 17)
ADDPROD_NAME, ADDPROD_PRICE = range(20, 22)

# ====================== 🕒 SUBSCRIPTION CHECK ======================
def is_subscription_active(store: dict) -> bool:
    """የነጋዴው የ 500 ብር ወርሃዊ ክፍያ አለማለቁን ያረጋግጣል"""
    reg_date_str = store.get("registration_date", datetime.now().strftime("%Y-%m-%d"))
    try:
        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
    except ValueError:
        reg_date = datetime.now()
        
    expiry_date = reg_date + timedelta(days=30)
    return datetime.now() < expiry_date

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
        [InlineKeyboardButton(f"{p['name']} - {p['price']} ብр", callback_data=f"prod_{key}")]
        for key, p in products.items()
    ]
    keyboard.append([InlineKeyboardButton("⬅️ ተመለስ", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)

# ====================== /start ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    # CASE 1: ደንበኛ ሲመጣ
    if args:
        store_id = args[0]
        store = storage.get_store(store_id)
        if not store:
            await update.message.reply_text("⚠️ ይህ የስቶር ማስፈንጠሪያ (link) ትክክል አይደለም።")
            return
            
        # የ 500 ብር ክፍያ ካለቀ ሱቁን መዝጋት
        if not is_subscription_active(store):
            await update.message.reply_text("⚠️ ይቅርታ፣ ይህ ሱቅ ለጊዜው አገልግሎት አያቀረብም። (Subscription Expired)")
            return

        context.user_data["store_id"] = store_id
        text = f"👋 እንኳን ወደ *{store['store_name']}* በደህና መጡ!\n\nከታች ካሉት አማራጮች ይምረጡ 👇"
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        return

    # CASE 2: ነጋዴ ሲመጣ
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if owner_store:
        store_id, store = owner_store
        status_text = "🟢 ንቁ (Active)" if is_subscription_active(store) else "🔴 የተዘጋ (Expired - እባክዎን 500 ብር ይክፈሉ)"
        
        await update.message.reply_text(
            f"👋 እንደገና በደህና መጡ፣ የ*{store['store_name']}* አስተዳዳሪ!\n"
            f"📌 የቦት ሁኔታ: {status_text}\n"
            f"💳 የክፍያ አካውንትዎ: {store.get('payment_method', 'አልተመዘገበም')}\n\n"
            "🏪 /mystore — የስቶርዎ መረጃ + link\n"
            "➕ /addproduct — ምርት ለመጨመር\n"
            "➖ /removeproduct — ምርት ለማስወገድ\n"
            "🧾 /myorders — የቅርብ ጊዜ ትዕዛዞች",
            parse_mode="Markdown",
        )
        return

    # CASE 3: አዲስ ነጋዴ
    text = (
        "👋 *ሰላም!*\n\n"
        "ይህ ቦት የራስዎን ሱቅ በቴሌግራም ላይ ለመክፈት የሚያስችል ነው።\n\n"
        "🏪 ነጋዴ ከሆኑ /register ብለው የራሶን ስቶር በደቂቃዎች ይክፈቱ።\n"
        "⚠️ ማሳሰቢያ፡ ለቦት ባለቤቱ በየወሩ 500 ብር ክፍያ አለው።"
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
    await update.message.reply_text("🏪 *ስቶርዎን እንክፍት!*\n\nየ can ሱቅዎን ስም ይፃፉ (ለምሳሌ፡ ኤልሳ ስቶር):", parse_mode="Markdown")
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
    
    instruction = (
        "💳 *የመክፈያ አካውንትዎን ያስገቡ*\n\n"
        "ደንበኞች እቃ ሲገዙ ብሩን የሚያስተላልፉበትን አካውንት እዚህ ይፃፉ።\n"
        "የንግድ ባንክ፣ የቴሌብር ቁጥር ወይም ሌላ የሚጠቀሙበትን በግልፅ ያስቀምጡ።\n\n"
        "ለምሳሌ፦ `የንግድ ባንክ: 1000xxxxxxxxx (አልማዝ አበበ) ወይም ቴሌብር: 09xxxxxxxx`"
    )
    await update.message.reply_text(instruction, parse_mode="Markdown")
    return REG_PAYMENT_METHOD

async def reg_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["payment_method"] = update.message.text
    await update.message.reply_text("📦 *የመጀመሪያ ምርትዎን ይጨምሩ*\n\nየምርቱን ስም ይፃፉ (ለምሳሌ፡ 👟 ጫማ):", parse_mode="Markdown")
    return REG_PRODUCT_NAME

async def reg_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["temp_product_name"] = update.message.text
    await update.message.reply_text("💵 ዋጋውን በቁጥር ብቻ ይፃፉ (ለምሳሌ፡ 1500):")
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
    await update.message.reply_text(f"✅ {name} - {price} ብር ተጨምሯል። ሌላ ይጨምራሉ?", reply_markup=InlineKeyboardMarkup(keyboard))
    return REG_MORE

async def reg_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "reg_more_yes":
        await query.edit_message_text("የምርቱን ስም ይፃፉ:")
        return REG_PRODUCT_NAME

    owner_id = query.from_user.id
    store_id = f"store_{owner_id}"
    store_data = context.user_data.pop("new_store")
    store_data["owner_id"] = owner_id
    store_data["registration_date"] = datetime.now().strftime("%Y-%m-%d")
    storage.save_store(store_id, store_data)

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={store_id}"

    text = (
        "🎉 *ስቶርዎ በተሳካ ሁኔታ ተከፍቷል!*\n\n"
        f"🏪 ስም: {store_data['store_name']}\n"
        f"💳 አካውንት: {store_data['payment_method']}\n"
        "⏰ የ 30 ቀን የሙከራ ጊዜ ተጀምሯል።\n\n"
        "ይህን ሊንክ ለደንበኞችዎ ያጋሩ፡\n"
        f"`{link}`"
    )
    await query.edit_message_text(text, parse_mode="Markdown")
    return ConversationHandler.END

# ====================== ምርት ማስተዳደሪያዎች (አልተለወጡም) ======================
async def addproduct_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if not owner_store: return ConversationHandler.END
    context.user_data["addprod_store_id"] = owner_store[0]
    await update.message.reply_text("📦 የምርቱን ስም ይፃፉ:")
    return ADDPROD_NAME

async def addproduct_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["addprod_name"] = update.message.text
    await update.message.reply_text("💵 ዋጋውን በቁጥር ብቻ ይፃፉ:")
    return ADDPROD_PRICE

async def addproduct_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: price = int(update.message.text.strip())
    except ValueError: return ADDPROD_PRICE
    store_id = context.user_data.pop("addprod_store_id")
    name = context.user_data.pop("addprod_name")
    storage.add_product(store_id, f"p{len(storage.get_store(store_id).get('products', {}))+1}", name, price)
    await update.message.reply_text(f"✅ {name} ተጨምሯል!")
    return ConversationHandler.END

async def removeproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if not owner_store: return
    store_id, store = owner_store
    keyboard = [[InlineKeyboardButton(f"❌ {p['name']}", callback_data=f"delprod|{store_id}|{key}")] for key, p in store.get("products", {}).items()]
    await update.message.reply_text("የሚያስወግዱትን ምርት ይምረጡ:", reply_markup=InlineKeyboardMarkup(keyboard))

async def removeproduct_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, store_id, key = query.data.split("|")
    storage.remove_product(store_id, key)
    await query.edit_message_text("✅ ምርቱ ተወግዷል።")

async def mystore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if not owner_store: return
    bot_username = (await context.bot.get_me()).username
    await update.message.reply_text(f"🏪 *{owner_store[1]['store_name']}*\n🔗 ሊንክ: `https://t.me/{bot_username}?start={owner_store[0]}`", parse_mode="Markdown")

async def myorders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_store = storage.get_store_by_owner(update.effective_user.id)
    if not owner_store: return
    orders = storage.get_orders_for_store(owner_store[0], limit=10)
    if not orders: return await update.message.reply_text("📭 እስካሁን ምንም ትዕዛዝ የለም።")
    lines = [f"🛍️ {o['product']} - {o['price']} ብር\n👤 {o['name']} | {o['phone']}\n📍 {o['address']}" for o in orders]
    await update.message.reply_text("\n\n".join(lines))

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    store = storage.get_store(context.user_data.get("store_id"))
    if query.data == "menu_price" and store:
        await query.edit_message_text("📋 *የምርት ዝርዝር*", reply_markup=products_keyboard(store.get("products", {})), parse_mode="Markdown")
    elif query.data == "menu_back":
        await query.edit_message_text("ከታች ካሉት አማራጮች ይምረጡ 👇", reply_markup=main_menu_keyboard())

# ====================== ደንበኛ ORDER FLOW & INSTANT TEXT ======================
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    store = storage.get_store(context.user_data.get("store_id"))
    await query.edit_message_text("🛒 የትኛውን ምርት ይፈልጋሉ?", reply_markup=products_keyboard(store.get("products", {})))
    return SELECT_PRODUCT

async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    store_id = context.user_data.get("store_id")
    store = storage.get_store(store_id)
    product = store.get("products", {}).get(query.data.replace("prod_", ""))
    context.user_data["order"] = {"store_id": store_id, "product": product["name"], "price": product["price"]}
    await query.edit_message_text(f"✅ {product['name']} ተመርጧል።\n\nእስኪ ስምዎን ይፃፉ:")
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["name"] = update.message.text
    await update.message.reply_text("📞 ስልክ ቁጥርዎን ይፃፉ:")
    return GET_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["phone"] = update.message.text
    await update.message.reply_text("📍 አድራሻዎን ይፃፉ:")
    return GET_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["address"] = update.message.text
    order = context.user_data["order"]
    summary = f"📦 *ትዕዛዝ ማረጋገጫ*\n\n🛍️ ምርት: {order['product']}\n💵 ዋጋ: {order['price']} ብር\n👤 ስም: {order['name']}\n📞 ስልክ: {order['phone']}\n📍 አድራሻ: {order['address']}\n\nትክክል ነው?"
    keyboard = [[InlineKeyboardButton("✅ አረጋግጥ", callback_data="confirm_yes")], [InlineKeyboardButton("❌ ሰርዝ", callback_data="confirm_no")]]
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CONFIRM

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        await query.edit_message_text("❌ ትዕዛዙ ተሰርዟል።")
        return ConversationHandler.END

    order = context.user_data["order"]
    order["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    storage.save_order(order)

    store = storage.get_store(order["store_id"])
    
    # 🚨 1. ለነጋዴው ወዲያውኑ የደንበኛውን ሙሉ መረጃ የያዘ TEXT መላክ!
    if store:
        owner_text = (
            "🔔 *አዲስ ትዕዛዝ ደርሶዎታል! (ክፍያ እየጠበቀ ነው)*\n\n"
            f"🛍️ ምርት: {order['product']}\n"
            f"💵 ዋጋ: {order['price']} ብር\n"
            f"👤 የደንበኛ ስም: {order['name']}\n"
            f"📞 ስልክ: {order['phone']}\n"
            f"📍 አድራሻ: {order['address']}\n\n"
            "⚠️ ደንበኛው ክፍያውን በባንክ ፈጽሞ ደረሰኝ እስኪልክልዎ ወይም በStars እስኪከፍል ይጠብቁ።"
        )
        await context.bot.send_message(chat_id=store["owner_id"], text=owner_text, parse_mode="Markdown")

    # 🚨 2. ለደንበኛው የነጋዴውን የክፍያ አማራጭ ማሳየት
    payment_instruction = (
        "🎉 *ትዕዛዝዎ በተሳካ ሁኔታ ተመዝግቧል!*\n\n"
        f"💵 ጠቅላላ ዋጋ: *{order['price']} ብር*\n\n"
        "👇 እባክዎን በፈለጉት አማራጭ ይክፈሉ፡\n"
        f"ℹ️ *የነጋዴው አካውንት፡* {store.get('payment_method', 'ባንክ አልተገለጸም')}\n\n"
        "ባንክ ከተጠቀሙ ብሩን አስተላልፈው ደረሰኙን ለነጋዴው በውስጥ መስመር ይላኩ።"
    )

    pay_keyboard = [
        [InlineKeyboardButton("⭐ በ Telegram Stars ክፈል", callback_data=f"star_pay_{order['price']}")]
    ]

    await query.edit_message_text(payment_instruction, reply_markup=InlineKeyboardMarkup(pay_keyboard), parse_mode="Markdown")
    return ConversationHandler.END

# ====================== 🌟 TELEGRAM STARS PAYMENT HANDLERS ======================
async def star_payment_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    price = int(query.data.split("_")[-1])
    stars_amount = max(1, price // 2) # 1 ስታር = 2 ብር በሚል ስሌት
    
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title="የእቃ ክፍያ",
        description="በቴሌግራም ስታርስ ክፍያዎን ይፈጽሙ",
        payload="store_product_payment",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice("ዋጋ", stars_amount)]
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "store_product_payment":
        await query.answer(ok=False, error_message="የክፍያ ስህተት ተፈጥሯል።")
    else:
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 ክፍያዎ በ Telegram Stars በተሳካ ሁኔታ ተጠናቋል! እናመሰግናለን። 🙏")

# ====================== MAIN ======================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    register_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_location)],
            REG_PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_payment_method)],
            REG_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_product_name)],
            REG_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_product_price)],
            REG_MORE: [CallbackQueryHandler(reg_more, pattern="^reg_more_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
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
        per_message=False,
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
    app.add_handler(CallbackQueryHandler(star_payment_start, pattern="^star_pay_"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    port = int(os.environ.get("PORT", 10000))
    render_url = os.environ.get("RENDER_EXTERNAL_URL")

    await app.initialize()

    if render_url:
        updater = app.updater
        if updater:
            await updater.start_webhook(listen="0.0.0.0", port=port, url_path=BOT_TOKEN, webhook_url=f"{render_url}/{BOT_TOKEN}")
            await app.start()
            while True: await asyncio.sleep(3600)
    else:
        await app.start()
        updater = app.updater
        if updater:
            await updater.start_polling()
            while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
