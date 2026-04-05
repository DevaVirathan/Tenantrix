"""Tenant-specific rate limiting middleware."""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.tenant_ratelimit import check_tenant_rate_limit

logger = logging.getLogger(__name__)


class TenantRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces tenant-specific rate limits using Redis.

    Extracts tenant ID and subscription tier from request and enforces
    per-tenant quotas. Returns 429 with Retry-After header when exceeded.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tenant rate limiting."""

        # Skip rate limiting for certain paths
        skip_paths = {"/health", "/health/detailed", "/docs", "/redoc", "/openapi.json"}
        if request.url.path in skip_paths:
            return await call_next(request)

        # Extract tenant info from request
        tenant_id = request.headers.get("X-Tenant-ID")

        # If no tenant in header, try to extract from JWT or path
        if not tenant_id:
            # Try to extract from Authorization header (will be validated by auth dependency)
            # This is an optimization to avoid database lookup for rate limiting
            # In production, you'd decode JWT to get tenant ID
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                # Anonymous requests use client IP as identifier
                tenant_id = f"anonymous:{request.client.host}"
            else:
                # For authenticated requests, rate limiting will be applied at endpoint level
                # This middleware applies to unauthenticated requests
                return await call_next(request)

        # Extract subscription tier (default to free)
        tier = request.headers.get("X-Subscription-Tier", "free")

        try:
            # Check rate limit
            allowed, remaining, retry_after = await check_tenant_rate_limit(
                tenant_id, tier, window_type="minute"
            )

            if not allowed:
                response = Response(
                    content='{"detail":"Rate limit exceeded"}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                )
                response.headers["Retry-After"] = str(retry_after)
                response.headers["X-RateLimit-Limit"] = "100"  # Default for display
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(int(__import__("time").time()) + retry_after)

                logger.warning(
                    f"Rate limit exceeded for tenant {tenant_id} - retry after {retry_after}s"
                )
                return response

        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # On error, allow request to prevent service disruption
            pass

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit-Reset"] = "60"

        return response
