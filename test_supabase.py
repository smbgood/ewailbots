#!/usr/bin/env python3
"""
Test script for Supabase database connection
Run this to verify your Supabase setup is working correctly
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_supabase_connection():
    """Test basic Supabase connection and operations"""
    print("🧪 Testing Supabase Connection...")
    
    try:
        # Test import
        from database import DatabaseManager
        print("✅ Database module imported successfully")
        
        # Test connection
        db = DatabaseManager()
        print("✅ Database connection established")
        
        # Test basic operations
        print("\n📊 Testing basic operations...")
        
        # Test creating an AI employee
        test_params = {
            "temperature": 0.8,
            "max_tokens": 1000,
            "model": "gpt-3.5-turbo",
            "personality": "helpful test assistant"
        }
        
        success = await db.create_ai_employee("TestBot", "GENERAL", test_params)
        print(f"✅ Create AI employee: {'Success' if success else 'Failed'}")
        
        # Test retrieving the employee
        employee = await db.get_ai_employee("TestBot")
        if employee:
            print(f"✅ Retrieve AI employee: Success - {employee['name']} ({employee['employee_type']})")
        else:
            print("❌ Retrieve AI employee: Failed")
        
        # Test getting all employees
        employees = await db.get_all_ai_employees()
        print(f"✅ Get all employees: {len(employees)} found")
        
        # Test user permissions
        await db.set_user_permission(12345, 2, 67890)
        perm_level = await db.get_user_permission(12345)
        print(f"✅ User permission test: Level {perm_level}")
        
        # Test conversation logging
        if employee:
            success = await db.log_conversation(
                employee['id'], 12345, 67890, 
                "Hello, test message", "Hello! How can I help you?"
            )
            print(f"✅ Conversation logging: {'Success' if success else 'Failed'}")
        
        print("\n🎉 Supabase connection test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you've installed the requirements: pip install -r requirements.txt")
        return False
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Check your .env file and ensure SUPABASE_URL and SUPABASE_ANON_KEY are set")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Check your Supabase configuration and ensure tables are created")
        return False

def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the key for security
            if 'KEY' in var:
                print(f"✅ {var}: {'*' * 20}{value[-4:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Copy env_example.txt to .env and fill in your Supabase credentials")
        return False
    
    print("✅ All required environment variables are set")
    return True

async def main():
    """Main test function"""
    print("🚀 Supabase Connection Test")
    print("=" * 40)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return
    
    print("\n" + "=" * 40)
    
    # Test Supabase connection
    success = await test_supabase_connection()
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Your Supabase connection is working!")
        print("2. You can now run the main bot: python run_bot.py")
        print("3. Or run the full test suite: python test_bot.py")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env file has correct Supabase credentials")
        print("2. Ensure you've run the migration script in Supabase")
        print("3. Verify your Supabase project is active")
        print("4. Check the SUPABASE_SETUP.md for detailed instructions")

if __name__ == "__main__":
    asyncio.run(main())
