@echo off
cd /d %~dp0
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" setup_mariadb_from_config.py
) else (
  python setup_mariadb_from_config.py
)
