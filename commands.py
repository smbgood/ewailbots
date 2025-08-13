import discord
from discord.ext import commands
from typing import Optional, Dict, Any
import json
from config import Config

# Import bot instance
# Note: The bot instance will be provided by the loader via the setup(bot) function.

class AdminCommands(commands.Cog):
    """Admin commands for managing AI employees and permissions"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Check if user has admin permissions"""
        return await self.bot.check_permissions(ctx, Config.PERMISSION_LEVELS["ADMIN"])
    
    @commands.command(name="create_employee")
    async def create_employee(self, ctx, name: str, employee_type: str, *, parameters: str = ""):
        """Create a new AI employee
        
        Usage: !create_employee <name> <type> [parameters]
        Types: SUPPORT, SALES, TECH, GENERAL
        Parameters: JSON string (optional)
        """
        try:
            # Parse parameters if provided
            params = {}
            if parameters:
                try:
                    params = json.loads(parameters)
                except json.JSONDecodeError:
                    await ctx.send("❌ Invalid JSON format for parameters!")
                    return
            
            # Create employee
            success = await self.bot.employee_manager.create_employee(name, employee_type, params)
            
            if success:
                embed = discord.Embed(
                    title="✅ Employee Created",
                    description=f"**{name}** has been created as a {employee_type} employee!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Name", value=name, inline=True)
                embed.add_field(name="Type", value=employee_type, inline=True)
                embed.add_field(name="Parameters", value=json.dumps(params, indent=2), inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Failed to create employee '{name}'. They may already exist.")
                
        except Exception as e:
            await ctx.send(f"❌ Error creating employee: {str(e)}")
    
    @commands.command(name="deactivate_employee")
    async def deactivate_employee(self, ctx, name: str):
        """Deactivate an AI employee"""
        success = await self.bot.employee_manager.deactivate_employee(name)
        
        if success:
            await ctx.send(f"✅ Employee '{name}' has been deactivated.")
        else:
            await ctx.send(f"❌ Failed to deactivate employee '{name}'.")
    
    @commands.command(name="update_employee")
    async def update_employee(self, ctx, name: str, *, parameters: str):
        """Update employee parameters
        
        Usage: !update_employee <name> <json_parameters>
        """
        try:
            params = json.loads(parameters)
            success = await self.bot.employee_manager.update_employee_parameters(name, params)
            
            if success:
                await ctx.send(f"✅ Employee '{name}' parameters updated successfully!")
            else:
                await ctx.send(f"❌ Failed to update employee '{name}'.")
                
        except json.JSONDecodeError:
            await ctx.send("❌ Invalid JSON format for parameters!")
        except Exception as e:
            await ctx.send(f"❌ Error updating employee: {str(e)}")
    
    @commands.command(name="set_permission")
    async def set_permission(self, ctx, user: discord.Member, level: int):
        """Set user permission level
        
        Levels: 1=USER, 2=MODERATOR, 3=ADMIN
        """
        if level not in [1, 2, 3]:
            await ctx.send("❌ Invalid permission level. Use 1, 2, or 3.")
            return
        
        success = await self.bot.db.set_user_permission(
            user.id, level, ctx.author.id
        )
        
        if success:
            level_names = {1: "USER", 2: "MODERATOR", 3: "ADMIN"}
            await ctx.send(f"✅ {user.mention} permission level set to {level_names[level]}")
        else:
            await ctx.send(f"❌ Failed to set permission level for {user.mention}")
    
    @commands.command(name="bulk_create")
    async def bulk_create(self, ctx, *, config_json: str):
        """Create multiple employees from JSON configuration"""
        try:
            configs = json.loads(config_json)
            if not isinstance(configs, list):
                await ctx.send("❌ Configuration must be a JSON array!")
                return
            
            results = await self.bot.employee_manager.bulk_create_employees(configs)
            
            # Create result embed
            embed = discord.Embed(
                title="📊 Bulk Employee Creation Results",
                color=discord.Color.blue()
            )
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            embed.add_field(name="Total", value=total_count, inline=True)
            embed.add_field(name="Successful", value=success_count, inline=True)
            embed.add_field(name="Failed", value=total_count - success_count, inline=True)
            
            # Add detailed results
            for name, success in results.items():
                status = "✅" if success else "❌"
                embed.add_field(name=name, value=status, inline=True)
            
            await ctx.send(embed=embed)
            
        except json.JSONDecodeError:
            await ctx.send("❌ Invalid JSON format!")
        except Exception as e:
            await ctx.send(f"❌ Error in bulk creation: {str(e)}")

class EmployeeCommands(commands.Cog):
    """Commands for managing and interacting with AI employees"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Check if user has moderator permissions"""
        return await self.bot.check_permissions(ctx, Config.PERMISSION_LEVELS["MODERATOR"])
    
    @commands.command(name="list_employees")
    async def list_employees(self, ctx):
        """List all active AI employees"""
        employees = await self.bot.employee_manager.get_all_employees()
        
        if not employees:
            await ctx.send("📋 No active AI employees found.")
            return
        
        embed = discord.Embed(
            title="👥 Active AI Employees",
            color=discord.Color.blue()
        )
        
        for emp in employees:
            embed.add_field(
                name=f"🤖 {emp['name']}",
                value=f"**Type:** {emp['type']}\n**Conversations:** {emp['conversation_count']}\n**Active:** {'Yes' if emp['active'] else 'No'}",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="employee_info")
    async def employee_info(self, ctx, name: str):
        """Get detailed information about an AI employee"""
        employee = await self.bot.employee_manager.get_employee(name)
        
        if not employee:
            await ctx.send(f"❌ Employee '{name}' not found.")
            return
        
        status = employee.get_status()
        
        embed = discord.Embed(
            title=f"🤖 {name} - Employee Information",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Type", value=status['type'], inline=True)
        embed.add_field(name="Conversations", value=status['conversation_count'], inline=True)
        embed.add_field(name="Active", value="Yes" if status['active'] else "No", inline=True)
        
        # Add parameters
        params_str = json.dumps(status['parameters'], indent=2)
        if len(params_str) > 1024:
            params_str = params_str[:1021] + "..."
        
        embed.add_field(name="Parameters", value=f"```json\n{params_str}\n```", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="reset_conversation")
    async def reset_conversation(self, ctx, name: str):
        """Reset conversation history for an employee"""
        success = await self.bot.employee_manager.reset_employee_conversation(name)
        
        if success:
            await ctx.send(f"✅ Conversation history reset for '{name}'.")
        else:
            await ctx.send(f"❌ Failed to reset conversation for '{name}'.")
    
    @commands.command(name="conversation_summary")
    async def conversation_summary(self, ctx, name: str):
        """Get conversation summary for an employee"""
        summary = await self.bot.employee_manager.get_employee_conversation_summary(name)
        
        if summary:
            embed = discord.Embed(
                title=f"💬 {name} - Conversation Summary",
                description=summary,
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Employee '{name}' not found or no conversations.")
    
    @commands.command(name="send_as")
    async def send_as(self, ctx, employee_name: str, channel: discord.TextChannel, *, message: str):
        """Send a message as a specific AI employee to a channel"""
        try:
            success = await self.bot.send_message_as_employee(
                channel, employee_name, message, ctx.author.id
            )
        except TypeError:
            success = await self.bot.send_message_as_employee(
                channel, employee_name, message
            )
        
        if success:
            await ctx.send(f"✅ Message sent as '{employee_name}' to {channel.mention}")
        else:
            await ctx.send(f"❌ Failed to send message as '{employee_name}'")
    
    @commands.command(name="dm_as")
    async def dm_as(self, ctx, employee_name: str, user: discord.Member, *, message: str):
        """Send a private message as a specific AI employee"""
        try:
            success = await self.bot.send_dm_as_employee(
                user, employee_name, message
            )
            
            if success:
                await ctx.send(f"✅ DM sent as '{employee_name}' to {user.mention}")
            else:
                await ctx.send(f"❌ Failed to send DM as '{employee_name}'")
                
        except discord.Forbidden:
            await ctx.send(f"❌ Cannot send DM to {user.mention}. They may have DMs disabled.")

class UserCommands(commands.Cog):
    """Basic user commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="help_ai")
    async def help_ai(self, ctx):
        """Show help for AI employee interactions"""
        embed = discord.Embed(
            title="🤖 AI Employee Help",
            description="Here's how to interact with AI employees:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Direct Mention",
            value="Use `@<employee_name> <message>` to talk to an AI employee directly",
            inline=False
        )
        
        embed.add_field(
            name="Available Commands",
            value="• `!list_employees` - List all AI employees\n• `!employee_info <name>` - Get employee details\n• `!help_ai` - Show this help message",
            inline=False
        )
        
        embed.add_field(
            name="Employee Types",
            value="• **SUPPORT** - Customer support specialist\n• **SALES** - Sales representative\n• **TECH** - Technical support\n• **GENERAL** - General assistant",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="stats")
    async def stats(self, ctx):
        """Show AI employee statistics"""
        stats = await self.bot.employee_manager.get_employee_stats()
        
        embed = discord.Embed(
            title="📊 AI Employee Statistics",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Total Employees", value=stats['total_employees'], inline=True)
        embed.add_field(name="Total Conversations", value=stats['total_conversations'], inline=True)
        embed.add_field(name="Active Employees", value=len(stats['active_employees']), inline=True)
        
        # Add type breakdown
        type_str = ""
        for emp_type, count in stats['employees_by_type'].items():
            type_str += f"• **{emp_type}**: {count}\n"
        
        if type_str:
            embed.add_field(name="Employees by Type", value=type_str, inline=False)
        
        await ctx.send(embed=embed)

class UtilityCommands(commands.Cog):
    """Utility commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check bot latency"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    
    @commands.command(name="status")
    async def status(self, ctx):
        """Show bot status"""
        embed = discord.Embed(
            title="🤖 Bot Status",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        # Add employee count
        employee_count = len(self.bot.employee_manager.active_employees)
        embed.add_field(name="AI Employees", value=employee_count, inline=True)
        
        await ctx.send(embed=embed)

# Note: setup for these cogs is defined at the bottom alongside grouped command cogs

class AIGroup(commands.Cog):
    """Grouped AI employee commands using the !ai prefix"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="ai", invoke_without_command=True)
    async def ai(self, ctx):
        """Show help for !ai commands"""
        await self.ai_help(ctx)

    @ai.command(name="help")
    async def ai_help(self, ctx):
        embed = discord.Embed(
            title="🤖 AI Employee Bot Help",
            description="Here are the available !ai commands:",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="👥 Employee Management",
            value=(
                "• `!ai create <name> <role> <personality>` - Create a new AI employee\n"
                "• `!ai list` - List all AI employees\n"
                "• `!ai info <name>` - Get employee information\n"
                "• `!ai update <name> [new_name] [new_role] [new_personality]` - Update employee settings\n"
                "• `!ai delete <name>` - Delete (deactivate) an employee"
            ),
            inline=False
        )

        embed.add_field(
            name="💬 Chat Commands",
            value=(
                "• `!chat message <employee> <message>` - Chat with an AI employee\n"
                "• `!chat ask <employee> <question>` - Ask an AI employee a question"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ Admin Commands",
            value=(
                "• `!admin permissions <user> <level>` - Manage user permissions\n"
                "• `!admin settings` - Bot configuration"
            ),
            inline=False
        )

        embed.set_footer(text="Use !ai help <command> for details about a specific command")
        await ctx.send(embed=embed)

    @ai.command(name="create")
    async def ai_create(self, ctx, name: str, role: str, *, personality: str):
        if not await self.bot.check_permissions(ctx, Config.PERMISSION_LEVELS["MODERATOR"]):
            await ctx.send("❌ You don't have permission to create employees!")
            return
        try:
            # Default parameters for creation
            params = Config.DEFAULT_AI_PARAMS.copy()
            params["role"] = role
            params["personality"] = personality
            success = await self.bot.employee_manager.create_employee(name, role, params)
            if success:
                embed = discord.Embed(
                    title="✅ Employee Created",
                    description=f"Successfully created AI employee **{name}**",
                    color=discord.Color.green()
                )
                embed.add_field(name="Role", value=role, inline=True)
                embed.add_field(name="Personality", value=personality, inline=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Failed to create employee '{name}'. They may already exist.")
        except Exception as e:
            await ctx.send(f"❌ Error creating employee: {str(e)}")

    @ai.command(name="list")
    async def ai_list(self, ctx):
        try:
            employees = await self.bot.employee_manager.get_all_employees()
            if not employees:
                await ctx.send("📝 No AI employees found.")
                return
            embed = discord.Embed(
                title="👥 AI Employees",
                description=f"Found {len(employees)} employee(s):",
                color=discord.Color.blue()
            )
            for employee in employees:
                embed.add_field(
                    name=f"🤖 {employee['name']}",
                    value=(
                        f"**Role:** {employee['type']}\n"
                        f"**Conversations:** {employee['conversation_count']}\n"
                        f"**Active:** {'Yes' if employee['active'] else 'No'}"
                    ),
                    inline=False
                )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error listing employees: {str(e)}")

    @ai.command(name="info")
    async def ai_info(self, ctx, name: str):
        try:
            employee = await self.bot.employee_manager.get_employee(name)
            if not employee:
                await ctx.send(f"❌ Employee '{name}' not found!")
                return
            status = employee.get_status()
            embed = discord.Embed(
                title=f"🤖 {name}",
                description=status.get("parameters", {}).get("personality", ""),
                color=discord.Color.blue()
            )
            embed.add_field(name="Role", value=status.get("type", ""), inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error getting employee info: {str(e)}")

    @ai.command(name="update")
    async def ai_update(self, ctx, name: str, new_name: str = None, new_role: str = None, *, new_personality: str = None):
        if not await self.bot.check_permissions(ctx, Config.PERMISSION_LEVELS["MODERATOR"]):
            await ctx.send("❌ You don't have permission to update employees!")
            return
        try:
            updates: Dict[str, Any] = {}
            if new_name:
                updates["name"] = new_name
            if new_role:
                updates["type"] = new_role
            if new_personality:
                params = Config.DEFAULT_AI_PARAMS.copy()
                params["personality"] = new_personality
                updates["parameters"] = params
            if not updates:
                await ctx.send("❌ No updates provided!")
                return
            success = await self.bot.employee_manager.update_employee_parameters(name, updates.get("parameters", {}))
            if success:
                await ctx.send(f"✅ Successfully updated '{name}'.")
            else:
                await ctx.send(f"❌ Failed to update '{name}'.")
        except Exception as e:
            await ctx.send(f"❌ Error updating employee: {str(e)}")

    @ai.command(name="delete")
    async def ai_delete(self, ctx, name: str):
        if not await self.bot.check_permissions(ctx, Config.PERMISSION_LEVELS["ADMIN"]):
            await ctx.send("❌ You don't have permission to delete employees!")
            return
        try:
            success = await self.bot.employee_manager.deactivate_employee(name)
            if success:
                await ctx.send(f"🗑️ Employee '{name}' deactivated.")
            else:
                await ctx.send(f"❌ Failed to deactivate employee '{name}'.")
        except Exception as e:
            await ctx.send(f"❌ Error deleting employee: {str(e)}")


class ChatGroup(commands.Cog):
    """Grouped chat commands using the !chat prefix"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="chat", invoke_without_command=True)
    async def chat(self, ctx):
        await ctx.send("Usage: !chat message <employee> <message> | !chat ask <employee> <question>")

    @chat.command(name="message")
    async def chat_message(self, ctx, employee: str, *, message: str):
        try:
            try:
                await self.bot.send_message_as_employee(ctx.channel, employee, message, ctx.author.id)
            except TypeError:
                await self.bot.send_message_as_employee(ctx.channel, employee, message)
        except Exception as e:
            await ctx.send(f"❌ Error chatting with employee: {str(e)}")

    @chat.command(name="ask")
    async def chat_ask(self, ctx, employee: str, *, question: str):
        try:
            try:
                await self.bot.send_message_as_employee(ctx.channel, employee, question, ctx.author.id)
            except TypeError:
                await self.bot.send_message_as_employee(ctx.channel, employee, question)
        except Exception as e:
            await ctx.send(f"❌ Error asking question: {str(e)}")


class AdminGroup(commands.Cog):
    """Grouped admin commands using the !admin prefix"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="admin", invoke_without_command=True)
    async def admin(self, ctx):
        await ctx.send("Usage: !admin permissions <user> <level> | !admin settings")

    @admin.command(name="permissions")
    async def admin_permissions(self, ctx, user: discord.Member, level: int):
        if ctx.author.id not in Config.ADMIN_USER_IDS:
            await ctx.send("❌ You don't have permission to manage permissions!")
            return
        if level not in [1, 2, 3]:
            await ctx.send("❌ Invalid permission level! Use 1 (User), 2 (Moderator), or 3 (Admin)")
            return
        try:
            success = await self.bot.db.set_user_permission(user.id, level)
            if success:
                level_names = {1: "User", 2: "Moderator", 3: "Admin"}
                embed = discord.Embed(
                    title="✅ Permissions Updated",
                    description=f"Updated {user.mention}'s permission level to **{level_names[level]}**",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to update permissions")
        except Exception as e:
            await ctx.send(f"❌ Error updating permissions: {str(e)}")

    @admin.command(name="settings")
    async def admin_settings(self, ctx):
        if ctx.author.id not in Config.ADMIN_USER_IDS:
            await ctx.send("❌ You don't have permission to view settings!")
            return
        embed = discord.Embed(
            title="⚙️ Bot Settings",
            description="Current bot configuration:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Guild ID", value=Config.GUILD_ID or "Global", inline=True)
        embed.add_field(name="Admin Users", value=len(Config.ADMIN_USER_IDS), inline=True)
        embed.add_field(name="AI Model", value=Config.DEFAULT_AI_PARAMS["model"], inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIGroup(bot))
    await bot.add_cog(ChatGroup(bot))
    await bot.add_cog(AdminGroup(bot))
