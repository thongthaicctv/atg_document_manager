from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models.user import User
from app.security import check_csrf_token, refresh_session_activity
from app.services.auth_service import authenticate_user
from app.services.log_service import write_log
from app.views import client_ip, context, templates

router = APIRouter(tags=["auth"])
BOOTSTRAP_ROOT_PASSWORD = "admin@123"


def _is_default_bootstrap_root(username: str, password: str) -> bool:
    return username.strip().lower() == "root" and password == BOOTSTRAP_ROOT_PASSWORD


def _root_user_exists(db) -> bool:
    root_id = db.execute(select(User.id).where(User.username == "root")).scalar_one_or_none()
    return root_id is not None


def _start_bootstrap_root_session(request: Request) -> None:
    request.session.clear()
    request.session["bootstrap_root"] = True
    request.session["role"] = "root"
    request.session["full_name"] = "Root khởi tạo"
    refresh_session_activity(request)


@router.get("/login")
def login_form(request: Request):
    if request.session.get("bootstrap_root"):
        return RedirectResponse("/settings/system", status_code=303)
    if request.session.get("user_id"):
        db = SessionLocal()
        try:
            user = db.get(User, int(request.session["user_id"]))
            if user and user.status == "active":
                return RedirectResponse("/", status_code=303)
            request.session.clear()
        except (SQLAlchemyError, ValueError):
            request.session.clear()
        finally:
            db.close()
    return templates.TemplateResponse(
        "login.html",
        context(
            request,
            initialized=request.query_params.get("initialized") == "1",
            restored=request.query_params.get("restored") == "1",
        ),
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
):
    check_csrf_token(request, csrf_token)
    db = SessionLocal()
    try:
        clean_username = username.strip()
        user = authenticate_user(db, clean_username, password)
        if not user and _is_default_bootstrap_root(clean_username, password) and not _root_user_exists(db):
            _start_bootstrap_root_session(request)
            return RedirectResponse("/settings/system?bootstrap=1", status_code=303)
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
        try:
            write_log(db, action="login", performed_by=user.id, ip_address=client_ip(request), note="Đăng nhập hệ thống.")
            db.commit()
        except SQLAlchemyError:
            db.rollback()
        return RedirectResponse("/", status_code=303)
    except SQLAlchemyError:
        db.rollback()
        if _is_default_bootstrap_root(username, password):
            _start_bootstrap_root_session(request)
            return RedirectResponse("/settings/system?bootstrap=1", status_code=303)
        return templates.TemplateResponse(
            "login.html",
            context(
                request,
                error="Database chưa sẵn sàng. Có thể đăng nhập root mặc định để khởi tạo lại dữ liệu.",
            ),
            status_code=400,
        )
    finally:
        db.close()


@router.get("/logout")
def logout_get(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.post("/logout")
def logout(
    request: Request,
    csrf_token: str = Form(...),
):
    check_csrf_token(request, csrf_token)
    user_id = request.session.get("user_id")
    if user_id and not request.session.get("bootstrap_root"):
        db = SessionLocal()
        try:
            write_log(db, action="logout", performed_by=int(user_id), ip_address=client_ip(request), note="Đăng xuất hệ thống.")
            db.commit()
        except SQLAlchemyError:
            db.rollback()
        finally:
            db.close()
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
