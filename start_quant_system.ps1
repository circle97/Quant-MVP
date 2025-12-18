#!/usr/bin/env pwsh
#
# Quant-MVP M7 量化交易系统快捷启动脚本
# 提供后端服务、Web界面的启动、停止、重启和状态查看功能
#

# 设置脚本字符编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# 脚本版本
$ScriptVersion = "1.0.0"

# 项目根目录
$ProjectRoot = $PSScriptRoot

# 激活虚拟环境的函数
function Activate-Venv {
    param (
        [string]$VenvPath = "$ProjectRoot\venv"
    )
    
    if (Test-Path "$VenvPath\Scripts\Activate.ps1") {
        & "$VenvPath\Scripts\Activate.ps1"
        Write-Host "已激活虚拟环境: $VenvPath" -ForegroundColor Green
        return $true
    } else {
        Write-Host "未找到虚拟环境: $VenvPath" -ForegroundColor Yellow
        return $false
    }
}

# 显示主菜单
function Show-MainMenu {
    Clear-Host
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "    Quant-MVP M7 量化交易系统管理工具    " -ForegroundColor Cyan
    Write-Host "                  版本 $ScriptVersion               " -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. 启动后端服务 (前台模式)" -ForegroundColor White
    Write-Host "2. 启动后端服务 (后台守护进程)" -ForegroundColor White
    Write-Host "3. 启动Web监控界面" -ForegroundColor White
    Write-Host "4. 停止后端服务" -ForegroundColor White
    Write-Host "5. 重启后端服务" -ForegroundColor White
    Write-Host "6. 查看服务状态" -ForegroundColor White
    Write-Host "7. 运行测试套件" -ForegroundColor White
    Write-Host "8. 退出" -ForegroundColor White
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
}

# 启动后端服务
function Start-BackendService {
    param (
        [bool]$Daemon = $false
    )
    
    Write-Host "正在启动后端服务..." -ForegroundColor Yellow
    
    if (Activate-Venv) {
        $Args = @("start")
        if ($Daemon) {
            $Args += "--daemon"
        }
        
        $Process = Start-Process -FilePath "python" -ArgumentList "$ProjectRoot\src\core\backend_service.py", $Args -Wait -PassThru
        
        if ($Process.ExitCode -eq 0) {
            Write-Host "后端服务启动成功!" -ForegroundColor Green
        } else {
            Write-Host "后端服务启动失败，退出码: $($Process.ExitCode)" -ForegroundColor Red
        }
    }
}

# 停止后端服务
function Stop-BackendService {
    Write-Host "正在停止后端服务..." -ForegroundColor Yellow
    
    if (Activate-Venv) {
        $Process = Start-Process -FilePath "python" -ArgumentList "$ProjectRoot\src\core\backend_service.py", "stop" -Wait -PassThru
        
        if ($Process.ExitCode -eq 0) {
            Write-Host "后端服务停止成功!" -ForegroundColor Green
        } else {
            Write-Host "后端服务停止失败，退出码: $($Process.ExitCode)" -ForegroundColor Red
        }
    }
}

# 重启后端服务
function Restart-BackendService {
    Write-Host "正在重启后端服务..." -ForegroundColor Yellow
    
    if (Activate-Venv) {
        $Process = Start-Process -FilePath "python" -ArgumentList "$ProjectRoot\src\core\backend_service.py", "restart" -Wait -PassThru
        
        if ($Process.ExitCode -eq 0) {
            Write-Host "后端服务重启成功!" -ForegroundColor Green
        } else {
            Write-Host "后端服务重启失败，退出码: $($Process.ExitCode)" -ForegroundColor Red
        }
    }
}

# 查看服务状态
function Get-ServiceStatus {
    Write-Host "正在查看服务状态..." -ForegroundColor Yellow
    
    if (Activate-Venv) {
        $Process = Start-Process -FilePath "python" -ArgumentList "$ProjectRoot\src\core\backend_service.py", "status" -Wait -PassThru -NoNewWindow
        
        if ($Process.ExitCode -eq 0) {
            Write-Host "服务状态查询完成!" -ForegroundColor Green
        } else {
            Write-Host "服务状态查询失败，退出码: $($Process.ExitCode)" -ForegroundColor Red
        }
    }
}

# 启动Web监控界面
function Start-WebInterface {
    Write-Host "正在启动Web监控界面..." -ForegroundColor Yellow
    
    if (Activate-Venv) {
        Write-Host "Web界面将在浏览器中打开，访问地址: http://localhost:8501" -ForegroundColor Cyan
        Write-Host "按 Ctrl+C 停止Web界面" -ForegroundColor Magenta
        Write-Host ""
        
        # 启动Streamlit应用
        $Process = Start-Process -FilePath "streamlit" -ArgumentList "run", "$ProjectRoot\src\web\app.py" -Wait -PassThru
        
        if ($Process.ExitCode -eq 0) {
            Write-Host "Web界面已停止" -ForegroundColor Green
        } else {
            Write-Host "Web界面异常停止，退出码: $($Process.ExitCode)" -ForegroundColor Red
        }
    }
}

# 运行测试套件
function Run-Tests {
    Write-Host "正在运行测试套件..." -ForegroundColor Yellow
    
    if (Activate-Venv) {
        $Process = Start-Process -FilePath "python" -ArgumentList "-m", "pytest", "-v" -Wait -PassThru
        
        if ($Process.ExitCode -eq 0) {
            Write-Host "测试全部通过!" -ForegroundColor Green
        } else {
            Write-Host "部分测试失败，退出码: $($Process.ExitCode)" -ForegroundColor Red
        }
    }
}

# 主函数
function Main {
    while ($true) {
        Show-MainMenu
        
        $Choice = Read-Host "请选择操作 (1-8)"
        Write-Host ""
        
        switch ($Choice) {
            "1" {
                Start-BackendService -Daemon $false
            }
            "2" {
                Start-BackendService -Daemon $true
            }
            "3" {
                Start-WebInterface
            }
            "4" {
                Stop-BackendService
            }
            "5" {
                Restart-BackendService
            }
            "6" {
                Get-ServiceStatus
            }
            "7" {
                Run-Tests
            }
            "8" {
                Write-Host "感谢使用 Quant-MVP M7 量化交易系统管理工具!" -ForegroundColor Cyan
                Write-Host "再见!" -ForegroundColor Cyan
                exit 0
            }
            default {
                Write-Host "无效的选择，请输入 1-8 之间的数字" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "按任意键返回主菜单..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

# 检查是否以管理员身份运行
# 注意：在Windows上，普通用户也可以运行此脚本

# 调用主函数
Main
