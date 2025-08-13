import discord
from discord.ext import commands
import asyncio
from typing import Optional, Dict, Any
from config import Config
from employee_manager import EmployeeManager
from database import DatabaseManager
import json
import os
import aiohttp

class AIEmployeeAppBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        # Use prefix commands with '!'
        super().__init__(command_prefix='!', intents=intents)
        
        self.employee_manager = EmployeeManager()
        self.db = DatabaseManager()
        self.http_session = None
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        print(f"Logged in as {self.user}")
        
        # Create HTTP session for API calls
        self.http_session = aiohttp.ClientSession()
        
        # Load prefix command cogs
        await self.load_extension('commands')
        
        # Load existing employees
        await self.employee_manager.load_existing_employees()
        print("AI Employees loaded successfully!")
        
        # Application slash command syncing removed; using prefix commands now
        
    async def close(self):
        """Clean up resources when bot shuts down"""
        if self.http_session:
            await self.http_session.close()
        await super().close()
        
    async def on_ready(self):
        """Called when the bot is ready"""
        print(f"Bot is ready! Serving {len(self.guilds)} guild(s)")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                        name="AI Employees | !help"
            )
        )
        
        # Send hello world message to #general channel
        await self.send_hello_message()
    
    async def send_hello_message(self):
        """Send a hello world message to the #general channel"""
        try:
            for guild in self.guilds:
                # Find the general channel
                general_channel = discord.utils.get(guild.channels, name='general')
                
                if general_channel and isinstance(general_channel, discord.TextChannel):
                    embed = discord.Embed(
                        title="🤖 Bot Online!",
                        description="Hello World! The AI Employee Bot is now online and ready to help!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Commands", value="Use `!help` to see available commands", inline=False)
                    embed.set_footer(text="AI Employee Bot")
                    
                    await general_channel.send(embed=embed)
                    print(f"✅ Hello message sent to #{general_channel.name} in {guild.name}")
                    break  # Only send to the first guild's general channel
                else:
                    print(f"⚠️  #general channel not found in {guild.name}")
                    
        except Exception as e:
            print(f"❌ Error sending hello message: {e}")
    
    async def check_permissions(self, interaction_or_ctx, required_level: int) -> bool:
        """Check if user has required permission level (works for both ctx and interaction)"""
        # Support both discord.Interaction and commands.Context
        user_obj = getattr(interaction_or_ctx, 'user', None) or getattr(interaction_or_ctx, 'author', None)
        user_id = getattr(user_obj, 'id', None)
        
        # Check if user is in admin list
        if user_id in Config.ADMIN_USER_IDS:
            return True
        
        # Check database permissions
        user_level = await self.db.get_user_permission(user_id)
        return user_level >= required_level
    
    async def send_message_as_employee(self, channel, employee_name: str, 
                                     message_content: str, user_id: int):
        """Send a message as an AI employee"""
        try:
            # Get employee
            employee = await self.employee_manager.get_employee(employee_name)
            if not employee:
                await channel.send(f"❌ Employee '{employee_name}' not found!")
                return
            
            # Generate response
            response = await employee.generate_response(message_content)
            
            # Create embed
            embed = discord.Embed(
                title=f"💬 {employee_name}",
                description=response,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"AI Employee • {employee_name}")
            
            await channel.send(embed=embed)
            
            # Log conversation (don't notify user if logging fails)
            try:
                await self.db.log_conversation(
                    employee.id,
                    user_id,
                    channel.id,
                    message_content,
                    response
                )
            except Exception as log_error:
                print(f"Error logging conversation: {log_error}")
            
        except Exception as e:
            print(f"Error sending message as employee: {e}")
            await channel.send(f"❌ An error occurred while processing your request.")

# Create bot instance
bot = AIEmployeeAppBot()

# Run the bot using application credentials
def run_app_bot():
    """Run the Discord bot using application credentials"""
    print("🔍 Validating Discord application credentials...")
    
    # Check if application credentials exist
    if not Config.DISCORD_APPLICATION_ID:
        print("❌ DISCORD_APPLICATION_ID not found in environment variables!")
        print("💡 Please check your .env file or environment variables.")
        return
    
    if not Config.DISCORD_CLIENT_SECRET:
        print("❌ DISCORD_CLIENT_SECRET not found in environment variables!")
        print("💡 Please check your .env file or environment variables.")
        return
    
    if not Config.DISCORD_PUBLIC_KEY:
        print("❌ DISCORD_PUBLIC_KEY not found in environment variables!")
        print("💡 Please check your .env file or environment variables.")
        return
    
    print("✅ Discord application credentials found")
    print(f"📱 Application ID: {Config.DISCORD_APPLICATION_ID}")
    print(f"🔑 Client Secret: {'*' * len(Config.DISCORD_CLIENT_SECRET)}")
    print(f"🔐 Public Key: {'*' * len(Config.DISCORD_PUBLIC_KEY)}")
    
    # Check if we have a token for authentication
    if not Config.DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is required for bot authentication!")
        print("💡 Even with application credentials, you still need a bot token.")
        print("   Please add DISCORD_TOKEN to your .env file.")
        return
    
    print("✅ Bot token found for authentication")
    print("🚀 Attempting to connect to Discord...")
    
    try:
        bot.run(Config.DISCORD_TOKEN)
    except discord.LoginFailure as e:
        print(f"❌ Discord login failed: {e}")
        print("💡 This usually means:")
        print("   - The token is invalid or expired")
        print("   - The bot has been deleted from Discord Developer Portal")
        print("   - The token was copied incorrectly")
        print("🔍 Please verify your token at: https://discord.com/developers/applications")
    except discord.HTTPException as e:
        print(f"❌ Discord HTTP error: {e}")
        print("💡 This could indicate:")
        print("   - Network connectivity issues")
        print("   - Discord API rate limiting")
        print("   - Invalid token format")
    except Exception as e:
        print(f"❌ Unexpected error running bot: {e}")
        print(f"💡 Error type: {type(e).__name__}")

if __name__ == "__main__":
    run_app_bot()
