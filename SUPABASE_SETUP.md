# Supabase Setup Guide

This guide will help you set up Supabase as your database backend for the Discord AI Employee Bot.

## Prerequisites

- A Supabase account (free tier available at [supabase.com](https://supabase.com))
- Python 3.8+ with pip

## Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/sign in
2. Click "New Project"
3. Choose your organization
4. Enter a project name (e.g., "discord-ai-bot")
5. Enter a database password (save this securely)
6. Choose a region close to your users
7. Click "Create new project"

## Step 2: Get Your Project Credentials

1. In your project dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (e.g., `https://abcdefghijklmnop.supabase.co`)
   - **anon public** key
   - **service_role** key (keep this secret!)

## Step 3: Set Up Environment Variables

1. Copy `env_example.txt` to `.env`
2. Fill in your Supabase credentials:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_guild_id_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

## Step 4: Create Database Tables

1. In your Supabase dashboard, go to **SQL Editor**
2. Copy the contents of `supabase_migration.sql`
3. Paste it into the SQL editor
4. Click "Run" to execute the migration

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 6: Test Your Setup

Run the bot to test the Supabase connection:

```bash
python run_bot.py
```

## Database Schema

The migration creates three main tables:

### `ai_employees`
- Stores AI employee configurations
- Uses JSONB for flexible parameter storage
- Includes active/inactive status tracking

### `user_permissions`
- Manages user permission levels
- Supports role-based access control

### `conversations`
- Logs all AI employee interactions
- Enables analytics and debugging

## Security Features

- **Row Level Security (RLS)** enabled by default
- **Public read access** for basic functionality
- **Authenticated user management** for data modifications
- **Indexes** for optimal query performance

## Troubleshooting

### Common Issues

1. **Connection Error**: Verify your SUPABASE_URL and SUPABASE_ANON_KEY
2. **Table Not Found**: Ensure you've run the migration script
3. **Permission Denied**: Check your RLS policies in Supabase

### Testing Database Connection

You can test your connection by running:

```python
from database import DatabaseManager

try:
    db = DatabaseManager()
    print("✅ Supabase connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Performance Tips

- Supabase automatically handles connection pooling
- Use the provided indexes for optimal query performance
- Consider enabling Supabase's real-time features for live updates
- Monitor your usage in the Supabase dashboard

## Support

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Discord](https://discord.supabase.com)
- [Python Supabase Client](https://github.com/supabase-community/supabase-py)
