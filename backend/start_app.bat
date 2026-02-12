@echo off
echo ========================================
echo    MusicAgent Startup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not detected!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if gui_app.py exists
if not exist "gui_app.py" (
    echo [ERROR] gui_app.py not found
    echo Please run this script in the backend directory
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Dependencies not installed!
    echo.
    echo Install dependencies now? (Y/N)
    set /p choice=Your choice: 
    if /i "%choice%"=="Y" (
        echo.
        echo Installing dependencies...
        call install_deps.bat
        echo.
    ) else (
        echo.
        echo Please run "install_deps.bat" first
        pause
        exit /b 1
    )
)

echo [INFO] Starting MusicAgent desktop application...
echo.
echo ----------------------------------------
echo  Important Notes:
echo  1. Configure DeepSeek API key first
echo  2. Install and open Sonic Pi before use
echo  3. MIDI files saved in midi_output/
echo ----------------------------------------
echo.

REM Start application
python gui_app.py

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo    Application Exited Abnormally
    echo ========================================
    echo.
    echo Possible causes:
    echo 1. API key not configured or invalid
    echo 2. Incomplete dependency installation
    echo 3. Network connection issues
    echo.
    echo Please check error message above
    echo.
)

pause
