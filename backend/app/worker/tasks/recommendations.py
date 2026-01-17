"""Background tasks for recommendation pre-computation."""

import asyncio
import logging
from datetime import datetime, timezone

import redis

from backend.app.core.config import settings
from backend.app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_redis_client() -> redis.Redis:
    """Get Redis client for caching recommendations."""
    return redis.from_url(settings.redis_url)


@celery_app.task(bind=True, max_retries=3)
def precompute_user_recommendations(self, user_id: str, limit: int = 50) -> dict:
    """
    Celery task: Pre-compute and cache recommendations for a user.

    This can be triggered after significant user activity to ensure
    fresh recommendations are ready when they next visit.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from backend.app.services.recommendations import get_hybrid_recommendations

    async def _precompute():
        engine = create_async_engine(settings.database_url, echo=False)
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as session:
            result = await get_hybrid_recommendations(
                session, user_id=user_id, limit=limit, include_reasons=True
            )

            # Cache the result
            cache_key = f"recommendations:{user_id}"
            cache_data = {
                "count": len(result.recommendations),
                "recommendation_type": result.recommendation_type,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }

            redis_client = get_redis_client()
            redis_client.hset(cache_key, mapping=cache_data)
            redis_client.expire(cache_key, 3600)  # Cache for 1 hour

            return {
                "user_id": user_id,
                "recommendations_count": len(result.recommendations),
                "recommendation_type": result.recommendation_type,
                "cached": True,
            }

    try:
        result = asyncio.run(_precompute())
        logger.info(f"Recommendations precomputed: {result}")
        return result
    except Exception as exc:
        logger.error(f"Recommendation precomputation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def warm_similar_users_cache(self, user_id: str) -> dict:
    """
    Celery task: Pre-compute similar users for collaborative filtering.

    This expensive operation can be done in the background to speed up
    recommendation generation.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from backend.app.models.rating import UserAlbumElo
    from backend.app.services.recommendations import CollaborativeScorer

    async def _warm_cache():
        engine = create_async_engine(settings.database_url, echo=False)
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as session:
            # Get user's albums
            result = await session.execute(
                select(UserAlbumElo.album_id).where(UserAlbumElo.user_id == user_id)
            )
            user_album_ids = set(row[0] for row in result.all())

            if len(user_album_ids) < 5:
                return {
                    "user_id": user_id,
                    "similar_users_found": 0,
                    "status": "insufficient_data",
                }

            # Find similar users
            scorer = CollaborativeScorer()
            similar_users = await scorer.find_similar_users(
                session,
                target_user_id=user_id,
                target_album_ids=user_album_ids,
                min_shared=5,
                max_users=20,
            )

            # Cache the result
            cache_key = f"similar_users:{user_id}"
            redis_client = get_redis_client()
            redis_client.set(cache_key, str(len(similar_users)), ex=3600)

            return {
                "user_id": user_id,
                "similar_users_found": len(similar_users),
                "cached": True,
            }

    try:
        result = asyncio.run(_warm_cache())
        logger.info(f"Similar users cache warmed: {result}")
        return result
    except Exception as exc:
        logger.error(f"Similar users cache warming failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True)
def cleanup_old_recommendation_caches(self) -> dict:
    """
    Celery task: Clean up stale recommendation caches.

    Should be run periodically to prevent Redis from filling up.
    """
    redis_client = get_redis_client()

    # Find and delete old recommendation caches
    pattern = "recommendations:*"
    deleted_count = 0

    for key in redis_client.scan_iter(match=pattern):
        # Check if cache is stale (older than 24 hours)
        ttl = redis_client.ttl(key)
        if ttl == -1:  # No expiry set
            redis_client.expire(key, 3600)  # Set 1 hour expiry
            deleted_count += 1

    logger.info(f"Cleaned up {deleted_count} recommendation caches")
    return {"caches_cleaned": deleted_count}
