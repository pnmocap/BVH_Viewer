@echo off
REM BVH Viewer 一键启动脚本（源码版）
REM 双击此文件即可运行程序

echo ========================================
echo   BVH Viewer 启动中...
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python 环境！
    echo 请确保已安装 Python 3.8+ 并添加到 PATH
    pause
    exit /b 1
)

REM 检查主程序文件
if not exist "bvh_visualizer_improved.py" (
    echo [错误] 未找到主程序文件！
    echo 请确保此脚本在项目根目录
    pause
    exit /b 1
)

REM 启动应用程序
echo [启动] 运行 BVH Viewer...
echo.
python bvh_visualizer_improved.py

REM 如果程序异常退出，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo [错误] 程序异常退出
    pause
)
