"""Universal back navigation helper for the bot."""
import logging
from typing import Callable, Dict, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Screen ID constants
SCREEN_START = "start"
SCREEN_AI_MENU = "ai_menu"
SCREEN_CATALOG = "catalog"
SCREEN_CART = "cart"
SCREEN_HISTORY = "history"
SCREEN_RECOMMEND_PRESETS = "recommend_presets"
SCREEN_ADMIN_MAIN = "admin_main"
SCREEN_ADMIN_LIST_FLOWERS = "admin_list_flowers"
SCREEN_ADMIN_ORDERS = "admin_orders"
SCREEN_ADMIN_USERS = "admin_users"

# Registry mapping screen IDs to renderer functions
_screen_registry: Dict[str, Callable] = {}


def register_screen(screen_id: str, renderer: Callable) -> None:
    """Register a screen renderer function.
    
    Args:
        screen_id: Unique identifier for the screen
        renderer: Async function that renders the screen (takes update, context)
    """
    _screen_registry[screen_id] = renderer
    logger.debug(f"Registered screen: {screen_id}")


def push_screen(context: ContextTypes.DEFAULT_TYPE, screen_id: str) -> None:
    """Push current screen to navigation stack.
    
    Args:
        context: The context object
        screen_id: ID of the screen being navigated from
    """
    if "nav_stack" not in context.user_data:
        context.user_data["nav_stack"] = []
    
    current = context.user_data.get("current_screen")
    if current and current != screen_id:
        # Only push if it's different from the target screen (avoid duplicates)
        context.user_data["nav_stack"].append(current)
        logger.debug(f"Pushed {current} to stack, navigating to {screen_id}")
    
    context.user_data["current_screen"] = screen_id


def pop_screen(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    """Pop previous screen from navigation stack.
    
    Args:
        context: The context object
        
    Returns:
        Screen ID to navigate to, or None if stack is empty
    """
    if "nav_stack" not in context.user_data:
        context.user_data["nav_stack"] = []
    
    stack = context.user_data["nav_stack"]
    if stack:
        previous = stack.pop()
        context.user_data["current_screen"] = previous
        logger.debug(f"Popped {previous} from stack")
        return previous
    
    # If stack is empty, go to start
    context.user_data["current_screen"] = SCREEN_START
    return SCREEN_START


async def handle_nav_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global navigation back handler.
    
    This handler pops the previous screen from the stack and re-renders it.
    """
    query = update.callback_query
    await query.answer()
    
    # Get previous screen
    previous_screen = pop_screen(context)
    
    if not previous_screen:
        previous_screen = SCREEN_START
    
    # Get renderer function
    renderer = _screen_registry.get(previous_screen)
    
    if renderer:
        try:
            await renderer(update, context)
        except Exception as e:
            logger.error(f"Error rendering screen {previous_screen}: {e}")
            await query.edit_message_text(
                "❌ Ошибка навигации. Используйте /start для возврата в главное меню."
            )
    else:
        logger.warning(f"No renderer found for screen: {previous_screen}")
        await query.edit_message_text(
            "❌ Ошибка навигации. Используйте /start для возврата в главное меню."
        )


def add_back_button(
    keyboard: list,
    callback_data: str = "nav_back",
    text: str = "◀️ Назад"
) -> list:
    """Add a back button to an inline keyboard.
    
    Args:
        keyboard: List of button rows
        callback_data: Callback data for the back button
        text: Button text
        
    Returns:
        Updated keyboard with back button added
    """
    keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    return keyboard
