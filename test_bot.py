#!/usr/bin/env python3
"""Simple test script to verify the bot setup."""
import asyncio
import os
import sys
import secrets

# Set test token with randomly generated value
# Format: bot{random_id}:AA{random_hex_32chars}
random_test_bot_token = f"bot{secrets.randbelow(1000000)}:AA{secrets.token_hex(16)}"
os.environ["TELEGRAM_BOT_TOKEN"] = random_test_bot_token
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_flower_bot.db"

async def test_database():
    """Test database initialization."""
    print("🧪 Testing database initialization...")
    from database import init_db, add_sample_flowers, async_session_maker, Flower
    from sqlalchemy import select
    
    # Initialize database
    await init_db()
    print("✓ Database tables created")
    
    # Add sample flowers
    await add_sample_flowers()
    print("✓ Sample flowers added")
    
    # Query flowers
    async with async_session_maker() as session:
        result = await session.execute(select(Flower))
        flowers = result.scalars().all()
        print(f"✓ Found {len(flowers)} flowers in database")
        
        for flower in flowers[:3]:
            print(f"  - {flower.name}: {flower.price}₽")
    
    return True

async def test_handlers():
    """Test handler imports and basic structure."""
    print("\n🧪 Testing handlers...")
    
    from handlers import flowers, orders, admin
    
    # Check required functions exist
    assert hasattr(flowers, 'start'), "flowers.start not found"
    assert hasattr(flowers, 'recommend'), "flowers.recommend not found"
    assert hasattr(flowers, 'build_conversation'), "flowers.build_conversation not found"
    print("✓ flowers.py handlers OK")
    
    assert hasattr(orders, 'add_to_cart'), "orders.add_to_cart not found"
    assert hasattr(orders, 'show_cart'), "orders.show_cart not found"
    assert hasattr(orders, 'pay_ton'), "orders.pay_ton not found"
    print("✓ orders.py handlers OK")
    
    assert hasattr(admin, 'admin_command'), "admin.admin_command not found"
    assert hasattr(admin, 'add_flower_conversation'), "admin.add_flower_conversation not found"
    print("✓ admin.py handlers OK")
    
    return True

async def test_bot_structure():
    """Test bot structure."""
    print("\n🧪 Testing bot structure...")
    
    import bot
    
    assert hasattr(bot, 'main'), "bot.main not found"
    assert hasattr(bot, 'post_init'), "bot.post_init not found"
    print("✓ bot.py structure OK")
    
    return True

async def main():
    """Run all tests."""
    print("=" * 60)
    print("🌸 flower-bot Test Suite")
    print("=" * 60)
    
    try:
        await test_database()
        await test_handlers()
        await test_bot_structure()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
        # Cleanup test database
        if os.path.exists("test_flower_bot.db"):
            os.remove("test_flower_bot.db")
            print("\n🧹 Test database cleaned up")
        
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
