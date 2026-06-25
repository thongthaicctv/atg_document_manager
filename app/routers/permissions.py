from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_root
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.user import User
from app.security import check_csrf_token
from app.services.permission_service import require_document_permission, revoke_permission, upsert_permission
from app.services.user_service import list_users
from app.views import client_ip, context, templates

router = APIRouter(prefix="/documents/{document_id}/permissions", tags=["permissions"])


def _get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy văn bản.")
    return document


@router.get("")
def permission_form(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_share")
    users = [
        user
        for user in list_users(db)
        if user.status == "active"
        and user.role == "user"
        and user.id != document.owner_id
    ]
    return templates.TemplateResponse(
        "document_permissions.html",
        context(request, current_user, document=document, users=users),
    )


@router.post("")
def save_permission(
    request: Request,
    document_id: int,
    csrf_token: str = Form(...),
    user_id: int = Form(...),
    can_view: bool = Form(False),
    can_edit: bool = Form(False),
    can_update_status: bool = Form(False),
    can_upload_file: bool = Form(False),
    can_share: bool = Form(False),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_share")
    target_user = db.get(User, user_id)
    if not target_user or target_user.status != "active" or target_user.role != "user":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Người dùng nhận quyền không hợp lệ.")
    if target_user.id == document.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chủ văn bản đã có toàn quyền.")
    upsert_permission(
        db,
        document=document,
        target_user_id=target_user.id,
        granted_by=current_user.id,
        can_view=can_view,
        can_edit=can_edit,
        can_update_status=can_update_status,
        can_upload_file=can_upload_file,
        can_share=can_share,
        note=note,
        ip_address=client_ip(request),
    )
    db.commit()
    return RedirectResponse(f"/documents/{document.id}/permissions", status_code=303)


@router.post("/{permission_id}/revoke")
def revoke(
    request: Request,
    document_id: int,
    permission_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_share")
    permission = db.execute(
        select(DocumentPermission).where(
            DocumentPermission.id == permission_id,
            DocumentPermission.document_id == document.id,
        )
    ).scalar_one_or_none()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bản ghi quyền.")
    revoke_permission(db, permission=permission, performed_by=current_user.id, ip_address=client_ip(request))
    db.commit()
    return RedirectResponse(f"/documents/{document.id}/permissions", status_code=303)
