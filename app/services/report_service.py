from __future__ import annotations

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from app.config import get_upload_dir
from app.constants import DOCUMENT_STATUSES
from app.models.document import Document
from app.services.document_service import latest_document_note, search_documents


def _status_label(status: str) -> str:
    return DOCUMENT_STATUSES.get(status, status)


def export_documents_excel(db: Session, **filters) -> Path:
    documents = search_documents(db, **filters)
    reports_dir = get_upload_dir() / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"bao_cao_van_ban_{datetime.utcnow():%Y%m%d_%H%M%S}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "Bao cao"

    title_font = Font(name="Times New Roman", size=16, bold=True)
    normal_font = Font(name="Times New Roman", size=13)
    header_font = Font(name="Times New Roman", size=13, bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E79")

    ws.merge_cells("A1:O1")
    ws["A1"] = "BÁO CÁO QUẢN LÝ VĂN BẢN ĐỀ XUẤT"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.merge_cells("A2:O2")
    ws["A2"] = f"Ngày xuất báo cáo: {datetime.now():%d/%m/%Y %H:%M}"
    ws["A2"].font = normal_font
    ws["A2"].alignment = Alignment(horizontal="center")

    status_counts: dict[str, int] = {}
    for doc in documents:
        status_counts[doc.status] = status_counts.get(doc.status, 0) + 1
    ws["A4"] = "Tổng số văn bản"
    ws["B4"] = len(documents)
    ws["A4"].font = ws["B4"].font = normal_font
    row = 5
    for status, label in DOCUMENT_STATUSES.items():
        ws.cell(row=row, column=1, value=label).font = normal_font
        ws.cell(row=row, column=2, value=status_counts.get(status, 0)).font = normal_font
        row += 1

    headers = [
        "STT",
        "Số văn bản",
        "Số/ký hiệu",
        "Tiêu đề",
        "Người đề xuất",
        "Người tạo",
        "Chủ văn bản",
        "Đơn vị",
        "Trạng thái hiện tại",
        "Ngày tạo",
        "Ngày cập nhật cuối",
        "Người cập nhật cuối",
        "Ghi chú cuối",
        "Số lượng file đính kèm",
        "Người được phân quyền xử lý",
    ]
    header_row = row + 1
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for index, doc in enumerate(documents, start=1):
        data_row = header_row + index
        permitted_users = ", ".join(p.user.full_name for p in doc.permissions if p.user)
        values = [
            index,
            doc.document_code or "",
            doc.document_number or "",
            doc.title,
            doc.proposer_name or "",
            doc.creator.full_name if doc.creator else "",
            doc.owner.full_name if doc.owner else "",
            doc.department or "",
            _status_label(doc.status),
            doc.created_at.strftime("%d/%m/%Y") if doc.created_at else "",
            doc.updated_at.strftime("%d/%m/%Y %H:%M") if doc.updated_at else "",
            doc.updater.full_name if doc.updater else "",
            latest_document_note(db, doc.id),
            len(doc.files),
            permitted_users,
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=data_row, column=col, value=value)
            cell.font = normal_font
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    ws.auto_filter.ref = f"A{header_row}:O{header_row + len(documents)}"
    widths = [8, 16, 18, 36, 22, 22, 22, 22, 24, 16, 20, 22, 36, 18, 36]
    for col, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = width

    wb.save(path)
    return path
