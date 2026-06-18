from __future__ import annotations

import json
import os
import shutil
import subprocess
from getpass import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.json"


def sql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def sql_identifier(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


def find_mysql_exe() -> str:
    env_path = os.environ.get("MYSQL_EXE")
    if env_path and Path(env_path).exists():
        return env_path

    path = shutil.which("mysql")
    if path:
        return path

    candidates = [
        r"C:\Program Files\MariaDB 11.4\bin\mysql.exe",
        r"C:\Program Files\MariaDB 11.3\bin\mysql.exe",
        r"C:\Program Files\MariaDB 11.2\bin\mysql.exe",
        r"C:\Program Files\MariaDB 10.11\bin\mysql.exe",
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    raise SystemExit(
        "Khong tim thay mysql.exe. Hay cai MariaDB client hoac set bien MYSQL_EXE "
        "tro toi mysql.exe, vi du: $env:MYSQL_EXE='C:\\Program Files\\MariaDB 11.4\\bin\\mysql.exe'"
    )


def build_sql() -> str:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    db = config["database"]
    database = str(db["database"])
    user = str(db["user"])
    password = str(db["password"])
    return f"""
CREATE DATABASE IF NOT EXISTS {sql_identifier(database)}
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS {sql_string(user)}@'localhost'
  IDENTIFIED BY {sql_string(password)};

CREATE USER IF NOT EXISTS {sql_string(user)}@'127.0.0.1'
  IDENTIFIED BY {sql_string(password)};

ALTER USER {sql_string(user)}@'localhost'
  IDENTIFIED BY {sql_string(password)};

ALTER USER {sql_string(user)}@'127.0.0.1'
  IDENTIFIED BY {sql_string(password)};

GRANT ALL PRIVILEGES ON {sql_identifier(database)}.*
  TO {sql_string(user)}@'localhost';

GRANT ALL PRIVILEGES ON {sql_identifier(database)}.*
  TO {sql_string(user)}@'127.0.0.1';

FLUSH PRIVILEGES;
"""


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    db = config["database"]
    mysql_exe = find_mysql_exe()
    print("Cong cu nay se tao database/user cho ung dung theo config.json.")
    print(f"Ung dung se dung user: {db['user']}")
    print(f"Ung dung se dung password: {db['password']}")
    print("")
    print("Ben duoi la thong tin tai khoan QUAN TRI MariaDB de tao user o tren.")
    print("Neu khong chac, thu bam Enter o 2 dong dau de dung root@localhost.")
    print("")
    root_user = input("User quan tri MariaDB [root] - KHONG nhap password tai dong nay: ").strip() or "root"
    if "@" in root_user:
        print("Ban vua nhap chuoi co dau @ vao o user. O nay chi nen la ten user, vi du: root")
        print("Hay chay lai .\\setup_mariadb.bat va bam Enter tai dong user neu muon dung root.")
        raise SystemExit(1)
    root_host = input("Host MariaDB [localhost] - bam Enter de dung localhost: ").strip() or "localhost"
    root_password = getpass("Password cua user quan tri MariaDB (mat khau root MariaDB): ")
    command = [
        mysql_exe,
        "-h",
        root_host,
        "-P",
        str(db["port"]),
        "-u",
        root_user,
        "--default-character-set=utf8mb4",
    ]
    if root_password:
        command.insert(-1, f"-p{root_password}")
    result = subprocess.run(command, input=build_sql(), text=True, capture_output=True)
    if result.returncode != 0:
        print("Khong tao duoc database/user MariaDB.")
        print(result.stderr.strip() or result.stdout.strip())
        raise SystemExit(result.returncode)

    print("Da tao/cap nhat database va user theo config.json:")
    print(f"Database: {db['database']}")
    print(f"User: {db['user']}")
    print(f"Password: {db['password']}")


if __name__ == "__main__":
    main()
