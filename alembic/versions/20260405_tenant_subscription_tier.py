"""Add subscription tier to organizations for tenant-specific rate limiting."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260405_tenant_subscription_tier"
down_revision = "20260405_1319_511703f0eb02_add_avatar_key_and_theme_preference_to_"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add subscription tier column to organizations table."""
    op.add_column(
        "organizations",
        sa.Column(
            "subscription_tier",
            sa.String(50),
            nullable=False,
            server_default="free",
        ),
    )
    
    # Create index for tier lookups
    op.create_index(
        "ix_organizations_subscription_tier",
        "organizations",
        ["subscription_tier"],
    )


def downgrade() -> None:
    """Remove subscription tier column."""
    op.drop_index("ix_organizations_subscription_tier", table_name="organizations")
    op.drop_column("organizations", "subscription_tier")
