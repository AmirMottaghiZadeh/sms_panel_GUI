@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 run_sms_panel.py
    exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
    python run_sms_panel.py
    exit /b %errorlevel%
)

echo Python 3 is required but was not found in PATH.
pause
exit /b 1
