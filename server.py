"""Combined server for bot webhook and Mini App API."""
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_combined_server():
    """Start combined bot webhook and API server."""
    from api import app as api_app
    from bot import HANDLERS, post_init, error_handler
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not found")
    
    # Create bot application
    application = Application.builder().token(token).build()
    
    # Initialize database and set commands
    await post_init(application)
    
    # Register handlers (same as bot.py)
    if 'flowers' in HANDLERS:
        from telegram.ext import CommandHandler
        application.add_handler(CommandHandler("start", HANDLERS['flowers'][0]))
        application.add_handler(CommandHandler("recommend", HANDLERS['flowers'][1]))
    
    if 'orders' in HANDLERS:
        from telegram.ext import CommandHandler
        application.add_handler(CommandHandler("cart", HANDLERS['orders']))
    
    if 'admin' in HANDLERS:
        from telegram.ext import CommandHandler
        application.add_handler(CommandHandler("admin", HANDLERS['admin']))
    
    # FSM /build
    try:
        from handlers.flowers import main_handlers
        main_handlers(application)
        logger.info("✅ FSM /build registered")
    except ImportError:
        logger.warning("⚠️ FSM handlers not found")
    
    # Register orders callbacks
    try:
        from handlers.orders import request_location, clear_cart, pay_ton, confirm_order
        from telegram.ext import CallbackQueryHandler
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
        from telegram.ext import CallbackQueryHandler
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
        from telegram.ext import CallbackQueryHandler
        application.add_handler(CallbackQueryHandler(handle_nav_back, pattern="^nav_back$"))
        logger.info("✅ Navigation back handler registered")
    except ImportError as e:
        logger.warning(f"⚠️ Navigation handler not registered: {e}")
    
    # Message handlers
    from telegram.ext import MessageHandler, filters
    # TODO: Implement location handling - currently handled in orders.py via CallbackQueryHandler
    # This is a placeholder to log location messages that arrive outside the order flow
    application.add_handler(MessageHandler(
        filters.LOCATION, 
        lambda u, c: logger.info(f"Location received from user {u.effective_user.id} outside order flow")
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex("^(повод:|бюджет:)"),
        lambda u, c: u.message.reply_text("📝 Запрос распознан")
    ))
    
    application.add_error_handler(error_handler)
    
    # Initialize bot
    await application.initialize()
    await application.start()
    
    # Set webhook
    webhook_base = os.getenv("WEBHOOK_URL")
    if webhook_base:
        webhook_path = "webhook"
        webhook_url = f"{webhook_base.rstrip('/')}/{webhook_path}"
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set: {webhook_url}")
    
    # Add webhook endpoint to FastAPI app
    @api_app.post("/webhook")
    async def telegram_webhook(request: Request):
        """Handle Telegram webhook updates."""
        try:
            data = await request.json()
            update = Update.de_json(data, application.bot)
            await application.update_queue.put(update)
            return Response(status_code=200)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return Response(status_code=500)
    
    # Run FastAPI server
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(api_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    logger.info(f"🚀 Starting combined server on port {port}")
    await server.serve()


if __name__ == "__main__":
    asyncio.run(start_combined_server())
