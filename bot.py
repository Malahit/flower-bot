"""Main bot application with webhook support and Bot API 9.x features."""
import os
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# SAFE imports с обработкой отсутствующих handlers
def safe_import_handlers():
    """Import handlers with fallbacks."""
    available = {}
    try:
        from handlers.flowers import start, recommend
        available['flowers'] = (start, recommend)
        logger.info("✅ Flowers handlers imported")
    except ImportError as e:
        logger.warning(f"⚠️ Flowers import failed: {e}")
    
    try:
        from handlers.orders import cart_command
        available['orders'] = cart_command
        logger.info("✅ Orders handlers imported")
    except ImportError:
        logger.warning("⚠️ Orders handlers not found")
    
    try:
        from handlers.admin import admin_command
        available['admin'] = admin_command
        logger.info("✅ Admin handlers imported")
    except ImportError:
        logger.warning("⚠️ Admin handlers not found")
    
    try:
        from database import init_db, add_sample_flowers
        available['database'] = (init_db, add_sample_flowers)
        logger.info("✅ Database imported")
    except ImportError:
        logger.warning("⚠️ Database not found")
    
    return available

HANDLERS = safe_import_handlers()

async def post_init(application: Application) -> None:
    """Initialize database and set bot commands."""
    # Init DB if available
    if 'database' in HANDLERS:
        try:
            await HANDLERS['database'][0]()
            await HANDLERS['database'][1]()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database init failed: {e}")
    
    # Set bot commands
    commands = [
        BotCommand("start", "🌸 Главное меню"),
        BotCommand("recommend", "🤖 AI рекомендация"),
        BotCommand("build", "🎨 Создать букет"),
        BotCommand("cart", "🛒 Корзина"),
        BotCommand("admin", "🔧 Админ панель"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot commands set")

async def error_handler(update: Update | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error("❌ Exception:", exc_info=context.error)

def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not found")
    
    application = Application.builder().token(token).post_init(post_init).build()
    
    # ✅ SAFE handler registration
    if 'flowers' in HANDLERS:
        application.add_handler(CommandHandler("start", HANDLERS['flowers'][0]))
        application.add_handler(CommandHandler("recommend", HANDLERS['flowers'][1]))
    
    if 'orders' in HANDLERS:
        application.add_handler(CommandHandler("cart", HANDLERS['orders']))
    
    if 'admin' in HANDLERS:
        application.add_handler(CommandHandler("admin", HANDLERS['admin']))
    
    # FSM /build из flowers.py (если register_build_handlers добавлен)
    try:
        from handlers.flowers import main_handlers
        main_handlers(application)
        logger.info("✅ FSM /build registered")
    except ImportError:
        logger.warning("⚠️ FSM handlers not found")
    
    # Register orders callbacks
    try:
        from handlers.orders import request_location, clear_cart, pay_ton, confirm_order
        application.add_handler(CallbackQueryHandler(request_location, pattern="^request_location$"))
        application.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear_cart$"))
        application.add_handler(CallbackQueryHandler(pay_ton, pattern="^pay_ton$"))
        application.add_handler(CallbackQueryHandler(confirm_order, pattern="^confirm_order_"))
        logger.info("✅ Orders callbacks registered")
    except ImportError as e:
        logger.warning(f"⚠️ Orders callbacks not registered: {e}")
    
    # Register admin callbacks
    try:
        from handlers.admin import (
            admin_list_flowers, admin_orders, admin_users, admin_back,
            add_flower_conversation, register_admin_screens
        )
        # Register admin screens first
        register_admin_screens()
        
        application.add_handler(CallbackQueryHandler(admin_list_flowers, pattern="^admin_list_flowers$"))
        application.add_handler(CallbackQueryHandler(admin_orders, pattern="^admin_orders$"))
        application.add_handler(CallbackQueryHandler(admin_users, pattern="^admin_users$"))
        application.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))
        application.add_handler(add_flower_conversation)
        logger.info("✅ Admin callbacks registered")
    except ImportError as e:
        logger.warning(f"⚠️ Admin callbacks not registered: {e}")
    
    # Register navigation back handler
    try:
        from handlers.navigation import handle_nav_back
        application.add_handler(CallbackQueryHandler(handle_nav_back, pattern="^nav_back$"))
        logger.info("✅ Navigation back handler registered")
    except ImportError as e:
        logger.warning(f"⚠️ Navigation handler not registered: {e}")
    
    # Message handlers (safe)
    application.add_handler(MessageHandler(filters.LOCATION, lambda u, c: logger.info("Location received")))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex("^(повод:|бюджет:)"),
        lambda u, c: u.message.reply_text("📝 Запрос распознан")
    ))
    
    application.add_error_handler(error_handler)
    
    # Webhook or polling
    webhook_base = os.getenv("WEBHOOK_URL")
    if webhook_base:
        port = int(os.getenv("PORT", 8080))
        webhook_path = "webhook"
        webhook_url = f"{webhook_base.rstrip('/')}/{webhook_path}"
        logger.info(f"🚀 Starting webhook: {webhook_url}:{port}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=webhook_url
        )
    else:
        logger.info("🔄 Starting polling")
        application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
