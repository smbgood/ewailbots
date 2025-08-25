# 🤖 AI Employee Discord Bot

A powerful Discord bot that manages multiple AI "employees" with different personalities and roles. The bot provides an admin interface for controlling AI parameters, sending messages through different employees, and managing user permissions.

## ✨ Features

- **Multiple AI Employees**: Create and manage different AI personalities with customizable parameters
- **Role-Based Access Control**: Admin, Moderator, and User permission levels
- **Channel & DM Support**: Send messages as AI employees to any channel or user
- **Parameter Control**: Adjust temperature, model, personality, and other AI parameters
- **Conversation History**: Track and manage AI employee interactions
- **Bulk Operations**: Create multiple employees at once with JSON configuration
- **Real-time Management**: Activate/deactivate employees and update parameters on the fly
 - **Social Posting**: Draft, schedule, and publish to Instagram and Facebook Pages

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (Windows 10 compatible)
- Discord Bot Token
- OpenAI API Key
- Discord Server (Guild) ID
- Supabase Account (free tier available)

### Bot Types

This project now supports two types of Discord bots:

1. **Traditional Bot** (`discord_bot.py`) - Uses prefix commands (!help, !create, etc.)
2. **Application Bot** (`discord_app_bot.py`) - Uses prefix commands (!help, !ai create, etc.)

**Recommendation**: Use the Application Bot for better user experience and modern Discord features.

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ewailbots
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   > **Note**: This project now uses Windows-compatible dependencies to avoid compilation issues on Windows 10.

3. **Set up environment variables**
   ```bash
   # Copy the example file
   cp env_example.txt .env
   
   # Edit .env with your actual values
   DISCORD_TOKEN=your_discord_bot_token_here
   GUILD_ID=your_guild_id_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Configure admin users**
   Edit `config.py` and add your Discord user ID to the `ADMIN_USER_IDS` list.

5. **Choose your bot type and run it**

   **Option A: Application Bot (Recommended)**
   ```bash
   # Set up Discord Application credentials in .env
   python run_app_bot.py
   ```
   
   **Option B: Traditional Bot**
   ```bash
   python run_bot.py
   ```
   
   > **Note**: For the Application Bot, you'll need additional Discord Application credentials. See [DISCORD_APP_SETUP.md](DISCORD_APP_SETUP.md) for detailed setup instructions.

## 🔧 Configuration

### Admin Users
Add your Discord user ID to the `ADMIN_USER_IDS` list in `config.py`:
```python
ADMIN_USER_IDS: List[int] = [
    123456789012345678,  # Your Discord ID
]
```

### Employee Types
The bot comes with predefined employee types:
- **SUPPORT**: Customer support specialist
- **SALES**: Sales representative
- **TECH**: Technical support
- **GENERAL**: General assistant

### Default AI Parameters
```python
DEFAULT_AI_PARAMS = {
    "temperature": 0.7,
    "max_tokens": 1000,
    "model": "gpt-3.5-turbo",
    "personality": "helpful and professional"
}
```

## 📚 Commands

### Application Bot Commands (Prefix Commands)

**AI Employee Management (Prefix Commands)**
- `!ai help` - Show help information
- `!ai create <name> <role> <personality>` - Create new AI employee
- `!ai list` - List all employees
- `!ai info <name>` - Get employee details
- `!ai update <name> [new_name] [new_role] [new_personality]` - Update employee
- `!ai delete <name>` - Delete an employee

**Chat Commands**
- `!chat message <employee> <message>` - Send message to AI employee
- `!chat ask <employee> <question>` - Ask AI employee a question

**Admin Commands**
- `!admin permissions <user> <level>` - Manage user permissions
- `!admin settings` - View bot configuration

### Traditional Bot Commands (Prefix Commands - Legacy)

**Admin Commands (Level 3)**
- `!create_employee <name> <type> [parameters]` - Create new AI employee
- `!deactivate_employee <name>` - Deactivate an employee
- `!update_employee <name> <json_parameters>` - Update employee parameters
- `!set_permission <user> <level>` - Set user permission level
- `!bulk_create <json_config>` - Create multiple employees

**Moderator Commands (Level 2)**
- `!list_employees` - List all active employees
- `!employee_info <name>` - Get employee details
- `!reset_conversation <name>` - Reset conversation history
- `!conversation_summary <name>` - Get conversation summary
- `!send_as <employee> <channel> <message>` - Send message as employee
- `!dm_as <employee> <user> <message>` - Send DM as employee

### User Commands (Level 1)
- `!help_ai` - Show AI employee help
- `!stats` - Show employee statistics

### Utility Commands
- `!ping` - Check bot latency
- `!status` - Show bot status

## 💬 Using AI Employees

### Direct Interaction
Use the `@` prefix to talk to AI employees directly:
```
@Darah Hello! How can you help me today?
@Bob What's the weather like?
```

### Sending Messages as Employees
Moderators can send messages as specific employees:
```
!send_as Darah #general Hello everyone! I'm here to help with support questions.
!dm_as Bob @user Welcome to our server!
```

## 🎯 Examples

### Creating an Employee
```
!create_employee Darah SUPPORT {"temperature": 0.8, "personality": "friendly and empathetic", "assistant_id": "asst_CSLH7PCfBuy7Xk68VkgvuSlx"}
```

### Bulk Employee Creation
```
!bulk_create [
  {"name": "Darah", "type": "SUPPORT", "parameters": {"temperature": 0.8, "assistant_id": "asst_CSLH7PCfBuy7Xk68VkgvuSlx"}},
  {"name": "Bob", "type": "SALES", "parameters": {"temperature": 0.9}},
  {"name": "Charlie", "type": "TECH", "parameters": {"temperature": 0.6}}
]
```

### Updating Parameters
```
!update_employee Darah {"temperature": 0.9, "max_tokens": 1500}
```

## 🔐 Permission Levels

- **Level 1 (USER)**: Basic access, can interact with AI employees
- **Level 2 (MODERATOR)**: Can manage employees and send messages as them
- **Level 3 (ADMIN)**: Full control, can create/delete employees and manage permissions

## 🗄️ Database

The bot uses Supabase to store:
- AI employee configurations
- User permissions
- Conversation history
- Employee statistics
- Social accounts and posts

## 🛠️ Customization

### Adding New Employee Types
Edit `config.py` and add new types to `EMPLOYEE_TYPES`:
```python
EMPLOYEE_TYPES = {
    "SUPPORT": "Customer support specialist",
    "SALES": "Sales representative",
    "TECH": "Technical support",
    "GENERAL": "General assistant",
    "CUSTOM": "Your custom role description"
}
```

### Custom AI Parameters
Each employee can have custom parameters:
```json
{
    "temperature": 0.8,
    "max_tokens": 2000,
    "model": "gpt-4",
    "personality": "professional and technical",
    "custom_field": "custom_value"
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**: Check if the bot has proper permissions in your Discord server
2. **AI responses failing**: Verify your OpenAI API key is valid and has credits
3. **Permission errors**: Ensure your user ID is in the admin list or has proper database permissions
4. **Database errors**: Check if the bot has write permissions in the current directory

### Token Issues

If you're getting "Improper token has been passed" errors:

1. **Test your configuration first**:
   ```bash
   # Windows Command Prompt
   test_config.bat
   
   # Windows PowerShell
   .\test_config.ps1
   
   # Or directly with Python
   python test_bot.py
   ```

2. **Common token problems**:
   - **Placeholder values**: Make sure you replaced `your_discord_bot_token_here` with your actual token
   - **Extra spaces**: Check your `.env` file for spaces around the `=` sign
   - **Wrong token**: Verify you're using the bot token, not the client secret
   - **Token format**: Discord bot tokens should be ~59 characters and start with `MTA`, `MTI`, or `OTk`

3. **Environment variable debugging**:
   The bot now provides detailed logging about token validation:
   - Token length and format
   - Environment variable loading status
   - Common configuration issues
   - File path and encoding problems

### Debug Mode
Enable debug logging by modifying the bot code or checking console output for error messages.

## 📝 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📞 Support

If you need help setting up or using the bot, please check the Discord documentation or open an issue in the repository.

## 📣 Social Posting

This project supports Instagram and Facebook Page posting using the Facebook Graph API.

### Configure Social Accounts (Supabase)

Insert rows into the `social_accounts` table with `account_key`, `platform`, and `credentials` JSON. See `supabase_migration.sql`.

Instagram `credentials` expected fields:
- `access_token`
- `ig_business_account_id`

Facebook Page `credentials` expected fields:
- `page_id`
- `page_access_token` (or `access_token`)

Graph API version is configurable via env: `FACEBOOK_GRAPH_API_VERSION` (default `v23.0`).

### Create Draft via Discord

```
!social "<prompt>" <account_key> <employee_name> <true|false|image_url> [draft|scheduled]
```

- Supports `platform` values `instagram` and `facebook` (Page), determined by the `social_accounts` row.
