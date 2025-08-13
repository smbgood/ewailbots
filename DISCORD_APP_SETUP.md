# Discord Application Bot Setup Guide

This guide will help you set up the AI Employee Discord Bot using Discord Application credentials instead of traditional bot tokens.

## What Changed?

The bot uses prefix commands with Discord Application credentials, which provides:
-- Familiar command style with exclamation prefix
- Improved command discovery and autocomplete
- More robust command handling
- Better integration with Discord's UI

## Prerequisites

1. **Discord Developer Account**: You need a Discord account and access to the [Discord Developer Portal](https://discord.com/developers/applications)
2. **Python 3.8+**: The bot requires Python 3.8 or higher
3. **Discord Bot**: You still need to create a Discord bot (the token is still required for authentication)

## Step 1: Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give your application a name (e.g., "AI Employee Bot")
4. Click "Create"

## Step 2: Configure Your Application

### Basic Information
- **Application ID**: Copy this - you'll need it for `DISCORD_APPLICATION_ID`
- **Public Key**: Copy this - you'll need it for `DISCORD_PUBLIC_KEY`

### Bot Configuration
1. Go to the "Bot" section in the left sidebar
2. Click "Add Bot"
3. **Bot Token**: Copy this - you'll need it for `DISCORD_TOKEN`
4. Enable the following options:
   - ✅ **Message Content Intent**
   - ✅ **Server Members Intent**
   - ✅ **Presence Intent**

### OAuth2 Configuration
1. Go to the "OAuth2" section
2. **Client Secret**: Copy this - you'll need it for `DISCORD_CLIENT_SECRET`
3. In "OAuth2 URL Generator":
   - Select scopes: `bot` and `applications.commands`
   - Select bot permissions: `Send Messages`, `Embed Links`
4. Copy the generated URL to invite your bot to your server

## Step 3: Environment Configuration

Create a `.env` file in your project root with the following variables:

```env
# Discord Application Configuration (OAuth2/Application Commands)
DISCORD_APPLICATION_ID=your_discord_application_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_PUBLIC_KEY=your_discord_public_key_here

# Legacy Discord Bot Token (still required for authentication)
DISCORD_TOKEN=your_discord_bot_token_here

# Optional: Specific guild/server ID (for faster command syncing)
GUILD_ID=your_guild_id_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration (optional)
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
```

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 5: Run the Application Bot

### Option 1: Python Script
```bash
python run_app_bot.py
```

### Option 2: Windows Batch File
```bash
run_app_bot_windows.bat
```

### Option 3: Windows PowerShell
```powershell
.\run_app_bot_windows.ps1
```

## Available Commands

The bot uses prefix commands instead of slash commands:

### AI Employee Management (Prefix Commands)
- `!ai help` - Show help information
- `!ai create <name> <role> <personality>` - Create a new AI employee
- `!ai list` - List all AI employees
- `!ai info <name>` - Get employee information
- `!ai update <name> [new_name] [new_role] [new_personality]` - Update employee
- `!ai delete <name>` - Delete an employee

### Chat Commands
- `!chat message <employee> <message>` - Send a message to an AI employee
- `!chat ask <employee> <question>` - Ask an AI employee a question

### Admin Commands
- `!admin permissions <user> <level>` - Manage user permissions
- `!admin settings` - View bot configuration

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Ensure all required variables are set in your `.env` file
   - Check that the file is named exactly `.env` (not `.env.txt`)

2. **"Discord login failed"**
   - Verify your bot token is correct
   - Ensure the bot hasn't been deleted from the Developer Portal
   - Check that the bot has the required permissions

3. **"Commands not appearing"**
   - Commands may take up to 1 hour to appear globally
   - For faster syncing, set a specific `GUILD_ID`
   - Ensure the bot has the `applications.commands` scope

4. **"Permission denied"**
   - Check that your user ID is in the `ADMIN_USER_IDS` list in `config.py`
   - Verify the bot has the required permissions in your Discord server

### Command Syncing

The bot automatically syncs commands when it starts. You can see the sync status in the console output:
- Guild-specific sync: Faster, commands appear immediately
- Global sync: Slower, commands may take up to 1 hour to appear

## Migration from Old Bot

If you're migrating from the old bot:

1. **Keep your existing bot token** - it's still needed for authentication
2. **Add the new application credentials** to your `.env` file
3. **Use the new runner scripts** (`run_app_bot.py` instead of `run_bot.py`)
4. **Update your commands** - use slash commands instead of prefix commands

## Security Notes

- **Never share your bot token or client secret**
- **Keep your `.env` file private** and don't commit it to version control
- **Use environment variables** in production deployments
- **Regularly rotate your credentials** for security

## Support

If you encounter issues:

1. Check the console output for error messages
2. Verify your environment variables are correct
3. Ensure your Discord application is properly configured
4. Check that the bot has the required permissions in your server

## Additional Resources

- [Discord Developer Documentation](https://discord.com/developers/docs)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
-- [Discord Bot Guide](https://discordpy.readthedocs.io/en/stable/)
