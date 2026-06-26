@echo off
setlocal
cd /d %~dp0

set PYTHON_EXE=python
if exist ".venv\Scripts\python.exe" set PYTHON_EXE=.venv\Scripts\python.exe

echo [1/2] Kiem tra PyInstaller...
%PYTHON_EXE% -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
  echo PyInstaller chua co, dang cai vao moi truong hien tai...
  %PYTHON_EXE% -m pip install pyinstaller
  if errorlevel 1 exit /b 1
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
