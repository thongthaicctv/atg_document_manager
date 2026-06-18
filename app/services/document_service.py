from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Select, and_, false, func, or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.constants import DOCUMENT_STATUSES
from app.models.document import Document
from app.models.document_log import DocumentLog
from app.models.document_permission import DocumentPermission
from app.models.user import User
from app.services.log_service import write_log

RECEIVED_TIME_PREFIX = "Giờ nhận:"


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
    sender_department: str | None = None,
    receiver_department: str | None = None,
    status: str | None = None,
    document_type: str | None = None,
    received_only: bool = False,
    document_type_names: list[str] | None = None,
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
    if sender_department:
        filters.append(Document.sender_department.like(f"%{sender_department.strip()}%"))
    if receiver_department:
        filters.append(Document.receiver_department.like(f"%{receiver_department.strip()}%"))
    if status:
        filters.append(Document.status == status)
    if document_type:
        filters.append(Document.document_type.like(f"%{document_type.strip()}%"))
    if document_type_names is not None:
        filters.append(Document.document_type.in_(document_type_names) if document_type_names else false())
    elif received_only:
        filters.append(
            or_(
                Document.document_type.like("%Đến%"),
                Document.document_type.like("%đến%"),
                Document.document_type.like("%Nhận%"),
                Document.document_type.like("%nhận%"),
                Document.document_type.like("%Vào%"),
                Document.document_type.like("%vào%"),
            )
        )
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
                Document.sender_department.like(q),
                Document.receiver_department.like(q),
            )
        )
    if filters:
        stmt = stmt.where(and_(*filters))
    return stmt.order_by(Document.updated_at.desc(), Document.created_at.desc())


def search_documents(db: Session, **filters) -> list[Document]:
    return list(db.execute(build_document_query(**filters)).scalars().unique())


def extract_received_time(note: str | None) -> str:
    for line in (note or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(RECEIVED_TIME_PREFIX):
            return stripped.removeprefix(RECEIVED_TIME_PREFIX).strip()
    return ""


def strip_received_time_note(note: str | None) -> str:
    lines = [
        line
        for line in (note or "").splitlines()
        if not line.strip().startswith(RECEIVED_TIME_PREFIX)
    ]
    return "\n".join(lines).strip()


def merge_note_with_received_time(note: str | None, received_time: str | None) -> str | None:
    cleaned_note = strip_received_time_note(note)
    if received_time:
        lines = [line for line in [cleaned_note, f"{RECEIVED_TIME_PREFIX} {received_time}"] if line]
        return "\n".join(lines)
    return cleaned_note or None


def preview_next_document_code(db: Session) -> str:
    try:
        next_id = db.execute(
            text(
                """
                SELECT AUTO_INCREMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'documents'
                """
            )
        ).scalar_one_or_none()
    except SQLAlchemyError:
        next_id = None

    if not next_id:
        next_id = (db.execute(select(func.max(Document.id))).scalar_one_or_none() or 0) + 1
    return f"{int(next_id):05d}"


def create_document(
    db: Session,
    *,
    user: User,
    ip_address: str | None,
    document_number: str | None,
    title: str,
    summary: str | None,
    content: str | None,
    document_type: str | None,
    proposer_name: str | None,
    department: str | None,
    sender_department: str | None,
    receiver_department: str | None,
    priority: str,
    due_date: date | None,
    note: str | None,
) -> Document:
    document = Document(
        document_code=None,
        document_number=document_number or None,
        title=title.strip(),
        summary=summary or None,
        content=content or None,
        document_type=document_type or None,
        proposer_name=proposer_name or user.full_name,
        department=department or user.department,
        sender_department=sender_department or None,
        receiver_department=receiver_department or None,
        owner_id=user.id,
        created_by=user.id,
        updated_by=user.id,
        status="new_draft",
        priority=priority,
        due_date=due_date,
        note=note or None,
    )
    db.add(document)
    db.flush()
    document.document_code = f"{document.id:05d}"
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
    document_number: str | None,
    title: str,
    summary: str | None,
    content: str | None,
    document_type: str | None,
    proposer_name: str | None,
    department: str | None,
    sender_department: str | None,
    receiver_department: str | None,
    priority: str,
    due_date: date | None,
    note: str | None,
) -> Document:
    document.document_number = document_number or None
    document.title = title.strip()
    document.summary = summary or None
    document.content = content or None
    document.document_type = document_type or None
    document.proposer_name = proposer_name or None
    document.department = department or None
    document.sender_department = sender_department or None
    document.receiver_department = receiver_department or None
    document.priority = priority
    document.due_date = due_date
    if due_date is None:
        document.reminder_dismissed_at = None
        document.reminder_dismissed_by = None
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
    effective_leader_name = leader_name.strip() if leader_name else None
    document.status = new_status
    document.leader_name = effective_leader_name or document.leader_name
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
        leader_name=document.leader_name or None,
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


def due_documents_for_user(db: Session, user: User, today: date | None = None) -> list[Document]:
    today = today or date.today()
    stmt = (
        select(Document)
        .where(
            Document.due_date.is_not(None),
            Document.due_date <= today,
            Document.reminder_dismissed_at.is_(None),
            Document.status.notin_(["issued", "archived", "cancelled"]),
        )
        .order_by(Document.due_date.asc(), Document.id.asc())
    )
    if user.role not in {"root", "admin"}:
        stmt = stmt.where(
            or_(
                Document.owner_id == user.id,
                Document.permissions.any(
                    and_(
                        DocumentPermission.user_id == user.id,
                        DocumentPermission.can_view.is_(True),
                    )
                ),
            )
        )
    return list(db.execute(stmt).scalars().unique())


def dismiss_due_reminders(db: Session, *, document_ids: list[int], user: User, dont_remind: bool) -> None:
    if not dont_remind:
        return
    if not document_ids:
        return
    documents = db.execute(select(Document).where(Document.id.in_(document_ids))).scalars().all()
    for document in documents:
        document.reminder_dismissed_at = datetime.utcnow()
        document.reminder_dismissed_by = user.id
