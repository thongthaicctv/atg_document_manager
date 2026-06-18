from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_config
from app.routers import auth, dashboard, documents, files, permissions, reports, users
from app.views import context, templates

config = get_config()

app = FastAPI(title=config["app_name"])

app.add_middleware(
    SessionMiddleware,
    secret_key=config["security"]["secret_key"],
    max_age=int(config["security"]["session_timeout_minutes"]) * 60,
    same_site="lax",
    https_only=False,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(documents.router)
app.include_router(files.router)
app.include_router(permissions.router)
app.include_router(users.router)
app.include_router(reports.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code in {301, 302, 303, 307, 308} and exc.headers and exc.headers.get("Location"):
        return RedirectResponse(exc.headers["Location"], status_code=exc.status_code)
    current_user = None
    if request.session.get("user_id"):
        current_user = type("SessionUser", (), {"full_name": request.session.get("full_name"), "role": request.session.get("role")})()
    return templates.TemplateResponse(
        "error.html",
        context(request, current_user, status_code=exc.status_code, message=exc.detail),
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    current_user = None
    if request.session.get("user_id"):
        current_user = type("SessionUser", (), {"full_name": request.session.get("full_name"), "role": request.session.get("role")})()
    return templates.TemplateResponse(
        "error.html",
        context(request, current_user, status_code=500, message="Hệ thống đang gặp lỗi, vui lòng thử lại sau."),
        status_code=500,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=config["host"], port=int(config["port"]), reload=False)
