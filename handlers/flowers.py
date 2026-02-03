"""Flower catalog and AI recommendation handlers."""
import json
import os
import logging
from typing import Dict, Any
from telegram import Update, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import httpx
from sqlalchemy import select
from database import async_session_maker, Flower, User

# Configure logging
logger = logging.getLogger(__name__)

# FSM states for bouquet builder
COLOR, QUANTITY, ADDONS, PREVIEW = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - open Telegram Mini App catalog."""
    user = update.effective_user

    # Save/update user in database
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.user_id == user.id))
        db_user = result.scalars().first()

        if not db_user:
            db_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            session.add(db_user)
            await session.commit()

    # Get flowers from database
    async with async_session_maker() as session:
        result = await session.execute(select(Flower).where(Flower.available == True))
        flowers = result.scalars().all()

    # Create WebApp button
    webapp_url = os.getenv("WEBAPP_URL", "https://your-app.railway.app/webapp/")
    keyboard = [
        [InlineKeyboardButton("🌸 Открыть каталог", web_app=WebAppInfo(url=webapp_url))],
        [InlineKeyboardButton("🤖 AI рекомендация", callback_data="ai_recommend")],
        [InlineKeyboardButton("🎨 Создать букет", callback_data="build_bouquet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 Привет, {user.first_name}!
\n"
        "🌺 Добро пожаловать в flower-bot - ваш персональный флорист!\n\n"
        "Что я умею:\n"
        "• 🌸 Показать каталог цветов\n"
        "• 🤖 Подобрать букет с помощью AI\n"
        "• 🎨 Создать букет по вашим предпочтениям\n"
        "• 📍 Доставить по адресу\n"
        "• 💫 Оплата через TON Stars\n\n"
        "Выберите действие:"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /recommend command - AI-powered bouquet recommendation using Perplexity."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(
            "🤖 AI Рекомендация букета\n\n"
            "Пожалуйста, опишите:\n"
            "• Повод (день рождения, свадьба, романтика)\n"
            "• Бюджет в рублях\n"
            "• Предпочтения по цвету (опционально)\n\n"
            "Пример: повод:день рождения, бюджет:2000, цвет:розовый"
        )
    else:
        await update.message.reply_text(
            "🤖 AI Рекомендация букета\n\n"
            "Пожалуйста, опишите:\n"
            "• Повод (день рождения, свадьба, романтика)\n"
            "• Бюджет в рублях\n"
            "• Предпочтения по цвету (опционально)\n\n"
            "Пример: повод:день рождения, бюджет:2000, цвет:розовый"
        )


async def process_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process AI recommendation request."""
    user_input = update.message.text

    # Parse user input
    params = {}
    for part in user_input.split(','):
        if ':' in part:
            key, value = part.split(':', 1)
            params[key.strip()] = value.strip()

    # Get available flowers
    async with async_session_maker() as session:
        result = await session.execute(select(Flower).where(Flower.available == True))
        flowers = result.scalars().all()

        flowers_context = "\n".join([f"- {f.name}: {f.description}, цена: {f.price}₽" for f in flowers])

    # Call Perplexity API
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    if not perplexity_key or perplexity_key == "your_perplexity_key_here":
        # Mock response for demo
        recommendation = (
            f"🌸 Рекомендация на основе ваших пожеланий:\n\n"
            f"Повод: {params.get('повод', 'не указан')}\n"
            f"Бюджет: {params.get('бюджет', 'не указан')}₽\n\n"
            f"💐 Рекомендуем: Букет 'День рождения'\n"
            f"Яркий микс из роз, хризантем и альстромерий - идеально подходит для вашего случая!\n"
            f"Цена: 2000₽\n\n"
            f"Или рассмотрите:\n"
            f"• Розы классические - 2500₽\n"
            f"• Тюльпаны микс - 1800₽"
        )
    else:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {perplexity_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.1-sonar-small-128k-online",
                        "messages": [
                            {
                                "role": "system",
                                "content": f"Ты флорист-консультант. Доступные букеты:\n{flowers_context}",
                            },
                            {
                                "role": "user",
                                "content": f"Порекомендуй букет для: {user_input}",
                            },
                        ],
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                recommendation = "🌸 " + data["choices"][0]["message"]["content"]
        except Exception as e:
            recommendation = f"❌ Ошибка при получении рекомендации: {str(e)}\n\nПопробуйте позже или выберите букет из каталога."

    await update.message.reply_text(recommendation)


# Bouquet builder FSM handlers
async def build_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start bouquet builder conversation."""
    query = update.callback_query
    msg = query.message if query else update.message
    if query:
        await query.answer()

    keyboard = [
        ["🔴 Красный", "🟡 Желтый"],
        ["🔵 Синий", "🟣 Фиолетовый"],
        ["🟢 Зеленый", "⚪ Белый"],
        ["🟠 Оранжевый", "🟤 Микс"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await msg.reply_text(
        "🎨 Создание вашего букета\n\n"
        "Шаг 1/3: Выберите основной цвет:",
        reply_markup=reply_markup,
    )

    return COLOR


async def build_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process color selection."""
    color = update.message.text
    context.user_data['bouquet_color'] = color

    keyboard = [
        ["5 цветов", "7 цветов"],
        ["11 цветов", "15 цветов"],
        ["21 цветок", "25 цветов"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ Цвет выбран: {color}\n\n"
        "Шаг 2/3: Выберите количество цветов:",
        reply_markup=reply_markup,
    )

    return QUANTITY


async def build_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process quantity selection."""
    quantity = update.message.text
    context.user_data['bouquet_quantity'] = quantity

    keyboard = [
        ["🎀 Лента", "🎁 Упаковка люкс"],
        ["🧸 Мягкая игрушка", "🍫 Конфеты"],
        ["❌ Без дополнений"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ Количество выбрано: {quantity}\n\n"
        "Шаг 3/3: Выберите дополнения:",
        reply_markup=reply_markup,
    )

    return ADDONS


async def build_addons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process addons and generate preview."""
    addons = update.message.text
    context.user_data['bouquet_addons'] = addons

    # Generate preview text
    color = context.user_data.get('bouquet_color', 'не выбран')
    quantity = context.user_data.get('bouquet_quantity', 'не выбрано')

    preview_text = (
        "🌸 Предпросмотр вашего букета:\n\n"
        f"🎨 Цвет: {color}\n"
        f"📊 Количество: {quantity}\n"
        f"✨ Дополнения: {addons}\n\n"
        "Генерирую изображение... ⏳"
    )

    message = await update.message.reply_text(preview_text)

    # Try to generate image using Stable Diffusion
    sd_url = os.getenv("STABLE_DIFFUSION_API_URL")
    image_generated = False

    if sd_url and sd_url != "http://localhost:7860":
        try:
            prompt = f"beautiful flower bouquet, {color} flowers, {quantity}, professional photography, high quality"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{sd_url}/sdapi/v1/txt2img",
                    json={
                        "prompt": prompt,
                        "negative_prompt": "ugly, blurry, low quality",
                        "steps": 20,
                        "width": 512,
                        "height": 512,
                    },
                    timeout=60.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("images"):
                        image_generated = True
        except Exception as e:
            logger.error(f"Stable Diffusion API error: {e}")

    if not image_generated:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new('RGB', (512, 512), color='white')
        draw = ImageDraw.Draw(img)
        text = f"{color}\n{quantity}\n{addons}"
        draw.text((256, 256), text, fill='black', anchor='mm')

        img_path = "/tmp/bouquet_preview.png"
        img.save(img_path)

        with open(img_path, 'rb') as photo_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo_file,
                caption=preview_text,
            )

    # Add reactions buttons
    keyboard = [
        [
            InlineKeyboardButton("🌸", callback_data="react_flower"),
            InlineKeyboardButton("❤️", callback_data="react_heart"),
            InlineKeyboardButton("👍", callback_data="react_like"),
        ],
        [
            InlineKeyboardButton("✅ Добавить в корзину", callback_data="add_to_cart"),
            InlineKeyboardButton("🔄 Начать заново", callback_data="build_bouquet"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.edit_text(
        preview_text.replace("Генерирую изображение... ⏳", ""),
        reply_markup=reply_markup,
    )

    return ConversationHandler.END


async def build_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel bouquet building."""
    await update.message.reply_text(
        "❌ Создание букета отменено.\n"
        "Используйте /start чтобы начать заново."
    )
    return ConversationHandler.END


# Conversation handler for bouquet builder
build_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("build", build_start),
        CallbackQueryHandler(build_start, pattern="^build_bouquet$"),
    ],
    states={
        COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, build_color)],
        QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, build_quantity)],
        ADDONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, build_addons)],
    },
    fallbacks=[CommandHandler("cancel", build_cancel)],
)