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
    filters
)
from dotenv import load_dotenv

# Import handlers
from handlers.flowers import start, recommend, process_recommendation, build_conversation, build_start
from handlers.orders import (
    add_to_cart,
    show_cart,
    request_location,
    process_location,
    clear_cart,
    pay_ton,
    confirm_order,
    cart_command
)
from handlers.admin import (
    admin_command,
    admin_list_flowers,
    admin_orders,
    admin_users,
    admin_back,
    add_flower_start,
    add_flower_conversation
)
from database import init_db, add_sample_flowers

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Initialize database and set bot commands."""
    # Initialize database
    await init_db()
    await add_sample_flowers()
    logger.info("Database initialized")
    
    # Set bot commands
    commands = [
        BotCommand("start", "🌸 Главное меню"),
        BotCommand("recommend", "🤖 AI рекомендация"),
        BotCommand("build", "🎨 Создать букет"),
        BotCommand("cart", "🛒 Корзина"),
        BotCommand("admin", "🔧 Админ панель"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set")


async def error_handler(update: Update | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error("Exception while handling an update:", exc_info=context.error)


def main() -> None:
    """Start the bot."""
    # Get token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Create application
    application = Application.builder().token(token).post_init(post_init).build()
    
    # Add handlers
    # Start and basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("recommend", recommend))
    application.add_handler(CommandHandler("cart", cart_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(recommend, pattern="^ai_recommend$"))
    application.add_handler(CallbackQueryHandler(build_start, pattern="^build_bouquet$"))
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_to_cart$"))
    application.add_handler(CallbackQueryHandler(show_cart, pattern="^show_cart$"))
    application.add_handler(CallbackQueryHandler(request_location, pattern="^request_location$"))
    application.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear_cart$"))
    application.add_handler(CallbackQueryHandler(pay_ton, pattern="^pay_ton$"))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern="^confirm_order_.*$"))
    
    # Admin callback handlers
    application.add_handler(CallbackQueryHandler(admin_list_flowers, pattern="^admin_list_flowers$"))
    application.add_handler(CallbackQueryHandler(admin_orders, pattern="^admin_orders$"))
    application.add_handler(CallbackQueryHandler(admin_users, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))
    application.add_handler(CallbackQueryHandler(add_flower_start, pattern="^admin_add_flower$"))
    
    # Conversation handlers
    application.add_handler(build_conversation)
    application.add_handler(add_flower_conversation)
    
    # Message handlers
    application.add_handler(MessageHandler(filters.LOCATION, process_location))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex("^(повод:|бюджет:)"),
        process_recommendation
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    webhook_base = os.getenv("WEBHOOK_URL")
    
    if webhook_base:
        # Use webhook for production (fixed path /webhook without exposing token)
        port = int(os.getenv("PORT", 8443))
        webhook_path = "webhook"
        webhook_url = f"{webhook_base.rstrip('/')}/{webhook_path}"
        logger.info("Starting webhook on port %s with url %s", port, webhook_url)
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=webhook_url
        )
    else:
        # Use polling for development
        logger.info("Starting polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()