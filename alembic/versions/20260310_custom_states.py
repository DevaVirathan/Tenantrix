"""add project_states table, state_id + sequence_id to tasks, identifier + issue_sequence to projects

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-03-10 14:00:00.000000+00:00
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create stategroup enum (use create_type=False to prevent auto-creation in create_table)
    stategroup_enum = postgresql.ENUM(
        "BACKLOG", "UNSTARTED", "STARTED", "COMPLETED", "CANCELLED",
        name="stategroup",
        create_type=False,
    )
    stategroup_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create project_states table
    op.create_table(
        "project_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6b7280"),
        sa.Column("group", stategroup_enum, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 3. Add identifier + issue_sequence to projects
    op.add_column("projects", sa.Column("identifier", sa.String(5), nullable=True, unique=True))
    op.add_column("projects", sa.Column("issue_sequence", sa.Integer, nullable=False, server_default="0"))

    # 4. Add state_id + sequence_id to tasks
    op.add_column("tasks", sa.Column("state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_states.id", ondelete="SET NULL"), nullable=True))
    op.add_column("tasks", sa.Column("sequence_id", sa.Integer, nullable=True))
    op.create_index(op.f("ix_tasks_state_id"), "tasks", ["state_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_state_id"), table_name="tasks")
    op.drop_column("tasks", "sequence_id")
    op.drop_column("tasks", "state_id")
    op.drop_column("projects", "issue_sequence")
    op.drop_column("projects", "identifier")
    op.drop_table("project_states")
    sa.Enum(name="stategroup").drop(op.get_bind(), checkfirst=True)
