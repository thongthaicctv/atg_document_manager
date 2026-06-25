from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_config, get_upload_dir
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.user import User
from app.services.log_service import write_log
from app.timezone import local_now

DANGEROUS_EXTENSIONS = {"exe", "bat", "cmd", "js", "vbs", "ps1", "sh"}


def _safe_original_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.() -]+", "_", name).strip(" .")
    return cleaned or "file"


def _extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def validate_extension(filename: str) -> str:
    ext = _extension(filename)
    allowed = set(get_config()["storage"]["allowed_extensions"])
    if not ext or ext in DANGEROUS_EXTENSIONS or ext not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không cho phép upload file .{ext or 'unknown'}.")
    return ext


def document_upload_dir(document_id: int) -> Path:
    today = local_now()
    directory = get_upload_dir() / f"{today:%Y}" / f"{today:%m}" / f"{today:%d}" / str(document_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


async def save_upload_file(
    db: Session,
    *,
    document: Document,
    upload: UploadFile,
    user: User,
    ip_address: str | None,
    is_scanned: bool = False,
) -> DocumentFile | None:
    if not upload or not upload.filename:
        return None

    ext = validate_extension(upload.filename)
    max_bytes = int(get_config()["storage"]["max_file_size_mb"]) * 1024 * 1024
    original_name = _safe_original_name(upload.filename)
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    destination = document_upload_dir(document.id) / stored_name

    size = 0
    with destination.open("wb") as out_file:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                out_file.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File vượt quá dung lượng cho phép.")
            out_file.write(chunk)

    record = DocumentFile(
        document_id=document.id,
        file_name=stored_name,
        original_name=original_name,
        file_path=str(destination),
        file_type=ext,
        file_size=size,
        uploaded_by=user.id,
        is_pdf=ext == "pdf",
        is_scanned=is_scanned,
    )
    db.add(record)
    db.flush()
    write_log(
        db,
        document_id=document.id,
        action="upload_file",
        performed_by=user.id,
        file_id=record.id,
        note=f"Upload file: {original_name}",
        ip_address=ip_address,
    )
    return record


def assert_path_inside_uploads(path: str) -> Path:
    target = Path(path).resolve()
    root = get_upload_dir().resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Đường dẫn file không hợp lệ.")
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy file.")
    return target


def delete_document_file(db: Session, *, file: DocumentFile, user: User, ip_address: str | None) -> None:
    path = assert_path_inside_uploads(file.file_path)
    document_id = file.document_id
    original_name = file.original_name
    if path.exists():
        path.unlink()
    db.delete(file)
    write_log(
        db,
        document_id=document_id,
        action="delete_file",
        performed_by=user.id,
        note=f"Xóa file: {original_name}",
        ip_address=ip_address,
    )


def copy_generated_pdf(
    db: Session,
    *,
    document: Document,
    pdf_path: Path,
    original_name: str,
    user: User,
    ip_address: str | None,
) -> DocumentFile:
    destination = document_upload_dir(document.id) / f"{uuid.uuid4().hex}.pdf"
    shutil.copyfile(pdf_path, destination)
    record = DocumentFile(
        document_id=document.id,
        file_name=destination.name,
        original_name=_safe_original_name(original_name),
        file_path=str(destination),
        file_type="pdf",
        file_size=destination.stat().st_size,
        uploaded_by=user.id,
        is_pdf=True,
        is_scanned=True,
    )
    db.add(record)
    db.flush()
    write_log(
        db,
        document_id=document.id,
        action="upload_file",
        performed_by=user.id,
        file_id=record.id,
        note=f"Ghép ảnh scan thành PDF: {record.original_name}",
        ip_address=ip_address,
    )
    return record
