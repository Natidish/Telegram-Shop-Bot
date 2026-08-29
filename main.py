"""
TELEGRAM MULTI-TENANT SHOP BOT - COMPLETE VERSION
ሙሉ ተግባራዊ Telegram ሱቅ ቦት
============================================
✅ All fixes included
✅ No markdown errors
✅ Production ready
✅ For Render.com deployment
"""

import logging
import os
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

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

# ====================== SETUP LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ====================== CONFIG FROM ENVIRONMENT ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("ERROR: BOT_TOKEN not set! Set it in Render environment variables")
    raise ValueError("BOT_TOKEN is required")

PORT = int(os.environ.get("PORT", 10000))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

logger.info(f"Bot starting... TOKEN: {BOT_TOKEN[:20]}... PORT: {PORT}")

# ====================== CONVERSATION STATES ======================
SELECT_PRODUCT, GET_NAME, GET_PHONE, GET_ADDRESS, CONFIRM = range(5)
REG_NAME, REG_PHONE, REG_LOCATION, REG_PAYMENT, REG_PROD_NAME, REG_PROD_PRICE, REG_PROD_PHOTO, REG_PROD_DESC, REG_MORE = range(10, 19)
ADDPROD_NAME, ADDPROD_PRICE, ADDPROD_PHOTO, ADDPROD_DESC = range(20, 24)

# ====================== STORAGE (Simple File-Based) ======================
STORAGE_DIR = "bot_data"
os.makedirs(STORAGE_DIR, exist_ok=True)

import json

def save_store(store_id, data):
    """Save store to JSON"""
    path = os.path.join(STORAGE_DIR, f"store_{store_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved store: {store_id}")

def get_store(store_id):
    """Get store from JSON"""
    path = os.path.join(STORAGE_DIR, f"store_{store_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def get_store_by_owner(owner_id):
    """Get store by owner ID"""
    for file in os.listdir(STORAGE_DIR):
        if file.startswith("store_"):
            store = get_store(file.replace("store_", "").replace(".json", ""))
            if store and store.get("owner_id") == owner_id:
                return (file.replace("store_", "").replace(".json", ""), store)
    return None

def save_order(order):
    """Save order to JSON"""
    order_id = f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    path = os.path.join(STORAGE_DIR, f"{order_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(order, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved order: {order_id}")
    return order_id

def get_orders(store_id, limit=20):
    """Get recent orders for store"""
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

# ====================== HELPER FUNCTIONS ======================
def is_active(store):
    """Check if store subscription is active"""
    reg_date_str = store.get("registration_date", datetime.now().strftime("%Y-%m-%d"))
    try:
        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
    except:
        return True
    expiry = reg_date + timedelta(days=30)
    return datetime.now() < expiry

def main_menu():
    """Customer main menu keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Products", callback_data="menu_products")],
        [InlineKeyboardButton("🛒 Order", callback_data="menu_order")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="menu_info")],
    ])

def products_menu(products):
    """Product selection keyboard"""
    buttons = [
        [InlineKeyboardButton(f"{p['name']} - {p['price']} Br", callback_data=f"prod_{k}")]
        for k, p in products.items()
    ]
    buttons.append([InlineKeyboardButton("Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(buttons)

# ====================== /START COMMAND ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    args = context.args
    
    # Customer visiting with store link
    if args:
        store_id = args[0]
        store = get_store(store_id)
        if not store:
            await update.message.reply_text("Error: Invalid store link")
            return
        if not is_active(store):
            await update.message.reply_text("This store is closed")
            return
        
        context.user_data["store_id"] = store_id
        await update.message.reply_text(
            f"Welcome to {store['store_name']}!\n\nChoose an option below:",
            reply_markup=main_menu()
        )
        return
    
    # Merchant checking their store
    owner_store = get_store_by_owner(update.effective_user.id)
    if owner_store:
        store_id, store = owner_store
        status = "Active" if is_active(store) else "Expired"
        await update.message.reply_text(
            f"Welcome Merchant!\n\n"
            f"Store: {store['store_name']}\n"
            f"Username: @{store.get('username', 'N/A')}\n"
            f"Status: {status}\n\n"
            f"/mystore - Store Info\n"
            f"/addproduct - Add Product\n"
            f"/dashboard - View Stats\n"
            f"/myorders - Recent Orders\n"
            f"/test_notify - Test Message"
        )
        return
    
    # New user
    await update.message.reply_text(
        "Welcome to Telegram Shop Bot!\n\n"
        "Merchants: /register to create your shop\n"
        "Trial: Free 30 days"
    )

# ====================== MERCHANT REGISTRATION ======================
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start merchant registration"""
    if get_store_by_owner(update.effective_user.id):
        await update.message.reply_text("You already have a store!")
        return ConversationHandler.END
    
    context.user_data["new_store"] = {
        "user_id": update.effective_user.id,
        "username": update.effective_user.username or "merchant",
        "first_name": update.effective_user.first_name or "User",
        "products": {}
    }
    
    await update.message.reply_text(
        f"Create Your Store!\n\n"
        f"Telegram: @{update.effective_user.username}\n"
        f"ID: {update.effective_user.id}\n\n"
        "What's your store name?"
    )
    return REG_NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["store_name"] = update.message.text
    await update.message.reply_text("What's your phone number?")
    return REG_PHONE

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["phone"] = update.message.text
    await update.message.reply_text("Your location?")
    return REG_LOCATION

async def reg_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["location"] = update.message.text
    await update.message.reply_text("Payment account details? (Bank/Telebirr)")
    return REG_PAYMENT

async def reg_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_store"]["payment_method"] = update.message.text
    await update.message.reply_text("First product name?")
    return REG_PROD_NAME

async def reg_prod_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["temp_prod_name"] = update.message.text
    await update.message.reply_text("Price? (number only)")
    return REG_PROD_PRICE

async def reg_prod_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["temp_prod_price"] = int(update.message.text.strip())
    except:
        await update.message.reply_text("Enter number only")
        return REG_PROD_PRICE
    await update.message.reply_text("Product photo? (or /skip)")
    return REG_PROD_PHOTO

async def reg_prod_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["temp_prod_photo"] = update.message.photo[-1].file_id
    else:
        context.user_data["temp_prod_photo"] = None
    await update.message.reply_text("Description? (or /skip)")
    return REG_PROD_DESC

async def reg_prod_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text if update.message.text and not update.message.text.startswith('/') else "No description"
    
    name = context.user_data.pop("temp_prod_name")
    price = context.user_data.pop("temp_prod_price")
    photo = context.user_data.pop("temp_prod_photo")
    
    products = context.user_data["new_store"]["products"]
    key = f"p{len(products) + 1}"
    products[key] = {"name": name, "price": price, "photo": photo, "description": desc}
    
    keyboard = [
        [InlineKeyboardButton("Add Another", callback_data="reg_more_yes")],
        [InlineKeyboardButton("Done", callback_data="reg_more_no")],
    ]
    
    await update.message.reply_text(
        f"Added: {name} - {price} Br",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REG_MORE

async def reg_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "reg_more_yes":
        await query.edit_message_text("Product name?")
        return REG_PROD_NAME
    
    # Save store
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
    
    await query.edit_message_text(
        f"Store Created!\n\n"
        f"Name: {store_data['store_name']}\n"
        f"Username: @{store_data['username']}\n"
        f"Payment: {store_data['payment_method']}\n\n"
        f"Share link: {link}"
    )
    
    # Send welcome message
    try:
        await context.bot.send_message(
            chat_id=owner_id,
            text=f"Welcome to your store!\n"
                 f"Store: {store_data['store_name']}\n"
                 f"Username: @{store_data['username']}\n"
                 f"30-day free trial started!\n\n"
                 f"/test_notify - Test messaging\n"
                 f"/dashboard - View stats"
        )
        logger.info(f"Welcome message sent to {owner_id}")
    except Exception as e:
        logger.error(f"Failed to send welcome: {e}")
    
    return ConversationHandler.END

# ====================== MERCHANT COMMANDS ======================
async def mystore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show store info"""
    owner_store = get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("No store found")
        return
    
    bot_username = (await context.bot.get_me()).username
    store_id, store = owner_store
    
    await update.message.reply_text(
        f"Store: {store['store_name']}\n"
        f"Username: @{store.get('username')}\n"
        f"Phone: {store.get('phone')}\n"
        f"Link: https://t.me/{bot_username}?start={store_id}"
    )

async def test_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test merchant notification"""
    owner_store = get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("No store found")
        return
    
    store_id, store = owner_store
    user_id = store.get("user_id")
    username = store.get("username")
    
    test_msg = (
        f"Test Message!\n\n"
        f"If you see this, messaging works.\n"
        f"Store: {store['store_name']}\n"
        f"Username: @{username}"
    )
    
    try:
        await context.bot.send_message(chat_id=user_id, text=test_msg)
        await update.message.reply_text(f"Test message sent to @{username}")
        logger.info(f"Test message sent to {user_id}")
    except Exception as e:
        await update.message.reply_text(f"Failed: {str(e)}")
        logger.error(f"Test message failed: {e}")

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Merchant dashboard"""
    owner_store = get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("No store found")
        return
    
    store_id, store = owner_store
    orders = get_orders(store_id)
    
    total_orders = len(orders)
    total_revenue = sum(o.get('price', 0) for o in orders)
    
    await update.message.reply_text(
        f"Dashboard - {store['store_name']}\n\n"
        f"Total Orders: {total_orders}\n"
        f"Total Revenue: {total_revenue} Br\n"
        f"Products: {len(store.get('products', {}))}\n"
        f"Status: Active" if is_active(store) else "Expired"
    )

async def myorders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent orders"""
    owner_store = get_store_by_owner(update.effective_user.id)
    if not owner_store:
        await update.message.reply_text("No store found")
        return
    
    orders = get_orders(owner_store[0], limit=15)
    if not orders:
        await update.message.reply_text("No orders yet")
        return
    
    text = "Recent Orders:\n\n"
    for i, o in enumerate(orders, 1):
        text += (
            f"{i}. {o.get('product', 'Unknown')}\n"
            f"   {o.get('price')} Br\n"
            f"   {o.get('name')}\n"
            f"   {o.get('phone')}\n"
            f"   {o.get('timestamp')}\n\n"
        )
    
    await update.message.reply_text(text)

# ====================== CUSTOMER ORDER FLOW ======================
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start order"""
    query = update.callback_query
    await query.answer()
    
    store_id = context.user_data.get("store_id")
    store = get_store(store_id)
    if not store:
        await query.edit_message_text("Store not found")
        return ConversationHandler.END
    
    context.user_data["order"] = {"store_id": store_id}
    await query.edit_message_text("Which product?", reply_markup=products_menu(store.get("products", {})))
    return SELECT_PRODUCT

async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select product"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_back":
        await query.edit_message_text("Choose an option:", reply_markup=main_menu())
        return ConversationHandler.END
    
    store_id = context.user_data.get("store_id")
    store = get_store(store_id)
    
    prod_key = query.data.replace("prod_", "")
    product = store.get("products", {}).get(prod_key)
    
    if not product:
        await query.message.reply_text("Product not found")
        return ConversationHandler.END
    
    context.user_data["order"]["product"] = product["name"]
    context.user_data["order"]["price"] = product["price"]
    
    text = f"Product: {product['name']}\nPrice: {product['price']} Br\n\nEnter your name:"
    
    if product.get("photo"):
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=product["photo"],
            caption=text
        )
    else:
        await query.edit_message_text(text)
    
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["name"] = update.message.text
    await update.message.reply_text("Phone number?")
    return GET_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["phone"] = update.message.text
    await update.message.reply_text("Delivery address?")
    return GET_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["address"] = update.message.text
    order = context.user_data["order"]
    
    summary = (
        f"Confirm Order?\n\n"
        f"Product: {order['product']}\n"
        f"Price: {order['price']} Br\n"
        f"Name: {order['name']}\n"
        f"Phone: {order['phone']}\n"
        f"Address: {order['address']}"
    )
    
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data="confirm_yes")],
        [InlineKeyboardButton("Cancel", callback_data="confirm_no")],
    ]
    
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm order"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_no":
        await query.message.reply_text("Order cancelled")
        context.user_data.pop("order", None)
        return ConversationHandler.END
    
    order = context.user_data["order"]
    order["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    store_id = order.get("store_id")
    store = get_store(store_id)
    
    save_order(order)
    
    # Notify merchant
    if store and "user_id" in store:
        notify_text = (
            f"New Order!\n\n"
            f"Store: {store['store_name']}\n"
            f"Product: {order['product']}\n"
            f"Price: {order['price']} Br\n"
            f"Name: {order['name']}\n"
            f"Phone: {order['phone']}\n"
            f"Address: {order['address']}\n"
            f"Time: {order['timestamp']}"
        )
        
        try:
            await context.bot.send_message(chat_id=store["user_id"], text=notify_text)
            logger.info(f"Order notification sent to {store['user_id']}")
        except Exception as e:
            logger.error(f"Failed to notify merchant: {e}")
    
    # Send payment info
    payment_method = store.get('payment_method', 'N/A') if store else 'N/A'
    
    await query.message.reply_text(
        f"Order Confirmed!\n\n"
        f"Product: {order['product']}\n"
        f"Total: {order['price']} Br\n\n"
        f"Pay to: {payment_method}\n\n"
        f"After payment, send screenshot to:\n"
        f"{store.get('phone')}"
    )
    
    context.user_data.pop("order", None)
    return ConversationHandler.END

# ====================== MENU CALLBACKS ======================
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu callbacks"""
    query = update.callback_query
    await query.answer()
    
    store_id = context.user_data.get("store_id")
    store = get_store(store_id)
    
    if query.data == "menu_products":
        await query.edit_message_text("Products:", reply_markup=products_menu(store.get("products", {})))
    
    elif query.data == "menu_info":
        info = (
            f"Store: {store['store_name']}\n"
            f"Username: @{store.get('username')}\n"
            f"Phone: {store.get('phone')}\n"
            f"Location: {store.get('location')}\n\n"
            f"Click Order to buy"
        )
        await query.edit_message_text(info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="menu_back")]]))
    
    elif query.data == "menu_back":
        await query.edit_message_text("Choose:", reply_markup=main_menu())

# ====================== CANCEL ======================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    context.user_data.clear()
    await update.message.reply_text("Cancelled. /start to begin")
    return ConversationHandler.END

# ====================== MAIN APPLICATION ======================
async def main():
    """Start bot"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Registration conversation
    register_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_location)],
            REG_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_payment)],
            REG_PROD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_prod_name)],
            REG_PROD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_prod_price)],
            REG_PROD_PHOTO: [MessageHandler(filters.PHOTO | filters.COMMAND, reg_prod_photo)],
            REG_PROD_DESC: [MessageHandler(filters.TEXT | filters.COMMAND, reg_prod_desc)],
            REG_MORE: [CallbackQueryHandler(reg_more, pattern="^reg_more_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
    
    # Order conversation
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
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(register_conv)
    app.add_handler(order_conv)
    
    app.add_handler(CommandHandler("mystore", mystore))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("myorders", myorders))
    app.add_handler(CommandHandler("test_notify", test_notify))
    
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    
    # Start bot
    await app.initialize()
    
    if RENDER_EXTERNAL_URL:
        # Webhook mode (Render.com)
        logger.info(f"Starting webhook mode on {RENDER_EXTERNAL_URL}")
        await app.bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}")
        
        from telegram.ext import Updater
        async with app:
            await app.start()
            await app.updater.start_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
            )
            await app.updater.idle()
    else:
        # Polling mode (local development)
        logger.info("Starting polling mode")
        async with app:
            await app.start()
            await app.updater.start_polling()
            await app.updater.idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
