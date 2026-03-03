"""M1 tests — verify ORM models and database schema."""

from __future__ import annotations

import uuid

from sqlalchemy import inspect

from app.db.base import Base
from app.db.session import engine
from app.models import (
    AuditLog,
    IdempotencyKey,
    Organization,
    Task,
    TaskLabel,
    User,
)
from app.models.membership import MembershipStatus, OrgRole
from app.models.project import ProjectStatus
from app.models.task import TaskPriority, TaskStatus

# ---------------------------------------------------------------------------
# Schema reflection tests
# ---------------------------------------------------------------------------

EXPECTED_TABLES = {
    "users",
    "organizations",
    "memberships",
    "invites",
    "refresh_tokens",
    "projects",
    "tasks",
    "comments",
    "labels",
    "task_labels",
    "audit_logs",
    "idempotency_keys",
}


def test_all_tables_exist_in_db():
    """All 12 app tables must be present in the database."""
    inspector = inspect(engine)
    actual = set(inspector.get_table_names())
    missing = EXPECTED_TABLES - actual
    assert not missing, f"Missing tables in DB: {missing}"


def test_metadata_tables_match_expected():
    """Base.metadata must have exactly the 12 expected tables registered."""
    registered = set(Base.metadata.tables.keys())
    assert registered == EXPECTED_TABLES


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


def test_org_role_values():
    assert set(OrgRole) == {
        OrgRole.OWNER,
        OrgRole.ADMIN,
        OrgRole.MEMBER,
        OrgRole.VIEWER,
    }


def test_membership_status_values():
    assert set(MembershipStatus) == {MembershipStatus.ACTIVE, MembershipStatus.INVITED}


def test_project_status_values():
    assert set(ProjectStatus) == {ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED}


def test_task_status_values():
    assert set(TaskStatus) == {
        TaskStatus.TODO,
        TaskStatus.IN_PROGRESS,
        TaskStatus.DONE,
        TaskStatus.BLOCKED,
    }


def test_task_priority_values():
    assert set(TaskPriority) == {
        TaskPriority.LOW,
        TaskPriority.MEDIUM,
        TaskPriority.HIGH,
        TaskPriority.URGENT,
    }


# ---------------------------------------------------------------------------
# Model instantiation tests (no DB round-trip needed)
# ---------------------------------------------------------------------------


def test_user_model_instantiation():
    u = User(email="test@example.com", password_hash="hashed")
    assert u.email == "test@example.com"


def test_organization_model_instantiation():
    org = Organization(name="Acme", slug="acme")
    assert org.slug == "acme"


def test_task_model_instantiation():
    t = Task(
        organization_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Fix bug",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        position=0,
    )
    assert t.title == "Fix bug"
    assert not t.is_deleted


def test_task_soft_delete_mixin():
    from datetime import UTC, datetime

    t = Task(
        organization_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Soft-delete me",
        position=0,
    )
    assert not t.is_deleted
    t.deleted_at = datetime.now(UTC)
    assert t.is_deleted


def test_task_label_composite_pk_columns():
    """TaskLabel must NOT have a surrogate 'id' column."""
    cols = {c.name for c in TaskLabel.__table__.columns}
    assert "task_id" in cols
    assert "label_id" in cols
    assert "id" not in cols


def test_audit_log_no_updated_at():
    """AuditLog should not expose updated_at."""
    assert not hasattr(AuditLog, "updated_at")


def test_idempotency_key_no_updated_at():
    """IdempotencyKey should not expose updated_at."""
    assert not hasattr(IdempotencyKey, "updated_at")
