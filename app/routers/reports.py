from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_root_or_admin
from app.models.user import User
from app.services import department_service, document_type_service
from app.services.report_service import export_documents_excel
from app.views import context, templates

router = APIRouter(prefix="/reports", tags=["reports"])


def _optional_query_date(value: str | None, label: str) -> date | None:
    if not value or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{label} không hợp lệ.") from exc


@router.get("")
def report_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    document_types = document_type_service.list_active_document_types(db)
    departments = department_service.list_active_departments(db)
    return templates.TemplateResponse(
        "report.html",
        context(request, current_user, filters=dict(request.query_params), document_types=document_types, departments=departments),
    )


@router.get("/export")
def export_report(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    created_by_name: str | None = Query(None),
    owner_name: str | None = Query(None),
    proposer_name: str | None = Query(None),
    department: str | None = Query(None),
    sender_department: str | None = Query(None),
    receiver_department: str | None = Query(None),
    document_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    parsed_from_date = _optional_query_date(from_date, "Từ ngày")
    parsed_to_date = _optional_query_date(to_date, "Đến ngày")
    path = export_documents_excel(
        db,
        from_date=parsed_from_date,
        to_date=parsed_to_date,
        status=status_filter,
        created_by_name=created_by_name,
        owner_name=owner_name,
        proposer_name=proposer_name,
        department=department,
        sender_department=sender_department,
        receiver_department=receiver_department,
        document_type=document_type,
    )
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
