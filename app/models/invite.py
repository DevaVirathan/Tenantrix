"""Invite model — org invitation tokens."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.membership import OrgRole

if TYPE_CHECKING:
    from app.models.organization import Organization


class Invite(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "invites"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    role: Mapped[OrgRole] = mapped_column(
        SAEnum(OrgRole, name="orgrole"), nullable=False, default=OrgRole.MEMBER
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="invites"
    )

    def __repr__(self) -> str:
        return f"<Invite org={self.organization_id} email={self.email!r}>"
