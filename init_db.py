from __future__ import annotations

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import get_config
from app.database import Base, engine
from app.models import Department, DocumentType, User
from app.security import hash_password


def ensure_database() -> None:
    cfg = get_config()["database"]
    user = quote_plus(str(cfg["user"]))
    password = quote_plus(str(cfg["password"]))
    url = f"mysql+pymysql://{user}:{password}@{cfg['host']}:{cfg['port']}/?charset=utf8mb4"
    bootstrap_engine = create_engine(url, future=True)
    with bootstrap_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
        conn.commit()


def seed_defaults(db: Session) -> None:
    root = db.query(User).filter(User.username == "root").one_or_none()
    if not root:
        db.add(
            User(
                username="root",
                password_hash=hash_password("admin@123"),
                full_name="Root Administrator",
                role="root",
                status="active",
            )
        )

    for name, code in [
        ("Văn phòng", "VAN_PHONG"),
        ("Tổ chức - Hành chính", "TO_CHUC_HANH_CHINH"),
        ("Tài chính - Kế toán", "TAI_CHINH_KE_TOAN"),
    ]:
        exists = db.query(Department).filter(Department.code == code).one_or_none()
        if not exists:
            db.add(Department(name=name, code=code))

    for name, code in [
        ("Công văn", "CONG_VAN"),
        ("Tờ trình", "TO_TRINH"),
        ("Đề xuất", "DE_XUAT"),
        ("Báo cáo", "BAO_CAO"),
    ]:
        exists = db.query(DocumentType).filter(DocumentType.code == code).one_or_none()
        if not exists:
            db.add(DocumentType(name=name, code=code))


def main() -> None:
    try:
        ensure_database()
        Base.metadata.create_all(bind=engine)
        with Session(engine) as db:
            seed_defaults(db)
            db.commit()
    except OperationalError as exc:
        cfg = get_config()["database"]
        print("Khong ket noi duoc MariaDB voi cau hinh hien tai.")
        print(f"Host: {cfg['host']}:{cfg['port']}")
        print(f"User: {cfg['user']}")
        print(f"Database: {cfg['database']}")
        print("")
        print("Cach xu ly:")
        print("1. Mo file config.json va dien dung password MariaDB.")
        print("2. Neu chua tao user/database, chay lenh:")
        print("   mysql -u root -p < setup_mariadb.sql")
        print("3. Sau do chay lai:")
        print("   .\\.venv\\Scripts\\python.exe init_db.py")
        print("")
        print(f"Loi goc: {exc}")
        raise SystemExit(1) from exc
    print("Đã khởi tạo database và tài khoản root mặc định.")
    print("Username: root")
    print("Password: admin@123")


if __name__ == "__main__":
    main()
