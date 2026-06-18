from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.constants import DOCUMENT_STATUSES
from app.dependencies import get_current_user, get_db
from app.models.document import Document
from app.models.user import User
from app.security import check_csrf_token
from app.services import document_service, file_service
from app.services.permission_service import get_document_permissions, require_document_permission
from app.views import client_ip, context, templates

router = APIRouter(prefix="/documents", tags=["documents"])


def _get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy văn bản.")
    return document


@router.get("")
def document_list(
    request: Request,
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    document_number: str | None = Query(None),
    title: str | None = Query(None),
    proposer_name: str | None = Query(None),
    created_by_name: str | None = Query(None),
    department: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    document_type: str | None = Query(None),
    quick: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = document_service.search_documents(
        db,
        from_date=from_date,
        to_date=to_date,
        document_number=document_number,
        title=title,
        proposer_name=proposer_name,
        created_by_name=created_by_name,
        department=department,
        status=status_filter,
        document_type=document_type,
        quick=quick,
    )
    filters = dict(request.query_params)
    return templates.TemplateResponse(
        "document_list.html",
        context(request, current_user, documents=documents, filters=filters),
    )


@router.get("/new")
def document_new_form(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse("document_form.html", context(request, current_user, document=None, mode="new"))


@router.post("/new")
async def document_create(
    request: Request,
    csrf_token: str = Form(...),
    document_code: str | None = Form(None),
    document_number: str | None = Form(None),
    title: str = Form(...),
    summary: str | None = Form(None),
    content: str | None = Form(None),
    document_type: str | None = Form(None),
    proposer_name: str | None = Form(None),
    department: str | None = Form(None),
    priority: str = Form("normal"),
    note: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    document = document_service.create_document(
        db,
        user=current_user,
        ip_address=client_ip(request),
        document_code=document_code,
        document_number=document_number,
        title=title,
        summary=summary,
        content=content,
        document_type=document_type,
        proposer_name=proposer_name,
        department=department,
        priority=priority,
        note=note,
    )
    for upload in files or []:
        await file_service.save_upload_file(db, document=document, upload=upload, user=current_user, ip_address=client_ip(request))
    db.commit()
    return RedirectResponse(f"/documents/{document.id}", status_code=303)


@router.get("/{document_id}")
def document_detail(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = _get_document_or_404(db, document_id)
    permissions = require_document_permission(db, current_user, document, "can_view")
    return templates.TemplateResponse(
        "document_detail.html",
        context(request, current_user, document=document, permissions=permissions),
    )


@router.get("/{document_id}/edit")
def document_edit_form(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_edit")
    return templates.TemplateResponse("document_form.html", context(request, current_user, document=document, mode="edit"))


@router.post("/{document_id}/edit")
def document_update(
    request: Request,
    document_id: int,
    csrf_token: str = Form(...),
    document_code: str | None = Form(None),
    document_number: str | None = Form(None),
    title: str = Form(...),
    summary: str | None = Form(None),
    content: str | None = Form(None),
    document_type: str | None = Form(None),
    proposer_name: str | None = Form(None),
    department: str | None = Form(None),
    priority: str = Form("normal"),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_edit")
    document_service.update_document(
        db,
        document=document,
        user=current_user,
        ip_address=client_ip(request),
        document_code=document_code,
        document_number=document_number,
        title=title,
        summary=summary,
        content=content,
        document_type=document_type,
        proposer_name=proposer_name,
        department=department,
        priority=priority,
        note=note,
    )
    db.commit()
    return RedirectResponse(f"/documents/{document.id}", status_code=303)


@router.get("/{document_id}/status")
def document_status_form(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = _get_document_or_404(db, document_id)
    permissions = get_document_permissions(db, current_user, document)
    require_document_permission(db, current_user, document, "can_update_status")
    return templates.TemplateResponse(
        "document_status_update.html",
        context(request, current_user, document=document, permissions=permissions),
    )


@router.post("/{document_id}/status")
async def document_status_update(
    request: Request,
    document_id: int,
    csrf_token: str = Form(...),
    new_status: str = Form(...),
    leader_name: str | None = Form(None),
    actual_date: date | None = Form(None),
    note: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    if new_status not in DOCUMENT_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trạng thái không hợp lệ.")
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_update_status")
    document_service.update_document_status(
        db,
        document=document,
        user=current_user,
        ip_address=client_ip(request),
        new_status=new_status,
        leader_name=leader_name,
        actual_date=actual_date,
        note=note,
    )
    if file and file.filename:
        require_document_permission(db, current_user, document, "can_upload_file")
        await file_service.save_upload_file(db, document=document, upload=file, user=current_user, ip_address=client_ip(request))
    db.commit()
    return RedirectResponse(f"/documents/{document.id}", status_code=303)
