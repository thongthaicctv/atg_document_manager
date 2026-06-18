from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_root, require_root_or_admin
from app.models.department import Department
from app.models.document_type import DocumentType
from app.models.user import User
from app.security import check_csrf_token
from app.services import department_service, document_type_service
from app.views import context, templates

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/document-types")
def document_type_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    document_types = document_type_service.list_active_document_types(db)
    return templates.TemplateResponse(
        "document_type_settings.html",
        context(
            request,
            current_user,
            document_types=document_types,
            document_type_branches=document_type_service.DOCUMENT_TYPE_BRANCHES,
        ),
    )


@router.get("/departments")
def department_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    departments = department_service.list_active_departments(db)
    return templates.TemplateResponse(
        "department_settings.html",
        context(request, current_user, departments=departments),
    )


@router.post("/departments")
def department_create(
    request: Request,
    csrf_token: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên phòng ban không được để trống.")
    department_service.create_department(db, name=name)
    db.commit()
    return RedirectResponse("/settings/departments", status_code=303)


@router.post("/departments/{department_id}/edit")
def department_edit(
    request: Request,
    department_id: int,
    csrf_token: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên phòng ban không được để trống.")
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng ban.")
    try:
        department_service.update_department(db, department=department, name=name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return RedirectResponse("/settings/departments", status_code=303)


@router.post("/departments/{department_id}/delete")
def department_delete(
    request: Request,
    department_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng ban.")
    department_service.delete_department(department)
    db.commit()
    return RedirectResponse("/settings/departments", status_code=303)


@router.post("/document-types")
def document_type_create(
    request: Request,
    csrf_token: str = Form(...),
    name: str = Form(...),
    branch: str = Form("outgoing"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên phân loại văn bản không được để trống.")
    document_type_service.create_document_type(db, name=name, branch=branch)
    db.commit()
    return RedirectResponse("/settings/document-types", status_code=303)


@router.post("/document-types/{document_type_id}/edit")
def document_type_edit(
    request: Request,
    document_type_id: int,
    csrf_token: str = Form(...),
    name: str = Form(...),
    branch: str = Form("outgoing"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên phân loại văn bản không được để trống.")
    document_type = db.get(DocumentType, document_type_id)
    if not document_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phân loại văn bản.")
    try:
        document_type_service.update_document_type(db, document_type=document_type, name=name, branch=branch)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return RedirectResponse("/settings/document-types", status_code=303)


@router.post("/document-types/{document_type_id}/delete")
def document_type_delete(
    request: Request,
    document_type_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    document_type = db.get(DocumentType, document_type_id)
    if not document_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phân loại văn bản.")
    document_type_service.delete_document_type(document_type)
    db.commit()
    return RedirectResponse("/settings/document-types", status_code=303)
