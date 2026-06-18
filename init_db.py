from __future__ import annotations

from sqlalchemy import or_, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import get_config
from app.database import Base, engine
from app.models import Department, DocumentType, User
from app.security import hash_password


def ensure_database() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def seed_default_users(db: Session) -> None:
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

    admin = db.query(User).filter(User.username == "admin").one_or_none()
    if not admin:
        db.add(
            User(
                username="admin",
                password_hash=hash_password("atg_123456"),
                full_name="Administrator",
                role="admin",
                status="active",
            )
        )
    else:
        admin.password_hash = hash_password("atg_123456")
        admin.full_name = admin.full_name or "Administrator"
        admin.role = "admin"
        admin.status = "active"


def seed_lookup_data(db: Session) -> None:
    for name, code in [
        ("Van phong", "VAN_PHONG"),
        ("To chuc - Hanh chinh", "TO_CHUC_HANH_CHINH"),
        ("Tai chinh - Ke toan", "TAI_CHINH_KE_TOAN"),
    ]:
        exists = db.query(Department).filter(or_(Department.code == code, Department.name == name)).one_or_none()
        if not exists:
            db.add(Department(name=name, code=code))
        else:
            exists.code = exists.code or code
            exists.is_active = True

    for name, code, branch in [
        ("Cong van", "CONG_VAN", "outgoing"),
        ("To trinh", "TO_TRINH", "outgoing"),
        ("De xuat", "DE_XUAT", "outgoing"),
        ("Bao cao", "BAO_CAO", "outgoing"),
    ]:
        exists = db.query(DocumentType).filter(or_(DocumentType.code == code, DocumentType.name == name)).one_or_none()
        if not exists:
            db.add(DocumentType(name=name, code=code, branch=branch))
        else:
            exists.code = exists.code or code
            exists.branch = exists.branch or branch
            exists.is_active = True


def column_exists(db: Session, table_name: str, column_name: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
              AND column_name = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).scalar_one()
    return int(row) > 0


def run_migrations(db: Session) -> None:
    if not column_exists(db, "document_types", "branch"):
        db.execute(text("ALTER TABLE document_types ADD COLUMN branch VARCHAR(20) NOT NULL DEFAULT 'outgoing'"))
        db.execute(text("CREATE INDEX ix_document_types_branch ON document_types (branch)"))
        db.execute(
            text(
                """
                UPDATE document_types
                SET branch = 'incoming'
                WHERE name LIKE '%Đến%'
                   OR name LIKE '%đến%'
                   OR name LIKE '%Nhận%'
                   OR name LIKE '%nhận%'
                   OR name LIKE '%Vào%'
                   OR name LIKE '%vào%'
                """
            )
        )

    if not column_exists(db, "documents", "due_date"):
        db.execute(text("ALTER TABLE documents ADD COLUMN due_date DATE NULL, ADD INDEX ix_documents_due_date (due_date)"))
    if not column_exists(db, "documents", "sender_department"):
        db.execute(text("ALTER TABLE documents ADD COLUMN sender_department VARCHAR(255) NULL, ADD INDEX ix_documents_sender_department (sender_department)"))
    if not column_exists(db, "documents", "receiver_department"):
        db.execute(text("ALTER TABLE documents ADD COLUMN receiver_department VARCHAR(255) NULL, ADD INDEX ix_documents_receiver_department (receiver_department)"))
    if not column_exists(db, "documents", "reminder_dismissed_at"):
        db.execute(text("ALTER TABLE documents ADD COLUMN reminder_dismissed_at DATETIME NULL"))
    if not column_exists(db, "documents", "reminder_dismissed_by"):
        db.execute(text("ALTER TABLE documents ADD COLUMN reminder_dismissed_by INT NULL"))

    db.execute(
        text(
            """
            UPDATE documents
            SET document_code = LPAD(id, 5, '0')
            WHERE document_code IS NULL
               OR document_code = ''
               OR document_code NOT REGEXP '^[0-9]+$'
            """
        )
    )


def seed_defaults(db: Session) -> None:
    seed_default_users(db)
    seed_lookup_data(db)


def main() -> None:
    try:
        ensure_database()
        Base.metadata.create_all(bind=engine)
        with Session(engine) as db:
            run_migrations(db)
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
        print("1. Kiem tra config.json da dung user/password MariaDB.")
        print("2. Tao database/user theo config bang lenh:")
        print("   .\\setup_mariadb.bat")
        print("3. Sau do chay lai:")
        print("   .\\.venv\\Scripts\\python.exe init_db.py")
        print("")
        print(f"Loi goc: {exc}")
        raise SystemExit(1) from exc

    print("Da khoi tao database va tai khoan mac dinh.")
    print("Root username: root")
    print("Root password: admin@123")
    print("Admin username: admin")
    print("Admin password: atg_123456")


if __name__ == "__main__":
    main()
