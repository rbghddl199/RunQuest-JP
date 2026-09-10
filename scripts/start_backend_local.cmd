@echo off
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%\backend"
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
endlocal
