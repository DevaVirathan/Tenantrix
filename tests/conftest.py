"""Pytest fixtures shared across the entire test suite."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

# Set test env before importing app modules
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/tenantrix_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-only")
os.environ.setdefault("ENVIRONMENT", "test")

from app.main import app

# ---------------------------------------------------------------------------
# Test DB engine (separate from the app engine so we can truncate freely)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.environ["DATABASE_URL"]
_test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

# Tables to truncate between tests (FK-safe order: children first)
_TRUNCATE_ORDER = [
    "task_labels",
    "audit_logs",
    "idempotency_keys",
    "comments",
    "tasks",
    "labels",
    "projects",
    "invites",
    "refresh_tokens",
    "memberships",
    "organizations",
    "users",
]


@pytest.fixture(autouse=True)
def _clean_db():
    """Truncate all app tables before every test for full isolation."""
    with _test_engine.connect() as conn, conn.begin():
        for table in _TRUNCATE_ORDER:
            conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture(scope="function")
def client():
    """TestClient backed by the real test DB (tables wiped per test)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
