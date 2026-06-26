@echo off
cd /d %~dp0
if exist "dist\ATG_Document_Manager_Server.exe" (
  start "" "%~dp0dist\ATG_Document_Manager_Server.exe"
  exit /b
)
if exist ".venv\Scripts\pythonw.exe" (
  start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0server_onefile.py"
  exit /b
)
start "" pythonw "%~dp0server_onefile.py"
exit /b
