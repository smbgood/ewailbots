# 🪟 Windows 10 Installation Guide

This guide helps you install the Discord AI Employee Bot on Windows 10 without encountering compilation issues.

## 🚨 Why This Guide?

The original dependencies (`asyncpg` and `pydantic`) have compilation issues on Windows 10 with Python 3.13. This project now uses Windows-compatible alternatives:

- **`httpx`** instead of `supabase` client (avoids `asyncpg` dependency)
- **`msgspec`** instead of `pydantic` (pure Python, no compilation needed)

## ✅ Prerequisites

- **Windows 10** (version 1903 or later)
- **Python 3.8+** (3.13 recommended)
- **Git** (optional, for cloning)

## 🚀 Installation Steps

### 1. Install Python

1. Download Python from [python.org](https://python.org)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

### 2. Clone/Download the Project

```cmd
git clone <your-repo-url>
cd ewailbots
```

Or download and extract the ZIP file.

### 3. Install Dependencies

**Option A: Use the installation script (Recommended)**
```cmd
# PowerShell (Run as Administrator)
.\install_windows.ps1

# Or Command Prompt (Run as Administrator)
install_windows.bat
```

**Option B: Manual installation**
```cmd
# Set compatibility environment variable
set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# Install dependencies
pip install -r requirements.txt
```

**Option C: If you still have issues**
```cmd
# Try the Windows-specific requirements
pip install -r requirements_windows.txt

# Or install packages individually
pip install discord.py==2.3.2 python-dotenv==1.0.0 openai>=1.99.9 asyncio-mqtt==0.16.1 aiohttp==3.9.1 msgspec==0.19.0 httpx==0.25.2 typing-extensions==4.8.0
```

The installation scripts will automatically try multiple approaches to avoid compilation errors!

### 4. Test Dependencies

Run the dependency test to verify everything works:

```cmd
python test_dependencies.py
```

You should see:
```
✅ httpx imported successfully
✅ msgspec imported successfully
✅ Database module imported successfully
✅ HTTP request test successful
✅ JSON encoding successful
✅ JSON decoding successful
✅ Data integrity verified
🎉 All dependency tests passed!
```

## 🔧 What Changed?

### Before (Problematic)
```txt
supabase==2.3.0      # Depends on asyncpg (compilation issues)
pydantic==2.5.0      # Compilation issues on Windows
asyncpg==0.29.0      # Direct compilation issues
openai==1.3.7        # Old version with problematic pydantic dependency
```

### After (Windows-Compatible)
```txt
httpx==0.25.2        # Pure Python HTTP client
msgspec==0.19.0      # Pure Python JSON library
openai>=1.99.9       # Newer version with Responses/Conversations support
# Removed: supabase, pydantic, asyncpg
# Updated: openai to newer version
```

## 🧪 Testing Your Setup

1. **Test dependencies**: `python test_dependencies.py`
2. **Test Supabase connection**: `python test_supabase.py`
3. **Test bot**: `python test_bot.py`

## 🆘 Troubleshooting

### "pydantic-core compilation failed"
This is the most common issue on Windows 10 with Python 3.13. The error shows:
```
error: the configured Python interpreter version (3.13) is newer than PyO3's maximum supported version (3.12)
```

**Solutions:**
1. **Use the installation scripts** (recommended):
   ```cmd
   .\install_windows.ps1
   # or
   install_windows.bat
   ```

2. **Set environment variable manually**:
   ```cmd
   set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
   pip install -r requirements.txt
   ```

3. **Use newer OpenAI version**:
   ```cmd
   pip install openai>=1.99.9
   ```

4. **Install packages individually**:
   ```cmd
   pip install discord.py==2.3.2 python-dotenv==1.0.0 openai>=1.99.9 asyncio-mqtt==0.16.1 aiohttp==3.9.1 msgspec==0.19.0 httpx==0.25.2 typing-extensions==4.8.0
   ```

### "pip install failed"
- Make sure you're using Python 3.8+
- Try: `pip install --upgrade pip`
- Try: `pip install --user -r requirements.txt`

### "Module not found"
- Verify Python is in your PATH
- Try: `python -m pip install -r requirements.txt`

### "Permission denied"
- Run Command Prompt as Administrator
- Or use: `pip install --user -r requirements.txt`

### Still having issues?
- Check Python version: `python --version`
- Check pip version: `pip --version`
- Try creating a virtual environment:
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  ```

## 🎯 Next Steps

Once dependencies are installed:

1. Copy `env_example.txt` to `.env`
2. Fill in your Discord and OpenAI credentials
3. Run `python discord_bot.py`

## 📚 Additional Resources

- [Python on Windows](https://docs.python.org/3/using/windows.html)
- [pip Installation](https://pip.pypa.io/en/stable/installation/)
- [Virtual Environments](https://docs.python.org/3/tutorial/venv.html)

---

**Need help?** Check the main README.md or create an issue in the repository.
