@echo off
cd /d %~dp0\..
call venv\Scripts\activate.bat
echo 正在运行A股数据演示...
python scripts\demo_astock_data.py
pause