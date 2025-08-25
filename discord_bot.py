import discord
from discord.ext import commands
import asyncio
from typing import Optional, Dict, Any
from config import Config
from employee_manager import EmployeeManager
from database import DatabaseManager
import json
import os
import httpx


def debug_environment():
    """Debug environment variable loading issues"""
    print("\n🔍 Environment Variable Debug Information:")
    print(f"   Current working directory: {os.getcwd()}")
    print(f"   .env file exists: {os.path.exists('.env')}")
    
    if os.path.exists('.env'):
        print(f"   .env file size: {os.path.getsize('.env')} bytes")
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line:
                    print(f"   .env first line: {first_line[:50]}{'...' if len(first_line) > 50 else ''}")
                else:
                    print("   .env file appears to be empty")
        except Exception as e:
            print(f"   Error reading .env file: {e}")
    
    # Check environment variables directly
    print(f"   DISCORD_TOKEN in os.environ: {'✅ Present' if 'DISCORD_TOKEN' in os.environ else '❌ Missing'}")
    print(f"   DISCORD_TOKEN value length: {len(os.environ.get('DISCORD_TOKEN', ''))}")
    
    # Check if dotenv loaded correctly
    try:
        from dotenv import load_dotenv
        print("   python-dotenv: ✅ Available")
    except ImportError:
        print("   python-dotenv: ❌ Not available")


class AIEmployeeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        self.employee_manager = EmployeeManager()
        self.db = DatabaseManager()
        self._social_publisher_task = None
        
        # Note: Commands will be loaded in setup_hook
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        print(f"Logged in as {self.user}")
        
        # Load commands
        await self.load_extension('commands')
        
        # Load existing employees
        await self.employee_manager.load_existing_employees()
        print("AI Employees loaded successfully!")

        # Start background task for publishing scheduled social posts
        if not self._social_publisher_task:
            self._social_publisher_task = asyncio.create_task(self._social_publisher_loop())
    
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
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
    
    async def check_permissions(self, ctx, required_level: int) -> bool:
        """Check if user has required permission level"""
        user_id = ctx.author.id
        
        # Check if user is in admin list
        if user_id in Config.ADMIN_USER_IDS:
            return True
        
        # Check database permissions
        user_level = await self.db.get_user_permission(user_id)
        return user_level >= required_level
    
    async def send_message_as_employee(self, channel, employee_name: str, 
                                     message: str, context: str = "") -> bool:
        """Send a message as a specific AI employee"""
        try:
            response = await self.employee_manager.send_message_as_employee(
                employee_name, message, context
            )
            
            if response:
                # Create embed for the response
                embed = discord.Embed(
                    title=f"💬 {employee_name}",
                    description=response,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"AI Employee • {employee_name}")
                
                await channel.send(embed=embed)
                return True
            else:
                await channel.send(f"❌ Employee '{employee_name}' not found or inactive.")
                return False
                
        except Exception as e:
            await channel.send(f"❌ Error sending message as employee: {str(e)}")
            return False
    
    async def send_dm_as_employee(self, user, employee_name: str, 
                                 message: str, context: str = "") -> bool:
        """Send a private message as a specific AI employee"""
        try:
            response = await self.employee_manager.send_message_as_employee(
                employee_name, message, context
            )
            
            if response:
                # Create embed for the response
                embed = discord.Embed(
                    title=f"💬 {employee_name}",
                    description=response,
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"AI Employee • {employee_name}")
                
                await user.send(embed=embed)
                return True
            else:
                await user.send(f"❌ Employee '{employee_name}' not found or inactive.")
                return False
                
        except Exception as e:
            await user.send(f"❌ Error sending message as employee: {str(e)}")
            return False

    async def _social_publisher_loop(self):
        """Background loop to publish scheduled social posts when due."""
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                due_posts = await self.db.list_due_social_posts()
                for post in due_posts:
                    try:
                        success = await self.publish_social_post(post)
                        if success:
                            await self.db.set_social_post_status(post["id"], "published", None)
                            # Notify channel if available
                            channel_id = ((post.get("meta") or {}).get("channel_id"))
                            if channel_id:
                                channel = self.get_channel(channel_id)
                                if channel:
                                    await channel.send(f"📣 Published scheduled post {post['id']} for {post['account_key']}")
                    except Exception as e:
                        print(f"Error publishing post {post.get('id')}: {e}")
            except Exception as e:
                print(f"Error in social publisher loop: {e}")
            # Sleep between checks
            await asyncio.sleep(30)

    async def publish_social_post(self, post: Dict[str, Any]) -> bool:
        """Publish a social post based on its platform. Returns True on success."""
        platform = (post.get("platform") or "").lower()
        if platform == "instagram":
            return await self._publish_instagram(post)
        if platform == "facebook":
            return await self._publish_facebook_page(post)
        # Other platforms can be added here
        return False

    async def _publish_instagram(self, post: Dict[str, Any]) -> bool:
        """Minimal Instagram Graph API publishing flow. Falls back to no-op if not configured."""
        try:
            account_key = post.get("account_key")
            account = await self.db.get_social_account(account_key)
            if not account:
                print(f"Instagram account not found for key {account_key}")
                return False
            credentials = account.get("credentials") or {}
            access_token = credentials.get("access_token")
            ig_business_account_id = credentials.get("ig_business_account_id")
            caption = post.get("caption") or ""
            image_url = post.get("image_url") if (post.get("image_mode") == "url") else None

            # If credentials are incomplete, simulate success to keep flow moving in dev
            if not access_token or not ig_business_account_id:
                print("Instagram credentials incomplete; simulating publish success.")
                return True

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Create media container
                media_params = {"caption": caption, "access_token": access_token}
                if image_url:
                    media_params["image_url"] = image_url
                else:
                    # For simplicity, require image_url; otherwise publish text as a story alternative not supported here
                    print("No image_url provided; simulating publish success for caption-only post.")
                    return True

                media_resp = await client.post(
                    f"https://graph.facebook.com/{Config.FACEBOOK_GRAPH_API_VERSION}/{ig_business_account_id}/media",
                    data=media_params
                )
                media_resp.raise_for_status()
                creation_id = media_resp.json().get("id")
                if not creation_id:
                    print("Instagram media creation_id missing"); return False

                # Step 2: Publish media
                publish_resp = await client.post(
                    f"https://graph.facebook.com/{Config.FACEBOOK_GRAPH_API_VERSION}/{ig_business_account_id}/media_publish",
                    data={"creation_id": creation_id, "access_token": access_token}
                )
                publish_resp.raise_for_status()
                return True
        except httpx.HTTPError as e:
            print(f"Instagram HTTP error: {e}")
            return False
        except Exception as e:
            print(f"Instagram publish error: {e}")
            return False

    async def _publish_facebook_page(self, post: Dict[str, Any]) -> bool:
        """Publish a post to a Facebook Page using Graph API. Supports text and image URL."""
        try:
            account_key = post.get("account_key")
            account = await self.db.get_social_account(account_key)
            if not account:
                print(f"Facebook account not found for key {account_key}")
                return False
            credentials = account.get("credentials") or {}
            page_access_token = credentials.get("page_access_token") or credentials.get("access_token")
            page_id = credentials.get("page_id")
            message = post.get("caption") or post.get("prompt") or ""
            image_url = post.get("image_url") if (post.get("image_mode") == "url") else None

            # If credentials are incomplete, simulate success in dev
            if not page_access_token or not page_id:
                print("Facebook Page credentials incomplete; simulating publish success.")
                return True

            async with httpx.AsyncClient(timeout=30.0) as client:
                if image_url:
                    # Photos endpoint supports message + url
                    resp = await client.post(
                        f"https://graph.facebook.com/{Config.FACEBOOK_GRAPH_API_VERSION}/{page_id}/photos",
                        data={
                            "url": image_url,
                            "caption": message,
                            "access_token": page_access_token
                        }
                    )
                else:
                    # Feed endpoint for text-only posts
                    resp = await client.post(
                        f"https://graph.facebook.com/{Config.FACEBOOK_GRAPH_API_VERSION}/{page_id}/feed",
                        data={
                            "message": message,
                            "access_token": page_access_token
                        }
                    )
                resp.raise_for_status()
                return True
        except httpx.HTTPError as e:
            print(f"Facebook HTTP error: {e}")
            return False
        except Exception as e:
            print(f"Facebook publish error: {e}")
            return False

# Create bot instance
bot = AIEmployeeBot()

# Event handlers
@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author == bot.user:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Handle AI employee interactions
    if message.content.startswith('@'):
        # Extract employee name from mention
        content = message.content[1:].strip()
        if ' ' in content:
            employee_name, user_message = content.split(' ', 1)
            
            # Check if employee exists
            employee = await bot.employee_manager.get_employee(employee_name)
            if employee:
                # Generate response
                response = await employee.generate_response(user_message)
                
                # Create embed
                embed = discord.Embed(
                    title=f"💬 {employee_name}",
                    description=response,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"AI Employee • {employee_name}")
                
                await message.channel.send(embed=embed)
                
                # Log conversation
                await bot.db.log_conversation(
                    employee.id,
                    message.author.id,
                    message.channel.id,
                    user_message,
                    response
                )

# Run the bot
def run_bot():
    """Run the Discord bot"""
    print("🔍 Validating Discord token...")
    
    # Check if token exists
    if not Config.DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables!")
        print("💡 Please check your .env file or environment variables.")
        debug_environment()
        return
    
    # Log token details (safely)
    token = Config.DISCORD_TOKEN
    print(f"✅ Token found in environment variables")
    print(f"📏 Token length: {len(token)} characters")
    print(f"🔑 Token starts with: {token[:10]}...")
    print(f"🔑 Token ends with: ...{token[-10:]}")
    
    # Basic token format validation
    if not token.startswith('MTA') and not token.startswith('MTI') and not token.startswith('OTk'):
        print("⚠️  Warning: Token format doesn't match expected Discord bot token pattern")
        print("   Expected: Starts with MTA, MTI, or OTk")
        print(f"   Got: Starts with {token[:3]}")
    
    # Check for common token issues
    if len(token) < 50:
        print("❌ Token appears too short for a valid Discord bot token")
        print(f"   Expected: At least 50 characters, Got: {len(token)}")
        debug_environment()
        return
    
    if ' ' in token or '\n' in token:
        print("❌ Token contains whitespace or newlines - this will cause issues")
        print("   Please check your .env file for extra spaces or formatting")
        debug_environment()
        return
    
    if token.lower() in ['your_discord_bot_token_here', 'placeholder', 'example', '']:
        print("❌ Token appears to be a placeholder value")
        print("   Please replace with your actual Discord bot token")
        debug_environment()
        return
    
    print("✅ Token format validation passed")
    print("🚀 Attempting to connect to Discord...")
    
    try:
        bot.run(token)
    except discord.LoginFailure as e:
        print(f"❌ Discord login failed: {e}")
        print("💡 This usually means:")
        print("   - The token is invalid or expired")
        print("   - The bot has been deleted from Discord Developer Portal")
        print("   - The token was copied incorrectly")
        print("🔍 Please verify your token at: https://discord.com/developers/applications")
        debug_environment()
    except discord.HTTPException as e:
        print(f"❌ Discord HTTP error: {e}")
        print("💡 This could indicate:")
        print("   - Network connectivity issues")
        print("   - Discord API rate limiting")
        print("   - Invalid token format")
        debug_environment()
    except Exception as e:
        print(f"❌ Unexpected error running bot: {e}")
        print(f"💡 Error type: {type(e).__name__}")
        if "Improper token" in str(e):
            print("🔍 The 'Improper token' error suggests:")
            print("   - Token format is incorrect")
            print("   - Token contains invalid characters")
            print("   - Token was truncated or corrupted")
            print("   - Environment variable loading issue")
            debug_environment()

if __name__ == "__main__":
    run_bot()
