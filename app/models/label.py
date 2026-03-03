"""Label model — colored tags scoped to an organization."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.task_label import TaskLabel


class Label(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_label_org_name"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # hex color e.g. "#FF5733"

    # Relationships
    organization: Mapped[Organization] = relationship("Organization")
    task_labels: Mapped[list[TaskLabel]] = relationship("TaskLabel", back_populates="label")

    def __repr__(self) -> str:
        return f"<Label id={self.id} name={self.name!r}>"
