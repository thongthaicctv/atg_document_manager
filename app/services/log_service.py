from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.document_log import DocumentLog


def write_log(
    db: Session,
    *,
    action: str,
    performed_by: int | None,
    document_id: int | None = None,
    old_status: str | None = None,
    new_status: str | None = None,
    note: str | None = None,
    leader_name: str | None = None,
    file_id: int | None = None,
    ip_address: str | None = None,
) -> DocumentLog:
    log = DocumentLog(
        document_id=document_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        note=note,
        leader_name=leader_name,
        file_id=file_id,
        performed_by=performed_by,
        ip_address=ip_address,
    )
    db.add(log)
    return log

