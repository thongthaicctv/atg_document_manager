from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import get_config, resource_path
from app.constants import (
    DOCUMENT_PRIORITIES,
    DOCUMENT_STATUSES,
    INCOMING_ACTIONS,
    INCOMING_DOCUMENT_STATUSES,
    INCOMING_STATUS_BADGE_CLASSES,
    LOG_ACTIONS,
    STATUS_BADGE_CLASSES,
    USER_ROLES,
    USER_STATUSES,
)
from app.security import get_csrf_token
from app.services.document_service import extract_received_time
from app.timezone import format_local_date, format_local_datetime, local_now

TEMPLATES_DIR = resource_path("app", "templates")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def status_label(status: str | None) -> str:
    return DOCUMENT_STATUSES.get(status or "", status or "")


def status_class(status: str | None) -> str:
    return STATUS_BADGE_CLASSES.get(status or "", "text-bg-secondary")


OUTGOING_STATUS_RANK = {
    "cancelled": 5,
    "new_draft": 10,
    "submitted_to_leader": 20,
    "need_revision": 30,
    "revised": 40,
    "leader_approved": 50,
    "issued": 60,
    "archived": 70,
}


def _process_status_key(document: Any) -> str:
    status = getattr(document, "status", None) or "new_draft"
    if getattr(document, "archived_at", None) or status == "archived":
        return "archived"
    if getattr(document, "issued_at", None) or status == "issued":
        return "issued"
    if getattr(document, "approved_at", None) or status == "leader_approved":
        return "leader_approved"
    if getattr(document, "submitted_to_leader_at", None) or status == "submitted_to_leader":
        return "submitted_to_leader"
    return status


def priority_label(priority: str | None) -> str:
    return DOCUMENT_PRIORITIES.get(priority or "", priority or "")


def role_label(role: str | None) -> str:
    return USER_ROLES.get(role or "", role or "")


def user_status_label(status: str | None) -> str:
    return USER_STATUSES.get(status or "", status or "")


def action_label(action: str | None) -> str:
    return LOG_ACTIONS.get(action or "", action or "")


def incoming_action_label(action: str | None) -> str:
    return INCOMING_ACTIONS.get(action or "", action or "Chưa phân loại")


def incoming_status_key(document: Any) -> str:
    related_outgoing = list(getattr(document, "related_outgoing_documents", []) or [])
    if related_outgoing:
        return max(
            (_process_status_key(item) for item in related_outgoing),
            key=lambda key: OUTGOING_STATUS_RANK.get(key, 0),
        )
    if getattr(document, "incoming_action", None) == "archive":
        return "archived"
    received_date = getattr(document, "due_date", None)
    if received_date and received_date < local_now().date():
        return "received"
    return "new_received"


def incoming_status_label(document: Any) -> str:
    key = incoming_status_key(document)
    return DOCUMENT_STATUSES.get(key) or INCOMING_DOCUMENT_STATUSES.get(key, key)


def incoming_status_class(document: Any) -> str:
    key = incoming_status_key(document)
    return STATUS_BADGE_CLASSES.get(key) or INCOMING_STATUS_BADGE_CLASSES.get(key, "text-bg-secondary")


def received_time_label(document: Any) -> str:
    if not document or not getattr(document, "due_date", None):
        return "-"
    value = document.due_date.strftime("%d/%m/%Y")
    received_time = extract_received_time(getattr(document, "note", None))
    return f"{value} {received_time}" if received_time else value


templates.env.filters["status_label"] = status_label
templates.env.filters["status_class"] = status_class
templates.env.filters["priority_label"] = priority_label
templates.env.filters["role_label"] = role_label
templates.env.filters["user_status_label"] = user_status_label
templates.env.filters["action_label"] = action_label
templates.env.filters["incoming_action_label"] = incoming_action_label
templates.env.filters["incoming_status_label"] = incoming_status_label
templates.env.filters["incoming_status_class"] = incoming_status_class
templates.env.filters["received_time_label"] = received_time_label
templates.env.filters["local_datetime"] = format_local_datetime
templates.env.filters["local_date"] = format_local_date


def client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def context(request: Request, current_user: Any | None = None, **extra: Any) -> dict[str, Any]:
    base = {
        "request": request,
        "app_name": get_config()["app_name"],
        "csrf_token": get_csrf_token(request),
        "current_user": current_user,
        "document_statuses": DOCUMENT_STATUSES,
        "incoming_document_statuses": INCOMING_DOCUMENT_STATUSES,
        "document_priorities": DOCUMENT_PRIORITIES,
        "incoming_actions": INCOMING_ACTIONS,
        "user_roles": USER_ROLES,
        "user_statuses": USER_STATUSES,
    }
    base.update(extra)
    return base
