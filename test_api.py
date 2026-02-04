#!/usr/bin/env python3
"""Test script for API endpoints."""
import asyncio
import os
import sys

# Set test environment
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_api_flower_bot.db"

async def test_api_endpoints():
    """Test API endpoints."""
    print("🧪 Testing API endpoints...")
    
    from database import init_db, add_sample_flowers
    from api import app
    from httpx import AsyncClient, ASGITransport
    
    # Initialize database
    await init_db()
    await add_sample_flowers()
    print("✓ Database initialized")
    
    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test root endpoint
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Flower Bot API"
        print("✓ Root endpoint OK")
        
        # Test health check
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("✓ Health check OK")
        
        # Test get all flowers
        response = await client.get("/api/flowers")
        assert response.status_code == 200
        flowers = response.json()
        assert len(flowers) > 0
        assert "id" in flowers[0]
        assert "name" in flowers[0]
        assert "price" in flowers[0]
        print(f"✓ Get all flowers OK (found {len(flowers)} flowers)")
        
        # Test category filtering
        response = await client.get("/api/flowers?category=roses")
        assert response.status_code == 200
        roses = response.json()
        print(f"✓ Category filtering OK (found {len(roses)} roses)")
        
        # Test get specific flower
        if flowers:
            flower_id = flowers[0]["id"]
            response = await client.get(f"/api/flowers/{flower_id}")
            assert response.status_code == 200
            flower = response.json()
            assert flower["id"] == flower_id
            print(f"✓ Get specific flower OK (ID: {flower_id})")
        
        # Test non-existent flower
        response = await client.get("/api/flowers/99999")
        assert response.status_code == 404
        print("✓ Non-existent flower returns 404")
        
        # Test categories endpoint
        response = await client.get("/api/categories")
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) > 0
        assert "category" in categories[0]
        assert "count" in categories[0]
        print(f"✓ Get categories OK (found {len(categories)} categories)")
    
    return True

async def main():
    """Run API tests."""
    print("=" * 60)
    print("🌸 flower-bot API Test Suite")
    print("=" * 60)
    
    try:
        await test_api_endpoints()
        
        print("\n" + "=" * 60)
        print("✅ All API tests passed!")
        print("=" * 60)
        
        # Cleanup test database
        if os.path.exists("test_api_flower_bot.db"):
            os.remove("test_api_flower_bot.db")
            print("\n🧹 Test database cleaned up")
        
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
