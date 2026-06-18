from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security import refresh_session_activity, session_is_expired


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def redirect_to_login() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_303_SEE_OTHER,
        detail="Yêu cầu đăng nhập.",
        headers={"Location": "/login"},
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise redirect_to_login()
    if session_is_expired(request):
        request.session.clear()
        raise redirect_to_login()
    user = db.get(User, int(user_id))
    if not user or user.status != "active":
        request.session.clear()
        raise redirect_to_login()
    refresh_session_activity(request)
    return user


def require_root_or_admin(user: User) -> None:
    if user.role not in {"root", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập.")


def require_root(user: User) -> None:
    if user.role != "root":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ tài khoản root được phép thao tác.")
