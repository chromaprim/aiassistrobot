@echo off
call "%~dp0manage.cmd" start
set "result=%errorlevel%"
pause
exit /b %result%
