@echo off
setlocal
cd /d "%~dp0.."

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.10 or newer is required.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 exit /b 1

echo Installing backend dependencies...
".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 exit /b 1

where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js 20.19+ and npm are required to build the browser workspace.
  exit /b 1
)

echo Installing and building the frontend...
pushd frontend
call npm install
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
popd

echo Installation complete.
