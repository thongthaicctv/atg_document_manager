from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.timezone import utc_now


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_code: Mapped[str | None] = mapped_column(String(100), index=True)
    document_number: Mapped[str | None] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    document_type: Mapped[str | None] = mapped_column(String(255), index=True)
    incoming_action: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    proposer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    proposer_name: Mapped[str | None] = mapped_column(String(255), index=True)
    department: Mapped[str | None] = mapped_column(String(255), index=True)
    sender_department: Mapped[str | None] = mapped_column(String(255), index=True)
    receiver_department: Mapped[str | None] = mapped_column(String(255), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new_draft", index=True)
    priority: Mapped[str] = mapped_column(String(30), nullable=False, default="normal")
    leader_name: Mapped[str | None] = mapped_column(String(255))
    submitted_to_leader_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    reminder_dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reminder_dismissed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_documents")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_documents")
    updater = relationship("User", foreign_keys=[updated_by])
    proposer = relationship("User", foreign_keys=[proposer_id])
    source_document = relationship("Document", remote_side=[id], foreign_keys=[source_document_id], back_populates="related_outgoing_documents")
    related_outgoing_documents = relationship("Document", foreign_keys=[source_document_id], back_populates="source_document")
    reminder_dismissed_user = relationship("User", foreign_keys=[reminder_dismissed_by])
    files = relationship("DocumentFile", back_populates="document", cascade="all, delete-orphan")
    logs = relationship("DocumentLog", back_populates="document", cascade="all, delete-orphan", order_by="DocumentLog.performed_at.desc()")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
