#!/usr/bin/env python3
"""Test bouquet builder flow improvements."""
import asyncio
import os

# Set a clearly dummy test token (not a real Telegram bot token)
os.environ["TELEGRAM_BOT_TOKEN"] = "TEST_TELEGRAM_BOT_TOKEN"

async def test_bouquet_flow():
    """Test the bouquet builder conversation flow."""
    print("🧪 Testing bouquet builder flow...")
    
    from handlers import flowers
    from telegram.ext import Application
    
    # Create a test application
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(token).build()
    
    # Register handlers
    flowers.main_handlers(application)
    
    # Verify build_conversation is now initialized
    assert flowers.build_conversation is not None, "build_conversation should be initialized after main_handlers"
    print("✓ build_conversation initialized")
    
    # Verify conversation states
    assert flowers.CHOOSE_COLOR in flowers.build_conversation.states, "CHOOSE_COLOR state missing"
    assert flowers.CHOOSE_QUANTITY in flowers.build_conversation.states, "CHOOSE_QUANTITY state missing"
    assert flowers.CHOOSE_ADDONS in flowers.build_conversation.states, "CHOOSE_ADDONS state missing"
    print("✓ All conversation states configured")
    
    # Verify CHOOSE_QUANTITY has CallbackQueryHandlers
    quantity_handlers = flowers.build_conversation.states[flowers.CHOOSE_QUANTITY]
    callback_handlers = [h for h in quantity_handlers if hasattr(h, 'pattern')]
    assert len(callback_handlers) >= 2, "CHOOSE_QUANTITY should have CallbackQueryHandlers"
    print(f"✓ CHOOSE_QUANTITY has {len(callback_handlers)} CallbackQueryHandlers")
    
    # Verify CHOOSE_ADDONS has CallbackQueryHandlers
    addons_handlers = flowers.build_conversation.states[flowers.CHOOSE_ADDONS]
    callback_handlers = [h for h in addons_handlers if hasattr(h, 'pattern')]
    assert len(callback_handlers) >= 3, "CHOOSE_ADDONS should have at least 3 CallbackQueryHandlers"
    print(f"✓ CHOOSE_ADDONS has {len(callback_handlers)} CallbackQueryHandlers")
    
    # Test addons keyboard builder
    print("\n🧪 Testing addons keyboard builder...")
    
    # Empty selection
    keyboard = flowers._build_addons_keyboard([])
    assert len(keyboard) == len(flowers.VALID_ADDONS) + 1, "Keyboard should have addon buttons + navigation row"
    print(f"✓ Empty selection keyboard has {len(keyboard)} rows")
    
    # With one addon selected
    keyboard = flowers._build_addons_keyboard(['🎀 Лента'])
    addon_buttons = keyboard[:-1]  # All except last row (navigation)
    selected = [btn[0].text for btn in addon_buttons if '✓' in btn[0].text]
    assert len(selected) == 1, "Should have 1 selected addon"
    assert '✓ 🎀 Лента' in selected[0], "Selected addon should have checkmark"
    print(f"✓ Keyboard shows {len(selected)} selected addon(s)")
    
    # With multiple addons selected
    keyboard = flowers._build_addons_keyboard(['🎀 Лента', '🍫 Шоколад'])
    addon_buttons = keyboard[:-1]
    selected = [btn[0].text for btn in addon_buttons if '✓' in btn[0].text]
    assert len(selected) == 2, "Should have 2 selected addons"
    print(f"✓ Keyboard shows {len(selected)} selected addons")
    
    # Verify navigation buttons
    nav_row = keyboard[-1]
    assert len(nav_row) == 2, "Navigation row should have 2 buttons"
    assert nav_row[0].callback_data == "back_to_quantity", "First nav button should be back"
    assert nav_row[1].callback_data == "addons_done", "Second nav button should be done"
    print("✓ Navigation buttons (Back/Done) present")
    
    # Verify valid options are enforced
    assert all(c in flowers.VALID_COLORS for c in ['🔴', '🟢', '🔵', '🟡', '⚪']), "Valid colors defined"
    assert all(q in flowers.VALID_QUANTITIES for q in [5, 7, 11, 15, 21, 25]), "Valid quantities defined"
    assert all(a in flowers.VALID_ADDONS for a in ['🎀 Лента', '📦 Упаковка', '🍫 Шоколад', '🧸 Игрушка']), "Valid addons defined"
    print("✓ All valid options are properly defined")
    
    print("\n✅ All bouquet builder flow tests passed!")
    return True

async def main():
    """Run all tests."""
    print("=" * 60)
    print("🌸 Bouquet Builder Flow Test Suite")
    print("=" * 60)
    
    try:
        await test_bouquet_flow()
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
