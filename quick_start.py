#!/usr/bin/env python3
"""
Quick start script for AI Employee Discord Bot
Creates sample employees and sets up basic configuration
"""

import asyncio
import json
import os
from employee_manager import EmployeeManager
from database import DatabaseManager

async def create_sample_employees():
    """Create sample AI employees for quick start"""
    print("Setting up sample AI employees...")
    
    manager = EmployeeManager()
    
    # Sample employee configurations
    sample_employees = [
        {
            "name": "Darah",
            "type": "SUPPORT",
            "parameters": {
                "temperature": 0.8,
                "max_tokens": 1000,
                "model": "gpt-5.5-mini",
                "personality": "friendly, empathetic, and patient customer support specialist",
                
            }
        },
        {
            "name": "Elody",
            "type": "SALES",
            "parameters": {
                "temperature": 0.9,
                "max_tokens": 1200,
                "model": "gpt-5.5-mini",
                "personality": "enthusiastic, persuasive, and knowledgeable sales representative",
                
            }
        },
        {
            "name": "Yusera",
            "type": "TECH",
            "parameters": {
                "temperature": 0.6,
                "max_tokens": 1500,
                "model": "gpt-5.5-mini",
                "personality": "technical, precise, and methodical IT support specialist"
            }
        }
    ]
    
    # Create employees
    results = await manager.bulk_create_employees(sample_employees)
    
    print("\nSample Employee Creation Results:")
    for name, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"{status}: {name}")
    
    return results

async def setup_basic_permissions():
    """Set up basic permission structure"""
    print("\nSetting up basic permissions...")
    
    db = DatabaseManager()
    
    # Set up some example permissions (you'll need to replace with actual user IDs)
    print("Note: You'll need to manually set permissions for specific users.")
    print("Use the !set_permission command once the bot is running.")
    
    return True

async def show_next_steps():
    """Show next steps for the user"""
    print("\nNext Steps:")
    print("1. Sample employees created successfully!")
    print("2. Configure your Discord bot token and OpenAI API key")
    print("3. Run the bot with: python run_bot.py")
    print("4. Add your Discord user ID to ADMIN_USER_IDS in config.py")
    print("5. Test the bot with: !ai list")
    print("\nAvailable Commands:")
    print("• !ai create <name> <role> <personality>")
    print("• !ai list")
    print("• !ai info <name>")
    print("• !chat message <employee> <message>")
    print("• !ai help")
    print("\nQuick Test:")
    print("Once running, try: @Darah Hello! How can you help me?")

async def main():
    """Main quick start function"""
    print("AI Employee Discord Bot - Quick Start")
    print("=" * 50)
    
    try:
        # Create sample employees
        results = await create_sample_employees()
        
        # Set up basic permissions
        await setup_basic_permissions()
        
        # Show next steps
        await show_next_steps()
        
        print("\nQuick start completed successfully!")
        
    except Exception as e:
        print(f"\nQuick start failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
