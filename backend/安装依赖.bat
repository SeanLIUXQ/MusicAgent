@echo off
chcp 65001 >nul
echo ========================================
echo    MusicAgent 依赖安装脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python！
    echo 请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/
    pause
    exit /b 1
)

echo [信息] 检测到Python版本:
python --version
echo.

REM 检查是否在backend目录
if not exist "requirements.txt" (
    echo [警告] 未找到requirements.txt文件
    echo 请确保在backend目录下运行此脚本
    echo.
    pause
    exit /b 1
)

echo [信息] 开始安装依赖包...
echo.

REM 升级pip
echo [步骤1/2] 升级pip到最新版本...
python -m pip install --upgrade pip
echo.

REM 安装依赖
echo [步骤2/2] 安装项目依赖...
pip install -r requirements.txt
echo.

if %errorlevel% equ 0 (
    echo ========================================
    echo    安装完成！
    echo ========================================
    echo.
    echo 已安装的核心包:
    echo   - openai (DeepSeek API)
    echo   - PyQt5 (桌面应用界面)
    echo   - music21 (音乐处理)
    echo   - mido (MIDI文件处理)
    echo   - flask (Web后端)
    echo.
    echo 提示: 请配置DeepSeek API密钥后再运行应用
    echo.
) else (
    echo ========================================
    echo    安装失败！
    echo ========================================
    echo.
    echo 请检查:
    echo 1. 网络连接是否正常
    echo 2. 是否有管理员权限
    echo 3. Python版本是否符合要求
    echo.
)

pause
