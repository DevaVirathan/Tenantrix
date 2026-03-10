"""add issue_type, story_points, start_date, due_date to tasks

Revision ID: a1b2c3d4e5f6
Revises: 10743138f2ab
Create Date: 2026-03-09 18:00:00.000000+00:00
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "10743138f2ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the issuetype enum
    issuetype_enum = sa.Enum("bug", "story", "epic", "task", "subtask", name="issuetype")
    issuetype_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns to tasks table
    op.add_column("tasks", sa.Column("issue_type", issuetype_enum, nullable=False, server_default="task"))
    op.add_column("tasks", sa.Column("story_points", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("start_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tasks", sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))

    # Add index on issue_type for filtering
    op.create_index(op.f("ix_tasks_issue_type"), "tasks", ["issue_type"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_issue_type"), table_name="tasks")
    op.drop_column("tasks", "due_date")
    op.drop_column("tasks", "start_date")
    op.drop_column("tasks", "story_points")
    op.drop_column("tasks", "issue_type")

    # Drop the enum type
    sa.Enum(name="issuetype").drop(op.get_bind(), checkfirst=True)
