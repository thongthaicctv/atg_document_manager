@echo off
setlocal
cd /d %~dp0

set PYTHON_EXE=python
if exist ".venv\Scripts\python.exe" set PYTHON_EXE=.venv\Scripts\python.exe

echo [1/2] Kiem tra moi truong build offline...
%PYTHON_EXE% -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
  echo Loi: Thieu PyInstaller trong moi truong hien tai.
  echo Build offline khong tu tai goi tu Internet.
  echo Hay cai san goi bang wheel/noi bo roi chay lai build_root_recovery_tool_onefile.bat.
  exit /b 1
)

echo [2/2] Dong goi root recovery onefile...
%PYTHON_EXE% -m PyInstaller ^
  --clean ^
  --noconfirm ^
  --onefile ^
  --console ^
  --name ATG_Root_Recovery_Tool ^
  --icon "icon.ico" ^
  --hidden-import passlib.handlers.bcrypt ^
  --hidden-import pymysql ^
  root_recovery_tool.py
if errorlevel 1 exit /b 1

echo Hoan tat.
echo File khoi phuc root: %CD%\dist\ATG_Root_Recovery_Tool.exe
echo Dat file exe cung thu muc voi config.json tren may server roi chay de reset mat khau root.
endlocal
