@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
set "result=%errorlevel%"
if not "%result%"=="0" echo Setup did not complete. Read the message above and docs\TROUBLESHOOTING.md.
pause
exit /b %result%
