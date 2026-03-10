"""Sprint model — time-boxed iteration for agile planning."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.task import Task


class SprintStatus(enum.StrEnum):
    BACKLOG = "backlog"
    ACTIVE = "active"
    CLOSED = "closed"


class Sprint(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sprints"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SprintStatus] = mapped_column(
        SAEnum(SprintStatus, name="sprintstatus"),
        nullable=False,
        default=SprintStatus.BACKLOG,
        index=True,
    )
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    goals: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped[Organization] = relationship("Organization")
    project: Mapped[Project] = relationship("Project")
    tasks: Mapped[list[Task]] = relationship("Task", back_populates="sprint", foreign_keys="Task.sprint_id")

    def __repr__(self) -> str:
        return f"<Sprint id={self.id} name={self.name!r} status={self.status}>"
