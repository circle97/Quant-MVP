cd $PSScriptRoot\..
.\venv\Scripts\Activate.ps1
Write-Host "正在运行A股数据演示..." -ForegroundColor Green
python scripts\demo_astock_data.py