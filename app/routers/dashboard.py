from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.security import verify_password
from app.services.document_service import count_by_status
from app.views import context, templates

router = APIRouter(tags=["dashboard"])


@router.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    counts = count_by_status(db)
    default_root_password = current_user.username == "root" and verify_password("admin@123", current_user.password_hash)
    return templates.TemplateResponse(
        "dashboard.html",
        context(
            request,
            current_user,
            counts=counts,
            default_root_password=default_root_password,
        ),
    )
