"""TaskLink — directional relationship between two tasks."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class LinkType(enum.StrEnum):
    BLOCKS = "blocks"
    IS_BLOCKED_BY = "is_blocked_by"
    RELATES_TO = "relates_to"
    DUPLICATE_OF = "duplicate_of"


class TaskLink(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "task_links"
    __table_args__ = (
        UniqueConstraint("source_task_id", "target_task_id", "link_type", name="uq_task_link"),
    )

    source_task_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_task_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_type: Mapped[LinkType] = mapped_column(
        SAEnum(LinkType, name="linktype"),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    source_task: Mapped[Task] = relationship(
        "Task", foreign_keys=[source_task_id], back_populates="outbound_links"
    )
    target_task: Mapped[Task] = relationship(
        "Task", foreign_keys=[target_task_id], back_populates="inbound_links"
    )
    created_by: Mapped[User | None] = relationship("User", foreign_keys=[created_by_user_id])

    def __repr__(self) -> str:
        return f"<TaskLink {self.source_task_id} --{self.link_type}--> {self.target_task_id}>"
