from telebot import types


# Utility function to create inline buttons

def create_inline_buttons() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    
    # Updated buttons
    birthday_button = types.InlineKeyboardButton("🎉 День рождения", callback_data="birthday")
    repeat_order_button = types.InlineKeyboardButton("🕒 Повторить заказ", callback_data="repeat_order")
    anniversary_button = types.InlineKeyboardButton("💍 Годовщина", callback_data="anniversary")
    apology_button = types.InlineKeyboardButton("😔 Извинение & Благодарность", callback_data="apology")
    
    # Adding buttons to keyboard
    keyboard.add(birthday_button)
    keyboard.add(repeat_order_button)
    keyboard.add(anniversary_button)
    keyboard.add(apology_button)
    
    return keyboard


# Other parts of the code remain unchanged
