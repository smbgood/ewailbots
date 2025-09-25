import os
from typing import List, Dict, Any
from dotenv import load_dotenv, find_dotenv

# Load environment variables
print("🔧 Loading configuration from environment variables...")
dotenv_path = find_dotenv(usecwd=True)
load_dotenv(dotenv_path=dotenv_path)
if dotenv_path:
    try:
        print(f"📄 .env loaded from: {dotenv_path}")
    except Exception:
        # Avoid encoding issues on some consoles
        pass

class Config:
    # Discord Application Configuration (OAuth2/Application Commands)
    DISCORD_APPLICATION_ID = os.getenv('DISCORD_APPLICATION_ID')
    DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
    DISCORD_PUBLIC_KEY = os.getenv('DISCORD_PUBLIC_KEY')
    
    # Legacy bot token support (for backward compatibility)
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    GUILD_ID = int(os.getenv('GUILD_ID', 0))
    
    # Log configuration status
    print(f"📋 Configuration loaded:")
    print(f"   DISCORD_APPLICATION_ID: {'✅ Set' if DISCORD_APPLICATION_ID else '❌ Missing'}")
    print(f"   DISCORD_CLIENT_SECRET: {'✅ Set' if DISCORD_CLIENT_SECRET else '❌ Missing'}")
    print(f"   DISCORD_PUBLIC_KEY: {'✅ Set' if DISCORD_PUBLIC_KEY else '❌ Missing'}")
    print(f"   DISCORD_TOKEN: {'✅ Set (legacy)' if DISCORD_TOKEN else '❌ Missing (legacy)'}")
    print(f"   GUILD_ID: {'✅ Set' if GUILD_ID else '❌ Missing (optional)'}")
    print(f"   OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"   SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing (optional)'}")
    # Do not print keys themselves; only signal presence for debugging
    print(f"   SUPABASE_ANON_KEY: {'✅ Set' if os.getenv('SUPABASE_ANON_KEY') else '❌ Missing'}")
    print(f"   SUPABASE_SERVICE_ROLE_KEY: {'✅ Set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '❌ Missing'}")
    
    # Admin Configuration
    ADMIN_USER_IDS: List[int] = [
        # Add admin user IDs here
        1404951216215294024
    ]
    
    # AI Employee Configuration
    DEFAULT_AI_PARAMS = {
        "temperature": 0.7,
        "max_tokens": 1000,
        "model": "gpt-3.5-turbo",
        "personality": "helpful and professional"
    }
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Permission Levels
    PERMISSION_LEVELS = {
        "ADMIN": 3,      # Full control
        "MODERATOR": 2,  # Can manage employees
        "USER": 1        # Basic access
    }
    
    # Employee Types
    EMPLOYEE_TYPES = {
        "SUPPORT": "Customer support specialist",
        "SALES": "Sales representative", 
        "TECH": "Technical support",
        "GENERAL": "General assistant"
    }

    # Facebook/Instagram Graph API
    FACEBOOK_GRAPH_API_VERSION = os.getenv('FACEBOOK_GRAPH_API_VERSION', 'v23.0')

    # Log selected Graph API version
    try:
        print(f"   FACEBOOK_GRAPH_API_VERSION: {FACEBOOK_GRAPH_API_VERSION}")
    except Exception:
        pass

    # Linear integration (optional)
    LINEAR_API_KEY = os.getenv('LINEAR_API_KEY')
    LINEAR_TEAM_ID = os.getenv('LINEAR_TEAM_ID')
    LINEAR_PROJECT_ID = os.getenv('LINEAR_PROJECT_ID')  # Optional default project
    try:
        print(f"   LINEAR_API_KEY: {'✅ Set' if LINEAR_API_KEY else '❌ Missing'}")
        print(f"   LINEAR_TEAM_ID: {'✅ Set' if LINEAR_TEAM_ID else '❌ Missing'}")
        print(f"   LINEAR_PROJECT_ID: {'✅ Set' if LINEAR_PROJECT_ID else '❌ Missing (optional)'}")
    except Exception:
        pass