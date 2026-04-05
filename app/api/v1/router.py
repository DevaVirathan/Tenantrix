"""API v1 — main router that aggregates all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    analytics, attachments, audit_logs, auth, comments, csv_tasks, health,
    modules, notifications, organizations, project_states, projects,
    rate_limits, saved_views, search, sprints, tasks, watchers, websocket,
)

api_router = APIRouter(prefix="/api/v1")

# System
api_router.include_router(health.router)

# Auth
api_router.include_router(auth.router)

# Rate Limiting & Quotas
api_router.include_router(rate_limits.router)

# M3 — Organisations
api_router.include_router(organizations.router)

# M4 — Projects
api_router.include_router(projects.router)

# Project States (custom workflow states)
api_router.include_router(project_states.router)

# M5 — Tasks
api_router.include_router(tasks.router)

# CSV Import/Export
api_router.include_router(csv_tasks.router)

# Sprints
api_router.include_router(sprints.router)

# Modules
api_router.include_router(modules.router)

# M6 — Comments
api_router.include_router(comments.router)

# Notifications
api_router.include_router(notifications.router)

# Analytics & Search
api_router.include_router(analytics.router)
api_router.include_router(search.router)

# Watchers
api_router.include_router(watchers.router)

# Saved Views
api_router.include_router(saved_views.router)

# Attachments
api_router.include_router(attachments.router)

# M7 — Audit Logs
api_router.include_router(audit_logs.router)

# WebSocket — real-time updates
api_router.include_router(websocket.router)
