from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.user import User
from app.services.log_service import write_log

PERMISSION_KEYS = ("can_view", "can_edit", "can_update_status", "can_upload_file", "can_share")


def full_permissions() -> dict[str, bool]:
    return {key: True for key in PERMISSION_KEYS}


def view_only_permissions() -> dict[str, bool]:
    permissions = {key: False for key in PERMISSION_KEYS}
    permissions["can_view"] = True
    return permissions


def get_document_permissions(db: Session, user: User, document: Document) -> dict[str, bool]:
    if user.role in {"root", "admin"}:
        return full_permissions()
    if user.id == document.owner_id:
        return full_permissions()

    row = db.execute(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == user.id,
        )
    ).scalar_one_or_none()
    if row:
        return {key: bool(getattr(row, key)) for key in PERMISSION_KEYS}

    return view_only_permissions()


def require_document_permission(db: Session, user: User, document: Document, permission: str) -> dict[str, bool]:
    permissions = get_document_permissions(db, user, document)
    if not permissions.get(permission, False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thao tác văn bản này.")
    return permissions


def upsert_permission(
    db: Session,
    *,
    document: Document,
    target_user_id: int,
    granted_by: int,
    can_view: bool,
    can_edit: bool,
    can_update_status: bool,
    can_upload_file: bool,
    can_share: bool,
    note: str | None,
    ip_address: str | None,
) -> DocumentPermission:
    permission = db.execute(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == target_user_id,
        )
    ).scalar_one_or_none()
    action = "update_permission"
    if permission is None:
        action = "grant_permission"
        permission = DocumentPermission(
            document_id=document.id,
            user_id=target_user_id,
            granted_by=granted_by,
        )
        db.add(permission)

    can_view = can_view or can_edit or can_update_status or can_upload_file or can_share
    permission.can_view = can_view
    permission.can_edit = can_edit
    permission.can_update_status = can_update_status
    permission.can_upload_file = can_upload_file
    permission.can_share = can_share
    permission.note = note or None
    permission.granted_by = granted_by

    write_log(
        db,
        document_id=document.id,
        action=action,
        performed_by=granted_by,
        note=f"Cấp/cập nhật quyền cho user_id={target_user_id}. {note or ''}".strip(),
        ip_address=ip_address,
    )
    return permission


def revoke_permission(db: Session, *, permission: DocumentPermission, performed_by: int, ip_address: str | None) -> None:
    document_id = permission.document_id
    user_id = permission.user_id
    db.delete(permission)
    write_log(
        db,
        document_id=document_id,
        action="revoke_permission",
        performed_by=performed_by,
        note=f"Thu hồi quyền của user_id={user_id}.",
        ip_address=ip_address,
    )
