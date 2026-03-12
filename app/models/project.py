"""Project model — a collection of tasks within an organization."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.project_state import ProjectState
    from app.models.task import Task


class ProjectStatus(enum.StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    identifier: Mapped[str | None] = mapped_column(String(5), nullable=True, unique=True)
    issue_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="projectstatus"),
        nullable=False,
        default=ProjectStatus.ACTIVE,
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="projects")
    tasks: Mapped[list[Task]] = relationship("Task", back_populates="project")
    states: Mapped[list[ProjectState]] = relationship(
        "ProjectState", back_populates="project", cascade="all, delete-orphan",
        order_by="ProjectState.position",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r}>"
