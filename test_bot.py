#!/usr/bin/env python3
"""
Test script for the Discord bot configuration
Run this to verify your setup before running the main bot
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test environment variable loading"""
    print("🔧 Testing Environment Variables...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.strip().split('\n')
                print(f"   📄 File contains {len(lines)} lines")
                
                # Check for common issues
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' not in line:
                            print(f"   ⚠️  Line {i}: Missing '=' separator: {line}")
                        elif line.endswith('='):
                            print(f"   ⚠️  Line {i}: Empty value: {line}")
                        elif ' =' in line or '= ' in line:
                            print(f"   ⚠️  Line {i}: Extra spaces around '=': {line}")
        except Exception as e:
            print(f"   ❌ Error reading .env file: {e}")
    else:
        print("❌ .env file not found")
        print("   💡 Create a .env file based on env_example.txt")
    
    # Load environment variables
    load_dotenv()
    
    # Test required variables
    required_vars = {
        'DISCORD_TOKEN': 'Discord Bot Token',
        'OPENAI_API_KEY': 'OpenAI API Key'
    }
    
    print("\n📋 Required Environment Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show first few characters safely
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var}: {display_value}")
            
            # Validate specific variables
            if var == 'DISCORD_TOKEN':
                validate_discord_token(value)
            elif var == 'OPENAI_API_KEY':
                validate_openai_key(value)
        else:
            print(f"   ❌ {var}: Missing ({description})")
    
    # Test optional variables
    optional_vars = {
        'GUILD_ID': 'Discord Server ID',
        'SUPABASE_URL': 'Supabase Project URL',
        'SUPABASE_ANON_KEY': 'Supabase Anonymous Key',
        'SUPABASE_SERVICE_ROLE_KEY': 'Supabase Service Role Key'
    }
    
    print("\n📋 Optional Environment Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ⚠️  {var}: Not set ({description})")

def validate_discord_token(token):
    """Validate Discord bot token format"""
    print(f"   🔍 Validating Discord token...")
    print(f"      Length: {len(token)} characters")
    print(f"      Starts with: {token[:10]}...")
    print(f"      Ends with: ...{token[-10:]}")
    
    # Check format
    if len(token) < 50:
        print(f"      ❌ Token too short (expected ≥50, got {len(token)})")
        return False
    
    if ' ' in token or '\n' in token:
        print(f"      ❌ Token contains whitespace/newlines")
        return False
    
    if token.lower() in ['your_discord_bot_token_here', 'placeholder', 'example']:
        print(f"      ❌ Token appears to be placeholder value")
        return False
    
    # Check if it looks like a valid Discord token
    if not any(token.startswith(prefix) for prefix in ['MTA', 'MTI', 'OTk']):
        print(f"      ⚠️  Token format doesn't match expected pattern")
        print(f"         Expected: Starts with MTA, MTI, or OTk")
        print(f"         Got: Starts with {token[:3]}")
        return False
    
    print(f"      ✅ Token format appears valid")
    return True

def validate_openai_key(key):
    """Validate OpenAI API key format"""
    print(f"   🔍 Validating OpenAI API key...")
    print(f"      Length: {len(key)} characters")
    print(f"      Starts with: {key[:10]}...")
    print(f"      Ends with: ...{key[-10:]}")
    
    # Check format
    if len(key) < 20:
        print(f"      ❌ Key too short (expected ≥20, got {len(key)})")
        return False
    
    if ' ' in key or '\n' in key:
        print(f"      ❌ Key contains whitespace/newlines")
        return False
    
    if key.lower() in ['your_openai_api_key_here', 'placeholder', 'example']:
        print(f"      ❌ Key appears to be placeholder value")
        return False
    
    # Check if it looks like a valid OpenAI key
    if not key.startswith('sk-'):
        print(f"      ⚠️  Key format doesn't match expected pattern")
        print(f"         Expected: Starts with 'sk-'")
        print(f"         Got: Starts with '{key[:3]}'")
        return False
    
    print(f"      ✅ API key format appears valid")
    return True

def test_dependencies():
    """Test if required dependencies are available"""
    print("\n🧪 Testing Dependencies...")
    
    try:
        import discord
        print(f"   ✅ discord.py: {discord.__version__}")
    except ImportError as e:
        print(f"   ❌ discord.py: {e}")
    
    try:
        import openai
        print(f"   ✅ openai: {openai.__version__}")
    except ImportError as e:
        print(f"   ❌ openai: {e}")
    
    try:
        from dotenv import load_dotenv
        print(f"   ✅ python-dotenv: Available")
    except ImportError as e:
        print(f"   ❌ python-dotenv: {e}")

def main():
    """Main test function"""
    print("🧪 Discord Bot Configuration Test")
    print("=" * 40)
    
    test_environment()
    test_dependencies()
    
    print("\n" + "=" * 40)
    print("🎯 Test Complete!")
    print("\n💡 If you see any ❌ errors above:")
    print("   1. Check your .env file format")
    print("   2. Verify your tokens are correct")
    print("   3. Ensure no extra spaces around '=' in .env")
    print("   4. Check that .env file is in the same directory as this script")

if __name__ == "__main__":
    main()
