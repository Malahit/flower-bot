"""Order and cart handlers with payment via TON Stars."""
import json
import os
from typing import Dict, Any, List
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import ContextTypes
import httpx
from yandex_geocoder import Client as YandexGeocoder
from sqlalchemy import select
from database import async_session_maker, Order, User, Flower


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add item to cart."""
    query = update.callback_query
    await query.answer("✅ Добавлено в корзину!")
    
    # Initialize cart if not exists
    if 'cart' not in context.user_data:
        context.user_data['cart'] = []
    
    # Get bouquet data from conversation
    bouquet = {
        'type': 'custom',
        'color': context.user_data.get('bouquet_color', 'Микс'),
        'quantity': context.user_data.get('bouquet_quantity', '11 цветов'),
        'addons': context.user_data.get('bouquet_addons', 'Без дополнений'),
        'price': 2500.0  # Base price
    }
    
    context.user_data['cart'].append(bouquet)
    
    await show_cart(update, context)


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display current cart."""
    cart = context.user_data.get('cart', [])
    
    if not cart:
        text = "🛒 Ваша корзина пуста\n\nИспользуйте /start для выбора цветов"
        keyboard = [[InlineKeyboardButton("🌸 К каталогу", callback_data="start")]]
    else:
        total = sum(item['price'] for item in cart)
        
        text = "🛒 Ваша корзина:\n\n"
        for i, item in enumerate(cart, 1):
            if item['type'] == 'custom':
                text += (
                    f"{i}. Букет на заказ\n"
                    f"   Цвет: {item['color']}\n"
                    f"   Количество: {item['quantity']}\n"
                    f"   Дополнения: {item['addons']}\n"
                    f"   Цена: {item['price']}₽\n\n"
                )
            else:
                text += f"{i}. {item.get('name', 'Букет')} - {item['price']}₽\n"
        
        text += f"\n💰 Итого: {total}₽"
        
        keyboard = [
            [InlineKeyboardButton("📍 Указать адрес доставки", callback_data="request_location")],
            [InlineKeyboardButton("💫 Оплатить TON Stars", callback_data="pay_ton")],
            [InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton("🌸 Продолжить покупки", callback_data="start")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def request_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Request location from user."""
    query = update.callback_query
    await query.answer()
    
    from telegram import KeyboardButton, ReplyKeyboardMarkup
    
    keyboard = [[KeyboardButton("📍 Отправить геолокацию", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await query.message.reply_text(
        "📍 Пожалуйста, отправьте вашу геолокацию для доставки\n\n"
        "Или напишите адрес текстом",
        reply_markup=reply_markup
    )


async def process_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process shared location and resolve address."""
    if update.message.location:
        location = update.message.location
        latitude = location.latitude
        longitude = location.longitude
        
        # Resolve address using Yandex Geocoder
        yandex_key = os.getenv("YANDEX_GEOCODE_API_KEY")
        
        if yandex_key and yandex_key != "your_yandex_key_here":
            try:
                geocoder = YandexGeocoder(yandex_key)
                result = geocoder.coordinates(f"{longitude}, {latitude}")
                address = result[0]['name'] if result else "Адрес не определен"
            except Exception as e:
                address = f"Координаты: {latitude}, {longitude}"
        else:
            # Mock address for demo
            address = f"Москва, ул. Примерная, д. 1 (координаты: {latitude:.4f}, {longitude:.4f})"
        
        context.user_data['delivery_address'] = address
        context.user_data['delivery_coords'] = (latitude, longitude)
        
        await update.message.reply_text(
            f"✅ Адрес доставки:\n{address}\n\n"
            "Используйте /cart для оформления заказа"
        )
    
    elif update.message.text:
        # Text address
        address = update.message.text
        context.user_data['delivery_address'] = address
        context.user_data['delivery_coords'] = None
        
        await update.message.reply_text(
            f"✅ Адрес доставки:\n{address}\n\n"
            "Используйте /cart для оформления заказа"
        )


async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear shopping cart."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['cart'] = []
    
    await query.message.edit_text(
        "🗑️ Корзина очищена\n\n"
        "Используйте /start для выбора цветов"
    )


async def pay_ton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process payment via TON Stars."""
    query = update.callback_query
    await query.answer()
    
    cart = context.user_data.get('cart', [])
    if not cart:
        await query.message.edit_text("❌ Корзина пуста")
        return
    
    total = sum(item['price'] for item in cart)
    
    # Check if address is set
    if 'delivery_address' not in context.user_data:
        await query.message.edit_text(
            "❌ Сначала укажите адрес доставки\n\n"
            "Используйте кнопку 'Указать адрес доставки'"
        )
        return
    
    # Create order in database
    user = update.effective_user
    
    async with async_session_maker() as session:
        # Ensure user exists
        result = await session.execute(
            select(User).where(User.user_id == user.id)
        )
        db_user = result.scalars().first()
        
        if not db_user:
            db_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(db_user)
            await session.flush()
        
        # Create order
        coords = context.user_data.get('delivery_coords', (None, None))
        order = Order(
            user_id=user.id,
            bouquet_json=json.dumps(cart, ensure_ascii=False),
            total_price=total,
            delivery_address=context.user_data.get('delivery_address'),
            geo_latitude=coords[0] if coords else None,
            geo_longitude=coords[1] if coords else None,
            status='pending',
            payment_status='unpaid',
            payment_method='ton_stars'
        )
        session.add(order)
        await session.commit()
        
        order_id = order.id
    
    # For TON Stars payment, we would use the Telegram Payment API
    # This is a simplified version
    
    try:
        # Create invoice
        title = f"Заказ #{order_id}"
        description = f"Оплата заказа на сумму {total}₽"
        payload = f"order_{order_id}"
        
        # TON Stars uses XTR currency
        prices = [LabeledPrice(label="Букет", amount=int(total * 100))]  # Amount in smallest currency unit
        
        # Note: For real TON Stars implementation, you need to configure payment provider
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Empty for TON Stars
            currency="XTR",  # TON Stars currency
            prices=prices
        )
        
        await query.message.edit_text(
            f"💫 Счет на оплату создан\n\n"
            f"Заказ #{order_id}\n"
            f"Сумма: {total}₽\n\n"
            f"Адрес доставки:\n{context.user_data.get('delivery_address')}\n\n"
            "Следуйте инструкциям для оплаты"
        )
        
    except Exception as e:
        # Fallback to simple confirmation
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить заказ", callback_data=f"confirm_order_{order_id}")],
            [InlineKeyboardButton("❌ Отменить", callback_data="clear_cart")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"💫 Заказ #{order_id} создан\n\n"
            f"Сумма: {total}₽\n"
            f"Адрес доставки:\n{context.user_data.get('delivery_address')}\n\n"
            "Нажмите 'Подтвердить заказ' для продолжения",
            reply_markup=reply_markup
        )


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm order after payment."""
    query = update.callback_query
    await query.answer()
    
    # Extract order_id from callback_data
    order_id = int(query.data.split('_')[-1])
    
    # Update order status
    async with async_session_maker() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalars().first()
        
        if order:
            order.status = 'paid'
            order.payment_status = 'paid'
            await session.commit()
    
    # Clear cart
    context.user_data['cart'] = []
    context.user_data.pop('delivery_address', None)
    context.user_data.pop('delivery_coords', None)
    
    await query.message.edit_text(
        f"✅ Заказ #{order_id} подтвержден!\n\n"
        "Мы приступили к сборке вашего букета.\n"
        "Доставка в течение 2-3 часов.\n\n"
        "Спасибо за заказ! 🌸"
    )


async def cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cart command."""
    await show_cart(update, context)
