"""System health check endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["system"])


@router.get("/health", summary="Health check")
def health_check() -> dict:
    """
    Returns the current application status, version, environment, and timestamp.

    This endpoint is public (no auth required) and is used by load balancers,
    Docker health checks, and CI pipelines to verify the service is running.
    """
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }
