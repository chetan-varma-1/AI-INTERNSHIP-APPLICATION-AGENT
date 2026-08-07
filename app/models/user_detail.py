"""Uploaded resume and cover-letter ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.user import User


class UserDetail(Base):
    """Structured data extracted from a user's uploaded document."""

    __tablename__ = "user_details"
    __table_args__ = (
        CheckConstraint(
            "type IN ('resume', 'cover_letter')",
            name="ck_user_details_type",
        ),
        Index("ix_user_details_user_id_type", "user_id", "type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column("type", String(20), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)

    education: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    projects: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    experience: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    profile_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    certifications: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, default=list
    )

    applicant_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    letter_date: Mapped[str | None] = mapped_column(String(60), nullable=True)
    hiring_manager_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    company_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(180), nullable=True)
    salutation: Mapped[str | None] = mapped_column(Text, nullable=True)
    opening_paragraph: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_paragraphs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    why_this_company: Mapped[str | None] = mapped_column(Text, nullable=True)
    closing_paragraph: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="details")
