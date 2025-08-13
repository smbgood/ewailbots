#!/usr/bin/env python3
"""
Simple runner script for the AI Employee Discord Bot
"""

import sys
import os
import asyncio

# Fix Windows console encoding issues
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from discord_bot import run_bot

def main():
    """Main entry point for the bot"""
    print("Starting AI Employee Discord Bot...")
    
    # Check if required environment variables are set
    required_vars = ['DISCORD_TOKEN', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment.")
        print("See env_example.txt for reference.")
        sys.exit(1)
    
    try:
        # Run the bot
        run_bot()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
