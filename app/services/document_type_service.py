from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_type import DocumentType

DOCUMENT_TYPE_BRANCHES = {
    "incoming": "Văn bản nhận về",
    "outgoing": "Văn bản đề xuất đi",
}


def normalize_branch(branch: str | None) -> str:
    return branch if branch in DOCUMENT_TYPE_BRANCHES else "outgoing"


def list_active_document_types(db: Session, branch: str | None = None) -> list[DocumentType]:
    stmt = select(DocumentType).where(DocumentType.is_active.is_(True))
    if branch:
        stmt = stmt.where(DocumentType.branch == normalize_branch(branch))
    return list(
        db.execute(
            stmt.order_by(DocumentType.branch.asc(), DocumentType.name.asc())
        ).scalars()
    )


def slug_code(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_").upper()
    return value[:80] or "DOCUMENT_TYPE"


def unique_code(db: Session, name: str, current_id: int | None = None) -> str:
    base_code = slug_code(name)
    code = base_code
    counter = 2
    while True:
        existing = db.execute(select(DocumentType).where(DocumentType.code == code)).scalar_one_or_none()
        if not existing or existing.id == current_id:
            return code
        suffix = f"_{counter}"
        code = f"{base_code[:80 - len(suffix)]}{suffix}"
        counter += 1


def create_document_type(db: Session, *, name: str, branch: str | None) -> DocumentType:
    clean_name = name.strip()
    existing = db.execute(select(DocumentType).where(DocumentType.name == clean_name)).scalar_one_or_none()
    if existing:
        existing.is_active = True
        existing.branch = normalize_branch(branch)
        return existing
    document_type = DocumentType(
        name=clean_name,
        code=unique_code(db, clean_name),
        branch=normalize_branch(branch),
        is_active=True,
    )
    db.add(document_type)
    return document_type


def update_document_type(db: Session, *, document_type: DocumentType, name: str, branch: str | None) -> DocumentType:
    clean_name = name.strip()
    existing = db.execute(select(DocumentType).where(DocumentType.name == clean_name)).scalar_one_or_none()
    if existing and existing.id != document_type.id:
        raise ValueError("Tên phân loại văn bản đã tồn tại.")
    document_type.name = clean_name
    document_type.code = unique_code(db, clean_name, current_id=document_type.id)
    document_type.branch = normalize_branch(branch)
    document_type.is_active = True
    return document_type


def branch_for_document_type_name(db: Session, name: str | None) -> str:
    if not name:
        return "outgoing"
    document_type = db.execute(select(DocumentType).where(DocumentType.name == name)).scalar_one_or_none()
    return normalize_branch(document_type.branch if document_type else None)


def delete_document_type(document_type: DocumentType) -> None:
    document_type.is_active = False
