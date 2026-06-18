from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department


def list_active_departments(db: Session) -> list[Department]:
    stmt = select(Department).where(Department.is_active.is_(True)).order_by(Department.name.asc())
    return list(db.execute(stmt).scalars())


def slug_code(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_").upper()
    return value[:80] or "DEPARTMENT"


def unique_code(db: Session, name: str, current_id: int | None = None) -> str:
    base_code = slug_code(name)
    code = base_code
    counter = 2
    while True:
        existing = db.execute(select(Department).where(Department.code == code)).scalar_one_or_none()
        if not existing or existing.id == current_id:
            return code
        suffix = f"_{counter}"
        code = f"{base_code[:80 - len(suffix)]}{suffix}"
        counter += 1


def create_department(db: Session, *, name: str) -> Department:
    clean_name = name.strip()
    existing = db.execute(select(Department).where(Department.name == clean_name)).scalar_one_or_none()
    if existing:
        existing.is_active = True
        existing.code = existing.code or unique_code(db, clean_name, current_id=existing.id)
        return existing
    department = Department(name=clean_name, code=unique_code(db, clean_name), is_active=True)
    db.add(department)
    return department


def update_department(db: Session, *, department: Department, name: str) -> Department:
    clean_name = name.strip()
    existing = db.execute(select(Department).where(Department.name == clean_name)).scalar_one_or_none()
    if existing and existing.id != department.id:
        raise ValueError("Tên phòng ban đã tồn tại.")
    department.name = clean_name
    department.code = unique_code(db, clean_name, current_id=department.id)
    department.is_active = True
    return department


def delete_department(department: Department) -> None:
    department.is_active = False
