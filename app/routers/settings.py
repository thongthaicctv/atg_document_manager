from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_config, save_config
from app.dependencies import get_current_user, get_db, require_root, require_root_or_admin
from app.models.department import Department
from app.models.document_type import DocumentType
from app.models.user import User
from app.security import check_csrf_token
from app.services import database_admin_service, department_service, document_type_service, license_service, startup_service
from app.views import context, templates

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/system")
def system_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    require_root(current_user)
    app_config = get_config()
    return templates.TemplateResponse(
        "system_settings.html",
        context(
            request,
            current_user,
            app_config=app_config,
            saved=request.query_params.get("saved") == "1",
            db_initialized=request.query_params.get("db_initialized") == "1",
            database_user_created=request.query_params.get("database_user_created") == "1",
            database_reset=request.query_params.get("database_reset") == "1",
            backup_saved=request.query_params.get("backup_saved") == "1",
            restored=request.query_params.get("restored") == "1",
            license_saved=request.query_params.get("license_saved") == "1",
            license_removed=request.query_params.get("license_removed") == "1",
            license_required=request.query_params.get("license_required") == "1",
            license_status=license_service.get_license_status(),
            bootstrap_mode=bool(request.session.get("bootstrap_root")),
        ),
    )


@router.get("/runtime")
def runtime_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    app_config = get_config()
    return templates.TemplateResponse(
        "runtime_settings.html",
        context(
            request,
            current_user,
            app_config=app_config,
            startup_status=startup_service.get_startup_status(),
            saved=request.query_params.get("saved") == "1",
        ),
    )


@router.post("/runtime")
def runtime_settings_save(
    request: Request,
    csrf_token: str = Form(...),
    auto_start_windows: bool = Form(False),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)

    try:
        startup_service.set_auto_start(auto_start_windows)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    app_config = get_config()
    app_config.setdefault("runtime", {})["auto_start_windows"] = auto_start_windows
    save_config(app_config)
    return RedirectResponse("/settings/runtime?saved=1", status_code=303)


@router.post("/system")
def system_settings_save(
    request: Request,
    csrf_token: str = Form(...),
    app_name: str = Form(...),
    database_host: str = Form(...),
    database_port: int = Form(...),
    database_user: str = Form(...),
    database_password: str = Form(...),
    database_name: str = Form(...),
    allow_wan_access: bool = Form(False),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    if database_port < 1 or database_port > 65535:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Port database không hợp lệ.")
    required_values = [database_host, database_user, database_name]
    if any(not value.strip() for value in required_values):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Host, user và tên database không được để trống.")

    if not app_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên hệ thống không được để trống.")

    app_config = get_config()
    app_config["app_name"] = app_name.strip()
    app_config["database"] = {
        "host": database_host.strip(),
        "port": database_port,
        "user": database_user.strip(),
        "password": database_password,
        "database": database_name.strip(),
    }
    app_config.setdefault("network", {})["allow_wan_access"] = allow_wan_access
    save_config(app_config)
    return RedirectResponse("/settings/system?saved=1", status_code=303)


@router.post("/system/license")
def system_install_license(
    request: Request,
    csrf_token: str = Form(...),
    license_key: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    if not license_key.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="License không được để trống.")
    try:
        license_service.install_license_key(license_key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RedirectResponse("/settings/system?license_saved=1", status_code=303)


@router.post("/system/license/remove")
def system_remove_license(
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    license_service.remove_license_key()
    return RedirectResponse("/settings/system?license_removed=1", status_code=303)


@router.post("/system/create-database-user")
def system_create_database_user(
    request: Request,
    csrf_token: str = Form(...),
    admin_host: str = Form("localhost"),
    admin_user: str = Form("root"),
    admin_password: str = Form(""),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    try:
        database_admin_service.create_database_and_user(
            admin_host=admin_host,
            admin_user=admin_user,
            admin_password=admin_password,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không tạo được database/user MariaDB. Kiểm tra tài khoản quản trị MariaDB. Lỗi: {exc}",
        ) from exc
    return RedirectResponse("/settings/system?database_user_created=1", status_code=303)


@router.post("/system/reset-database")
def system_reset_database(
    request: Request,
    csrf_token: str = Form(...),
    admin_host: str = Form("localhost"),
    admin_user: str = Form("root"),
    admin_password: str = Form(""),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    try:
        database_admin_service.reset_database_and_user(
            admin_host=admin_host,
            admin_user=admin_user,
            admin_password=admin_password,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không reset được database MariaDB. Kiểm tra tài khoản quản trị MariaDB. Lỗi: {exc}",
        ) from exc
    return RedirectResponse("/settings/system?database_reset=1", status_code=303)


@router.post("/system/init-database")
def system_initialize_database(
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    try:
        database_admin_service.initialize_configured_database()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không khởi tạo được bảng dữ liệu. Kiểm tra lại cấu hình MariaDB. Lỗi: {exc}",
        ) from exc
    if request.session.get("bootstrap_root"):
        request.session.clear()
        return RedirectResponse("/login?initialized=1", status_code=303)
    return RedirectResponse("/settings/system?db_initialized=1", status_code=303)


@router.post("/system/backup-directory")
def system_save_backup_directory(
    request: Request,
    csrf_token: str = Form(...),
    backup_dir: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    try:
        clean_backup_dir = database_admin_service.ensure_backup_directory(backup_dir)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    app_config = get_config()
    app_config.setdefault("backup", {})["backup_dir"] = clean_backup_dir
    save_config(app_config)
    return RedirectResponse("/settings/system?backup_saved=1", status_code=303)


@router.post("/system/restore-database")
def system_restore_database(
    request: Request,
    csrf_token: str = Form(...),
    restore_sql_path: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    try:
        database_admin_service.restore_sql_backup(restore_sql_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không phục hồi được dữ liệu từ file SQL. Kiểm tra lại file backup và cấu hình database. Lỗi: {exc}",
        ) from exc
    if request.session.get("bootstrap_root"):
        request.session.clear()
        return RedirectResponse("/login?restored=1", status_code=303)
    return RedirectResponse("/settings/system?restored=1", status_code=303)


@router.get("/document-types")
def document_type_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    document_types = document_type_service.list_active_document_types(db)
    return templates.TemplateResponse(
        "document_type_settings.html",
        context(
            request,
            current_user,
            document_types=document_types,
            document_type_branches=document_type_service.DOCUMENT_TYPE_BRANCHES,
        ),
    )


@router.get("/departments")
def department_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_root_or_admin(current_user)
    departments = department_service.list_active_departments(db)
    return templates.TemplateResponse(
        "department_settings.html",
        context(request, current_user, departments=departments),
    )


@router.post("/departments")
def department_create(
    request: Request,
    csrf_token: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên phòng ban không được để trống.")
    department_service.create_department(db, name=name)
    db.commit()
    return RedirectResponse("/settings/departments", status_code=303)


@router.post("/departments/{department_id}/edit")
def department_edit(
    request: Request,
    department_id: int,
    csrf_token: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên phòng ban không được để trống.")
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng ban.")
    try:
        department_service.update_department(db, department=department, name=name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return RedirectResponse("/settings/departments", status_code=303)


@router.post("/departments/{department_id}/delete")
def department_delete(
    request: Request,
    department_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng ban.")
    department_service.delete_department(department)
    db.commit()
    return RedirectResponse("/settings/departments", status_code=303)


@router.post("/document-types")
def document_type_create(
    request: Request,
    csrf_token: str = Form(...),
    name: str = Form(...),
    branch: str = Form("outgoing"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên phân loại văn bản không được để trống.")
    document_type_service.create_document_type(db, name=name, branch=branch)
    db.commit()
    return RedirectResponse("/settings/document-types", status_code=303)


@router.post("/document-types/{document_type_id}/edit")
def document_type_edit(
    request: Request,
    document_type_id: int,
    csrf_token: str = Form(...),
    name: str = Form(...),
    branch: str = Form("outgoing"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root_or_admin(current_user)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên phân loại văn bản không được để trống.")
    document_type = db.get(DocumentType, document_type_id)
    if not document_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phân loại văn bản.")
    try:
        document_type_service.update_document_type(db, document_type=document_type, name=name, branch=branch)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return RedirectResponse("/settings/document-types", status_code=303)


@router.post("/document-types/{document_type_id}/delete")
def document_type_delete(
    request: Request,
    document_type_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    require_root(current_user)
    document_type = db.get(DocumentType, document_type_id)
    if not document_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phân loại văn bản.")
    document_type_service.delete_document_type(document_type)
    db.commit()
    return RedirectResponse("/settings/document-types", status_code=303)
