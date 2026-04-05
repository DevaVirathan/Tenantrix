"""Caching service with decorators for Redis-backed caching."""

from __future__ import annotations

import functools
import json
import logging
from typing import Any, Callable, TypeVar

from app.core.config import settings
from app.core.redis import get_redis_client, redis_delete_pattern

logger = logging.getLogger(__name__)

T = TypeVar("T")


def cache_key(*args: Any, prefix: str = "", suffix: str = "") -> str:
    """Generate a cache key from arguments."""
    key_parts = [str(arg) for arg in args if arg is not None]
    key = ":".join(key_parts) if key_parts else "cache"
    if prefix:
        key = f"{prefix}:{key}"
    if suffix:
        key = f"{key}:{suffix}"
    return key


def cache(
    ttl_minutes: int | None = None,
    prefix: str = "",
    key_builder: Callable[..., str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching function results in Redis.

    Args:
        ttl_minutes: Time to live in minutes (default: CACHE_TTL_MINUTES from settings)
        prefix: Key prefix for organization
        key_builder: Custom function to build cache key from args/kwargs

    Example:
        @cache(ttl_minutes=30, prefix="users")
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """
    if ttl_minutes is None:
        ttl_minutes = settings.CACHE_TTL_MINUTES

    ttl_seconds = ttl_minutes * 60

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                # Build cache key
                if key_builder:
                    key = key_builder(*args, **kwargs)
                else:
                    # Default: use first arg as identifier
                    key = cache_key(*args, prefix=prefix)

                # Try to get from cache
                client = await get_redis_client()
                cached_value = await client.get(key)

                if cached_value is not None:
                    try:
                        result = json.loads(cached_value)
                        logger.debug(f"Cache hit for key: {key}")
                        return result
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Failed to decode cached value for key: {key}")

                # Cache miss — call function
                result = await func(*args, **kwargs)

                # Store in Redis
                try:
                    cached_data = json.dumps(result, default=str)
                    await client.setex(key, ttl_seconds, cached_data)
                    logger.debug(f"Cached result for key: {key} (TTL: {ttl_seconds}s)")
                except (TypeError, ValueError) as e:
                    logger.warning(f"Failed to cache result for key {key}: {e}")

                return result

            except Exception as e:
                logger.error(f"Cache operation failed: {e}")
                # Fall through to direct function call on error
                return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def cache_invalidate(prefix: str = "", pattern: str = "") -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for invalidating cache after function execution.

    Args:
        prefix: Prefix to match for invalidation
        pattern: Redis pattern to match for invalidation

    Example:
        @cache_invalidate(prefix="users")
        async def update_user(user_id: int, ...):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Call the function first
            result = await func(*args, **kwargs)

            # Invalidate cache
            try:
                invalidate_pattern = pattern or f"{prefix}:*"
                deleted_count = await redis_delete_pattern(invalidate_pattern)
                if deleted_count > 0:
                    logger.debug(f"Invalidated {deleted_count} cache entries matching pattern: {invalidate_pattern}")
            except Exception as e:
                logger.error(f"Cache invalidation failed: {e}")

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


async def get_cached(key: str) -> Any:
    """Get a value from cache."""
    try:
        client = await get_redis_client()
        cached_value = await client.get(key)
        if cached_value is not None:
            return json.loads(cached_value)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached value for key {key}: {e}")
        return None


async def set_cached(key: str, value: Any, ttl_minutes: int | None = None) -> bool:
    """Set a value in cache."""
    try:
        ttl = ttl_minutes or settings.CACHE_TTL_MINUTES
        ttl_seconds = ttl * 60
        client = await get_redis_client()
        cached_data = json.dumps(value, default=str)
        await client.setex(key, ttl_seconds, cached_data)
        logger.debug(f"Cached value for key: {key}")
        return True
    except Exception as e:
        logger.error(f"Failed to set cached value for key {key}: {e}")
        return False


async def invalidate_cache(prefix: str = "", pattern: str = "") -> int:
    """Manually invalidate cache entries."""
    try:
        invalidate_pattern = pattern or f"{prefix}:*"
        deleted_count = await redis_delete_pattern(invalidate_pattern)
        logger.debug(f"Invalidated {deleted_count} cache entries matching pattern: {invalidate_pattern}")
        return deleted_count
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        return 0
