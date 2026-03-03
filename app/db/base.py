"""SQLAlchemy declarative base and reusable ORM mixins."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base — all ORM models inherit from this."""


class UUIDMixin:
    """Primary key as a UUID, generated server-side by Python."""
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        sort_order=-10,
    )


class TimestampMixin:
    """Automatic created_at / updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        sort_order=100,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        sort_order=101,
    )


class SoftDeleteMixin:
    """Soft-delete support via deleted_at timestamp (NULL = active)."""
    deleted_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
        sort_order=102,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
