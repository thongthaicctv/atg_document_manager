from __future__ import annotations

import html
import re

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from markupsafe import Markup
from sqlalchemy.orm import Session

from app.config import get_config, resource_path
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.security import check_csrf_token, hash_password, verify_password
from app.views import context, templates

router = APIRouter(prefix="/account", tags=["account"])
USER_GUIDE_PATH = resource_path("HUONG_DAN_SU_DUNG_CAN_BO.md")


def _inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def _markdown_to_html(markdown_text: str) -> str:
    parts: list[str] = []
    list_type: str | None = None

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            parts.append(f"</{list_type}>")
            list_type = None

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            close_list()
            continue
        if line.startswith("### "):
            close_list()
            parts.append(f"<h3>{_inline_markdown(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            close_list()
            parts.append(f"<h2>{_inline_markdown(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            close_list()
            parts.append(f"<h1>{_inline_markdown(line[2:])}</h1>")
            continue
        if line.startswith("- "):
            if list_type != "ul":
                close_list()
                parts.append("<ul>")
                list_type = "ul"
            parts.append(f"<li>{_inline_markdown(line[2:])}</li>")
            continue

        ordered_match = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered_match:
            if list_type != "ol":
                close_list()
                parts.append("<ol>")
                list_type = "ol"
            parts.append(f"<li>{_inline_markdown(ordered_match.group(1))}</li>")
            continue

        close_list()
        parts.append(f"<p>{_inline_markdown(line)}</p>")

    close_list()
    return "\n".join(parts)


def _load_user_guide_html() -> Markup:
    if not USER_GUIDE_PATH.exists():
        return Markup("<p>Chưa tìm thấy file hướng dẫn sử dụng.</p>")
    guide_text = USER_GUIDE_PATH.read_text(encoding="utf-8")
    return Markup(_markdown_to_html(guide_text))


@router.get("/guide")
def user_guide(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "account_guide.html",
        context(request, current_user, guide_html=_load_user_guide_html()),
    )


@router.get("/password")
def password_form(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "account_password.html",
        context(
            request,
            current_user,
            changed=request.query_params.get("changed") == "1",
            min_length=int(get_config()["security"]["password_min_length"]),
        ),
    )


@router.post("/password")
def password_update(
    request: Request,
    csrf_token: str = Form(...),
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    min_length = int(get_config()["security"]["password_min_length"])

    def render_error(message: str):
        return templates.TemplateResponse(
            "account_password.html",
            context(request, current_user, error=message, min_length=min_length),
            status_code=400,
        )

    if not verify_password(current_password, current_user.password_hash):
        return render_error("Mật khẩu hiện tại không đúng.")
    if len(new_password) < min_length:
        return render_error(f"Mật khẩu mới tối thiểu {min_length} ký tự.")
    if new_password != confirm_password:
        return render_error("Mật khẩu mới và xác nhận mật khẩu không khớp.")
    if verify_password(new_password, current_user.password_hash):
        return render_error("Mật khẩu mới không được trùng với mật khẩu hiện tại.")

    account = db.get(User, current_user.id)
    if not account or account.status != "active":
        return render_error("Tài khoản không còn hoạt động. Vui lòng đăng nhập lại.")

    account.password_hash = hash_password(new_password)
    db.commit()
    return RedirectResponse("/account/password?changed=1", status_code=303)
