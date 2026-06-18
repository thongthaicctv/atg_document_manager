from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.constants import DOCUMENT_STATUSES
from app.models.document import Document
from app.models.document_log import DocumentLog
from app.models.user import User
from app.services.log_service import write_log


def _date_start(value: date | None) -> datetime | None:
    return datetime.combine(value, time.min) if value else None


def _date_end(value: date | None) -> datetime | None:
    return datetime.combine(value, time.max) if value else None


def build_document_query(
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    document_number: str | None = None,
    title: str | None = None,
    proposer_name: str | None = None,
    created_by_name: str | None = None,
    owner_name: str | None = None,
    department: str | None = None,
    status: str | None = None,
    document_type: str | None = None,
    quick: str | None = None,
) -> Select[tuple[Document]]:
    stmt = select(Document)
    filters = []
    if from_date:
        filters.append(Document.created_at >= _date_start(from_date))
    if to_date:
        filters.append(Document.created_at <= _date_end(to_date))
    if document_number:
        filters.append(Document.document_number.like(f"%{document_number.strip()}%"))
    if title:
        filters.append(Document.title.like(f"%{title.strip()}%"))
    if proposer_name:
        filters.append(Document.proposer_name.like(f"%{proposer_name.strip()}%"))
    if owner_name:
        filters.append(Document.owner.has(User.full_name.like(f"%{owner_name.strip()}%")))
    if department:
        filters.append(Document.department.like(f"%{department.strip()}%"))
    if status:
        filters.append(Document.status == status)
    if document_type:
        filters.append(Document.document_type.like(f"%{document_type.strip()}%"))
    if created_by_name:
        filters.append(Document.creator.has(User.full_name.like(f"%{created_by_name.strip()}%")))
    if quick:
        q = f"%{quick.strip()}%"
        filters.append(
            or_(
                Document.document_code.like(q),
                Document.document_number.like(q),
                Document.title.like(q),
                Document.summary.like(q),
                Document.proposer_name.like(q),
                Document.department.like(q),
            )
        )
    if filters:
        stmt = stmt.where(and_(*filters))
    return stmt.order_by(Document.updated_at.desc(), Document.created_at.desc())


def search_documents(db: Session, **filters) -> list[Document]:
    return list(db.execute(build_document_query(**filters)).scalars().unique())


def create_document(
    db: Session,
    *,
    user: User,
    ip_address: str | None,
    document_code: str | None,
    document_number: str | None,
    title: str,
    summary: str | None,
    content: str | None,
    document_type: str | None,
    proposer_name: str | None,
    department: str | None,
    priority: str,
    note: str | None,
) -> Document:
    document = Document(
        document_code=document_code or None,
        document_number=document_number or None,
        title=title.strip(),
        summary=summary or None,
        content=content or None,
        document_type=document_type or None,
        proposer_name=proposer_name or user.full_name,
        department=department or user.department,
        owner_id=user.id,
        created_by=user.id,
        updated_by=user.id,
        status="new_draft",
        priority=priority,
        note=note or None,
    )
    db.add(document)
    db.flush()
    write_log(
        db,
        document_id=document.id,
        action="create_document",
        performed_by=user.id,
        new_status=document.status,
        note="Tạo văn bản đề xuất.",
        ip_address=ip_address,
    )
    return document


def update_document(
    db: Session,
    *,
    document: Document,
    user: User,
    ip_address: str | None,
    document_code: str | None,
    document_number: str | None,
    title: str,
    summary: str | None,
    content: str | None,
    document_type: str | None,
    proposer_name: str | None,
    department: str | None,
    priority: str,
    note: str | None,
) -> Document:
    document.document_code = document_code or None
    document.document_number = document_number or None
    document.title = title.strip()
    document.summary = summary or None
    document.content = content or None
    document.document_type = document_type or None
    document.proposer_name = proposer_name or None
    document.department = department or None
    document.priority = priority
    document.note = note or None
    document.updated_by = user.id
    write_log(
        db,
        document_id=document.id,
        action="update_document",
        performed_by=user.id,
        note="Cập nhật thông tin văn bản.",
        ip_address=ip_address,
    )
    return document


def update_document_status(
    db: Session,
    *,
    document: Document,
    user: User,
    ip_address: str | None,
    new_status: str,
    leader_name: str | None,
    actual_date: date | None,
    note: str | None,
) -> Document:
    old_status = document.status
    document.status = new_status
    document.leader_name = leader_name or document.leader_name
    document.updated_by = user.id
    actual_datetime = datetime.combine(actual_date, time.min) if actual_date else datetime.utcnow()

    if new_status == "submitted_to_leader":
        document.submitted_to_leader_at = actual_datetime
    elif new_status == "leader_approved":
        document.approved_at = actual_datetime
    elif new_status == "issued":
        document.issued_at = actual_datetime
    elif new_status == "archived":
        document.archived_at = actual_datetime

    label = DOCUMENT_STATUSES.get(new_status, new_status)
    write_log(
        db,
        document_id=document.id,
        action="update_status",
        performed_by=user.id,
        old_status=old_status,
        new_status=new_status,
        leader_name=leader_name or None,
        note=note or f"Cập nhật trạng thái: {label}",
        ip_address=ip_address,
    )
    return document


def count_by_status(db: Session) -> dict[str, int]:
    rows = db.execute(select(Document.status, func.count(Document.id)).group_by(Document.status)).all()
    counts = {status: 0 for status in DOCUMENT_STATUSES}
    counts.update({status: int(count) for status, count in rows})
    counts["total"] = int(db.execute(select(func.count(Document.id))).scalar_one())
    return counts


def latest_document_note(db: Session, document_id: int) -> str:
    log = db.execute(
        select(DocumentLog)
        .where(DocumentLog.document_id == document_id)
        .order_by(DocumentLog.performed_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return log.note if log and log.note else ""
