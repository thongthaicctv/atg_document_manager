from __future__ import annotations

from ipaddress import ip_address

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_config, resource_path
from app.routers import auth, dashboard, documents, files, permissions, reports, settings, users
from app.services.license_service import get_license_status
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


def _parse_ip(value: str | None):
    if not value:
        return None
    try:
        return ip_address(value.strip())
    except ValueError:
        return None


def _is_lan_ip(value: str | None) -> bool:
    parsed = _parse_ip(value)
    if not parsed:
        return False
    return parsed.is_private or parsed.is_loopback or parsed.is_link_local


def _request_access_ip(request: Request) -> str | None:
    peer_host = request.client.host if request.client else None
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for and _is_lan_ip(peer_host):
        return forwarded_for.split(",", 1)[0].strip()
    return peer_host


@app.middleware("http")
async def restrict_wan_access(request: Request, call_next):
    network_config = get_config().get("network", {})
    allow_wan_access = bool(network_config.get("allow_wan_access", True))
    if not allow_wan_access:
        access_ip = _request_access_ip(request)
        if not _is_lan_ip(access_ip):
            return PlainTextResponse(
                "Truy cập WAN đang tắt. Vui lòng truy cập từ mạng LAN nội bộ.",
                status_code=403,
            )
    return await call_next(request)


LICENSE_BYPASS_PREFIXES = (
    "/static",
    "/login",
    "/logout",
    "/license-required",
    "/settings/system",
)
LICENSE_BYPASS_EXACT = {"/favicon.ico", "/logo.png"}


def _license_bypass_allowed(path: str) -> bool:
    if path in LICENSE_BYPASS_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in LICENSE_BYPASS_PREFIXES)


@app.middleware("http")
async def require_machine_license(request: Request, call_next):
    if _license_bypass_allowed(request.url.path):
        return await call_next(request)

    license_status = get_license_status()
    if license_status.valid:
        return await call_next(request)

    session = request.scope.get("session") or {}
    if session.get("bootstrap_root") or session.get("role") == "root":
        return RedirectResponse("/settings/system?license_required=1", status_code=303)
    return RedirectResponse("/license-required", status_code=303)


STATIC_DIR = resource_path("app", "static")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(str(resource_path("icon.ico")))


@app.get("/logo.png", include_in_schema=False)
async def logo():
    return FileResponse(str(resource_path("logo.png")))


@app.get("/license-required")
async def license_required(request: Request):
    current_user = None
    if request.session.get("full_name"):
        current_user = type(
            "SessionUser",
            (),
            {
                "full_name": request.session.get("full_name"),
                "role": request.session.get("role"),
                "bootstrap_mode": bool(request.session.get("bootstrap_root")),
            },
        )()
    return templates.TemplateResponse(
        "license_required.html",
        context(request, current_user, license_status=get_license_status()),
        status_code=403,
    )

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(documents.router)
app.include_router(files.router)
app.include_router(permissions.router)
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(settings.router)


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

    uvicorn.run("app.main:app", host=config["host"], port=int(config["port"]), reload=False, access_log=False)
