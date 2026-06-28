@echo off
cd /d %~dp0
set PYTHONUTF8=1
set ATG_SERVER_CONSOLE=1
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" server_onefile.py --console
  exit /b %ERRORLEVEL%
)
python server_onefile.py --console
exit /b %ERRORLEVEL%
