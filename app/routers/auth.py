from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.security import check_csrf_token, refresh_session_activity
from app.services.auth_service import authenticate_user
from app.services.log_service import write_log
from app.views import client_ip, context, templates

router = APIRouter(tags=["auth"])


@router.get("/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", context(request))


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    check_csrf_token(request, csrf_token)
    user = authenticate_user(db, username.strip(), password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            context(request, error="Tên đăng nhập hoặc mật khẩu không đúng, hoặc tài khoản đã bị khóa."),
            status_code=400,
        )

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["role"] = user.role
    request.session["full_name"] = user.full_name
    refresh_session_activity(request)
    write_log(db, action="login", performed_by=user.id, ip_address=client_ip(request), note="Đăng nhập hệ thống.")
    db.commit()
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(
    request: Request,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    check_csrf_token(request, csrf_token)
    user_id = request.session.get("user_id")
    if user_id:
        write_log(db, action="logout", performed_by=int(user_id), ip_address=client_ip(request), note="Đăng xuất hệ thống.")
        db.commit()
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
