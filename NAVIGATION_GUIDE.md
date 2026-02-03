# Universal Back Navigation Guide

This document describes the universal back navigation system implemented in the flower-bot.

## Overview

The bot now has a consistent back navigation system across all screens. Every inline keyboard menu includes a "◀️ Назад" (Back) button that returns to the previous screen using a LIFO (Last-In-First-Out) navigation stack.

## Key Features

1. **Navigation Stack**: Tracks user navigation history in `context.user_data["nav_stack"]`
2. **Current Screen**: Maintains current screen ID in `context.user_data["current_screen"]`
3. **Screen Registry**: Maps screen IDs to renderer functions for dynamic navigation
4. **Universal Back Button**: Single "nav_back" callback handler for all back actions

## Implementation Details

### Navigation Module (`handlers/navigation.py`)

The navigation module provides:

- **Screen constants**: Pre-defined screen IDs (e.g., `SCREEN_START`, `SCREEN_AI_MENU`)
- **`register_screen()`**: Register a screen renderer function
- **`push_screen()`**: Push current screen to navigation stack
- **`pop_screen()`**: Pop and return previous screen from stack
- **`handle_nav_back()`**: Global callback handler for back navigation
- **`add_back_button()`**: Helper to add back button to keyboards

### Registered Screens

1. **Main Screens** (flowers.py):
   - `SCREEN_START` - Main menu (/start command)
   - `SCREEN_AI_MENU` - AI recommendation menu
   - `SCREEN_CATALOG` - Flower catalog
   - `SCREEN_CART` - Shopping cart
   - `SCREEN_HISTORY` - Order history
   - `SCREEN_RECOMMEND_PRESETS` - Recommendation presets

2. **Admin Screens** (admin.py):
   - `SCREEN_ADMIN_MAIN` - Admin panel main menu
   - `SCREEN_ADMIN_LIST_FLOWERS` - Flower list
   - `SCREEN_ADMIN_ORDERS` - Orders list
   - `SCREEN_ADMIN_USERS` - Users list

### Navigation Flow Example

```
User flow:
/start → AI Menu → AI Preset (Birthday)
  ↓        ↓         ↓
START    AI_MENU   PRESET_RESULT

Navigation stack progression:
1. START (stack: [])
2. AI_MENU (stack: [START])
3. PRESET_RESULT (stack: [START, AI_MENU])

Pressing Back:
PRESET_RESULT → AI_MENU (stack: [START])
AI_MENU → START (stack: [])
START → START (stack: [] - nowhere to go)
```

## Modified Files

1. **handlers/navigation.py** (NEW)
   - Core navigation system implementation

2. **handlers/flowers.py**
   - Added render functions for all menu screens
   - Updated all callbacks to use navigation system
   - Registered screen renderers
   - Added back buttons to all inline keyboards

3. **handlers/admin.py**
   - Added render functions for admin screens
   - Updated admin callbacks to use navigation system
   - Registered admin screen renderers
   - Added back buttons to admin keyboards

4. **handlers/orders.py**
   - Updated `show_cart()` to include back button

5. **bot.py**
   - Registered missing callback handlers
   - Registered navigation back handler
   - Registered admin screen renderers

## FSM Builder Unchanged

The bouquet builder FSM (Finite State Machine) at `/build` was intentionally left unchanged as it already has its own back navigation system built into the conversation handler states:
- `back_to_color` - Return to color selection
- `back_to_quantity` - Return to quantity selection

These FSM-specific back buttons continue to work as before.

## Testing the Navigation

To test the navigation system:

1. Start the bot with `/start`
2. Navigate through menus: Start → AI Menu → Select a preset
3. Press "◀️ Назад" - should return to AI Menu
4. Press "◀️ Назад" again - should return to Start
5. Try other flows:
   - Start → Catalog → Back
   - Start → Cart → Back
   - Start → History → Back
   - /admin → List Flowers → Back

All screens should now have a visible back button, and pressing it should return to the immediately previous screen.

## Backward Compatibility

- Existing `back_to_start` callback still works but now uses `_render_start_menu()`
- All existing callback_data values preserved
- FSM builder back buttons unchanged
- No breaking changes to business logic
