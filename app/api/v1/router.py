"""API v1 — main router that aggregates all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, health

api_router = APIRouter(prefix="/api/v1")

# System
api_router.include_router(health.router)

# Auth
api_router.include_router(auth.router)

# Future routers will be added here as milestones are completed:
# from app.api.v1 import organizations, projects, tasks, comments
# api_router.include_router(organizations.router, prefix="/organizations")
# api_router.include_router(projects.router, prefix="/projects")
# api_router.include_router(tasks.router, prefix="/tasks")
# api_router.include_router(comments.router, prefix="/comments")
