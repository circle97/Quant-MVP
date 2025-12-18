@echo off
REM 
REM Quant-MVP M7 量化交易系统快捷启动脚本 (批处理版本)
REM 提供后端服务、Web界面的启动、停止、重启和状态查看功能
REM 

REM 设置字符编码为UTF-8
chcp 65001 >nul

REM 脚本版本
set "ScriptVersion=1.0.0"

REM 项目根目录
set "ProjectRoot=%~dp0"

REM 虚拟环境路径
set "VenvPath=%ProjectRoot%venv"

REM 服务脚本路径
set "BackendServiceScript=%ProjectRoot%src\core\backend_service.py"
set "WebAppScript=%ProjectRoot%src\web\app.py"

REM 显示主菜单
:ShowMainMenu
cls
color 0A
echo =========================================
echo    Quant-MVP M7 量化交易系统管理工具    
echo                  版本 %ScriptVersion%               
echo =========================================
echo.
echo 1. 启动后端服务 (前台模式)
echo 2. 启动后端服务 (后台守护进程)
echo 3. 启动Web监控界面
echo 4. 停止后端服务
echo 5. 重启后端服务
echo 6. 查看服务状态
echo 7. 运行测试套件
echo 8. 退出
echo.
echo =========================================
echo.

REM 获取用户选择
:GetChoice
choice /c 12345678 /n /m "请选择操作 (1-8): "

if errorlevel 8 goto ExitScript
if errorlevel 7 goto RunTests
if errorlevel 6 goto GetServiceStatus
if errorlevel 5 goto RestartBackendService
if errorlevel 4 goto StopBackendService
if errorlevel 3 goto StartWebInterface
if errorlevel 2 goto StartBackendServiceDaemon
if errorlevel 1 goto StartBackendServiceForeground

REM 激活虚拟环境
:ActivateVenv
if exist "%VenvPath%\Scripts\activate.bat" (
    call "%VenvPath%\Scripts\activate.bat"
    echo 已激活虚拟环境: %VenvPath%
    echo.
    exit /b 0
) else (
    echo 未找到虚拟环境: %VenvPath%
    echo.
    exit /b 1
)

REM 1. 启动后端服务 (前台模式)
:StartBackendServiceForeground
echo 正在启动后端服务 (前台模式)...
echo.
call :ActivateVenv
if %errorlevel% equ 0 (
    python "%BackendServiceScript%" start
    pause
    goto ShowMainMenu
)
pause
goto ShowMainMenu

REM 2. 启动后端服务 (后台守护进程)
:StartBackendServiceDaemon
echo 正在启动后端服务 (后台守护进程)...
echo.
call :ActivateVenv
if %errorlevel% equ 0 (
    python "%BackendServiceScript%" start --daemon
    pause
    goto ShowMainMenu
)
pause
goto ShowMainMenu

REM 3. 启动Web监控界面
:StartWebInterface
echo 正在启动Web监控界面...
echo.
echo Web界面将在浏览器中打开，访问地址: http://localhost:8501
echo 按 Ctrl+C 停止Web界面
echo.
call :ActivateVenv
if %errorlevel% equ 0 (
    streamlit run "%WebAppScript%"
    pause
    goto ShowMainMenu
)
pause
goto ShowMainMenu

REM 4. 停止后端服务
:StopBackendService
echo 正在停止后端服务...
echo.
call :ActivateVenv
if %errorlevel% equ 0 (
    python "%BackendServiceScript%" stop
    pause
    goto ShowMainMenu
)
pause
goto ShowMainMenu

REM 5. 重启后端服务
:RestartBackendService
echo 正在重启后端服务...
echo.
call :ActivateVenv
if %errorlevel% equ 0 (
    python "%BackendServiceScript%" restart
    pause
    goto ShowMainMenu
)
pause
goto ShowMainMenu

REM 6. 查看服务状态
:GetServiceStatus
echo 正在查看服务状态...
echo.
call :ActivateVenv
if %errorlevel% equ 0 (
    python "%BackendServiceScript%" status
    pause
    goto ShowMainMenu
)
pause
goto ShowMainMenu

REM 7. 跑测试套件
:RunTests
echo 正在跑测试套件...
echo.
call :ActivateVenv
if %errorlevel% equ 0 (
    python -m pytest -v
    pause
    goto ShowMainMenu
)
pause
goto ShowMainMenu

REM 8. 退出脚本
:ExitScript
echo.
echo 感谢使用 Quant-MVP M7 量化交易系统管理工具!
echo 再见!
echo.
pause
exit /b 0

REM 启动脚本主程序
goto ShowMainMenu
