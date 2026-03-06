"""API v1 — main router aggregating all domain routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.routers.audit_logs.router import router as audit_logs_router
from app.routers.auth.router import router as auth_router
from app.routers.comments.router import router as comments_router
from app.routers.health.router import router as health_router
from app.routers.organizations.router import router as organizations_router
from app.routers.projects.router import router as projects_router
from app.routers.tasks.router import router as tasks_router

api_router = APIRouter(prefix="/api/v1")

# System
api_router.include_router(health_router)

# Auth
api_router.include_router(auth_router)

# Organizations (M3)
api_router.include_router(organizations_router)

# Projects (M4)
api_router.include_router(projects_router)

# Tasks (M5)
api_router.include_router(tasks_router)

# Comments (M6)
api_router.include_router(comments_router)

# Audit Logs (M7)
api_router.include_router(audit_logs_router)
