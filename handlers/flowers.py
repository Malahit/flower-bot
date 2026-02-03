from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Existing code

# Updated start function

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    # Updated welcome_text assignment
    welcome_text = f"""👋 Привет, {user.first_name}!

🌸 flower-bot - доставка цветов
✨ AI рекомендации букетов
🎨 Конструктор букетов
💳 Оплата TON Stars

Выберите действие:"""
    await update.message.reply_text(welcome_text)

# Other existing code