"""API v1 — compatibility shim. Main router moved to app.routers.setup_router."""

from __future__ import annotations

# Re-export for backwards compatibility
from app.routers.setup_router import api_router  # noqa: F401
