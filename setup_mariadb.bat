@echo off
cd /d %~dp0
cmd /c "mysql -u root -p < setup_mariadb.sql"
