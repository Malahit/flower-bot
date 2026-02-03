"""Flower catalog and AI recommendation handlers."""
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

logger = logging.getLogger(__name__)

# FSM States
CHOOSE_COLOR, CHOOSE_QUANTITY, CHOOSE_ADDONS, SHOW_PREVIEW = range(4)

# Valid options
VALID_COLORS = ['🔴', '🟢', '🔵', '🟡', '⚪']
VALID_QUANTITIES = [5, 7, 11, 15, 21, 25]
VALID_ADDONS = ['🎀 Лента', '📦 Упаковка', '🍫 Шоколад', '🧸 Игрушка']

# Placeholder for build_conversation (initialized in main_handlers)
build_conversation = None

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
    # Clear any previous bouquet data
    context.user_data.pop("color", None)
    context.user_data.pop("quantity", None)
    context.user_data.pop("addons", None)
    
    await update.message.reply_text(
        "🌸 Шаг 1/3: Выберите цвет:\n🔴 🟢 🔵 🟡 ⚪"
    )
    return CHOOSE_COLOR

async def choose_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Choose color step."""
    color = update.message.text.strip()
    if color not in VALID_COLORS:
        await update.message.reply_text("❌ Выберите цвет из эмодзи: 🔴 🟢 🔵 🟡 ⚪")
        return CHOOSE_COLOR
    
    context.user_data["color"] = color
    
    # Create inline keyboard with quantity options and navigation
    buttons = []
    for i in range(0, len(VALID_QUANTITIES), 2):
        row = []
        for j in range(2):
            if i + j < len(VALID_QUANTITIES):
                qty = VALID_QUANTITIES[i + j]
                row.append(InlineKeyboardButton(str(qty), callback_data=f"qty_{qty}"))
        buttons.append(row)
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "✅ Цвет выбран!\n\n🌸 Шаг 2/3: Выберите количество:",
        reply_markup=reply_markup
    )
    return CHOOSE_QUANTITY

async def choose_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Choose quantity step - handle callback from inline buttons."""
    query = update.callback_query
    await query.answer()
    
    # Extract quantity from callback data
    try:
        quantity = int(query.data.split('_')[1])
        if quantity not in VALID_QUANTITIES:
            await query.message.reply_text("❌ Выберите из предложенных вариантов")
            return CHOOSE_QUANTITY
    except (ValueError, IndexError):
        await query.message.reply_text("❌ Ошибка обработки выбора")
        return CHOOSE_QUANTITY
    
    context.user_data["quantity"] = quantity
    
    # Initialize empty addons list
    if "addons" not in context.user_data:
        context.user_data["addons"] = []
    
    # Create inline keyboard with addon options and navigation
    keyboard = _build_addons_keyboard(context.user_data.get("addons", []))
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✅ Количество выбрано!\n\n🌸 Шаг 3/3: Выберите дополнения:",
        reply_markup=reply_markup
    )
    return CHOOSE_ADDONS


def _build_addons_keyboard(selected_addons: list) -> list:
    """Build inline keyboard for addons selection with toggle state."""
    buttons = []
    
    # Add addon buttons with checkmark for selected items
    for addon in VALID_ADDONS:
        prefix = "✓ " if addon in selected_addons else ""
        buttons.append([InlineKeyboardButton(
            f"{prefix}{addon}", 
            callback_data=f"addon_{addon}"
        )])
    
    # Add navigation buttons
    buttons.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_quantity"),
        InlineKeyboardButton("✅ Готово", callback_data="addons_done")
    ])
    
    return buttons

async def toggle_addon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle addon toggle - add/remove from selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract addon from callback data
    addon = query.data.replace("addon_", "")
    
    # Validate addon
    if addon not in VALID_ADDONS:
        await query.answer("❌ Недопустимое дополнение", show_alert=True)
        return CHOOSE_ADDONS
    
    # Initialize addons list if not exists
    if "addons" not in context.user_data:
        context.user_data["addons"] = []
    
    # Toggle addon
    if addon in context.user_data["addons"]:
        context.user_data["addons"].remove(addon)
    else:
        context.user_data["addons"].append(addon)
    
    # Update keyboard
    keyboard = _build_addons_keyboard(context.user_data["addons"])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_reply_markup(reply_markup=reply_markup)
    return CHOOSE_ADDONS


async def back_to_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to quantity selection from addons."""
    query = update.callback_query
    await query.answer()
    
    # Reset addons
    context.user_data["addons"] = []
    
    # Create inline keyboard with quantity options
    buttons = []
    for i in range(0, len(VALID_QUANTITIES), 2):
        row = []
        for j in range(2):
            if i + j < len(VALID_QUANTITIES):
                qty = VALID_QUANTITIES[i + j]
                row.append(InlineKeyboardButton(str(qty), callback_data=f"qty_{qty}"))
        buttons.append(row)
    
    # Add back button to return to color selection
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_color")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(
        "🌸 Шаг 2/3: Выберите количество:",
        reply_markup=reply_markup
    )
    return CHOOSE_QUANTITY


async def back_to_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to color selection from quantity."""
    query = update.callback_query
    await query.answer()
    
    # Reset quantity
    context.user_data.pop("quantity", None)
    
    await query.edit_message_text(
        "🌸 Шаг 1/3: Выберите цвет:\n🔴 🟢 🔵 🟡 ⚪"
    )
    return CHOOSE_COLOR


async def addons_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finish addons selection and show preview."""
    query = update.callback_query
    await query.answer()
    
    # Get bouquet details
    color = context.user_data.get('color', 'Не выбран')
    quantity = context.user_data.get('quantity', 0)
    addons = context.user_data.get('addons', [])
    
    # Format addons list
    addons_text = ", ".join(addons) if addons else "без дополнений"
    
    # Show preview
    preview_text = (
        "✅ Букет готов!\n\n"
        f"Цвет: {color}\n"
        f"Количество: {quantity}\n"
        f"Дополнения: {addons_text}\n\n"
        "Добавьте в корзину?"
    )
    
    await query.edit_message_text(preview_text)
    
    # Add to cart (optional)
    context.user_data["cart"] = context.user_data.get("cart", []) + [{
        "color": color,
        "quantity": quantity,
        "addons": addons
    }]
    
    logger.info(f"Bouquet created: {color}, {quantity}, {addons}")
    
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
    
    # FSM - Export as build_conversation for compatibility
    global build_conversation
    build_conversation = ConversationHandler(
        entry_points=[CommandHandler("build", start_build)],
        states={
            CHOOSE_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_color)],
            CHOOSE_QUANTITY: [
                CallbackQueryHandler(choose_quantity, pattern="^qty_"),
                CallbackQueryHandler(back_to_color, pattern="^back_to_color$"),
            ],
            CHOOSE_ADDONS: [
                CallbackQueryHandler(toggle_addon, pattern="^addon_"),
                CallbackQueryHandler(back_to_quantity, pattern="^back_to_quantity$"),
                CallbackQueryHandler(addons_done, pattern="^addons_done$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(build_conversation)
    
    logger.info("Flower handlers registered")
