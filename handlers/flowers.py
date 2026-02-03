"""Flower catalog and AI recommendation handlers."""
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

logger = logging.getLogger(__name__)

# FSM States
CHOOSE_COLOR, CHOOSE_QUANTITY, CHOOSE_ADDONS, SHOW_PREVIEW = range(4)

# Valid options
VALID_COLORS = ['🔴', '🟢', '🔵', '🟡', '⚪']
VALID_QUANTITIES = [5, 7, 11, 15, 21, 25]
VALID_ADDONS = ['🎀 Лента', '📦 Упаковка', '🍫 Шоколад', '🧸 Игрушка']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}! 🌸\n\n"
        "/main - Каталог\n"
        "/recommend - AI рекомендации\n"
        "/build - Собрать букет"
    )

async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🤖 Генерирую рекомендации...")

# FSM Command Handlers
async def start_build(update: Update, context: CallbackContext) -> int:
    logger.info("FSM build started")
    await update.message.reply_text(
        "Шаг 1/4: Выберите основной цвет (🔴, 🟢, 🔵, 🟡, ⚪)"
    )
    return CHOOSE_COLOR

async def choose_color(update: Update, context: CallbackContext) -> int:
    logger.info("FSM step: choose_color")
    color = update.message.text.strip()
    if color not in VALID_COLORS:
        await update.message.reply_text("Некорректный цвет. Используйте предложенные эмодзи.")
        return CHOOSE_COLOR

    context.user_data["color"] = color
    await update.message.reply_text("Шаг 2/4: Укажите количество (5, 7, 11, 15, 21, 25).")
    return CHOOSE_QUANTITY

async def choose_quantity(update: Update, context: CallbackContext) -> int:
    logger.info("FSM step: choose_quantity")
    try:
        quantity = int(update.message.text.strip())
        if quantity not in VALID_QUANTITIES:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Некорректное количество. Укажите одно из предложенных значений.")
        return CHOOSE_QUANTITY

    context.user_data["quantity"] = quantity
    buttons = [[InlineKeyboardButton(addon, callback_data=addon)] for addon in VALID_ADDONS]
    await update.message.reply_text("Шаг 3/4: Выберите дополнения.", reply_markup=InlineKeyboardMarkup(buttons))
    return CHOOSE_ADDONS

async def choose_addons(update: Update, context: CallbackContext) -> int:
    logger.info("FSM step: choose_addons")
    addon = update.message.text.strip()
    if addon not in VALID_ADDONS:
        await update.message.reply_text("Некорректное дополнение. Выберите из предложенных.")
        return CHOOSE_ADDONS

    if "addons" not in context.user_data:
        context.user_data["addons"] = []
    context.user_data["addons"].append(addon)

    color = context.user_data["color"]
    quantity = context.user_data["quantity"]
    addons = ", ".join(context.user_data["addons"])
    await update.message.reply_text(
        f"Предварительный выбор:\nЦвет: {color}\nКоличество: {quantity}\nДополнения: {addons}\n\nДобавить в корзину или изменить?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Добавить в корзину", callback_data="add_to_cart")],
            [InlineKeyboardButton("Изменить", callback_data="modify")]
        ])
    )
    return SHOW_PREVIEW

async def show_preview(update: Update, context: CallbackContext) -> int:
    logger.info("FSM step: show_preview")
    action = update.callback_query.data
    if action == "add_to_cart":
        bouquet_json = {
            "color": context.user_data["color"],
            "quantity": context.user_data["quantity"],
            "addons": context.user_data["addons"]
        }
        if "cart" not in context.user_data:
            context.user_data["cart"] = []
        context.user_data["cart"].append(bouquet_json)

        await update.callback_query.edit_message_text("Букет добавлен в корзину.")
    else:
        await update.callback_query.edit_message_text("Вы можете изменить параметры через /build.")
    return ConversationHandler.END

async def cancel_build(update: Update, context: CallbackContext) -> int:
    logger.info("FSM step: cancel_build")
    context.user_data.clear()
    await update.message.reply_text("Сессия создания букета отменена.")
    return ConversationHandler.END

# Register FSM Handlers
def register_build_handlers(application):
    build_conversation = ConversationHandler(
        entry_points=[CommandHandler("build", start_build)],
        states={
            CHOOSE_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_color)],
            CHOOSE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_quantity)],
            CHOOSE_ADDONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_addons)],
            SHOW_PREVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_preview)],
        },
        fallbacks=[CommandHandler("cancel", cancel_build)],
    )
    application.add_handler(build_conversation)


# Logging configuration
logger = logging.getLogger(__name__)

# Main Handlers Registration
def main_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("recommend", recommend))
    register_build_handlers(application)