"""Comment model — task comments with soft delete."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.organization import Organization
    from app.db.models.task import Task
    from app.db.models.user import User


class Comment(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "comments"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    organization: Mapped[Organization] = relationship("Organization")
    task: Mapped[Task] = relationship("Task", back_populates="comments")
    author: Mapped[User | None] = relationship("User", foreign_keys=[author_user_id])

    def __repr__(self) -> str:
        return f"<Comment id={self.id} task={self.task_id}>"
