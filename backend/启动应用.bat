@echo off
chcp 65001 >nul
echo ========================================
echo    MusicAgent 启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python！
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 检查gui_app.py是否存在
if not exist "gui_app.py" (
    echo [错误] 未找到gui_app.py文件
    echo 请确保在backend目录下运行此脚本
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 依赖包未安装！
    echo.
    echo 是否现在安装依赖？(Y/N)
    set /p choice=请选择: 
    if /i "%choice%"=="Y" (
        echo.
        echo 正在安装依赖...
        call 安装依赖.bat
        echo.
    ) else (
        echo.
        echo 请先运行"安装依赖.bat"安装依赖包
        pause
        exit /b 1
    )
)

echo [信息] 正在启动MusicAgent桌面应用...
echo.
echo ----------------------------------------
echo  提示:
echo  1. 请确保已配置DeepSeek API密钥
echo  2. 使用前请先安装并打开Sonic Pi
echo  3. 生成的MIDI文件保存在midi_output目录
echo ----------------------------------------
echo.

REM 启动应用
python gui_app.py

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo    应用异常退出
    echo ========================================
    echo.
    echo 可能的原因:
    echo 1. API密钥未配置或无效
    echo 2. 依赖包安装不完整
    echo 3. 网络连接问题
    echo.
    echo 请检查上方的错误信息
    echo.
)

pause
