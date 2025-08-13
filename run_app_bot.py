#!/usr/bin/env python3
"""
Runner script for the AI Employee Discord Bot
Uses Discord Application credentials with prefix commands (!help, !ai, etc.)
"""

import sys
import os
import asyncio

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Fix Windows console encoding issues
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from discord_app_bot import run_app_bot

def main():
    """Main entry point for the application bot"""
    print("🚀 Starting AI Employee Discord Application Bot...")
    print("📱 This bot uses Discord Application credentials and prefix commands (!)")
    
    # Check if required environment variables are set
    required_vars = ['DISCORD_APPLICATION_ID', 'DISCORD_CLIENT_SECRET', 'DISCORD_PUBLIC_KEY', 'DISCORD_TOKEN', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Please set these in your .env file or environment.")
        print("📋 See env_example.txt for reference.")
        print("\n🔑 Required Discord Application credentials:")
        print("   - DISCORD_APPLICATION_ID: Your Discord application ID")
        print("   - DISCORD_CLIENT_SECRET: Your Discord application client secret")
        print("   - DISCORD_PUBLIC_KEY: Your Discord application public key")
        print("   - DISCORD_TOKEN: Your Discord bot token (still required for authentication)")
        sys.exit(1)
    
    print("✅ All required environment variables are set")
    print("🔧 Starting Discord Application Bot...")
    
    try:
        # Run the application bot
        run_app_bot()
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running application bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
