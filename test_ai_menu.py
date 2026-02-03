#!/usr/bin/env python3
"""Test script for AI-enhanced start menu functionality."""
import asyncio
import os
import sys

# Set test token
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_ai_menu.db"

async def test_ai_menu_handlers():
    """Test AI menu handlers exist and are properly configured."""
    print("🧪 Testing AI menu handlers...")
    
    from handlers import flowers
    
    # Check new handlers exist
    assert hasattr(flowers, 'handle_ai_callback'), "handle_ai_callback not found"
    assert hasattr(flowers, 'handle_ai_menu_callback'), "handle_ai_menu_callback not found"
    assert hasattr(flowers, 'handle_catalog_callback'), "handle_catalog_callback not found"
    assert hasattr(flowers, 'handle_cart_callback'), "handle_cart_callback not found"
    assert hasattr(flowers, 'handle_history_callback'), "handle_history_callback not found"
    assert hasattr(flowers, 'handle_build_start_callback'), "handle_build_start_callback not found"
    assert hasattr(flowers, 'handle_back_to_start_callback'), "handle_back_to_start_callback not found"
    print("✓ All new callback handlers exist")
    
    return True

async def test_database_helpers():
    """Test database helper functions."""
    print("\n🧪 Testing database helpers...")
    
    from database import (
        init_db, 
        add_sample_flowers, 
        get_user, 
        get_popular_flower, 
        get_user_last_order, 
        format_order_summary,
        async_session_maker,
        User,
        Order
    )
    import json
    
    # Initialize database
    await init_db()
    await add_sample_flowers()
    print("✓ Database initialized")
    
    # Test get_popular_flower
    flower = await get_popular_flower()
    assert flower is not None, "get_popular_flower returned None"
    assert flower.name, "Flower has no name"
    assert flower.photo_url, "Flower has no photo_url"
    print(f"✓ get_popular_flower: {flower.name}")
    
    # Test get_user (should return None for non-existent user)
    user = await get_user(999999)
    assert user is None, "get_user should return None for non-existent user"
    print("✓ get_user returns None for non-existent user")
    
    # Create a test user
    async with async_session_maker() as session:
        test_user = User(
            user_id=12345,
            username="testuser",
            first_name="Test",
            preferred_colors="красные",
            preferred_budget=2000.0
        )
        session.add(test_user)
        await session.commit()
    
    # Test get_user (should return the created user)
    user = await get_user(12345)
    assert user is not None, "get_user returned None for existing user"
    assert user.username == "testuser", "User data incorrect"
    assert user.preferred_colors == "красные", "User preferences incorrect"
    print("✓ get_user returns correct user data")
    
    # Test get_user_last_order (should return None for user with no orders)
    last_order = await get_user_last_order(12345)
    assert last_order is None, "get_user_last_order should return None when no orders"
    print("✓ get_user_last_order returns None when no orders")
    
    # Create a test order
    async with async_session_maker() as session:
        test_order = Order(
            user_id=12345,
            bouquet_json=json.dumps([{"name": "Розы", "quantity": "11 шт"}]),
            total_price=2500.0,
            status="delivered"
        )
        session.add(test_order)
        await session.commit()
    
    # Test get_user_last_order (should return the created order)
    last_order = await get_user_last_order(12345)
    assert last_order is not None, "get_user_last_order returned None"
    assert last_order.total_price == 2500.0, "Order price incorrect"
    print("✓ get_user_last_order returns correct order")
    
    # Test format_order_summary
    summary = format_order_summary(last_order)
    assert "Розы" in summary, "Order summary doesn't contain flower name"
    print(f"✓ format_order_summary: {summary}")
    
    return True

async def test_start_handler():
    """Test that start handler is updated."""
    print("\n🧪 Testing start handler...")
    
    from handlers import flowers
    import inspect
    
    # Check that start handler uses new imports
    source = inspect.getsource(flowers.start)
    assert "get_user" in source, "start handler doesn't use get_user"
    assert "get_popular_flower" in source, "start handler doesn't use get_popular_flower"
    assert "get_user_last_order" in source, "start handler doesn't use get_user_last_order"
    assert "reply_photo" in source, "start handler doesn't use reply_photo"
    print("✓ start handler uses new helper functions")
    
    # Check that it has the new inline keyboard structure
    assert "ai_menu" in source, "start handler missing ai_menu callback"
    assert "catalog" in source, "start handler missing catalog callback"
    assert "cart" in source, "start handler missing cart callback"
    assert "history" in source, "start handler missing history callback"
    assert "build_start" in source, "start handler missing build_start callback"
    assert "ai:occasion:birthday" in source, "start handler missing AI preset callbacks"
    print("✓ start handler has new inline keyboard structure")
    
    return True

async def test_recommendation_flow():
    """Test that AI recommendation flow works."""
    print("\n🧪 Testing AI recommendation flow...")
    
    from handlers import flowers
    
    # Test _generate_recommendation still exists and works
    recommendation = await flowers._generate_recommendation("birthday", "2000")
    assert recommendation, "_generate_recommendation returned empty string"
    assert "birthday" in recommendation.lower() or "день рождения" in recommendation.lower(), \
        "Recommendation doesn't mention occasion"
    print("✓ _generate_recommendation works")
    
    return True

async def main():
    """Run all tests."""
    print("=" * 60)
    print("🌸 AI-Enhanced Start Menu Test Suite")
    print("=" * 60)
    
    try:
        await test_ai_menu_handlers()
        await test_database_helpers()
        await test_start_handler()
        await test_recommendation_flow()
        
        print("\n" + "=" * 60)
        print("✅ All AI menu tests passed!")
        print("=" * 60)
        
        # Cleanup test database
        if os.path.exists("test_ai_menu.db"):
            os.remove("test_ai_menu.db")
            print("\n🧹 Test database cleaned up")
        
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
