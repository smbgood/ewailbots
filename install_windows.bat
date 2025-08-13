@echo off
REM Windows Installation Script for Discord AI Employee Bot
REM This script helps avoid compilation issues on Windows 10 with Python 3.13

echo 🚀 Installing Discord AI Employee Bot Dependencies on Windows
echo ============================================================

REM Check Python version
echo 🔍 Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found in PATH
    echo 💡 Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)
python --version
echo ✅ Python found

REM Check pip
echo 🔍 Checking pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip not found, trying python -m pip...
    set USE_PYTHON_PIP=1
) else (
    echo ✅ pip found
    set USE_PYTHON_PIP=0
)

REM Set environment variables to help with Python 3.13 compatibility
echo 🔧 Setting environment variables for Python 3.13 compatibility...
set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
echo ✅ Set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

REM Upgrade pip first
echo ⬆️ Upgrading pip...
if %USE_PYTHON_PIP%==1 (
    python -m pip install --upgrade pip
) else (
    pip install --upgrade pip
)
if %errorlevel% neq 0 (
    echo ⚠️ pip upgrade failed, continuing anyway...
)

REM Try installing with main requirements first
echo 📦 Installing dependencies from requirements.txt...
if %USE_PYTHON_PIP%==1 (
    python -m pip install -r requirements.txt
) else (
    pip install -r requirements.txt
)

if %errorlevel% neq 0 (
    echo ❌ Main requirements failed, trying Windows-specific requirements...
    
    REM Try Windows-specific requirements
    echo 📦 Installing Windows-specific dependencies...
    if %USE_PYTHON_PIP%==1 (
        python -m pip install -r requirements_windows.txt
    ) else (
        pip install -r requirements_windows.txt
    )
    
    if %errorlevel% neq 0 (
        echo ❌ Windows-specific requirements also failed
        echo 💡 Trying alternative approach...
        
        REM Try installing packages individually with specific versions
        echo 📦 Installing packages individually...
        set packages=discord.py==2.3.2 python-dotenv==1.0.0 openai>=1.12.0 asyncio-mqtt==0.16.1 aiohttp==3.9.1 msgspec==0.19.0 httpx==0.25.2 typing-extensions==4.8.0
        
        for %%p in (%packages%) do (
            echo 📦 Installing %%p...
            if %USE_PYTHON_PIP%==1 (
                python -m pip install %%p
            ) else (
                pip install %%p
            )
            if !errorlevel! neq 0 (
                echo ❌ Failed to install %%p
            ) else (
                echo ✅ %%p installed successfully
            )
        )
    )
)

REM Test the installation
echo 🧪 Testing installation...
python test_dependencies.py
if %errorlevel% neq 0 (
    echo ⚠️ Some tests failed, but installation may still be usable
) else (
    echo ✅ All tests passed!
)

echo 🎉 Installation completed!
echo 💡 Next steps:
echo    1. Copy env_example.txt to .env
echo    2. Fill in your Discord and OpenAI credentials
echo    3. Run: python discord_bot.py

echo 🔧 If you still have issues, try:
echo    - Using a virtual environment
echo    - Installing Python 3.11 or 3.12 instead of 3.13
echo    - Running as Administrator

pause
