"""Tests for tenant-specific rate limiting."""

from __future__ import annotations

import asyncio
import time

import pytest

from app.core.tenant_ratelimit import (
    SubscriptionTier,
    check_tenant_rate_limit,
    get_rate_limit_config,
    get_tenant_rate_limit_status,
    reset_tenant_rate_limit,
)


@pytest.mark.asyncio
async def test_get_rate_limit_config_free_tier():
    """Test getting rate limit config for free tier."""
    config = await get_rate_limit_config(SubscriptionTier.FREE)

    assert config.tier == SubscriptionTier.FREE
    assert config.requests_per_minute == 100
    assert config.requests_per_hour == 5000
    assert config.requests_per_day == 50000


@pytest.mark.asyncio
async def test_get_rate_limit_config_pro_tier():
    """Test getting rate limit config for pro tier."""
    config = await get_rate_limit_config(SubscriptionTier.PRO)

    assert config.tier == SubscriptionTier.PRO
    assert config.requests_per_minute == 1000
    assert config.requests_per_hour == 50000
    assert config.requests_per_day == 500000


@pytest.mark.asyncio
async def test_get_rate_limit_config_enterprise_tier():
    """Test getting rate limit config for enterprise tier."""
    config = await get_rate_limit_config(SubscriptionTier.ENTERPRISE)

    assert config.tier == SubscriptionTier.ENTERPRISE
    assert config.requests_per_minute == 10000
    assert config.requests_per_hour == 500000
    assert config.requests_per_day == 5000000


@pytest.mark.asyncio
async def test_check_tenant_rate_limit_within_quota():
    """Test that requests within quota are allowed."""
    tenant_id = "test-tenant-1"

    # Reset first
    await reset_tenant_rate_limit(tenant_id)

    # Should allow first request
    allowed, remaining, retry_after = await check_tenant_rate_limit(
        tenant_id, SubscriptionTier.FREE, window_type="minute"
    )

    assert allowed is True
    assert remaining == 99  # 100 limit - 1 used
    assert retry_after == 0


@pytest.mark.asyncio
async def test_check_tenant_rate_limit_exceed_quota():
    """Test that requests exceeding quota are rejected."""
    tenant_id = "test-tenant-2"

    # Reset first
    await reset_tenant_rate_limit(tenant_id)

    # Make 100 requests (free tier limit)
    for i in range(100):
        allowed, _, _ = await check_tenant_rate_limit(
            tenant_id, SubscriptionTier.FREE, window_type="minute"
        )
        assert allowed is True, f"Request {i} should be allowed"

    # 101st request should be rejected
    allowed, remaining, retry_after = await check_tenant_rate_limit(
        tenant_id, SubscriptionTier.FREE, window_type="minute"
    )

    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


@pytest.mark.asyncio
async def test_check_tenant_rate_limit_different_tiers():
    """Test that different tiers have different quotas."""
    tenant_free = "test-tenant-free"
    tenant_pro = "test-tenant-pro"

    await reset_tenant_rate_limit(tenant_free)
    await reset_tenant_rate_limit(tenant_pro)

    # Free tier: 100/min
    for i in range(100):
        allowed, _, _ = await check_tenant_rate_limit(
            tenant_free, SubscriptionTier.FREE, window_type="minute"
        )
        assert allowed is True

    allowed, _, _ = await check_tenant_rate_limit(
        tenant_free, SubscriptionTier.FREE, window_type="minute"
    )
    assert allowed is False  # Free tier limit exceeded

    # Pro tier: 1000/min (should allow more)
    for i in range(500):
        allowed, _, _ = await check_tenant_rate_limit(
            tenant_pro, SubscriptionTier.PRO, window_type="minute"
        )
        assert allowed is True

    allowed, _, _ = await check_tenant_rate_limit(
        tenant_pro, SubscriptionTier.PRO, window_type="minute"
    )
    assert allowed is True  # Pro tier should still allow


@pytest.mark.asyncio
async def test_get_tenant_rate_limit_status():
    """Test getting rate limit status for a tenant."""
    tenant_id = "test-tenant-status"

    await reset_tenant_rate_limit(tenant_id)

    # Make some requests
    for i in range(10):
        await check_tenant_rate_limit(
            tenant_id, SubscriptionTier.FREE, window_type="minute"
        )

    status = await get_tenant_rate_limit_status(tenant_id, SubscriptionTier.FREE)

    assert status["tier"] == "free"
    assert status["limits"]["per_minute"] == 100
    assert status["limits"]["per_hour"] == 5000
    assert status["limits"]["per_day"] == 50000

    assert status["usage"]["per_minute"]["used"] == 10
    assert status["usage"]["per_minute"]["limit"] == 100
    assert status["usage"]["per_minute"]["remaining"] == 90


@pytest.mark.asyncio
async def test_reset_tenant_rate_limit():
    """Test resetting rate limit for a tenant."""
    tenant_id = "test-tenant-reset"

    await reset_tenant_rate_limit(tenant_id)

    # Make requests
    for i in range(50):
        await check_tenant_rate_limit(
            tenant_id, SubscriptionTier.FREE, window_type="minute"
        )

    # Verify requests were counted
    status_before = await get_tenant_rate_limit_status(tenant_id, SubscriptionTier.FREE)
    assert status_before["usage"]["per_minute"]["used"] == 50

    # Reset
    await reset_tenant_rate_limit(tenant_id)

    # Verify counter is reset
    status_after = await get_tenant_rate_limit_status(tenant_id, SubscriptionTier.FREE)
    assert status_after["usage"]["per_minute"]["used"] == 0


@pytest.mark.asyncio
async def test_rate_limit_per_window():
    """Test rate limiting for different windows (minute/hour/day)."""
    tenant_id = "test-tenant-windows"

    await reset_tenant_rate_limit(tenant_id)

    # Minute window
    allowed, _, _ = await check_tenant_rate_limit(
        tenant_id, SubscriptionTier.FREE, window_type="minute"
    )
    assert allowed is True

    # Hour window
    allowed, _, _ = await check_tenant_rate_limit(
        tenant_id, SubscriptionTier.FREE, window_type="hour"
    )
    assert allowed is True

    # Day window
    allowed, _, _ = await check_tenant_rate_limit(
        tenant_id, SubscriptionTier.FREE, window_type="day"
    )
    assert allowed is True


if __name__ == "__main__":
    # Run with: pytest tests/test_tenant_rate_limiting.py -v
    pytest.main([__file__, "-v"])
