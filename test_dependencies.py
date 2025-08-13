#!/usr/bin/env python3
"""
Test script for new dependencies
Run this to verify the new Windows-compatible dependencies work correctly
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_new_dependencies():
    """Test that new dependencies work correctly"""
    print("🧪 Testing New Dependencies...")
    
    try:
        # Test httpx import
        import httpx
        print("✅ httpx imported successfully")
        
        # Test msgspec import
        import msgspec
        print("✅ msgspec imported successfully")
        
        # Test database import
        from database import DatabaseManager
        print("✅ Database module imported successfully")
        
        # Test basic HTTP functionality
        print("\n🌐 Testing HTTP functionality...")
        
        # Test a simple HTTP request
        async with httpx.AsyncClient() as client:
            response = await client.get("https://httpbin.org/get")
            if response.status_code == 200:
                print("✅ HTTP request test successful")
            else:
                print(f"❌ HTTP request test failed: {response.status_code}")
        
        # Test JSON encoding/decoding with msgspec
        print("\n📝 Testing JSON functionality...")
        test_data = {
            "name": "TestBot",
            "type": "GENERAL",
            "active": True,
            "parameters": {"temp": 0.8, "tokens": 1000}
        }
        
        # Encode
        encoded = msgspec.json.encode(test_data)
        print("✅ JSON encoding successful")
        
        # Decode
        decoded = msgspec.json.decode(encoded)
        print("✅ JSON decoding successful")
        
        if decoded == test_data:
            print("✅ Data integrity verified")
        else:
            print("❌ Data integrity check failed")
        
        print("\n🎉 All dependency tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you've installed the new requirements: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Check the error details above")
        return False

async def main():
    """Main test function"""
    print("🚀 Dependency Compatibility Test")
    print("=" * 40)
    
    # Test new dependencies
    success = await test_new_dependencies()
    
    if success:
        print("\n✅ All tests passed! Your new dependencies are working correctly.")
        print("💡 You can now run your Discord bot without the problematic packages.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        print("💡 Make sure you've installed the updated requirements.txt")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
