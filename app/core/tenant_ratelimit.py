"""Tenant-specific rate limiting using Redis sliding window."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Tuple

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Available subscription tiers."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a subscription tier."""

    tier: SubscriptionTier
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int


# Rate limiting quotas per tier
RATE_LIMIT_CONFIGS: dict[SubscriptionTier, RateLimitConfig] = {
    SubscriptionTier.FREE: RateLimitConfig(
        tier=SubscriptionTier.FREE,
        requests_per_minute=100,
        requests_per_hour=5000,
        requests_per_day=50000,
    ),
    SubscriptionTier.PRO: RateLimitConfig(
        tier=SubscriptionTier.PRO,
        requests_per_minute=1000,
        requests_per_hour=50000,
        requests_per_day=500000,
    ),
    SubscriptionTier.ENTERPRISE: RateLimitConfig(
        tier=SubscriptionTier.ENTERPRISE,
        requests_per_minute=10000,
        requests_per_hour=500000,
        requests_per_day=5000000,
    ),
}


async def get_rate_limit_config(tier: str | SubscriptionTier) -> RateLimitConfig:
    """Get rate limit configuration for a tier."""
    if isinstance(tier, str):
        tier = SubscriptionTier(tier.lower())

    return RATE_LIMIT_CONFIGS.get(tier, RATE_LIMIT_CONFIGS[SubscriptionTier.FREE])


async def check_tenant_rate_limit(
    tenant_id: str,
    tier: str | SubscriptionTier,
    window_type: str = "minute",
) -> Tuple[bool, int, int]:
    """
    Check if tenant has exceeded rate limit using sliding window.

    Returns:
        Tuple[allowed: bool, remaining: int, retry_after_seconds: int]
            - allowed: Whether request is allowed
            - remaining: Requests remaining in window
            - retry_after_seconds: How many seconds to retry after (0 if allowed)
    """
    config = await get_rate_limit_config(tier)

    # Select limit based on window
    if window_type == "minute":
        limit = config.requests_per_minute
        window_seconds = 60
    elif window_type == "hour":
        limit = config.requests_per_hour
        window_seconds = 3600
    elif window_type == "day":
        limit = config.requests_per_day
        window_seconds = 86400
    else:
        raise ValueError(f"Invalid window_type: {window_type}")

    client = await get_redis_client()
    key = f"ratelimit:{tenant_id}:{window_type}"

    current_time = time.time()
    window_start = current_time - window_seconds

    try:
        # Remove expired entries (outside sliding window)
        await client.zremrangebyscore(key, "-inf", window_start)

        # Get current count in window
        current_count = await client.zcard(key)

        if current_count < limit:
            # Add new request with current timestamp
            await client.zadd(key, {str(current_time): current_time})

            # Set key expiration to window_seconds + 1
            await client.expire(key, window_seconds + 1)

            remaining = limit - current_count - 1
            logger.debug(
                f"Tenant {tenant_id} ({tier}): {current_count + 1}/{limit} "
                f"requests in {window_type}"
            )

            return True, remaining, 0

        else:
            # Exceeded limit - calculate retry-after
            oldest_request = await client.zrange(key, 0, 0, withscores=True)

            if oldest_request:
                oldest_timestamp = oldest_request[0][1]
                retry_after = int(ceil((oldest_timestamp + window_seconds) - current_time))
            else:
                retry_after = window_seconds

            logger.warning(
                f"Tenant {tenant_id} ({tier}): Rate limit exceeded "
                f"({limit} requests/{window_type}, retry after {retry_after}s)"
            )

            return False, 0, max(1, retry_after)

    except Exception as e:
        logger.error(f"Rate limit check error for tenant {tenant_id}: {e}")
        # On error, allow request to prevent service disruption
        return True, limit, 0


async def get_tenant_rate_limit_status(
    tenant_id: str,
    tier: str | SubscriptionTier,
) -> dict:
    """Get current rate limit status for a tenant."""
    config = await get_rate_limit_config(tier)
    client = await get_redis_client()

    current_time = time.time()
    status = {
        "tier": tier if isinstance(tier, str) else tier.value,
        "limits": {
            "per_minute": config.requests_per_minute,
            "per_hour": config.requests_per_hour,
            "per_day": config.requests_per_day,
        },
        "usage": {},
    }

    # Check each window
    for window_type, window_seconds in [("minute", 60), ("hour", 3600), ("day", 86400)]:
        key = f"ratelimit:{tenant_id}:{window_type}"
        window_start = current_time - window_seconds

        await client.zremrangebyscore(key, "-inf", window_start)
        current_count = await client.zcard(key)

        if window_type == "minute":
            limit = config.requests_per_minute
        elif window_type == "hour":
            limit = config.requests_per_hour
        else:
            limit = config.requests_per_day

        status["usage"][window_type] = {
            "used": current_count,
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset_in_seconds": window_seconds,
        }

    return status


async def reset_tenant_rate_limit(tenant_id: str) -> None:
    """Reset all rate limit counters for a tenant."""
    client = await get_redis_client()

    for window_type in ["minute", "hour", "day"]:
        key = f"ratelimit:{tenant_id}:{window_type}"
        await client.delete(key)

    logger.info(f"Rate limit reset for tenant {tenant_id}")
