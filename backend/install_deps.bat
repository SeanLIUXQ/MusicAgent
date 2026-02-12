@echo off
echo ========================================
echo    MusicAgent Dependency Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not detected!
    echo Please install Python 3.8 or higher
    echo Download: https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Python version detected:
python --version
echo.

REM Check if in backend directory
if not exist "requirements.txt" (
    echo [WARNING] requirements.txt not found
    echo Please run this script in the backend directory
    echo.
    pause
    exit /b 1
)

echo [INFO] Installing dependencies...
echo.

REM Upgrade pip
echo [Step 1/2] Upgrading pip to latest version...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [Step 2/2] Installing project dependencies...
pip install -r requirements.txt
echo.

if %errorlevel% equ 0 (
    echo ========================================
    echo    Installation Complete!
    echo ========================================
    echo.
    echo Installed core packages:
    echo   - openai (DeepSeek API)
    echo   - PyQt5 (Desktop GUI)
    echo   - music21 (Music processing)
    echo   - mido (MIDI file handling)
    echo   - flask (Web backend)
    echo.
    echo NOTE: Please configure DeepSeek API key before running
    echo.
) else (
    echo ========================================
    echo    Installation Failed!
    echo ========================================
    echo.
    echo Please check:
    echo 1. Network connection is normal
    echo 2. Administrator privileges available
    echo 3. Python version meets requirements
    echo.
)

pause
