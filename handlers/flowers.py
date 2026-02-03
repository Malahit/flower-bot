"""Flower catalog and AI recommendation handlers."""
from __future__ import annotations

import os
from functools import wraps
from typing import Any, Dict

import httpx
import structlog
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from sqlalchemy import select

from database import Flower, User, async_session_maker

logger = structlog.get_logger(__name__)

# FSM states for bouquet builder
COLOR, QUANTITY, ADDONS, PREVIEW = range(4)


def handle_error(func):
    """Decorator to catch and log handler errors."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.exception("handler_error", handler=func.__name__, error=str(exc))
            target = update.effective_message if update else None
            if target:
                await target.reply_text("❌ Произошла ошибка, попробуйте позже.")
            return None

    return wrapper


@handle_error
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

    # Get flowers from database (not used yet, but keep for future webapp)
    async with async_session_maker() as session:
        await session.execute(select(Flower).where(Flower.available.is_(True)))

    webapp_url = os.getenv("WEBAPP_URL", "https://your-app.railway.app/webapp/")
    keyboard = [
        [InlineKeyboardButton("🌸 Открыть каталог", web_app=WebAppInfo(url=webapp_url))],
        [InlineKeyboardButton("🤖 AI рекомендация", callback_data="ai_recommend")],
        [InlineKeyboardButton("🎨 Создать букет", callback_data="build_bouquet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ✅ СТРОКА 61 ИСПРАВЛЕНА: тройные кавычки + правильный перенос
    welcome_text = f"""👋 Привет, {user.first_name}! 🌸

🌸 flower-bot - доставка цветов
✨ AI рекомендации букетов
🎨 Конструктор букетов
💳 Оплата TON Stars

Выберите действие:"""

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


@handle_error
async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /recommend command - AI-powered bouquet recommendation using Perplexity."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(_recommend_prompt())
    else:
        await update.message.reply_text(_recommend_prompt())


def _recommend_prompt() -> str:
    return (
        "🤖 AI Рекомендация букета\n\n"
        "Пожалуйста, опишите:\n"
        "• Повод (день рождения, свадьба, романтика)\n"
        "• Бюджет в рублях\n"
        "• Предпочтения по цвету (опционально)\n\n"
        "Пример: повод:день рождения, бюджет:2000, цвет:розовый"
    )


@handle_error
async def process_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process AI recommendation request."""
    user_input = update.message.text

    params: Dict[str, Any] = {}
    for part in user_input.split(','):
        if ':' in part:
            key, value = part.split(':', 1)
            params[key.strip()] = value.strip()

    async with async_session_maker() as session:
        result = await session.execute(select(Flower).where(Flower.available.is_(True)))
        flowers = result.scalars().all()
        flowers_context = "\n".join(
            [f"- {f.name}: {f.description}, цена: {f.price}₽" for f in flowers]
        )

    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    recommendation: str

    if not perplexity_key or perplexity_key == "your_perplexity_key_here":
        recommendation = (
            "🌸 Рекомендация на основе ваших пожеланий:\n\n"
            f"Повод: {params.get('повод', 'не указан')}\n"
            f"Бюджет: {params.get('бюджет', 'не указан')}₽\n\n"
            "💐 Рекомендуем: Букет 'День рождения'\n"
            "Яркий микс из роз, хризантем и альстромерий — идеально подходит для вашего случая!\n"
            "Цена: 2000₽\n\n"
            "Или рассмотрите:\n"
            "• Розы классические - 2500₽\n"
            "• Тюльпаны микс - 1800₽"
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
        except Exception as exc:  # noqa: BLE001
            logger.warning("perplexity_fallback", error=str(exc))
            recommendation = (
                "🌸 Не удалось получить ответ от AI.\n"
                "Попробуйте позже или опишите букет подробнее."
            )

    await update.message.reply_text(recommendation)


@handle_error
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
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await msg.reply_text(
        "🎨 Создание вашего букета\n\n"
        "Шаг 1/3: Выберите основной цвет:",
        reply_markup=reply_markup,
    )

    return COLOR


@handle_error
async def build_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    color = update.message.text
    context.user_data["bouquet_color"] = color

    keyboard = 
