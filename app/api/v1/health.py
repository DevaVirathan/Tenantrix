"""System health check endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings
from app.core.redis import redis_health_check

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


@router.get("/health/detailed", summary="Detailed health check with dependencies")
async def health_check_detailed() -> dict:
    """
    Returns detailed health status including Redis and other dependencies.

    This endpoint checks both the application and its critical dependencies.
    """
    redis_ok = await redis_health_check()

    return {
        "status": "ok" if redis_ok else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "dependencies": {
            "redis": "ok" if redis_ok else "down",
        },
    }
