"""Flower catalog and AI recommendation handlers."""
import logging
import os
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
from sqlalchemy import select
from database import async_session_maker, Flower

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

async def _generate_recommendation(occasion: str, budget: str) -> str:
    """
    Generate AI recommendation for a bouquet.
    
    Args:
        occasion: The occasion (e.g., 'birthday', 'romance', 'apology', 'wedding')
        budget: The budget description (e.g., '2000', '2500+', 'soft', 'premium')
    
    Returns:
        The recommendation text
    """
    # Fetch available flowers from database
    flowers_text = ""
    try:
        async with async_session_maker() as session:
            result = await session.execute(select(Flower).where(Flower.available == True))
            flowers = result.scalars().all()
            if flowers:
                flowers_text = "\n".join([f"- {f.name}: {f.price}₽" for f in flowers[:5]])
            else:
                flowers_text = "Каталог временно недоступен"
    except Exception as e:
        logger.error(f"Error fetching flowers: {e}")
        flowers_text = "Ошибка загрузки каталога"
    
    # Try to use Perplexity API if configured
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    if perplexity_key:
        try:
            import httpx
            prompt = f"Порекомендуй букет для события '{occasion}' с бюджетом '{budget}'. Доступные цветы:\n{flowers_text}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-sonar-small-128k-online",
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    recommendation = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if recommendation:
                        return f"🤖 AI рекомендация:\n\n{recommendation}"
        except Exception as e:
            logger.warning(f"Perplexity API error: {e}")
    
    # Fallback: simple recommendation based on occasion and budget
    recommendations = {
        "birthday": "Яркий букет 'День рождения' (микс из роз, хризантем и альстромерий) - идеален для праздника! 🎉",
        "romance": "Классические красные розы - символ любви и страсти. 15 роз в элегантной упаковке. 💕",
        "apology": "Нежные розовые пионы - мягкий и искренний жест примирения. 🌸",
        "wedding": "Роскошный букет из пионов и роз премиум класса - для особого дня! 💐",
    }
    
    base_recommendation = recommendations.get(occasion, "Розы классические - универсальный выбор для любого повода.")
    
    return (
        f"🤖 Рекомендация для '{occasion}' (бюджет: {budget}):\n\n"
        f"{base_recommendation}\n\n"
        f"Доступные букеты:\n{flowers_text}"
    )


async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /recommend command."""
    # Create preset buttons
    keyboard = [
        [InlineKeyboardButton("🎉 День рождения (2000₽)", callback_data="rec_preset:birthday:2000")],
        [InlineKeyboardButton("💕 Романтика (2500+₽)", callback_data="rec_preset:romance:2500+")],
        [InlineKeyboardButton("🌸 Извинение (деликатно)", callback_data="rec_preset:apology:soft")],
        [InlineKeyboardButton("💐 Свадьба (премиум)", callback_data="rec_preset:wedding:premium")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 Выберите готовый вариант или опишите свой запрос:\n"
        "(например: 'повод: день рождения, бюджет: 3000')",
        reply_markup=reply_markup
    )
    logger.info("Recommend command called")

# FSM Handlers
async def handle_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle preset recommendation button clicks."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: "rec_preset:occasion:budget"
    try:
        _, occasion, budget = query.data.split(":", 2)
        
        # Show processing message
        await query.edit_message_text("🤖 Генерирую рекомендацию...")
        
        # Generate recommendation using the helper
        recommendation = await _generate_recommendation(occasion, budget)
        
        # Send recommendation
        await query.edit_message_text(recommendation)
        logger.info(f"Preset recommendation generated: {occasion}, {budget}")
        
    except Exception as e:
        logger.error(f"Error handling preset callback: {e}")
        await query.edit_message_text("❌ Ошибка при генерации рекомендации. Попробуйте снова.")


async def start_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start bouquet builder FSM."""
    logger.info(f"FSM build started for user {update.effective_user.id}")
    await update.message.reply_text(
        "🌸 Конструктор букетов\n\n"
        "💡 Подсказка: если не уверены в выборе, попробуйте /recommend для AI-помощи\n\n"
        "Шаг 1/4: Выберите цвет:\n🔴 🟢 🔵 🟡 ⚪"
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
    
    # Callback handler for recommendation presets
    application.add_handler(CallbackQueryHandler(handle_preset_callback, pattern="^rec_preset:"))
    
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


# Export the conversation handler for testing
build_conversation = ConversationHandler(
    entry_points=[CommandHandler("build", start_build)],
    states={
        CHOOSE_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_color)],
        CHOOSE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_quantity)],
        CHOOSE_ADDONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_addons)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
