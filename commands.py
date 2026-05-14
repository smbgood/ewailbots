import asyncio
import discord
from discord.ext import commands
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
import json
import re
import httpx
from config import Config
from image_generator import generate_image

# Import bot instance
# Note: The bot instance will be provided by the loader via the setup(bot) function.


class SocialCommands(commands.Cog):
    """Commands for creating social media posts (drafts, scheduling, publishing)"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Require moderator permissions for social posting"""
        return await self.bot.check_permissions(ctx, Config.PERMISSION_LEVELS["MODERATOR"])

    @commands.command(name="social")
    async def social(self, ctx, prompt: str, account_key: str, employee_name: str, image: str, status: str = "draft", section: str = "", keywords: str = ""):
        """Create a social media post draft.

        Usage:
        !social "<prompt>" <account_key> <employee_name> <true|false|image_url> [draft|scheduled] [section] [keywords]

        - prompt: caption generation prompt or text
        - account_key: configured social account key (e.g., EW-Insta)
        - employee_name: AI employee to generate content
        - image: 'true' to generate, 'false' for no image, or a direct image URL
        - status: default 'draft' (others reserved)
        - section: optional website section to highlight/promote
        - keywords: optional SEO/trend keywords to work in
        """
        try:
            # Validate account exists
            account = await self.bot.db.get_social_account(account_key)
            if not account:
                await ctx.send(f"❌ Social account '{account_key}' not found or inactive.")
                return
            platform = (account.get("platform") or "").lower()
            if platform not in ("instagram", "facebook"):
                await ctx.send("❌ Currently only Instagram and Facebook Page accounts are supported for this command.")
                return

            # Validate employee
            employee = await self.bot.employee_manager.get_employee(employee_name)
            if not employee:
                await ctx.send(f"❌ Employee '{employee_name}' not found.")
                return

            # Determine image mode and possible URL
            image_mode = "none"
            image_url = None
            normalized = (image or "").strip().lower()
            if normalized == "true":
                image_mode = "generate"
            elif normalized == "false":
                image_mode = "none"
            else:
                image_mode = "url"
                image_url = image

            section_text = (section or "").strip()
            keywords_text = (keywords or "").strip()

            # Generate caption using employee (platform-aware prompt)
            platform_nice = "Instagram" if platform == "instagram" else "Facebook Page"
            caption_prompt = (
                f"Write a {platform_nice} post caption for this prompt. "
                f"Keep it concise, engaging, and appropriate for {platform_nice}. Prompt: {prompt}"
            )
            if section_text:
                caption_prompt += f" Highlight or promote this website section: {section_text}."
            if keywords_text:
                caption_prompt += f" Consider these keywords if relevant: {keywords_text}."
            caption = await employee.generate_response(caption_prompt)

            image_meta: Dict[str, Any] = {}
            if image_mode == "generate":
                image_prompt = "Create a high-quality social media image that highlights a website section."
                if section_text:
                    image_prompt += f" Section: {section_text}."
                image_prompt += f" Theme or focus: {prompt}. Style: clean, modern, vibrant, no text."
                try:
                    image_result = await asyncio.to_thread(generate_image, image_prompt)
                    image_url = image_result.get("image_url")
                    image_meta = {
                        "image_prompt": image_prompt,
                        "image_source": image_result.get("source"),
                        "image_path": image_result.get("image_path"),
                        "image_revised_prompt": image_result.get("revised_prompt"),
                    }
                    if image_url:
                        print(f"Generated social image URL: {image_url}")
                    else:
                        image_meta["image_error"] = "Image generated without a usable URL"
                except Exception as e:
                    image_meta = {
                        "image_prompt": image_prompt,
                        "image_error": str(e),
                    }
                    print(f"Image generation failed: {e}")

            # Create draft post in DB
            data = {
                "account_key": account_key,
                "platform": platform,
                "status": status or "draft",
                "prompt": prompt,
                "caption": caption,
                "image_mode": image_mode,
                "image_url": image_url,
                "employee_name": employee_name,
                "requested_by_user_id": ctx.author.id,
                "meta": {
                    "channel_id": ctx.channel.id,
                    "section": section_text or None,
                    "keywords": keywords_text or None,
                    **image_meta,
                }
            }

            created = await self.bot.db.create_social_post(data)
            if not created:
                await ctx.send("❌ Failed to create social post draft.")
                return

            embed = discord.Embed(
                title="📝 Social Post Draft Created",
                color=discord.Color.blurple(),
                description=f"Draft for **{account_key}** ({platform_nice})"
            )
            embed.add_field(name="Prompt", value=prompt[:256] + ("..." if len(prompt) > 256 else ""), inline=False)
            embed.add_field(name="Caption (generated)", value=caption[:1024] + ("..." if len(caption) > 1024 else ""), inline=False)
            embed.add_field(name="Employee", value=employee_name, inline=True)
            embed.add_field(name="Image", value=(image_mode if image_mode != "url" else f"url: {image_url}"), inline=True)
            embed.add_field(name="Status", value=created.get("status", status), inline=True)
            embed.set_footer(text=f"Post ID: {created.get('id')}")

            # Add Approve/Reject buttons
            view = SocialPostView(self.bot, created.get('id'), created.get('requested_by_user_id'), created.get('account_key'))
            msg = await ctx.send(embed=embed, view=view)
            view.set_message(msg)
            if image_mode == "generate" and not image_url:
                await ctx.send("⚠️ Image generation did not provide a usable URL. Draft created without an image.")

        except Exception as e:
            await ctx.send(f"❌ Error creating social post: {str(e)}")


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


class MeetingCommands(commands.Cog):
    """Commands to orchestrate multi-employee meetings"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Require moderator permissions for meetings"""
        return await self.bot.check_permissions(ctx, Config.PERMISSION_LEVELS["MODERATOR"])

    @commands.command(name="meeting")
    async def meeting(self, ctx, participants: str, rounds: int, *, topic: str):
        """Run a structured meeting between AI employees.

        Usage:
        !meeting <name1,name2,...> <rounds> "<topic/context>"
        """
        # Parse and validate participants
        names: List[str] = [n.strip() for n in (participants or "").split(",") if n.strip()]
        if len(names) < 2:
            await ctx.send("❌ Please provide at least two participant names, separated by commas.")
            return
        if not isinstance(rounds, int) or rounds < 1 or rounds > 10:
            await ctx.send("❌ Rounds must be an integer between 1 and 10.")
            return

        # Resolve employees
        employees = []
        missing = []
        for name in names:
            emp = await self.bot.employee_manager.get_employee(name)
            if not emp:
                missing.append(name)
            else:
                employees.append(emp)

        if missing:
            await ctx.send(f"❌ The following employees were not found or inactive: {', '.join(missing)}")
            return

        # Announce meeting start
        start_embed = discord.Embed(
            title="🧑‍💼🤖 AI Meeting Started",
            description=f"Topic: {topic}",
            color=discord.Color.blurple()
        )
        start_embed.add_field(name="Participants", value=", ".join(names), inline=False)
        start_embed.add_field(name="Rounds", value=str(rounds), inline=True)
        # Send initial message and create a thread to consolidate the meeting output
        thread = None
        try:
            start_msg = await ctx.send(embed=start_embed)
            thread_name = f"Meeting: {topic}"
            if len(thread_name) > 100:
                thread_name = thread_name[:97] + "..."
            thread = await start_msg.create_thread(name=thread_name, auto_archive_duration=1440)
            await thread.send(f"Participants: {', '.join(names)} • Rounds: {rounds}")
        except Exception:
            thread = None

        # Shared meeting context for system prompt
        colleagues = ", ".join(names)
        system_context = (
            f"You are participating in a structured, time-boxed meeting with AI colleagues: {colleagues}.\n"
            f"Focus: {topic}\n\n"
            "Guidelines:\n"
            "- Be concise (<= 150 words) and concrete.\n"
            "- Build on prior comments; avoid repetition.\n"
            "- Address colleagues by name when relevant.\n"
            "- Offer specific recommendations, assumptions, and risks.\n"
        )

        transcript: List[Tuple[str, str]] = []  # (speaker, text)

        # Run meeting rounds
        for r in range(1, rounds + 1):
            for emp in employees:
                # Compile recent transcript for context (limit to last 8 entries to keep prompts manageable)
                if transcript:
                    recent = transcript[-8:]
                    transcript_text = "\n".join([f"{speaker}: {text}" for speaker, text in recent])
                else:
                    transcript_text = "(none yet)"

                prompt_lines = [
                    f"Round {r}/{rounds}.",
                    "Transcript so far:",
                    transcript_text,
                    "",
                    f"Your turn, {emp.name}. Provide your contribution for this round."
                ]
                if r == rounds:
                    prompt_lines.append(
                        "In this final turn, briefly summarize your viewpoint and propose 3-5 concrete action items."
                    )
                prompt = "\n".join(prompt_lines)

                # Generate response
                try:
                    response_text = await emp.generate_response(prompt, context=system_context)
                except TypeError:
                    response_text = await emp.generate_response(prompt)

                transcript.append((emp.name, response_text))

                # Send response embed
                response_embed = discord.Embed(
                    title=f"Round {r} — {emp.name}",
                    description=response_text,
                    color=discord.Color.blue()
                )
                if thread:
                    await thread.send(embed=response_embed)
                else:
                    await ctx.send(embed=response_embed)

        # Optional overall summary using the first participant
        try:
            full_transcript = "\n".join([f"{s}: {t}" for s, t in transcript])
            summary_prompt = (
                f"Full transcript below. Summarize the meeting on '{topic}' into 5 concise bullets, "
                f"then list 5 next actions with suggested owners chosen from: {colleagues}.\n\n"
                f"Transcript:\n{full_transcript}"
            )
            overall = await employees[0].generate_response(summary_prompt, context=system_context)
        except Exception:
            overall = None

        end_embed = discord.Embed(
            title="✅ Meeting Concluded",
            description=f"Topic: {topic}",
            color=discord.Color.green()
        )
        # Helper to split and send long text as multiple messages to avoid Discord limits
        def _chunk_text(text: str, max_len: int = 1900) -> List[str]:
            parts: List[str] = []
            current: List[str] = []
            current_len = 0
            for paragraph in text.split("\n"):
                # Ensure at least newline preserved between paragraphs
                pl = len(paragraph)
                if current_len + pl + (1 if current else 0) <= max_len:
                    if current:
                        current.append(paragraph)
                        current_len += pl + 1
                    else:
                        current = [paragraph]
                        current_len = pl
                else:
                    if current:
                        parts.append("\n".join(current))
                    # If paragraph itself is too long, hard-split
                    start = 0
                    while start < pl:
                        take = min(max_len, pl - start)
                        parts.append(paragraph[start:start+take])
                        start += take
                    current = []
                    current_len = 0
            if current:
                parts.append("\n".join(current))
            return parts
        
        # Decide outcome and persist to Supabase along with conversation ids
        outcome_text = None
        try:
            decision_prompt = (
                "Based on the full meeting transcript and topic, output a single, concise outcome line.\n"
                "Format exactly as: Outcome: <short decision statement>.\n"
                f"Topic: {topic}\n\nTranscript:\n{full_transcript}"
            )
            outcome_raw = await employees[0].generate_response(decision_prompt, context=system_context)
            # Normalize to a short line and strip any leading label
            if outcome_raw:
                line = outcome_raw.strip().split("\n", 1)[0]
                if line.lower().startswith("outcome:"):
                    line = line.split(":", 1)[1].strip()
                outcome_text = line
        except Exception:
            outcome_text = None

        # Collect conversation ids from participating employees
        conversation_ids: List[str] = []
        try:
            for emp in employees:
                cid = getattr(emp, "conversation_id", None)
                if isinstance(cid, str) and cid:
                    conversation_ids.append(cid)
        except Exception:
            pass

        try:
            await self.bot.db.log_meeting_outcome(
                user_id=ctx.author.id,
                channel_id=ctx.channel.id,
                topic=topic,
                participants=names,
                summary=overall,
                outcome=(outcome_text or "No clear outcome decided"),
                conversation_ids=conversation_ids
            )
            if outcome_text:
                end_embed.add_field(name="Outcome", value=outcome_text, inline=False)
        except Exception:
            # Even if persistence fails, still finish gracefully
            if outcome_text:
                end_embed.add_field(name="Outcome", value=outcome_text, inline=False)

        # Send concluding embed
        if thread:
            await thread.send(embed=end_embed)
        else:
            await ctx.send(embed=end_embed)

        # After conclusion, send full summary/next actions without truncation
        if overall:
            target = thread or ctx
            header = "Summary & Next Actions"
            await target.send(header)
            for idx, chunk in enumerate(_chunk_text(overall)):
                prefix = "(cont’d)\n" if idx > 0 else ""
                await target.send(prefix + chunk)

            # Try to auto-create Linear issues if configured
            try:
                if getattr(Config, 'LINEAR_API_KEY', None) and getattr(Config, 'LINEAR_TEAM_ID', None):
                    # Extract action lines heuristically (numbered or bulleted)
                    action_lines: List[str] = []
                    for line in overall.split("\n"):
                        if re.match(r"^\s*(?:\d+\.|[-•])\s+", line):
                            action_lines.append(re.sub(r"^\s*(?:\d+\.|[-•])\s+", "", line).strip())
                    created_details: List[Dict[str, Any]] = []
                    for action in action_lines[:10]:
                        owner_match = re.search(r"owner[:\-]\s*([^\)\n]+)", action, flags=re.IGNORECASE)
                        owner = owner_match.group(1).strip() if owner_match else None
                        title = re.sub(r"\s*\(.*?owner.*?\)\s*", "", action, flags=re.IGNORECASE)
                        if len(title) > 80:
                            title = title[:77] + "..."
                        description = (
                            f"Topic: {topic}\n"
                            f"Suggested owner: {owner or 'Unassigned'}\n\n"
                            f"Proposed by AI meeting participants: {', '.join(names)}.\n\n"
                            f"Full context summary:\n{overall}"
                        )
                        mutation = {
                            "query": (
                                "mutation IssueCreate($input: IssueCreateInput!) { "
                                "issueCreate(input: $input) { success issue { identifier url title } } }"
                            ),
                            "variables": {
                                "input": {
                                    "teamId": getattr(Config, 'LINEAR_TEAM_ID', None),
                                    "title": title,
                                    "description": description,
                                }
                            }
                        }
                        project_id = getattr(Config, 'LINEAR_PROJECT_ID', None)
                        if project_id:
                            mutation["variables"]["input"]["projectId"] = project_id
                        headers = {
                            "Authorization": f"Bearer {getattr(Config, 'LINEAR_API_KEY', '')}",
                            "Content-Type": "application/json"
                        }
                        async with httpx.AsyncClient(timeout=30) as client:
                            resp = await client.post("https://api.linear.app/graphql", json=mutation, headers=headers)
                            issue_url = None
                            issue_identifier = None
                            issue_id = None
                            success_flag = None
                            errors_payload: Any = None
                            raw_text: str = ""
                            try:
                                raw_text = resp.text or ""
                                data = resp.json()
                                # Check for GraphQL errors
                                if isinstance(data, dict) and data.get("errors"):
                                    errors_payload = data.get("errors")
                                payload = (data or {}).get("data") or {}
                                icreate = payload.get("issueCreate") or {}
                                success_flag = icreate.get("success")
                                issue = icreate.get("issue") or {}
                                if issue:
                                    issue_url = issue.get("url")
                                    issue_identifier = issue.get("identifier")
                                    issue_id = issue.get("id")
                                # Fallback: build URL from identifier if missing
                                if not issue_url and issue_identifier:
                                    issue_url = f"https://linear.app/issue/{issue_identifier}"
                            except Exception:
                                pass
                            created_details.append({
                                "title": title,
                                "url": issue_url,
                                "identifier": issue_identifier,
                                "id": issue_id,
                                "success": success_flag,
                                "errors": errors_payload,
                                "http_status": getattr(resp, "status_code", None),
                                "raw": (raw_text[:1000] + ("..." if len(raw_text) > 1000 else "")),
                                "description": description
                            })
                    if created_details:
                        await target.send("Created Linear issues:")
                        for entry in created_details:
                            line = f"- [{entry.get('identifier') or '?'}] {entry.get('title') or ''}\n{entry.get('url') or '(no url returned)'}"
                            await target.send(line)
                            # Send full description in chunks to avoid Discord limits
                            desc = entry.get("description") or ""
                            for idx, chunk in enumerate(_chunk_text(desc)):
                                prefix = "Description (cont’d):\n" if idx > 0 else "Description:\n"
                                await target.send(prefix + chunk)
                            # If we still lack a URL and identifier, provide a concise debug snippet
                            if not entry.get("url") and not entry.get("identifier"):
                                debug_msg = "Linear API response did not include url/identifier. "
                                status = entry.get("http_status")
                                if status:
                                    debug_msg += f"HTTP {status}. "
                                errors = entry.get("errors")
                                if errors:
                                    debug_msg += f"Errors: {errors}"
                                else:
                                    debug_msg += "Body snippet: " + (entry.get("raw") or "")
                                await target.send(debug_msg)
                else:
                    # Not configured; notify once in the thread
                    target = thread or ctx
                    await target.send("ℹ️ Linear integration is not configured. Set LINEAR_API_KEY and LINEAR_TEAM_ID to enable auto-issue creation.")
            except Exception as e:
                # Fail gracefully without breaking the meeting flow
                await (thread or ctx).send(f"⚠️ Failed to create Linear issues automatically: {str(e)}")

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
    await bot.add_cog(SocialCommands(bot))
    await bot.add_cog(MeetingCommands(bot))


class SocialPostView(discord.ui.View):
    def __init__(self, bot, post_id: int, requested_by_user_id: int, account_key: str, timeout: Optional[float] = 600):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.post_id = post_id
        self.requested_by_user_id = requested_by_user_id
        self.account_key = account_key
        self.message: Optional[discord.Message] = None

    def set_message(self, message: discord.Message):
        self.message = message

    async def _ensure_permissions(self, interaction: discord.Interaction) -> bool:
        # Allow moderators; optionally restrict to the requester
        has_perm = await self.bot.check_permissions(interaction, Config.PERMISSION_LEVELS["MODERATOR"]) if hasattr(self.bot, 'check_permissions') else True
        if not has_perm:
            await interaction.response.send_message("❌ You don't have permission to manage this post.", ephemeral=True)
            return False
        return True

    async def _update_status_field(self, new_status: str):
        if not self.message:
            return
        try:
            embed = self.message.embeds[0] if self.message.embeds else None
            if not embed:
                return
            # Rebuild embed with updated status
            new_embed = discord.Embed(title=embed.title, description=embed.description, color=embed.color)
            for field in embed.fields:
                if field.name.lower() == "status":
                    new_embed.add_field(name=field.name, value=new_status, inline=field.inline)
                else:
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            new_embed.set_footer(text=embed.footer.text if embed.footer else "")
            await self.message.edit(embed=new_embed, view=self)
        except Exception as e:
            print(f"Failed to update embed status: {e}")

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._ensure_permissions(interaction):
            return
        # Show a choice: Publish Now or Schedule...
        await interaction.response.send_message(
            "Choose when to publish:",
            view=ScheduleOrNowView(self.bot, self.post_id, self._update_status_field),
            ephemeral=True
        )

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._ensure_permissions(interaction):
            return
        updated = await self.bot.db.set_social_post_status(self.post_id, "cancelled")
        if updated:
            await self._update_status_field("cancelled")
            await interaction.response.send_message("🛑 Post has been cancelled.", ephemeral=True)
            # Disable buttons after cancel
            self.disable_all_items()
            if self.message:
                await self.message.edit(view=self)
        else:
            await interaction.response.send_message("❌ Failed to cancel post.", ephemeral=True)


class ScheduleOrNowView(discord.ui.View):
    def __init__(self, bot, post_id: int, status_updater):
        super().__init__(timeout=300)
        self.bot = bot
        self.post_id = post_id
        self.status_updater = status_updater

    @discord.ui.button(label="Now", style=discord.ButtonStyle.primary)
    async def publish_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Publish immediately
        post = await self.bot.db.get_social_post_by_id(self.post_id)
        if not post:
            await interaction.response.send_message("❌ Post not found.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        success = await self.bot.publish_social_post(post)
        if success:
            await self.bot.db.set_social_post_status(self.post_id, "published")
            await self.status_updater("published")
            await interaction.followup.send("✅ Post published now.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to publish post.", ephemeral=True)

    @discord.ui.button(label="Schedule...", style=discord.ButtonStyle.secondary)
    async def schedule(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SchedulePostModal(self.bot, self.post_id, self.status_updater))


class SchedulePostModal(discord.ui.Modal, title="Schedule Post"):
    when_input = discord.ui.TextInput(
        label="When",
        placeholder="YYYY-MM-DD HH:MM (UTC) or 'now'",
        required=False,
        max_length=64
    )

    def __init__(self, bot, post_id: int, status_updater):
        super().__init__()
        self.bot = bot
        self.post_id = post_id
        self.status_updater = status_updater

    async def on_submit(self, interaction: discord.Interaction):
        raw = (str(self.when_input.value) or "").strip().lower()
        if raw in ("", "now"):
            # Immediate publish
            post = await self.bot.db.get_social_post_by_id(self.post_id)
            if not post:
                await interaction.response.send_message("❌ Post not found.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True, thinking=True)
            success = await self.bot.publish_social_post(post)
            if success:
                await self.bot.db.set_social_post_status(self.post_id, "published")
                await self.status_updater("published")
                await interaction.followup.send("✅ Post published now.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to publish post.", ephemeral=True)
            return

        # Parse datetime
        dt = None
        try:
            try:
                # Try ISO 8601 with or without 'T'
                cleaned = raw.replace('t', ' ').replace('z', '')
                dt = datetime.fromisoformat(cleaned)
            except Exception:
                pass
            if dt is None:
                # Try common "YYYY-MM-DD HH:MM" pattern
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
            # Assume naive is UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            await interaction.response.send_message("❌ Invalid datetime. Use YYYY-MM-DD HH:MM (UTC) or 'now'.", ephemeral=True)
            return

        iso = dt.astimezone(timezone.utc).isoformat()
        updated = await self.bot.db.set_social_post_status(self.post_id, "scheduled", iso)
        if updated:
            await self.status_updater("scheduled")
            await interaction.response.send_message(f"🗓️ Post scheduled for {iso}.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to schedule post.", ephemeral=True)
