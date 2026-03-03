"""TaskLabel — association table linking tasks to labels (many-to-many)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.label import Label
    from app.models.task import Task


class TaskLabel(Base):
    """Pure association table — no surrogate PK, no timestamps."""

    __tablename__ = "task_labels"
    __table_args__ = (
        PrimaryKeyConstraint("task_id", "label_id", name="pk_task_label"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    label_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("labels.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    task: Mapped[Task] = relationship("Task", back_populates="task_labels")
    label: Mapped[Label] = relationship("Label", back_populates="task_labels")

    def __repr__(self) -> str:
        return f"<TaskLabel task={self.task_id} label={self.label_id}>"
