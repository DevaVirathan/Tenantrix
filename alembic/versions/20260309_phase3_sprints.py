"""create sprints table, add sprint_id to tasks

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-09 20:00:00.000000+00:00
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create sprintstatus enum
    sprintstatus_enum = postgresql.ENUM("backlog", "active", "closed", name="sprintstatus", create_type=False)
    sprintstatus_enum.create(op.get_bind(), checkfirst=True)

    # Create sprints table
    op.create_table(
        "sprints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sprintstatus_enum, nullable=False, server_default="backlog"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("goals", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_sprints_organization_id"), "sprints", ["organization_id"])
    op.create_index(op.f("ix_sprints_project_id"), "sprints", ["project_id"])
    op.create_index(op.f("ix_sprints_status"), "sprints", ["status"])

    # Add sprint_id to tasks
    op.add_column(
        "tasks",
        sa.Column(
            "sprint_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sprints.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(op.f("ix_tasks_sprint_id"), "tasks", ["sprint_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_sprint_id"), table_name="tasks")
    op.drop_column("tasks", "sprint_id")

    op.drop_index(op.f("ix_sprints_status"), table_name="sprints")
    op.drop_index(op.f("ix_sprints_project_id"), table_name="sprints")
    op.drop_index(op.f("ix_sprints_organization_id"), table_name="sprints")
    op.drop_table("sprints")
    sa.Enum(name="sprintstatus").drop(op.get_bind(), checkfirst=True)
