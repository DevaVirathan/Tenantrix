"""ProjectState model — custom workflow states per project (like Plane)."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project


class StateGroup(enum.StrEnum):
    BACKLOG = "backlog"
    UNSTARTED = "unstarted"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectState(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_states"

    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6b7280")
    group: Mapped[StateGroup] = mapped_column(
        SAEnum(StateGroup, name="stategroup"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    project: Mapped[Project] = relationship("Project", back_populates="states")

    def __repr__(self) -> str:
        return f"<ProjectState id={self.id} name={self.name!r} group={self.group}>"


# Default states seeded when a project is created
DEFAULT_PROJECT_STATES = [
    {"name": "Backlog", "group": StateGroup.BACKLOG, "color": "#a3a3a3", "position": 0, "is_default": False},
    {"name": "Todo", "group": StateGroup.UNSTARTED, "color": "#f97316", "position": 1, "is_default": True},
    {"name": "In Progress", "group": StateGroup.STARTED, "color": "#3b82f6", "position": 2, "is_default": False},
    {"name": "Done", "group": StateGroup.COMPLETED, "color": "#22c55e", "position": 3, "is_default": False},
    {"name": "Cancelled", "group": StateGroup.CANCELLED, "color": "#ef4444", "position": 4, "is_default": False},
]
