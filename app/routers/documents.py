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
from app.services import department_service, document_service, document_type_service, file_service, pdf_service
from app.services.permission_service import get_document_permissions, require_document_permission
from app.views import client_ip, context, templates

router = APIRouter(prefix="/documents", tags=["documents"])


def _optional_form_date(value: str | None) -> date | None:
    if not value or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ngày không hợp lệ.") from exc


def _optional_form_time(value: str | None) -> str:
    if not value or not value.strip():
        return ""
    value = value.strip()
    parts = value.split(":")
    if len(parts) != 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Giờ nhận không hợp lệ.")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Giờ nhận không hợp lệ.") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Giờ nhận không hợp lệ.")
    return f"{hour:02d}:{minute:02d}"


def _branch_from_params(branch: str | None = None, received: str | None = None) -> str:
    if received == "1":
        return "incoming"
    return document_type_service.normalize_branch(branch)


def _get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy văn bản.")
    return document


def _has_uploads(uploads: list[UploadFile] | None) -> bool:
    return any(upload and upload.filename for upload in uploads or [])


def _date_label_for_branch(branch: str) -> str:
    return "Ngày nhận" if branch == "incoming" else "Ngày hết hạn"


def _note_for_branch(branch: str, received_time: str | None) -> str | None:
    if branch == "incoming":
        return document_service.merge_note_with_received_time(None, _optional_form_time(received_time))
    return None


def _departments_for_branch(branch: str, sender_department: str | None, receiver_department: str | None) -> tuple[str | None, str | None]:
    if branch == "incoming":
        return (sender_department or None, None)
    return (None, receiver_department or None)


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
    sender_department: str | None = Query(None),
    receiver_department: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    document_type: str | None = Query(None),
    received: str | None = Query(None),
    quick: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    list_branch = "incoming" if received == "1" else None
    branch_types = document_type_service.list_active_document_types(db, branch=list_branch) if list_branch else None
    documents = document_service.search_documents(
        db,
        from_date=from_date,
        to_date=to_date,
        document_number=document_number,
        title=title,
        proposer_name=proposer_name,
        created_by_name=created_by_name,
        department=department,
        sender_department=sender_department,
        receiver_department=receiver_department,
        status=status_filter,
        document_type=document_type,
        received_only=received == "1",
        document_type_names=[item.name for item in branch_types] if branch_types is not None else None,
        quick=quick,
    )
    filters = dict(request.query_params)
    document_types = branch_types if branch_types is not None else document_type_service.list_active_document_types(db)
    departments = department_service.list_active_departments(db)
    document_branches = {
        document.id: document_type_service.branch_for_document_type_name(db, document.document_type)
        for document in documents
    }
    date_column_label = "Thời gian nhận" if list_branch == "incoming" else "Ngày nhận/hết hạn"
    show_sender_department = list_branch in {None, "incoming"}
    show_receiver_department = list_branch is None
    return templates.TemplateResponse(
        "document_list.html",
        context(
            request,
            current_user,
            documents=documents,
            filters=filters,
            document_types=document_types,
            departments=departments,
            document_branches=document_branches,
            date_column_label=date_column_label,
            show_sender_department=show_sender_department,
            show_receiver_department=show_receiver_department,
        ),
    )


@router.get("/new")
def document_new_form(
    request: Request,
    branch: str | None = Query(None),
    received: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form_branch = _branch_from_params(branch=branch, received=received)
    document_types = document_type_service.list_active_document_types(db, branch=form_branch)
    departments = department_service.list_active_departments(db)
    next_document_code = document_service.preview_next_document_code(db)
    return templates.TemplateResponse(
        "document_form.html",
        context(
            request,
            current_user,
            document=None,
            mode="new",
            document_types=document_types,
            departments=departments,
            form_branch=form_branch,
            form_branch_label=document_type_service.DOCUMENT_TYPE_BRANCHES[form_branch],
            date_label=_date_label_for_branch(form_branch),
            show_received_time=form_branch == "incoming",
            show_sender_department=form_branch == "incoming",
            show_receiver_department=form_branch == "outgoing",
            next_document_code=next_document_code,
            received_time="",
        ),
    )


@router.post("/new")
async def document_create(
    request: Request,
    csrf_token: str = Form(...),
    document_number: str | None = Form(None),
    title: str = Form(...),
    summary: str | None = Form(None),
    content: str | None = Form(None),
    document_type: str | None = Form(None),
    sender_department: str | None = Form(None),
    receiver_department: str | None = Form(None),
    priority: str = Form("normal"),
    due_date: str | None = Form(None),
    received_time: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
    scan_images: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    selected_branch = document_type_service.branch_for_document_type_name(db, document_type)
    sender_department, receiver_department = _departments_for_branch(selected_branch, sender_department, receiver_department)
    document = document_service.create_document(
        db,
        user=current_user,
        ip_address=client_ip(request),
        document_number=document_number,
        title=title,
        summary=summary,
        content=content,
        document_type=document_type,
        proposer_name=current_user.full_name,
        department=current_user.department,
        sender_department=sender_department,
        receiver_department=receiver_department,
        priority=priority,
        due_date=_optional_form_date(due_date),
        note=_note_for_branch(selected_branch, received_time),
    )
    for upload in files or []:
        await file_service.save_upload_file(db, document=document, upload=upload, user=current_user, ip_address=client_ip(request))
    if _has_uploads(scan_images):
        pdf_path = await pdf_service.images_to_pdf(scan_images or [], output_name=f"scan_{document.id}.pdf")
        try:
            file_service.copy_generated_pdf(
                db,
                document=document,
                pdf_path=pdf_path,
                original_name=f"scan_document_{document.document_code or document.id}.pdf",
                user=current_user,
                ip_address=client_ip(request),
            )
        finally:
            pdf_path.unlink(missing_ok=True)
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
    document_branch = document_type_service.branch_for_document_type_name(db, document.document_type)
    return templates.TemplateResponse(
        "document_detail.html",
        context(
            request,
            current_user,
            document=document,
            permissions=permissions,
            document_branch=document_branch,
            date_label="Thời gian nhận" if document_branch == "incoming" else "Ngày hết hạn",
        ),
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
    form_branch = document_type_service.branch_for_document_type_name(db, document.document_type)
    document_types = document_type_service.list_active_document_types(db, branch=form_branch)
    departments = department_service.list_active_departments(db)
    return templates.TemplateResponse(
        "document_form.html",
        context(
            request,
            current_user,
            document=document,
            mode="edit",
            document_types=document_types,
            departments=departments,
            form_branch=form_branch,
            form_branch_label=document_type_service.DOCUMENT_TYPE_BRANCHES[form_branch],
            date_label=_date_label_for_branch(form_branch),
            show_received_time=form_branch == "incoming",
            show_sender_department=form_branch == "incoming",
            show_receiver_department=form_branch == "outgoing",
            received_time=document_service.extract_received_time(document.note),
        ),
    )


@router.post("/{document_id}/edit")
def document_update(
    request: Request,
    document_id: int,
    csrf_token: str = Form(...),
    document_number: str | None = Form(None),
    title: str = Form(...),
    summary: str | None = Form(None),
    content: str | None = Form(None),
    document_type: str | None = Form(None),
    sender_department: str | None = Form(None),
    receiver_department: str | None = Form(None),
    priority: str = Form("normal"),
    due_date: str | None = Form(None),
    received_time: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_edit")
    selected_branch = document_type_service.branch_for_document_type_name(db, document_type)
    sender_department, receiver_department = _departments_for_branch(selected_branch, sender_department, receiver_department)
    document_service.update_document(
        db,
        document=document,
        user=current_user,
        ip_address=client_ip(request),
        document_number=document_number,
        title=title,
        summary=summary,
        content=content,
        document_type=document_type,
        proposer_name=document.proposer_name or current_user.full_name,
        department=current_user.department,
        sender_department=sender_department,
        receiver_department=receiver_department,
        priority=priority,
        due_date=_optional_form_date(due_date),
        note=_note_for_branch(selected_branch, received_time),
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
    actual_date: str | None = Form(None),
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
        actual_date=_optional_form_date(actual_date),
        note=note,
    )
    if file and file.filename:
        require_document_permission(db, current_user, document, "can_upload_file")
        await file_service.save_upload_file(db, document=document, upload=file, user=current_user, ip_address=client_ip(request))
    db.commit()
    return RedirectResponse(f"/documents/{document.id}", status_code=303)
