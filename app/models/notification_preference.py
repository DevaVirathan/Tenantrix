"""NotificationPreference model — per-user notification settings."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class NotificationPreference(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_frequency: Mapped[str] = mapped_column(
        String(20), default="instant", nullable=False,
    )  # instant | daily | weekly
    events: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
        server_default="{}",
    )
    # events schema: {"task.assigned": true, "task.state_changed": true, "comment.created": true, ...}

    def __repr__(self) -> str:
        return f"<NotificationPreference user_id={self.user_id}>"
