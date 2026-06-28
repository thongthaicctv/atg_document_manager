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
  echo Hay cai san goi bang wheel/noi bo roi chay lai build_license_tool_onefile.bat.
  exit /b 1
)

echo [2/2] Dong goi license_tool onefile...
%PYTHON_EXE% -m PyInstaller ^
  --clean ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name ATG_License_Tool ^
  --hidden-import pymysql ^
  --hidden-import tkinter ^
  --hidden-import tkinter.ttk ^
  --hidden-import tkinter.filedialog ^
  --hidden-import tkinter.messagebox ^
  --hidden-import tkinter.simpledialog ^
  license_tool.py
if errorlevel 1 exit /b 1

echo Hoan tat.
echo File license tool: %CD%\dist\ATG_License_Tool.exe
echo Mat khau mo tool: antn@2016
echo Private key mac dinh: D:\ATG_DOCUMENT\license\atg_license_private.json
endlocal
