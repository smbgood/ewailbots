@echo off
chcp 65001 >nul
echo 🚀 Starting AI Employee Discord Application Bot...
echo 📱 This bot uses Discord Application credentials and prefix commands (!)
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo 💡 Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found
    echo 💡 Please create a .env file with your Discord Application credentials
    echo 📋 See env_example.txt for reference
    pause
    exit /b 1
)

echo ✅ Environment file found
echo 🔧 Starting Discord Application Bot...
echo.

REM Run the application bot
python run_app_bot.py

echo.
echo Bot has stopped. Press any key to exit...
pause >nul
