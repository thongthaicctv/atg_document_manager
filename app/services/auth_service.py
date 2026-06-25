from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.security import verify_password
from app.timezone import utc_now


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user or user.status != "active":
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login = utc_now()
    return user
