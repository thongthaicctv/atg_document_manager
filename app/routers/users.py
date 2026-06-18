from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_config
from app.dependencies import get_current_user, get_db, require_root, require_root_or_admin
from app.models.user import User
from app.security import check_csrf_token
from app.services import department_service, user_service
from app.views import context, templates

router = APIRouter(prefix="/users", tags=["users"])


def _assert_role_allowed(actor: User, role: str, target: User | None = None) -> None:
    if actor.role == "root":
        return
    if target and actor.id == target.id:
        if role != target.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin không được tự đổi role tài khoản.")
        return
    if role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin chỉ được tạo/sửa tài khoản user.")
    if target and target.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin không được sửa tài khoản root/admin.")


@router.get("")
def user_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    users = user_service.list_users(db)
    if current_user.role == "admin":
        users = [account for account in users if account.role != "root"]
    return templates.TemplateResponse("user_list.html", context(request, current_user, users=users))


@router.get("/new")
def user_new_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    departments = department_service.list_active_departments(db)
    return templates.TemplateResponse("user_form.html", context(request, current_user, account=None, mode="new", departments=departments))


@router.post("/new")
def user_create(
    request: Request,
    csrf_token: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    phone: str | None = Form(None),
    email: str | None = Form(None),
    department: str | None = Form(None),
    role: str = Form("user"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    _assert_role_allowed(current_user, role)
    min_len = int(get_config()["security"]["password_min_length"])
    if len(password) < min_len:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Mật khẩu tối thiểu {min_len} ký tự.")
    if user_service.get_user_by_username(db, username.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên đăng nhập đã tồn tại.")
    user_service.create_user(
        db,
        username=username,
        password=password,
        full_name=full_name,
        phone=phone,
        email=email,
        department=department,
        role=role,
    )
    db.commit()
    return RedirectResponse("/users", status_code=303)


@router.get("/{user_id}/edit")
def user_edit_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    account = db.get(User, user_id)
    if not account or account.status == "disabled":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản.")
    _assert_role_allowed(current_user, account.role, account)
    departments = department_service.list_active_departments(db)
    return templates.TemplateResponse("user_form.html", context(request, current_user, account=account, mode="edit", departments=departments))


@router.post("/{user_id}/edit")
def user_update(
    request: Request,
    user_id: int,
    csrf_token: str = Form(...),
    full_name: str = Form(...),
    phone: str | None = Form(None),
    email: str | None = Form(None),
    department: str | None = Form(None),
    role: str = Form("user"),
    password: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    account = db.get(User, user_id)
    if not account or account.status == "disabled":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản.")
    effective_role = account.role if current_user.role != "root" and current_user.id == account.id else role
    _assert_role_allowed(current_user, effective_role, account)
    if password and len(password) < int(get_config()["security"]["password_min_length"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu mới quá ngắn.")
    user_service.update_user(
        account,
        full_name=full_name,
        phone=phone,
        email=email,
        department=department,
        role=effective_role,
        password=password,
    )
    db.commit()
    return RedirectResponse("/users", status_code=303)


@router.post("/{user_id}/status")
def user_status(
    request: Request,
    user_id: int,
    csrf_token: str = Form(...),
    new_status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    account = db.get(User, user_id)
    if not account or account.status == "disabled":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản.")
    _assert_role_allowed(current_user, account.role, account)
    if account.id == current_user.id and new_status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tự khóa tài khoản đang đăng nhập.")
    if new_status not in {"active", "locked"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trạng thái tài khoản không hợp lệ.")
    user_service.set_user_status(account, new_status)
    db.commit()
    return RedirectResponse("/users", status_code=303)


@router.post("/{user_id}/delete")
def user_delete(
    request: Request,
    user_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    account = db.get(User, user_id)
    if not account or account.status == "disabled":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản.")
    _assert_role_allowed(current_user, account.role, account)
    if account.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xóa tài khoản đang đăng nhập.")
    user_service.soft_delete_user(account)
    db.commit()
    return RedirectResponse("/users", status_code=303)
