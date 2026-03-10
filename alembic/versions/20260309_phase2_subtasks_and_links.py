"""add parent_task_id to tasks, create task_links table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-09 19:00:00.000000+00:00
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add parent_task_id to tasks (self-referential FK)
    op.add_column(
        "tasks",
        sa.Column(
            "parent_task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index(op.f("ix_tasks_parent_task_id"), "tasks", ["parent_task_id"])

    # Create linktype enum (before table so create_table doesn't auto-create it)
    linktype_enum = postgresql.ENUM("blocks", "is_blocked_by", "relates_to", "duplicate_of", name="linktype", create_type=False)
    linktype_enum.create(op.get_bind(), checkfirst=True)

    # Create task_links table
    op.create_table(
        "task_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("link_type", linktype_enum, nullable=False),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_task_id", "target_task_id", "link_type", name="uq_task_link"),
    )
    op.create_index(op.f("ix_task_links_source_task_id"), "task_links", ["source_task_id"])
    op.create_index(op.f("ix_task_links_target_task_id"), "task_links", ["target_task_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_task_links_target_task_id"), table_name="task_links")
    op.drop_index(op.f("ix_task_links_source_task_id"), table_name="task_links")
    op.drop_table("task_links")
    sa.Enum(name="linktype").drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_tasks_parent_task_id"), table_name="tasks")
    op.drop_column("tasks", "parent_task_id")
