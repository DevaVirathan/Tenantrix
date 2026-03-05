"""API v1 — main router that aggregates all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import audit_logs, auth, comments, health, organizations, projects, tasks

api_router = APIRouter(prefix="/api/v1")

# System
api_router.include_router(health.router)

# Auth
api_router.include_router(auth.router)

# M3 — Organisations
api_router.include_router(organizations.router)

# M4 — Projects
api_router.include_router(projects.router)

# M5 — Tasks
api_router.include_router(tasks.router)

# M6 — Comments
api_router.include_router(comments.router)

# M7 — Audit Logs
api_router.include_router(audit_logs.router)
