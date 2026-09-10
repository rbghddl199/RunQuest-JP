@echo off
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%\frontend"
call npm run dev -- --host 127.0.0.1 --port 5173
endlocal
