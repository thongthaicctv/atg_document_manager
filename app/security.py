from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from passlib.context import CryptContext

from app.config import get_config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def validate_csrf(request: Request) -> None:
    form = await request.form()
    form_token = form.get("csrf_token")
    check_csrf_token(request, str(form_token or ""))


def check_csrf_token(request: Request, form_token: str) -> None:
    session_token = request.session.get("csrf_token")
    if not form_token or not session_token or not secrets.compare_digest(str(form_token), str(session_token)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token không hợp lệ.")


def refresh_session_activity(request: Request) -> None:
    request.session["last_activity"] = datetime.utcnow().isoformat()


def session_is_expired(request: Request) -> bool:
    raw = request.session.get("last_activity")
    if not raw:
        return False
    timeout = int(get_config()["security"]["session_timeout_minutes"])
    try:
        last_activity = datetime.fromisoformat(raw)
    except ValueError:
        return True
    return datetime.utcnow() - last_activity > timedelta(minutes=timeout)
