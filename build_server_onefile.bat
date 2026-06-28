@echo off
setlocal
cd /d %~dp0

set PYTHON_EXE=python
if exist ".venv\Scripts\python.exe" set PYTHON_EXE=.venv\Scripts\python.exe

echo [1/3] Kiem tra moi truong build offline...
%PYTHON_EXE% -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
  echo Loi: Thieu PyInstaller trong moi truong hien tai.
  echo Build offline khong tu tai goi tu Internet.
  echo Hay cai san goi bang wheel/noi bo roi chay lai build_server_onefile.bat.
  exit /b 1
)

%PYTHON_EXE% -c "import pystray" >nul 2>nul
if errorlevel 1 (
  echo Loi: Thieu pystray trong moi truong hien tai.
  echo Build offline khong tu tai goi tu Internet.
  echo Hay cai san requirements tu kho wheel/noi bo roi chay lai build_server_onefile.bat.
  exit /b 1
)

echo [2/3] Dong goi server onefile...
%PYTHON_EXE% -m PyInstaller ^
  --clean ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name ATG_Document_Manager_Server ^
  --icon "icon.ico" ^
  --add-data "app\templates;app\templates" ^
  --add-data "app\static;app\static" ^
  --add-data "icon.ico;." ^
  --add-data "logo.png;." ^
  --hidden-import passlib.handlers.bcrypt ^
  --hidden-import pymysql ^
  --hidden-import pystray ^
  --hidden-import pystray._win32 ^
  --hidden-import uvicorn.lifespan.on ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websockets.auto ^
  server_onefile.py
if errorlevel 1 exit /b 1

echo [3/3] Hoan tat.
echo File server: %CD%\dist\ATG_Document_Manager_Server.exe
echo.
echo Luu y:
echo - Dat config.json va license.key cung thu muc voi file exe neu da co san.
echo - Neu chua co license, dang nhap root va vao Cau hinh he thong de lay ma may va gan license.
echo - Server chay an o khay he thong. Bam icon ATG de mo web hoac thoat server.
echo - Build nay khong phu thuoc CDN/API online; static/templates duoc dong goi local.
endlocal
