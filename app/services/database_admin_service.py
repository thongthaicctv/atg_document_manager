from __future__ import annotations

from pathlib import Path

import pymysql
from sqlalchemy import create_engine

from app.config import get_config, get_database_url
from init_db import initialize_database


def initialize_configured_database() -> None:
    engine = create_engine(get_database_url(), pool_pre_ping=True, pool_recycle=3600, future=True)
    try:
        initialize_database(engine)
    finally:
        engine.dispose()


def _sql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _sql_identifier(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


def create_database_and_user(*, admin_host: str, admin_user: str, admin_password: str) -> None:
    config = get_config()
    db_config = config["database"]
    database = str(db_config["database"])
    app_user = str(db_config["user"])
    app_password = str(db_config["password"])
    host = admin_host.strip() or str(db_config["host"])
    user = admin_user.strip() or "root"

    statements = [
        f"""
        CREATE DATABASE IF NOT EXISTS {_sql_identifier(database)}
          CHARACTER SET utf8mb4
          COLLATE utf8mb4_unicode_ci
        """,
        f"CREATE USER IF NOT EXISTS {_sql_string(app_user)}@'localhost' IDENTIFIED BY {_sql_string(app_password)}",
        f"CREATE USER IF NOT EXISTS {_sql_string(app_user)}@'127.0.0.1' IDENTIFIED BY {_sql_string(app_password)}",
        f"ALTER USER {_sql_string(app_user)}@'localhost' IDENTIFIED BY {_sql_string(app_password)}",
        f"ALTER USER {_sql_string(app_user)}@'127.0.0.1' IDENTIFIED BY {_sql_string(app_password)}",
        f"GRANT ALL PRIVILEGES ON {_sql_identifier(database)}.* TO {_sql_string(app_user)}@'localhost'",
        f"GRANT ALL PRIVILEGES ON {_sql_identifier(database)}.* TO {_sql_string(app_user)}@'127.0.0.1'",
        "FLUSH PRIVILEGES",
    ]

    connection = pymysql.connect(
        host=host,
        port=int(db_config["port"]),
        user=user,
        password=admin_password,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
    finally:
        connection.close()


def reset_database_and_user(*, admin_host: str, admin_user: str, admin_password: str) -> None:
    config = get_config()
    db_config = config["database"]
    database = str(db_config["database"])
    host = admin_host.strip() or str(db_config["host"])
    user = admin_user.strip() or "root"

    connection = pymysql.connect(
        host=host,
        port=int(db_config["port"]),
        user=user,
        password=admin_password,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {_sql_identifier(database)}")
    finally:
        connection.close()

    create_database_and_user(admin_host=admin_host, admin_user=admin_user, admin_password=admin_password)


def _iter_sql_statements(sql_text: str):
    statement: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0
    length = len(sql_text)

    while index < length:
        char = sql_text[index]
        next_char = sql_text[index + 1] if index + 1 < length else ""

        if quote:
            statement.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue

        if char in {"'", '"', "`"}:
            quote = char
            statement.append(char)
            index += 1
            continue

        if char == "-" and next_char == "-" and (index + 2 >= length or sql_text[index + 2].isspace()):
            index += 2
            while index < length and sql_text[index] not in "\r\n":
                index += 1
            continue

        if char == "#":
            index += 1
            while index < length and sql_text[index] not in "\r\n":
                index += 1
            continue

        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < length and not (sql_text[index] == "*" and sql_text[index + 1] == "/"):
                index += 1
            index += 2
            continue

        if char == ";":
            sql = "".join(statement).strip()
            if sql:
                yield sql
            statement = []
            index += 1
            continue

        statement.append(char)
        index += 1

    sql = "".join(statement).strip()
    if sql:
        yield sql


def _should_skip_restore_statement(statement: str) -> bool:
    normalized = statement.lstrip().upper()
    return normalized.startswith(("CREATE DATABASE", "DROP DATABASE", "USE "))


def restore_sql_backup(sql_path: str) -> int:
    clean_value = sql_path.strip()
    if not clean_value:
        raise ValueError("Đường dẫn file backup SQL không được để trống.")

    backup_file = Path(clean_value).expanduser()
    if not backup_file.is_absolute():
        raise ValueError("Vui lòng nhập đường dẫn tuyệt đối tới file .sql trên máy cài server.")
    if not backup_file.exists() or not backup_file.is_file():
        raise ValueError("Không tìm thấy file backup SQL.")
    if backup_file.suffix.lower() != ".sql":
        raise ValueError("File phục hồi phải có định dạng .sql.")

    sql_text = backup_file.read_text(encoding="utf-8-sig")
    config = get_config()
    db_config = config["database"]
    connection = pymysql.connect(
        host=str(db_config["host"]),
        port=int(db_config["port"]),
        user=str(db_config["user"]),
        password=str(db_config["password"]),
        database=str(db_config["database"]),
        charset="utf8mb4",
        autocommit=False,
    )
    restored_count = 0
    try:
        with connection.cursor() as cursor:
            for statement in _iter_sql_statements(sql_text):
                if _should_skip_restore_statement(statement):
                    continue
                cursor.execute(statement)
                restored_count += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return restored_count


def ensure_backup_directory(path_value: str) -> str:
    clean_value = path_value.strip()
    if not clean_value:
        raise ValueError("Đường dẫn thư mục backup không được để trống.")

    backup_dir = Path(clean_value).expanduser()
    if not backup_dir.is_absolute():
        raise ValueError("Vui lòng nhập đường dẫn tuyệt đối tới thư mục backup trên máy cài server.")

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(f"Không tạo được thư mục backup: {exc}") from exc
    if not backup_dir.is_dir():
        raise ValueError("Đường dẫn backup không phải là thư mục.")
    return str(backup_dir)
