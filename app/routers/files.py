from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.user import User
from app.security import check_csrf_token
from app.services import file_service, pdf_service
from app.services.permission_service import require_document_permission
from app.views import client_ip

router = APIRouter(tags=["files"])


def _get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy văn bản.")
    return document


@router.post("/documents/{document_id}/files")
async def upload_files(
    request: Request,
    document_id: int,
    csrf_token: str = Form(...),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_upload_file")
    for upload in files or []:
        await file_service.save_upload_file(db, document=document, upload=upload, user=current_user, ip_address=client_ip(request))
    db.commit()
    return RedirectResponse(f"/documents/{document.id}", status_code=303)


@router.post("/documents/{document_id}/scan-pdf")
async def scan_to_pdf(
    request: Request,
    document_id: int,
    csrf_token: str = Form(...),
    scan_images: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    document = _get_document_or_404(db, document_id)
    require_document_permission(db, current_user, document, "can_upload_file")
    pdf_path = await pdf_service.images_to_pdf(scan_images or [], output_name=f"scan_{document.id}.pdf")
    file_service.copy_generated_pdf(
        db,
        document=document,
        pdf_path=pdf_path,
        original_name=f"scan_document_{document.id}.pdf",
        user=current_user,
        ip_address=client_ip(request),
    )
    pdf_path.unlink(missing_ok=True)
    db.commit()
    return RedirectResponse(f"/documents/{document.id}", status_code=303)


@router.get("/files/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.get(DocumentFile, file_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy file.")
    require_document_permission(db, current_user, record.document, "can_view")
    path = file_service.assert_path_inside_uploads(record.file_path)
    return FileResponse(path, filename=record.original_name, media_type="application/octet-stream")


@router.post("/files/{file_id}/delete")
def delete_file(
    request: Request,
    file_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_csrf_token(request, csrf_token)
    record = db.get(DocumentFile, file_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy file.")
    require_document_permission(db, current_user, record.document, "can_upload_file")
    document_id = record.document_id
    file_service.delete_document_file(db, file=record, user=current_user, ip_address=client_ip(request))
    db.commit()
    return RedirectResponse(f"/documents/{document_id}", status_code=303)

