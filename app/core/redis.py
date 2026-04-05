"""Redis client and connection management."""

from __future__ import annotations

import logging
from typing import Any

from redis.asyncio import AsyncRedis, from_url

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis instance
redis_client: AsyncRedis[bytes] | None = None


async def get_redis_client() -> AsyncRedis[bytes]:
    """Get or create the global Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = await from_url(
            settings.REDIS_URL,
            encoding=None,
            decode_responses=False,
        )
    return redis_client


async def init_redis() -> None:
    """Initialize Redis connection on startup."""
    try:
        client = await get_redis_client()
        # Test connection with ping
        pong = await client.ping()
        if pong:
            logger.info("✓ Redis connected successfully")
        else:
            raise RuntimeError("Redis ping failed")
    except Exception as e:
        logger.error(f"✗ Failed to connect to Redis: {e}")
        raise


async def close_redis() -> None:
    """Close Redis connection on shutdown."""
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
        logger.info("✓ Redis connection closed")


async def redis_get(key: str) -> Any:
    """Get a value from Redis."""
    client = await get_redis_client()
    return await client.get(key)


async def redis_set(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    """Set a value in Redis with optional TTL."""
    client = await get_redis_client()
    if ttl_seconds:
        await client.setex(key, ttl_seconds, value)
    else:
        await client.set(key, value)


async def redis_delete(key: str) -> int:
    """Delete a key from Redis."""
    client = await get_redis_client()
    return await client.delete(key)


async def redis_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern."""
    client = await get_redis_client()
    keys = await client.keys(pattern)
    if keys:
        return await client.delete(*keys)
    return 0


async def redis_exists(key: str) -> bool:
    """Check if a key exists in Redis."""
    client = await get_redis_client()
    return await client.exists(key) > 0


async def redis_incr(key: str, amount: int = 1) -> int:
    """Increment a counter in Redis."""
    client = await get_redis_client()
    return await client.incrby(key, amount)


async def redis_health_check() -> bool:
    """Health check for Redis."""
    try:
        client = await get_redis_client()
        pong = await client.ping()
        return pong is True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
