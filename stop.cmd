@echo off
call "%~dp0manage.cmd" stop
set "result=%errorlevel%"
pause
exit /b %result%
