"""Rate limiting and tenant quota endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, OrgMember, get_current_user
from app.core.tenant_ratelimit import (
    SubscriptionTier,
    get_rate_limit_config,
    get_tenant_rate_limit_status,
    reset_tenant_rate_limit,
)
from app.db.session import get_db
from app.models.organization import Organization
from app.models.membership import Membership

router = APIRouter(prefix="/rate-limits", tags=["rate-limiting"])


@router.get("/config", summary="Get global rate limit configuration")
async def get_rate_limit_config_endpoint() -> dict:
    """
    Get rate limiting configuration for all subscription tiers.

    Returns tier-specific quotas:
    - Free: 100 req/min, 5000 req/hour, 50000 req/day
    - Pro: 1000 req/min, 50000 req/hour, 500000 req/day
    - Enterprise: 10000 req/min, 500000 req/hour, 5000000 req/day
    """
    configs = {}

    for tier in SubscriptionTier:
        config = await get_rate_limit_config(tier)
        configs[tier.value] = {
            "tier": config.tier.value,
            "requests_per_minute": config.requests_per_minute,
            "requests_per_hour": config.requests_per_hour,
            "requests_per_day": config.requests_per_day,
        }

    return {"tiers": configs}


@router.get(
    "/orgs/{org_id}/status",
    summary="Get rate limit status for organization",
)
async def get_org_rate_limit_status(
    org_and_membership: Annotated[tuple, Depends(OrgMember)],
) -> dict:
    """
    Get current rate limit usage for an organization.

    Shows remaining requests for the current minute, hour, and day.
    """
    org, _membership = org_and_membership
    status_data = await get_tenant_rate_limit_status(str(org.id), org.subscription_tier)

    return {
        "organization_id": str(org.id),
        "organization_name": org.name,
        "subscription_tier": org.subscription_tier,
        "rate_limits": status_data,
    }


@router.post(
    "/orgs/{org_id}/reset",
    summary="Reset rate limit counters (admin only)",
)
async def reset_org_rate_limit(
    org_id: str = Path(..., description="Organization ID"),
    current_user: Annotated[object, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> dict:
    """
    Reset all rate limit counters for an organization.

    **Requires admin or owner role.**
    """
    from uuid import UUID

    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format",
        )

    org = db.get(Organization, org_uuid)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    from app.models.membership import OrgRole

    membership = (
        db.query(Membership)
        .filter_by(organization_id=org_uuid, user_id=current_user.id)
        .first()
    )

    if not membership or membership.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    if membership.role not in [OrgRole.ADMIN, OrgRole.OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can reset rate limits",
        )

    await reset_tenant_rate_limit(str(org.id))

    return {
        "message": "Rate limit counters reset successfully",
        "organization_id": str(org.id),
        "organization_name": org.name,
    }


@router.get("/docs", summary="Rate limiting documentation")
async def get_rate_limiting_docs() -> dict:
    """
    Get documentation on rate limiting.

    Returns information about:
    - Per-tenant quotas
    - Sliding window algorithm
    - Rate limit headers
    - Retry-After header usage
    """
    return {
        "title": "Tenant-Specific Rate Limiting",
        "description": "Redis-backed sliding window rate limiting with per-tenant quotas",
        "algorithm": "Sliding Window (Redis sorted sets)",
        "tiers": {
            "free": {
                "requests_per_minute": 100,
                "requests_per_hour": 5000,
                "requests_per_day": 50000,
                "use_case": "Development and low-traffic applications",
            },
            "pro": {
                "requests_per_minute": 1000,
                "requests_per_hour": 50000,
                "requests_per_day": 500000,
                "use_case": "Production applications with moderate traffic",
            },
            "enterprise": {
                "requests_per_minute": 10000,
                "requests_per_hour": 500000,
                "requests_per_day": 5000000,
                "use_case": "High-traffic production applications",
            },
        },
        "headers": {
            "request_headers": {
                "X-Tenant-ID": "Optional: Explicitly set tenant ID",
                "X-Subscription-Tier": "Optional: Specify tier (default: from org or 'free')",
            },
            "response_headers": {
                "X-RateLimit-Limit": "Maximum requests in window",
                "X-RateLimit-Remaining": "Requests remaining in window",
                "X-RateLimit-Reset": "Unix timestamp when limit resets",
                "Retry-After": "Seconds to wait before retrying (on 429)",
            },
        },
        "status_codes": {
            "200": "Request successful",
            "429": "Rate limit exceeded - see Retry-After header",
        },
        "endpoints": {
            "get_config": "GET /api/v1/rate-limits/config",
            "get_status": "GET /api/v1/rate-limits/orgs/{org_id}/status",
            "reset": "POST /api/v1/rate-limits/orgs/{org_id}/reset",
            "docs": "GET /api/v1/rate-limits/docs",
        },
    }
