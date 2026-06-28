from __future__ import annotations

import argparse
import getpass
import sys
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.config import get_config
from app.database import Base, SessionLocal, engine
from app.models import User  # noqa: F401 - import models so metadata is complete.
from app.security import hash_password


DEFAULT_ROOT_USERNAME = "root"
DEFAULT_ROOT_FULL_NAME = "Root Administrator"


def _mysql_error_code(exc: OperationalError) -> int | None:
    original = getattr(exc, "orig", None)
    args = getattr(original, "args", ())
    if not args:
        return None
    try:
        return int(args[0])
    except (TypeError, ValueError):
        return None


def _quote_identifier(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


def _try_create_database_if_missing() -> None:
    cfg = get_config()["database"]
    user = quote_plus(str(cfg["user"]))
    password = quote_plus(str(cfg["password"]))
    host = cfg["host"]
    port = cfg["port"]
    database = str(cfg["database"])
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/?charset=utf8mb4"
    bootstrap_engine = create_engine(url, future=True)
    try:
        with bootstrap_engine.begin() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS {_quote_identifier(database)} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        bootstrap_engine.dispose()


def _ensure_tables() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as exc:
        if _mysql_error_code(exc) != 1049:
            raise
        _try_create_database_if_missing()
        Base.metadata.create_all(bind=engine)


def _prompt_password(min_length: int) -> str:
    while True:
        password = getpass.getpass("Nhap mat khau moi cho root: ").strip()
        if len(password) < min_length:
            print(f"Mat khau toi thieu {min_length} ky tu.")
            continue
        confirm = getpass.getpass("Nhap lai mat khau moi: ").strip()
        if password != confirm:
            print("Hai lan nhap mat khau khong khop.")
            continue
        return password


def reset_root_password(username: str, password: str) -> str:
    _ensure_tables()
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).one_or_none()
        if user:
            user.password_hash = hash_password(password)
            user.role = "root"
            user.status = "active"
            user.full_name = user.full_name or DEFAULT_ROOT_FULL_NAME
            action = "Da reset mat khau tai khoan root hien co."
        else:
            user = User(
                username=username,
                password_hash=hash_password(password),
                full_name=DEFAULT_ROOT_FULL_NAME,
                role="root",
                status="active",
            )
            db.add(user)
            action = "Da tao moi tai khoan root."
        db.commit()
    return action


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cong cu khoi phuc tai khoan root cho ATG Document Manager.",
    )
    parser.add_argument(
        "--username",
        default=DEFAULT_ROOT_USERNAME,
        help="Ten tai khoan root can khoi phuc. Mac dinh: root.",
    )
    parser.add_argument(
        "--password",
        default="",
        help="Mat khau moi. Khuyen nghi bo trong de tool hoi mat khau an.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = get_config()
        min_length = int(config["security"].get("password_min_length", 6))
        password = args.password.strip() if args.password else _prompt_password(min_length)
        if len(password) < min_length:
            print(f"Loi: Mat khau toi thieu {min_length} ky tu.")
            return 2
        action = reset_root_password(args.username.strip() or DEFAULT_ROOT_USERNAME, password)
    except OperationalError as exc:
        cfg = get_config()["database"]
        print("Khong ket noi duoc MariaDB hoac khong du quyen tao database.")
        print(f"Host: {cfg['host']}:{cfg['port']}")
        print(f"User: {cfg['user']}")
        print(f"Database: {cfg['database']}")
        print("Hay kiem tra MariaDB dang chay va config.json dung user/password.")
        print(f"Loi goc: {exc}")
        return 1
    except SQLAlchemyError as exc:
        print("Khong cap nhat duoc tai khoan root trong database.")
        print(f"Loi goc: {exc}")
        return 1
    except Exception as exc:
        print("Khong khoi phuc duoc tai khoan root.")
        print(f"Loi goc: {exc}")
        return 1

    print(action)
    print(f"Username: {args.username.strip() or DEFAULT_ROOT_USERNAME}")
    print("Password: da cap nhat theo mat khau vua nhap.")
    print("Co the dang nhap web bang tai khoan root ngay bay gio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
