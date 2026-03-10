"""Task model — the core work-item entity."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.module import Module
    from app.models.sprint import Sprint
    from app.models.task_label import TaskLabel
    from app.models.task_link import TaskLink
    from app.models.user import User


class TaskStatus(enum.StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class IssueType(enum.StrEnum):
    BUG = "bug"
    STORY = "story"
    EPIC = "epic"
    TASK = "task"
    SUBTASK = "subtask"


class Task(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tasks"

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
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="taskstatus"),
        nullable=False,
        default=TaskStatus.TODO,
        index=True,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority, name="taskpriority"),
        nullable=False,
        default=TaskPriority.MEDIUM,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issue_type: Mapped[IssueType] = mapped_column(
        SAEnum(IssueType, name="issuetype"),
        nullable=False,
        default=IssueType.TASK,
        index=True,
    )
    story_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sprint_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Relationships
    organization: Mapped[Organization] = relationship("Organization")
    project: Mapped[Project] = relationship("Project", back_populates="tasks")
    assignee: Mapped[User | None] = relationship("User", foreign_keys=[assignee_user_id])
    created_by: Mapped[User | None] = relationship("User", foreign_keys=[created_by_user_id])
    sprint: Mapped[Sprint | None] = relationship("Sprint", back_populates="tasks")
    module: Mapped[Module | None] = relationship("Module", back_populates="tasks")
    comments: Mapped[list[Comment]] = relationship("Comment", back_populates="task")
    task_labels: Mapped[list[TaskLabel]] = relationship("TaskLabel", back_populates="task")
    parent: Mapped[Task | None] = relationship(
        "Task", remote_side="Task.id", back_populates="subtasks", foreign_keys=[parent_task_id]
    )
    subtasks: Mapped[list[Task]] = relationship(
        "Task", back_populates="parent", foreign_keys="Task.parent_task_id"
    )
    outbound_links: Mapped[list[TaskLink]] = relationship(
        "TaskLink", foreign_keys="TaskLink.source_task_id", back_populates="source_task", cascade="all, delete-orphan"
    )
    inbound_links: Mapped[list[TaskLink]] = relationship(
        "TaskLink", foreign_keys="TaskLink.target_task_id", back_populates="target_task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"
