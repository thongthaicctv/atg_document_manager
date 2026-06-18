from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.security import hash_password


def list_users(db: Session) -> list[User]:
    return list(db.execute(select(User).order_by(User.role, User.full_name)).scalars())


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.execute(select(User).where(User.username == username)).scalar_one_or_none()


def create_user(
    db: Session,
    *,
    username: str,
    password: str,
    full_name: str,
    phone: str | None,
    email: str | None,
    department: str | None,
    role: str,
) -> User:
    user = User(
        username=username.strip(),
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        phone=phone or None,
        email=email or None,
        department=department or None,
        role=role,
        status="active",
    )
    db.add(user)
    return user


def update_user(
    user: User,
    *,
    full_name: str,
    phone: str | None,
    email: str | None,
    department: str | None,
    role: str,
    password: str | None = None,
) -> User:
    user.full_name = full_name.strip()
    user.phone = phone or None
    user.email = email or None
    user.department = department or None
    user.role = role
    if password:
        user.password_hash = hash_password(password)
    return user


def set_user_status(user: User, status: str) -> User:
    user.status = status
    return user

