"""create modules table, add module_id to tasks

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-10 00:00:00.000000+00:00
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    modulestatus_enum = postgresql.ENUM("active", "closed", name="modulestatus", create_type=False)
    modulestatus_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", modulestatus_enum, nullable=False, server_default="active"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_modules_organization_id"), "modules", ["organization_id"])
    op.create_index(op.f("ix_modules_project_id"), "modules", ["project_id"])
    op.create_index(op.f("ix_modules_status"), "modules", ["status"])

    op.add_column(
        "tasks",
        sa.Column("module_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("modules.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index(op.f("ix_tasks_module_id"), "tasks", ["module_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_module_id"), table_name="tasks")
    op.drop_column("tasks", "module_id")

    op.drop_index(op.f("ix_modules_status"), table_name="modules")
    op.drop_index(op.f("ix_modules_project_id"), table_name="modules")
    op.drop_index(op.f("ix_modules_organization_id"), table_name="modules")
    op.drop_table("modules")
    sa.Enum(name="modulestatus").drop(op.get_bind(), checkfirst=True)
