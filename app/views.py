from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import get_config
from app.constants import DOCUMENT_PRIORITIES, DOCUMENT_STATUSES, LOG_ACTIONS, STATUS_BADGE_CLASSES, USER_ROLES, USER_STATUSES
from app.security import get_csrf_token

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def status_label(status: str | None) -> str:
    return DOCUMENT_STATUSES.get(status or "", status or "")


def status_class(status: str | None) -> str:
    return STATUS_BADGE_CLASSES.get(status or "", "text-bg-secondary")


def priority_label(priority: str | None) -> str:
    return DOCUMENT_PRIORITIES.get(priority or "", priority or "")


def role_label(role: str | None) -> str:
    return USER_ROLES.get(role or "", role or "")


def user_status_label(status: str | None) -> str:
    return USER_STATUSES.get(status or "", status or "")


def action_label(action: str | None) -> str:
    return LOG_ACTIONS.get(action or "", action or "")


templates.env.filters["status_label"] = status_label
templates.env.filters["status_class"] = status_class
templates.env.filters["priority_label"] = priority_label
templates.env.filters["role_label"] = role_label
templates.env.filters["user_status_label"] = user_status_label
templates.env.filters["action_label"] = action_label


def client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def context(request: Request, user: Any | None = None, **extra: Any) -> dict[str, Any]:
    base = {
        "request": request,
        "app_name": get_config()["app_name"],
        "csrf_token": get_csrf_token(request),
        "current_user": user,
        "document_statuses": DOCUMENT_STATUSES,
        "document_priorities": DOCUMENT_PRIORITIES,
        "user_roles": USER_ROLES,
        "user_statuses": USER_STATUSES,
    }
    base.update(extra)
    return base
