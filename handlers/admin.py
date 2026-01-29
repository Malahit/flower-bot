"""Admin handlers for flower management and orders viewing."""
import os
import io
from typing import List
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from sqlalchemy import select, desc
from minio import Minio
from minio.error import S3Error
import base64
from database import async_session_maker, Flower, Order, User

# Admin states for FSM
FLOWER_NAME, FLOWER_DESC, FLOWER_PRICE, FLOWER_CATEGORY, FLOWER_PHOTO = range(5)

# Admin user IDs from environment
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip().isdigit()]


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in ADMIN_IDS or len(ADMIN_IDS) == 0  # Allow all if no admins configured


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command - show admin panel."""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить цветок", callback_data="admin_add_flower")],
        [InlineKeyboardButton("📋 Список цветов", callback_data="admin_list_flowers")],
        [InlineKeyboardButton("📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )


async def admin_list_flowers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all flowers."""
    query = update.callback_query
    await query.answer()
    
    async with async_session_maker() as session:
        result = await session.execute(select(Flower).order_by(Flower.id))
        flowers = result.scalars().all()
        
        if not flowers:
            text = "📋 Цветов в базе нет\n\nИспользуйте 'Добавить цветок' для добавления"
        else:
            text = "📋 Список цветов:\n\n"
            for flower in flowers:
                status = "✅" if flower.available else "❌"
                text += (
                    f"{status} ID: {flower.id}\n"
                    f"   Название: {flower.name}\n"
                    f"   Цена: {flower.price}₽\n"
                    f"   Категория: {flower.category or 'не указана'}\n\n"
                )
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Удалить цветок", callback_data="admin_delete_flower")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup)


async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View all orders."""
    query = update.callback_query
    await query.answer()
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Order).order_by(desc(Order.created_at)).limit(20)
        )
        orders = result.scalars().all()
        
        if not orders:
            text = "📦 Заказов нет"
        else:
            text = "📦 Последние заказы:\n\n"
            for order in orders:
                text += (
                    f"🆔 Заказ #{order.id}\n"
                    f"👤 User ID: {order.user_id}\n"
                    f"💰 Сумма: {order.total_price}₽\n"
                    f"📍 Адрес: {order.delivery_address or 'не указан'}\n"
                    f"📊 Статус: {order.status}\n"
                    f"💳 Оплата: {order.payment_status}\n"
                    f"📅 Дата: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Split message if too long
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (показаны первые заказы)"
    
    await query.message.edit_text(text, reply_markup=reply_markup)


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View all users."""
    query = update.callback_query
    await query.answer()
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).order_by(desc(User.created_at)).limit(20)
        )
        users = result.scalars().all()
        
        if not users:
            text = "👥 Пользователей нет"
        else:
            text = "👥 Последние пользователи:\n\n"
            for user in users:
                username = f"@{user.username}" if user.username else "без username"
                text += (
                    f"🆔 {user.user_id}\n"
                    f"👤 {user.first_name or ''} {user.last_name or ''}\n"
                    f"📝 {username}\n"
                    f"📅 Регистрация: {user.created_at.strftime('%Y-%m-%d')}\n\n"
                )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (показаны первые пользователи)"
    
    await query.message.edit_text(text, reply_markup=reply_markup)


async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Go back to admin panel."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить цветок", callback_data="admin_add_flower")],
        [InlineKeyboardButton("📋 Список цветов", callback_data="admin_list_flowers")],
        [InlineKeyboardButton("📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "🔧 Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )


# Add flower conversation handlers
async def add_flower_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start adding a new flower."""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "➕ Добавление нового цветка\n\n"
        "Шаг 1/5: Введите название цветка:",
        reply_markup=ForceReply(selective=True)
    )
    
    return FLOWER_NAME


async def flower_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process flower name."""
    context.user_data['flower_name'] = update.message.text
    
    await update.message.reply_text(
        "Шаг 2/5: Введите описание цветка:",
        reply_markup=ForceReply(selective=True)
    )
    
    return FLOWER_DESC


async def flower_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process flower description."""
    context.user_data['flower_desc'] = update.message.text
    
    await update.message.reply_text(
        "Шаг 3/5: Введите цену (в рублях):",
        reply_markup=ForceReply(selective=True)
    )
    
    return FLOWER_PRICE


async def flower_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process flower price."""
    try:
        price = float(update.message.text)
        context.user_data['flower_price'] = price
        
        await update.message.reply_text(
            "Шаг 4/5: Введите категорию (roses, tulips, peonies, mixed, другое):",
            reply_markup=ForceReply(selective=True)
        )
        
        return FLOWER_CATEGORY
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат цены. Введите число:",
            reply_markup=ForceReply(selective=True)
        )
        return FLOWER_PRICE


async def flower_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process flower category."""
    context.user_data['flower_category'] = update.message.text
    
    await update.message.reply_text(
        "Шаг 5/5: Отправьте фото цветка (или /skip чтобы пропустить):"
    )
    
    return FLOWER_PHOTO


async def flower_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process flower photo and save to MinIO."""
    photo_url = None
    
    if update.message.photo:
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download photo
        photo_bytes = await file.download_as_bytearray()
        
        # Upload to MinIO
        minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        minio_access = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        minio_secret = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        minio_bucket = os.getenv("MINIO_BUCKET", "flowers")
        
        try:
            # Initialize MinIO client
            client = Minio(
                minio_endpoint,
                access_key=minio_access,
                secret_key=minio_secret,
                secure=False  # Set to True for HTTPS
            )
            
            # Create bucket if it doesn't exist
            if not client.bucket_exists(minio_bucket):
                client.make_bucket(minio_bucket)
            
            # Upload photo
            file_name = f"flower_{context.user_data['flower_name'].replace(' ', '_')}_{photo.file_id}.jpg"
            client.put_object(
                minio_bucket,
                file_name,
                io.BytesIO(photo_bytes),
                length=len(photo_bytes),
                content_type="image/jpeg"
            )
            
            photo_url = f"http://{minio_endpoint}/{minio_bucket}/{file_name}"
            
        except Exception as e:
            # If MinIO fails, use placeholder or Telegram file_id
            photo_url = f"https://api.telegram.org/file/bot{context.bot.token}/{file.file_path}"
    
    # Save flower to database
    async with async_session_maker() as session:
        flower = Flower(
            name=context.user_data['flower_name'],
            description=context.user_data['flower_desc'],
            price=context.user_data['flower_price'],
            category=context.user_data['flower_category'],
            photo_url=photo_url,
            available=True
        )
        session.add(flower)
        await session.commit()
        flower_id = flower.id
    
    await update.message.reply_text(
        f"✅ Цветок добавлен!\n\n"
        f"🆔 ID: {flower_id}\n"
        f"Название: {context.user_data['flower_name']}\n"
        f"Цена: {context.user_data['flower_price']}₽\n"
        f"Категория: {context.user_data['flower_category']}\n"
        f"Фото: {'загружено' if photo_url else 'не загружено'}"
    )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


async def flower_skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip photo upload."""
    # Save flower to database without photo
    async with async_session_maker() as session:
        flower = Flower(
            name=context.user_data['flower_name'],
            description=context.user_data['flower_desc'],
            price=context.user_data['flower_price'],
            category=context.user_data['flower_category'],
            photo_url=None,
            available=True
        )
        session.add(flower)
        await session.commit()
        flower_id = flower.id
    
    await update.message.reply_text(
        f"✅ Цветок добавлен без фото!\n\n"
        f"🆔 ID: {flower_id}\n"
        f"Название: {context.user_data['flower_name']}\n"
        f"Цена: {context.user_data['flower_price']}₽\n"
        f"Категория: {context.user_data['flower_category']}"
    )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


async def add_flower_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel adding flower."""
    await update.message.reply_text(
        "❌ Добавление цветка отменено"
    )
    context.user_data.clear()
    return ConversationHandler.END


# Conversation handler for adding flowers
add_flower_conversation = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^admin_add_flower$"), add_flower_start)
    ],
    states={
        FLOWER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, flower_name)],
        FLOWER_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, flower_desc)],
        FLOWER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, flower_price)],
        FLOWER_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, flower_category)],
        FLOWER_PHOTO: [
            MessageHandler(filters.PHOTO, flower_photo),
            CommandHandler("skip", flower_skip_photo)
        ],
    },
    fallbacks=[CommandHandler("cancel", add_flower_cancel)],
)
