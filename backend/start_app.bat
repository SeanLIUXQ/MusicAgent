@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo Runtime not installed. Running dependency setup...
  call backend\install_deps.bat
  if errorlevel 1 exit /b 1
)

if not exist "frontend\dist\index.html" (
  where npm >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Frontend build missing and npm is not available.
    exit /b 1
  )
  pushd frontend
  call npm install
  if errorlevel 1 exit /b 1
  call npm run build
  if errorlevel 1 exit /b 1
  popd
)

".venv\Scripts\python.exe" backend\gui_app.py
