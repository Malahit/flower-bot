"""Flower catalog and AI recommendation handlers."""
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)

# FSM States
CHOOSE_COLOR, CHOOSE_QUANTITY, CHOOSE_ADDONS, SHOW_PREVIEW = range(4)

# Valid options
VALID_COLORS = ['🔴', '🟢', '🔵', '🟡', '⚪']
VALID_QUANTITIES = [5, 7, 11, 15, 21, 25]
VALID_ADDONS = ['🎀 Лента', '📦 Упаковка', '🍫 Шоколад', '🧸 Игрушка']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}! 🌸\n\n"
        "/recommend - AI рекомендации\n"
        "/build - Собрать букет\n"
        "/cart - Корзина"
    )
    logger.info(f"User {user.id} started bot")

async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /recommend command."""
    await update.message.reply_text("🤖 Генерирую AI-рекомендации... (Perplexity)")
    logger.info("Recommend command called")

# FSM Handlers
async def start_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start bouquet builder FSM."""
    logger.info(f"FSM build started for user {update.effective_user.id}")
    await update.message.reply_text(
        "🌸 Шаг 1/4: Выберите цвет:\n🔴 🟢 🔵 🟡 ⚪"
    )
    return CHOOSE_COLOR

async def choose_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Choose color step."""
    color = update.message.text.strip()
    if color not in VALID_COLORS:
        await update.message.reply_text("❌ Выберите цвет из эмодзи: 🔴 🟢 🔵 🟡 ⚪")
        return CHOOSE_COLOR
    
    context.user_data["color"] = color
    await update.message.reply_text("✅ Цвет выбран!\n\nШаг 2/4: Количество (5, 7, 11, 15, 21, 25):")
    return CHOOSE_QUANTITY

async def choose_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Choose quantity step."""
    try:
        quantity = int(update.message.text.strip())
        if quantity not in VALID_QUANTITIES:
            raise ValueError("Invalid quantity")
    except ValueError:
        await update.message.reply_text("❌ Укажите: 5, 7, 11, 15, 21 или 25")
        return CHOOSE_QUANTITY
    
    context.user_data["quantity"] = quantity
    buttons = [[InlineKeyboardButton(addon, callback_data=f"addon_{addon}")] for addon in VALID_ADDONS]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("✅ Количество выбрано!\n\nШаг 3/4: Дополнения:", reply_markup=reply_markup)
    return CHOOSE_QUANTITY  # Ждём callback для addons

async def choose_addons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle addons (placeholder - use CallbackQueryHandler in prod)."""
    await update.message.reply_text(
        f"✅ Букет готов!\n"
        f"Цвет: {context.user_data.get('color', 'Не выбран')}\n"
        f"Количество: {context.user_data.get('quantity', 0)}\n"
        f"Добавьте в корзину?"
    )
    context.user_data["cart"] = context.user_data.get("cart", []) + [{
        "color": context.user_data["color"],
        "quantity": context.user_data["quantity"]
    }]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel FSM."""
    context.user_data.clear()
    await update.message.reply_text("❌ Отменено. /build для нового букета.")
    return ConversationHandler.END

def main_handlers(application: Application) -> None:
    """Register all flower handlers."""
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("recommend", recommend))
    
    # FSM
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("build", start_build)],
        states={
            CHOOSE_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_color)],
            CHOOSE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_quantity)],
            CHOOSE_ADDONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_addons)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    
    logger.info("Flower handlers registered")
