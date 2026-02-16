@echo off
echo ========================================
echo     俄罗斯方块游戏启动器
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python！
    echo 请从 https://www.python.org/downloads/ 下载并安装Python
    echo 安装时请勾选"Add Python to PATH"
    pause
    exit /b 1
)

REM 检查Pygame是否安装
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [警告] Pygame未安装，正在自动安装...
    pip install pygame
    if errorlevel 1 (
        echo [错误] Pygame安装失败！
        echo 请手动运行: pip install pygame
        pause
        exit /b 1
    )
    echo [成功] Pygame安装完成！
)

echo [信息] 正在启动俄罗斯方块游戏...
echo.
echo 游戏控制说明：
echo   ← → : 左右移动
echo   ↑    : 旋转方块
echo   ↓    : 加速下落
echo   空格 : 硬降落
echo   R    : 重新开始
echo   ESC  : 退出游戏
echo   A    : 切换AI模式
echo.
echo ========================================
echo.

REM 启动游戏
python tetris.py

if errorlevel 1 (
    echo [错误] 游戏启动失败！
    echo 请检查：
    echo 1. Python版本是否为3.11+
    echo 2. Pygame是否安装成功
    echo 3. tetris.py文件是否存在
    pause
    exit /b 1
)

echo.
echo 游戏已结束。
pause