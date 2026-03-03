"""API v1 — main router that aggregates all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, health, organizations, projects

api_router = APIRouter(prefix="/api/v1")

# System
api_router.include_router(health.router)

# Auth
api_router.include_router(auth.router)

# M3 — Organisations
api_router.include_router(organizations.router)

# M4 — Projects
api_router.include_router(projects.router)

# Future routers will be added here as milestones are completed:
# from app.api.v1 import tasks, comments
# api_router.include_router(tasks.router)
# api_router.include_router(comments.router)
