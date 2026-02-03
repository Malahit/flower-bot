"""Flower catalog and AI recommendation handlers."""
from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict
from io import BytesIO

import httpx
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    WebAppInfo,
    InputFile,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from sqlalchemy import select
from database import async_session_maker, Flower, User

# Try to import optional dependencies
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import webuiapi
    WEBUI_AVAILABLE = True
except ImportError:
    WEBUI_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# FSM States for bouquet builder
BOUQUET_COLOR, BOUQUET_QUANTITY, BOUQUET_ADDONS = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - show main menu with catalog."""
    user = update.effective_user
    
    # Create or update user in database
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.user_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            db_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(db_user)
            await session.commit()
    
    # Get webapp URL for catalog
    webapp_url = os.getenv("WEBAPP_URL", "https://example.com/webapp")
    
    # Create inline keyboard with catalog and features
    keyboard = [
        [InlineKeyboardButton("🌸 Каталог цветов", web_app=WebAppInfo(url=webapp_url))],
        [InlineKeyboardButton("🤖 AI Рекомендация", callback_data="ai_recommend")],
        [InlineKeyboardButton("🎨 Создать букет", callback_data="build_bouquet")],
        [InlineKeyboardButton("🛒 Корзина", callback_data="show_cart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🌸 Добро пожаловать в Flower Bot, {user.first_name}!\n\n"
        "Я помогу вам выбрать идеальный букет для любого случая.\n\n"
        "✨ Возможности:\n"
        "🌸 Каталог - просмотр всех доступных букетов\n"
        "🤖 AI Рекомендация - подбор букета на основе повода и бюджета\n"
        "🎨 Создать букет - конструктор букета с превью\n"
        "🛒 Корзина - просмотр и оплата заказа\n\n"
        "Выберите действие:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup)


async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /recommend command or callback - AI-powered bouquet recommendation."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    instruction_text = (
        "🤖 AI Рекомендация букета\n\n"
        "Расскажите мне о вашем событии в формате:\n"
        "повод:<событие>, бюджет:<сумма>, цвет:<цвет>\n\n"
        "Примеры:\n"
        "• повод:день рождения, бюджет:2000\n"
        "• повод:свадьба, бюджет:5000, цвет:белый\n"
        "• повод:годовщина, бюджет:3000, цвет:красный\n\n"
        "Или просто напишите текстом что вам нужно!"
    )
    
    await message.reply_text(instruction_text)


async def process_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process AI recommendation request from user text."""
    text = update.message.text.lower()
    
    # Parse user input
    occasion = ""
    budget = None
    color = ""
    
    # Simple parsing
    if "повод:" in text:
        parts = text.split("повод:")[1].split(",")[0].strip()
        occasion = parts
    
    if "бюджет:" in text:
        parts = text.split("бюджет:")[1].split(",")[0].strip()
        try:
            budget = float(''.join(filter(str.isdigit, parts)))
        except ValueError:
            budget = None
    
    if "цвет:" in text:
        parts = text.split("цвет:")[1].split(",")[0].strip()
        color = parts
    
    # Get flowers from database
    async with async_session_maker() as session:
        result = await session.execute(
            select(Flower).where(Flower.available == True)
        )
        flowers = result.scalars().all()
    
    if not flowers:
        await update.message.reply_text(
            "😔 К сожалению, в данный момент нет доступных букетов.\n"
            "Попробуйте позже или обратитесь к администратору."
        )
        return
    
    # Simple recommendation logic (can be enhanced with Perplexity API)
    recommended = None
    
    # Filter by budget if specified
    if budget:
        suitable = [f for f in flowers if f.price <= budget]
        if suitable:
            # Pick the most expensive within budget
            recommended = max(suitable, key=lambda x: x.price)
        else:
            # Get cheapest option
            recommended = min(flowers, key=lambda x: x.price)
    else:
        # Random recommendation
        import random
        recommended = random.choice(flowers)
    
    # Create recommendation response
    recommendation_text = (
        f"🌸 Рекомендация на основе ваших пожеланий:\n\n"
    )
    
    if occasion:
        recommendation_text += f"Повод: {occasion}\n"
    if budget:
        recommendation_text += f"Бюджет: {budget}₽\n"
    if color:
        recommendation_text += f"Предпочтительный цвет: {color}\n"
    
    recommendation_text += (
        f"\n💐 Рекомендуем: {recommended.name}\n"
        f"{recommended.description or 'Прекрасный выбор для любого случая!'}\n"
        f"Цена: {recommended.price}₽\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Добавить в корзину", callback_data=f"add_flower_{recommended.id}")],
        [InlineKeyboardButton("🌸 К каталогу", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if recommended.photo_url:
        try:
            await update.message.reply_photo(
                photo=recommended.photo_url,
                caption=recommendation_text,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Failed to send photo: {e}")
            await update.message.reply_text(recommendation_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(recommendation_text, reply_markup=reply_markup)


async def build_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start bouquet builder conversation."""
    query = update.callback_query
    await query.answer()
    
    # Color selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("🔴 Красный", callback_data="color_red"),
            InlineKeyboardButton("🟡 Желтый", callback_data="color_yellow"),
        ],
        [
            InlineKeyboardButton("🔵 Синий", callback_data="color_blue"),
            InlineKeyboardButton("🟣 Фиолетовый", callback_data="color_purple"),
        ],
        [
            InlineKeyboardButton("⚪ Белый", callback_data="color_white"),
            InlineKeyboardButton("🌈 Микс", callback_data="color_mixed"),
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_build")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "🎨 Создание букета - Шаг 1/3\n\n"
        "Выберите основной цвет букета:",
        reply_markup=reply_markup
    )
    
    return BOUQUET_COLOR


async def bouquet_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle color selection."""
    query = update.callback_query
    await query.answer()
    
    color = query.data.replace("color_", "")
    color_names = {
        "red": "🔴 Красный",
        "yellow": "🟡 Желтый",
        "blue": "🔵 Синий",
        "purple": "🟣 Фиолетовый",
        "white": "⚪ Белый",
        "mixed": "🌈 Микс"
    }
    
    context.user_data['bouquet_color'] = color_names.get(color, "🌈 Микс")
    
    # Quantity selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("5 цветов", callback_data="qty_5"),
            InlineKeyboardButton("7 цветов", callback_data="qty_7"),
        ],
        [
            InlineKeyboardButton("11 цветов", callback_data="qty_11"),
            InlineKeyboardButton("15 цветов", callback_data="qty_15"),
        ],
        [
            InlineKeyboardButton("21 цветок", callback_data="qty_21"),
            InlineKeyboardButton("25 цветов", callback_data="qty_25"),
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_build")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"🎨 Создание букета - Шаг 2/3\n\n"
        f"Выбран цвет: {context.user_data['bouquet_color']}\n\n"
        f"Выберите количество цветов:",
        reply_markup=reply_markup
    )
    
    return BOUQUET_QUANTITY


async def bouquet_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity selection."""
    query = update.callback_query
    await query.answer()
    
    qty = query.data.replace("qty_", "")
    context.user_data['bouquet_quantity'] = f"{qty} цветов"
    
    # Add-ons selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("🎀 Лента", callback_data="addon_ribbon"),
            InlineKeyboardButton("📦 Упаковка люкс", callback_data="addon_luxury"),
        ],
        [
            InlineKeyboardButton("🧸 Мягкая игрушка", callback_data="addon_teddy"),
            InlineKeyboardButton("🍫 Конфеты", callback_data="addon_candy"),
        ],
        [InlineKeyboardButton("✅ Без дополнений", callback_data="addon_none")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_build")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"🎨 Создание букета - Шаг 3/3\n\n"
        f"Цвет: {context.user_data['bouquet_color']}\n"
        f"Количество: {context.user_data['bouquet_quantity']}\n\n"
        f"Выберите дополнения:",
        reply_markup=reply_markup
    )
    
    return BOUQUET_ADDONS


async def bouquet_addons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle add-ons selection and generate preview."""
    query = update.callback_query
    await query.answer("Генерируем превью...")
    
    addon = query.data.replace("addon_", "")
    addon_names = {
        "ribbon": "🎀 Лента",
        "luxury": "📦 Упаковка люкс",
        "teddy": "🧸 Мягкая игрушка",
        "candy": "🍫 Конфеты",
        "none": "Без дополнений"
    }
    
    context.user_data['bouquet_addons'] = addon_names.get(addon, "Без дополнений")
    
    # Calculate price
    base_price = 1500
    qty_prices = {"5": 1000, "7": 1500, "11": 2000, "15": 2500, "21": 3000, "25": 3500}
    qty = context.user_data['bouquet_quantity'].split()[0]
    price = qty_prices.get(qty, 2000)
    
    addon_prices = {"ribbon": 200, "luxury": 500, "teddy": 800, "candy": 600, "none": 0}
    price += addon_prices.get(addon, 0)
    
    context.user_data['bouquet_price'] = price
    
    # Generate preview
    bouquet_description = (
        f"💐 Ваш букет:\n\n"
        f"Цвет: {context.user_data['bouquet_color']}\n"
        f"Количество: {context.user_data['bouquet_quantity']}\n"
        f"Дополнения: {context.user_data['bouquet_addons']}\n"
        f"Цена: {price}₽\n"
    )
    
    # Try to generate image preview
    preview_image = await generate_bouquet_preview(context.user_data)
    
    keyboard = [
        [InlineKeyboardButton("🌸 Добавить в корзину", callback_data="add_to_cart")],
        [InlineKeyboardButton("❤️", callback_data="react_heart"), 
         InlineKeyboardButton("👍", callback_data="react_thumbs"),
         InlineKeyboardButton("🎉", callback_data="react_party")],
        [InlineKeyboardButton("🔙 В меню", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if preview_image:
        try:
            await query.message.reply_photo(
                photo=preview_image,
                caption=bouquet_description,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to send preview image: {e}")
            await query.message.reply_text(bouquet_description, reply_markup=reply_markup)
    else:
        await query.message.edit_text(bouquet_description, reply_markup=reply_markup)
    
    return ConversationHandler.END


async def cancel_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel bouquet builder."""
    query = update.callback_query
    await query.answer()
    
    # Clear user data
    context.user_data.clear()
    
    await query.message.edit_text(
        "❌ Создание букета отменено.\n\n"
        "Используйте /start для возврата в главное меню."
    )
    
    return ConversationHandler.END


async def generate_bouquet_preview(bouquet_data: dict) -> BytesIO | None:
    """Generate bouquet preview image using Stable Diffusion or Pillow fallback."""
    
    # Try Stable Diffusion first
    sd_api_url = os.getenv("STABLE_DIFFUSION_API_URL")
    if sd_api_url and WEBUI_AVAILABLE:
        try:
            prompt = f"beautiful flower bouquet, {bouquet_data.get('bouquet_color', 'mixed')} flowers"
            # Note: webuiapi integration would go here
            # For now, skip to Pillow fallback
            pass
        except Exception as e:
            logger.warning(f"Stable Diffusion failed: {e}")
    
    # Pillow fallback - simple colored preview
    if PILLOW_AVAILABLE:
        try:
            # Create simple preview
            width, height = 512, 512
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Map colors
            color_map = {
                "🔴 Красный": (220, 20, 60),
                "🟡 Желтый": (255, 215, 0),
                "🔵 Синий": (65, 105, 225),
                "🟣 Фиолетовый": (138, 43, 226),
                "⚪ Белый": (255, 250, 250),
                "🌈 Микс": (255, 182, 193)
            }
            
            color = bouquet_data.get('bouquet_color', '🌈 Микс')
            fill_color = color_map.get(color, (255, 182, 193))
            
            # Draw a simple flower representation
            # Draw circles to represent flowers
            import random
            random.seed(42)
            
            qty_str = bouquet_data.get('bouquet_quantity', '11 цветов')
            qty = int(qty_str.split()[0])
            
            for _ in range(min(qty, 15)):  # Limit visual flowers
                x = random.randint(100, width - 100)
                y = random.randint(100, height - 100)
                r = random.randint(30, 50)
                draw.ellipse([x-r, y-r, x+r, y+r], fill=fill_color, outline='darkgreen', width=3)
            
            # Add text
            text = f"{bouquet_data.get('bouquet_quantity', '11 цветов')}\n{color}"
            draw.text((20, 20), text, fill='black')
            
            # Save to BytesIO
            bio = BytesIO()
            bio.name = 'bouquet_preview.png'
            img.save(bio, 'PNG')
            bio.seek(0)
            
            return bio
        except Exception as e:
            logger.error(f"Pillow preview generation failed: {e}")
    
    return None


# Create conversation handler for bouquet builder
build_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(build_start, pattern="^build_bouquet$")],
    states={
        BOUQUET_COLOR: [CallbackQueryHandler(bouquet_color, pattern="^color_")],
        BOUQUET_QUANTITY: [CallbackQueryHandler(bouquet_quantity, pattern="^qty_")],
        BOUQUET_ADDONS: [CallbackQueryHandler(bouquet_addons, pattern="^addon_")],
    },
    fallbacks=[CallbackQueryHandler(cancel_build, pattern="^cancel_build$")],
)
