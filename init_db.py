from __future__ import annotations

from sqlalchemy import or_, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import get_config
from app.database import Base, engine
from app.models import Department, DocumentType, User
from app.security import hash_password


def _mysql_error_code(exc: OperationalError) -> int | None:
    original = getattr(exc, "orig", None)
    args = getattr(original, "args", ())
    if not args:
        return None
    try:
        return int(args[0])
    except (TypeError, ValueError):
        return None


def _is_table_exists_error(exc: OperationalError) -> bool:
    return _mysql_error_code(exc) == 1050 or "already exists" in str(exc).lower()


def ensure_database(target_engine=None) -> None:
    active_engine = target_engine or engine
    with active_engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def create_schema_tables(target_engine=None) -> None:
    active_engine = target_engine or engine
    for table in Base.metadata.sorted_tables:
        try:
            table.create(bind=active_engine, checkfirst=False)
        except OperationalError as exc:
            if _is_table_exists_error(exc):
                continue
            raise


def seed_default_users(db: Session) -> None:
    root = db.query(User).filter(User.username == "root").one_or_none()
    if not root:
        db.add(
            User(
                username="root",
                password_hash=hash_password("Nongdan80B"),
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
        admin.full_name = admin.full_name or "Administrator"


def seed_lookup_data(db: Session) -> None:
    for name, code in [
        ("Ban 1", "BAN_1"),
        ("Ban 2", "BAN_2"),
        ("Ban 6", "BAN_6"),
    ]:
        exists = db.query(Department).filter(or_(Department.code == code, Department.name == name)).one_or_none()
        if not exists:
            db.add(Department(name=name, code=code))
        else:
            exists.code = exists.code or code
            exists.is_active = True

    for name, code, branch in [
        ("Công văn đến", "CONG_VAN_DEN", "incoming"),
        ("Cong van", "CONG_VAN", "outgoing"),
        ("To trinh", "TO_TRINH", "outgoing"),
        ("De xuat", "DE_XUAT", "outgoing"),
        ("Bao cao", "BAO_CAO", "outgoing"),
    ]:
        matches = db.query(DocumentType).filter(or_(DocumentType.code == code, DocumentType.name == name)).all()
        exists = next((item for item in matches if item.code == code), None) or (matches[0] if matches else None)
        if not exists:
            db.add(DocumentType(name=name, code=code, branch=branch))
        else:
            if name == "Công văn đến" and exists.name == "Cong van den":
                vietnamese_type = (
                    db.query(DocumentType)
                    .filter(DocumentType.id != exists.id, DocumentType.branch == "incoming", DocumentType.name.like("%Công%Văn%Đến%"))
                    .one_or_none()
                )
                if vietnamese_type:
                    exists.is_active = False
                    vietnamese_type.is_active = True
                    vietnamese_type.branch = branch
                    continue
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
    if not column_exists(db, "documents", "incoming_action"):
        db.execute(text("ALTER TABLE documents ADD COLUMN incoming_action VARCHAR(50) NULL, ADD INDEX ix_documents_incoming_action (incoming_action)"))
    if not column_exists(db, "documents", "source_document_id"):
        db.execute(text("ALTER TABLE documents ADD COLUMN source_document_id INT NULL, ADD INDEX ix_documents_source_document_id (source_document_id)"))
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


def initialize_database(target_engine=None) -> None:
    active_engine = target_engine or engine
    ensure_database(active_engine)
    create_schema_tables(active_engine)
    with Session(active_engine) as db:
        run_migrations(db)
        seed_defaults(db)
        db.commit()


def main() -> None:
    try:
        initialize_database()
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
    print("Root password mac dinh khi tao moi: Nongdan80B")
    print("Admin username: admin")
    print("Admin password mac dinh khi tao moi: atg_123456")


if __name__ == "__main__":
    main()
