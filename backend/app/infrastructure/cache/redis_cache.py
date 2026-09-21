"""Async Redis cache wrapper with graceful degradation if Redis is unavailable."""
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._ttl = settings.cache_ttl_seconds
        try:
            self._redis: Optional[aioredis.Redis] = aioredis.from_url(
                settings.redis_url, decode_responses=True
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("cache_init_failed", error=str(exc))
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            return None
        try:
            raw = await self._redis.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:  # pragma: no cover
            logger.warning("cache_get_failed", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self._redis:
            return
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl or self._ttl)
        except Exception as exc:  # pragma: no cover
            logger.warning("cache_set_failed", key=key, error=str(exc))

    async def delete(self, key: str) -> None:
        if not self._redis:
            return
        try:
            await self._redis.delete(key)
        except Exception as exc:  # pragma: no cover
            logger.warning("cache_delete_failed", key=key, error=str(exc))


_cache_client: Optional[CacheClient] = None


def get_cache() -> CacheClient:
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client
