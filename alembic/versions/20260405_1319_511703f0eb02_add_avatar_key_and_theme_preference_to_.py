"""add avatar_key and theme_preference to users

Revision ID: 511703f0eb02
Revises: n2o3p4q5r6s7
Create Date: 2026-04-05 13:19:58.609948+00:00
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "511703f0eb02"
down_revision: Union[str, None] = "n2o3p4q5r6s7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_key", sa.String(500), nullable=True))
    op.add_column(
        "users",
        sa.Column("theme_preference", sa.String(20), nullable=True, server_default="system"),
    )


def downgrade() -> None:
    op.drop_column("users", "theme_preference")
    op.drop_column("users", "avatar_key")
