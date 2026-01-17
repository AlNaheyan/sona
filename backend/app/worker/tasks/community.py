"""Background tasks for community score calculations."""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.app.core.config import settings
from backend.app.models.album import Album
from backend.app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Create async session maker for background tasks."""
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _update_album_bayesian_score(
    session: AsyncSession, album_id: str, global_mean: float, min_ratings: int
) -> None:
    """
    Update Bayesian score for a single album.

    Bayesian average: (C * m + sum_of_ratings) / (C + n)
    where C = minimum ratings threshold, m = global mean,
    n = number of ratings for this album.
    """
    result = await session.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()

    if not album:
        return

    if album.rating_count == 0:
        album.bayesian_score = None
        return

    # Calculate Bayesian average
    n = album.rating_count
    avg = album.rating_sum / n if n > 0 else 0
    bayesian = (min_ratings * global_mean + album.rating_sum) / (min_ratings + n)

    album.bayesian_score = bayesian
    album.community_mean = avg


async def _recalculate_all_scores() -> dict:
    """Recalculate Bayesian scores for all albums."""
    session_maker = get_async_session_maker()
    min_ratings = 5  # Minimum ratings for confidence

    async with session_maker() as session:
        # Get all albums with ratings
        result = await session.execute(
            select(Album).where(Album.rating_count > 0)
        )
        albums = result.scalars().all()

        if not albums:
            return {"albums_updated": 0, "global_mean": 0}

        # Calculate global mean
        total_sum = sum(a.rating_sum for a in albums)
        total_count = sum(a.rating_count for a in albums)
        global_mean = total_sum / total_count if total_count > 0 else 5.0

        # Update each album
        for album in albums:
            await _update_album_bayesian_score(
                session, album.id, global_mean, min_ratings
            )

        await session.commit()

        return {
            "albums_updated": len(albums),
            "global_mean": round(global_mean, 2),
        }


@celery_app.task(bind=True, max_retries=3)
def recalculate_all_community_scores(self) -> dict:
    """
    Celery task: Recalculate Bayesian scores for all albums.

    This task should be run periodically (e.g., daily) to ensure
    community rankings remain accurate as new ratings come in.
    """
    logger.info("Starting community score recalculation")

    try:
        result = asyncio.run(_recalculate_all_scores())
        logger.info(f"Community scores updated: {result}")
        return result
    except Exception as exc:
        logger.error(f"Community score recalculation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def update_single_album_score(self, album_id: str) -> dict:
    """
    Celery task: Update Bayesian score for a single album.

    Called after a new rating is submitted. This is more efficient
    than recalculating all scores.
    """
    async def _update_single():
        session_maker = get_async_session_maker()
        min_ratings = 5

        async with session_maker() as session:
            # Get global stats
            result = await session.execute(
                select(Album).where(Album.rating_count > 0)
            )
            albums = result.scalars().all()

            if not albums:
                return {"album_id": album_id, "updated": False}

            total_sum = sum(a.rating_sum for a in albums)
            total_count = sum(a.rating_count for a in albums)
            global_mean = total_sum / total_count if total_count > 0 else 5.0

            # Update the specific album
            await _update_album_bayesian_score(
                session, album_id, global_mean, min_ratings
            )
            await session.commit()

            return {
                "album_id": album_id,
                "updated": True,
                "global_mean": round(global_mean, 2),
            }

    try:
        result = asyncio.run(_update_single())
        logger.info(f"Album score updated: {result}")
        return result
    except Exception as exc:
        logger.error(f"Album score update failed: {exc}")
        raise self.retry(exc=exc, countdown=30)
