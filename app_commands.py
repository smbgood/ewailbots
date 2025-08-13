import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from config import Config
from employee_manager import EmployeeManager
from database import DatabaseManager



class AIEmployeeCommands(app_commands.Group):
    """AI Employee management commands"""
    
    def __init__(self):
        super().__init__(name="ai", description="Manage AI employees")
        self.employee_manager = EmployeeManager()
        self.db = DatabaseManager()
    
    @app_commands.command(name="help", description="Show help information")
    async def help_command(self, interaction: discord.Interaction):
        """Show help information for AI Employee commands"""
        embed = discord.Embed(
            title="🤖 AI Employee Bot Help",
            description="Here are the available commands:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👥 Employee Management",
            value="• `!ai create` - Create a new AI employee\n"
                  "• `!ai list` - List all AI employees\n"
                  "• `!ai info <name>` - Get employee information\n"
                  "• `!ai update` - Update employee settings\n"
                  "• `!ai delete` - Delete an employee",
            inline=False
        )
        
        embed.add_field(
            name="💬 Chat Commands",
            value="• `!chat message <employee> <message>` - Chat with an AI employee\n"
                  "• `!chat ask <employee> <question>` - Ask an AI employee a question",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Admin Commands",
            value="• `!admin permissions` - Manage user permissions\n"
                  "• `!admin settings` - Bot configuration",
            inline=False
        )
        
        embed.set_footer(text="Use !help <command> for detailed information about a specific command")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="create", description="Create a new AI employee")
    @app_commands.describe(
        name="The name of the employee",
        role="The role/type of employee",
        personality="The personality description"
    )
    async def create_employee(
        self, 
        interaction: discord.Interaction, 
        name: str, 
        role: str, 
        personality: str
    ):
        """Create a new AI employee"""
        # Check permissions using the bot's method
        if not await interaction.client.check_permissions(interaction, 2):
            await interaction.response.send_message("❌ You don't have permission to create employees!", ephemeral=True)
            return
        
        try:
            # Create employee
            employee = await self.employee_manager.create_employee(
                name=name,
                role=role,
                personality=personality,
                created_by=interaction.user.id
            )
            
            embed = discord.Embed(
                title="✅ Employee Created",
                description=f"Successfully created AI employee **{name}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Role", value=role, inline=True)
            embed.add_field(name="Personality", value=personality, inline=True)
            embed.add_field(name="ID", value=employee.id, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating employee: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="list", description="List all AI employees")
    async def list_employees(self, interaction: discord.Interaction):
        """List all AI employees"""
        try:
            employees = await self.employee_manager.get_all_employees()
            
            if not employees:
                await interaction.response.send_message("📝 No AI employees found.")
                return
            
            embed = discord.Embed(
                title="👥 AI Employees",
                description=f"Found {len(employees)} employee(s):",
                color=discord.Color.blue()
            )
            
            for employee in employees:
                embed.add_field(
                    name=f"🤖 {employee.name}",
                    value=f"**Role:** {employee.role}\n"
                          f"**Personality:** {employee.personality[:100]}{'...' if len(employee.personality) > 100 else ''}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error listing employees: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="info", description="Get information about an AI employee")
    @app_commands.describe(name="The name of the employee")
    async def employee_info(self, interaction: discord.Interaction, name: str):
        """Get detailed information about an AI employee"""
        try:
            employee = await self.employee_manager.get_employee(name)
            
            if not employee:
                await interaction.response.send_message(f"❌ Employee '{name}' not found!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🤖 {employee.name}",
                description=employee.personality,
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Role", value=employee.role, inline=True)
            embed.add_field(name="ID", value=employee.id, inline=True)
            embed.add_field(name="Created", value=f"<t:{int(employee.created_at.timestamp())}:R>", inline=True)
            
            # Add conversation stats if available
            try:
                stats = await self.db.get_employee_stats(employee.id)
                if stats:
                    embed.add_field(name="Total Conversations", value=stats['total_conversations'], inline=True)
                    embed.add_field(name="Last Active", value=f"<t:{int(stats['last_active'].timestamp())}:R>" if stats['last_active'] else "Never", inline=True)
            except:
                pass
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting employee info: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="update", description="Update an AI employee")
    @app_commands.describe(
        name="The name of the employee to update",
        new_name="New name (optional)",
        new_role="New role (optional)",
        new_personality="New personality (optional)"
    )
    async def update_employee(
        self, 
        interaction: discord.Interaction, 
        name: str, 
        new_name: Optional[str] = None,
        new_role: Optional[str] = None,
        new_personality: Optional[str] = None
    ):
        """Update an AI employee's information"""
        # Check permissions using the bot's method
        if not await interaction.client.check_permissions(interaction, 2):
            await interaction.response.send_message("❌ You don't have permission to update employees!", ephemeral=True)
            return
        
        try:
            # Get current employee
            employee = await self.employee_manager.get_employee(name)
            if not employee:
                await interaction.response.send_message(f"❌ Employee '{name}' not found!", ephemeral=True)
                return
            
            # Update fields
            updates = {}
            if new_name:
                updates['name'] = new_name
            if new_role:
                updates['role'] = new_role
            if new_personality:
                updates['personality'] = new_personality
            
            if not updates:
                await interaction.response.send_message("❌ No updates provided!", ephemeral=True)
                return
            
            # Update employee
            await self.employee_manager.update_employee(employee.id, updates)
            
            embed = discord.Embed(
                title="✅ Employee Updated",
                description=f"Successfully updated **{name}**",
                color=discord.Color.green()
            )
            
            for field, value in updates.items():
                embed.add_field(name=f"New {field.title()}", value=value, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating employee: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="delete", description="Delete an AI employee")
    @app_commands.describe(name="The name of the employee to delete")
    async def delete_employee(self, interaction: discord.Interaction, name: str):
        """Delete an AI employee"""
        # Check permissions using the bot's method
        if not await interaction.client.check_permissions(interaction, 3):
            await interaction.response.send_message("❌ You don't have permission to delete employees!", ephemeral=True)
            return
        
        try:
            # Get employee
            employee = await self.employee_manager.get_employee(name)
            if not employee:
                await interaction.response.send_message(f"❌ Employee '{name}' not found!", ephemeral=True)
                return
            
            # Delete employee
            await self.employee_manager.delete_employee(employee.id)
            
            embed = discord.Embed(
                title="🗑️ Employee Deleted",
                description=f"Successfully deleted AI employee **{name}**",
                color=discord.Color.red()
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error deleting employee: {str(e)}", ephemeral=True)
    


class ChatCommands(app_commands.Group):
    """Chat with AI employees"""
    
    def __init__(self):
        super().__init__(name="chat", description="Chat with AI employees")
        self.employee_manager = EmployeeManager()
        self.db = DatabaseManager()
    
    @app_commands.command(name="message", description="Send a message to an AI employee")
    @app_commands.describe(
        employee="The name of the employee to chat with",
        message="Your message to the employee"
    )
    async def chat_message(
        self, 
        interaction: discord.Interaction, 
        employee: str, 
        message: str
    ):
        """Send a message to an AI employee"""
        try:
            # Get employee
            ai_employee = await self.employee_manager.get_employee(employee)
            if not ai_employee:
                await interaction.response.send_message(f"❌ Employee '{employee}' not found!", ephemeral=True)
                return
            
            # Defer response since AI generation might take time
            await interaction.response.defer()
            
            # Generate response
            response = await ai_employee.generate_response(message)
            
            # Create embed
            embed = discord.Embed(
                title=f"💬 {employee}",
                description=response,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"AI Employee • {employee}")
            
            # Log conversation
            await self.db.log_conversation(
                ai_employee.id,
                interaction.user.id,
                interaction.channel_id,
                message,
                response
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error chatting with employee: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="ask", description="Ask an AI employee a question")
    @app_commands.describe(
        employee="The name of the employee to ask",
        question="Your question for the employee"
    )
    async def ask_question(
        self, 
        interaction: discord.Interaction, 
        employee: str, 
        question: str
    ):
        """Ask an AI employee a question"""
        try:
            # Get employee
            ai_employee = await self.employee_manager.get_employee(employee)
            if not ai_employee:
                await interaction.response.send_message(f"❌ Employee '{employee}' not found!", ephemeral=True)
                return
            
            # Defer response since AI generation might take time
            await interaction.response.defer()
            
            # Generate response
            response = await ai_employee.generate_response(question)
            
            # Create embed
            embed = discord.Embed(
                title=f"❓ {employee}",
                description=f"**Question:** {question}\n\n**Answer:** {response}",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"AI Employee • {employee}")
            
            # Log conversation
            await self.db.log_conversation(
                ai_employee.id,
                interaction.user.id,
                interaction.channel_id,
                question,
                response
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error asking question: {str(e)}", ephemeral=True)

class AdminCommands(app_commands.Group):
    """Administrative commands"""
    
    def __init__(self):
        super().__init__(name="admin", description="Administrative commands")
        self.db = DatabaseManager()
    
    @app_commands.command(name="permissions", description="Manage user permissions")
    @app_commands.describe(
        user="The user to manage permissions for",
        level="The permission level (1=User, 2=Moderator, 3=Admin)"
    )
    async def manage_permissions(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member, 
        level: int
    ):
        """Manage user permissions"""
        # Check if user is admin
        if interaction.user.id not in Config.ADMIN_USER_IDS:
            await interaction.response.send_message("❌ You don't have permission to manage permissions!", ephemeral=True)
            return
        
        if level not in [1, 2, 3]:
            await interaction.response.send_message("❌ Invalid permission level! Use 1 (User), 2 (Moderator), or 3 (Admin)", ephemeral=True)
            return
        
        try:
            # Update user permission
            await self.db.set_user_permission(user.id, level)
            
            level_names = {1: "User", 2: "Moderator", 3: "Admin"}
            embed = discord.Embed(
                title="✅ Permissions Updated",
                description=f"Updated {user.mention}'s permission level to **{level_names[level]}**",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating permissions: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="settings", description="View bot settings")
    async def view_settings(self, interaction: discord.Interaction):
        """View bot configuration settings"""
        # Check if user is admin
        if interaction.user.id not in Config.ADMIN_USER_IDS:
            await interaction.response.send_message("❌ You don't have permission to view settings!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⚙️ Bot Settings",
            description="Current bot configuration:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Guild ID", value=Config.GUILD_ID or "Global", inline=True)
        embed.add_field(name="Admin Users", value=len(Config.ADMIN_USER_IDS), inline=True)
        embed.add_field(name="AI Model", value=Config.DEFAULT_AI_PARAMS["model"], inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Register command groups with the bot
async def setup(bot):
    """Setup function to register all command groups"""
    bot.tree.add_command(AIEmployeeCommands())
    bot.tree.add_command(ChatCommands())
    bot.tree.add_command(AdminCommands())
