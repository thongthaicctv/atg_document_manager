from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_root_or_admin
from app.models.user import User
from app.services.report_service import export_documents_excel
from app.views import context, templates

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def report_form(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    return templates.TemplateResponse("report.html", context(request, current_user, filters=dict(request.query_params)))


@router.get("/export")
def export_report(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    created_by_name: str | None = Query(None),
    owner_name: str | None = Query(None),
    proposer_name: str | None = Query(None),
    department: str | None = Query(None),
    document_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    path = export_documents_excel(
        db,
        from_date=from_date,
        to_date=to_date,
        status=status_filter,
        created_by_name=created_by_name,
        owner_name=owner_name,
        proposer_name=proposer_name,
        department=department,
        document_type=document_type,
    )
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
