#!/usr/bin/env python3
"""
Windows-specific launcher for the AI Employee Discord Bot
Handles UTF-8 encoding issues on Windows
"""

import sys
import os
import asyncio

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    # Set environment variable for Python
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # Reconfigure stdout and stderr for UTF-8
    import codecs
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    if hasattr(sys.stderr, 'detach'):
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from discord_bot import run_bot

def main():
    """Main entry point for the bot"""
    print("Starting AI Employee Discord Bot...")
    
    # Check if required environment variables are set
    required_vars = ['DISCORD_TOKEN', 'OPENAI_API_KEY']
    missing_vars = []
    
    print("🔍 Checking environment variables...")
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"   ❌ {var}: Missing")
        else:
            # Show first few characters safely
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment.")
        print("See env_example.txt for reference.")
        
        # Additional debugging info
        print("\n🔍 Debug information:")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   .env file exists: {os.path.exists('.env')}")
        if os.path.exists('.env'):
            print(f"   .env file size: {os.path.getsize('.env')} bytes")
        
        sys.exit(1)
    
    print("✅ All required environment variables are set")
    
    try:
        # Run the bot
        run_bot()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        print(f"💡 Error type: {type(e).__name__}")
        sys.exit(1)

if __name__ == "__main__":
    main()
