"""Redis caching service for external API responses."""

import json
import logging
from typing import Any

import redis.asyncio as redis

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis cache for API responses."""

    def __init__(self, redis_url: str = None) -> None:
        self._redis_url = redis_url or settings.redis_url
        self._client: redis.Redis | None = None

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client (lazy initialization)."""
        if self._client is None:
            self._client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Returns:
            Cached value (deserialized from JSON) or None if not found/expired.
        """
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
        except redis.RedisError as e:
            logger.warning(f"Redis GET error for key '{key}': {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for key '{key}': {e}")
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time-to-live in seconds (default 1 hour)

        Returns:
            True if successful, False otherwise.
        """
        try:
            client = await self._get_client()
            serialized = json.dumps(value)
            await client.set(key, serialized, ex=ttl_seconds)
            return True
        except redis.RedisError as e:
            logger.warning(f"Redis SET error for key '{key}': {e}")
        except (TypeError, ValueError) as e:
            logger.warning(f"JSON serialize error for key '{key}': {e}")
        return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except redis.RedisError as e:
            logger.warning(f"Redis DELETE error for key '{key}': {e}")
        return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "mb:search:*")

        Returns:
            Number of keys deleted.
        """
        try:
            client = await self._get_client()
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await client.delete(*keys)
            return len(keys)
        except redis.RedisError as e:
            logger.warning(f"Redis DELETE pattern error for '{pattern}': {e}")
        return 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Cache key prefixes
class CacheKeys:
    """Cache key builders for consistent naming."""

    @staticmethod
    def musicbrainz_search(query: str, limit: int) -> str:
        """Key for MusicBrainz search results."""
        # Normalize query for consistent caching
        normalized = query.lower().strip()
        return f"mb:search:{normalized}:{limit}"

    @staticmethod
    def musicbrainz_album(mbid: str) -> str:
        """Key for MusicBrainz album lookup."""
        return f"mb:album:{mbid}"

    @staticmethod
    def cover_art(mbid: str) -> str:
        """Key for cover art URL."""
        return f"cover:{mbid}"


# Cache TTL values (in seconds)
class CacheTTL:
    """TTL constants for different cache types."""

    SEARCH_RESULTS = 3600  # 1 hour - search results can change
    ALBUM_METADATA = 86400  # 24 hours - album metadata is stable
    COVER_ART = 604800  # 7 days - cover art URLs rarely change


# Singleton instance
cache_service = CacheService()
