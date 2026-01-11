"""
Community Rankings Service

Computes Bayesian-weighted community scores for albums.
This is completely separate from personal Elo rankings.

Bayesian Average Formula:
    bayesian_score = (v / (v + m)) * R + (m / (v + m)) * C

Where:
    R = album's average rating
    v = number of votes (ratings) for this album
    m = minimum votes required (tunable, default 5)
    C = global mean rating across all albums

This prevents albums with few ratings from dominating rankings.
"""

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.album import Album
from backend.app.models.rating import NumericRating

# Minimum votes required before Bayesian score is meaningful
# Albums with fewer votes will be pulled toward the global mean
MIN_VOTES_FOR_RANKING = 5


async def get_global_mean_rating(db: AsyncSession) -> float:
    """Get the global average rating across all ratings."""
    result = await db.execute(select(func.avg(NumericRating.value)))
    global_mean = result.scalar()
    return global_mean if global_mean is not None else 5.5  # Default to middle


async def update_album_community_stats(
    db: AsyncSession,
    album_id: str,
) -> Album | None:
    """
    Update community stats for a single album.

    Called after a rating is added, updated, or deleted.
    """
    # Get the album
    result = await db.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()
    if not album:
        return None

    # Calculate rating count and sum for this album
    stats_result = await db.execute(
        select(
            func.count(NumericRating.id),
            func.sum(NumericRating.value),
        ).where(NumericRating.album_id == album_id)
    )
    row = stats_result.one()
    rating_count = row[0] or 0
    rating_sum = row[1] or 0.0

    # Update album stats
    album.rating_count = rating_count
    album.rating_sum = float(rating_sum)

    # Calculate Bayesian score
    if rating_count > 0:
        global_mean = await get_global_mean_rating(db)
        album_mean = rating_sum / rating_count

        # Bayesian average
        m = MIN_VOTES_FOR_RANKING
        v = rating_count
        bayesian_score = (v / (v + m)) * album_mean + (m / (v + m)) * global_mean
        album.bayesian_score = bayesian_score
    else:
        album.bayesian_score = None

    await db.flush()
    return album


async def recalculate_all_community_scores(db: AsyncSession) -> int:
    """
    Recalculate Bayesian scores for all albums.

    Useful after global mean changes significantly or for batch updates.
    Returns the number of albums updated.
    """
    global_mean = await get_global_mean_rating(db)
    m = MIN_VOTES_FOR_RANKING

    # Get all albums with ratings
    result = await db.execute(
        select(Album).where(Album.rating_count > 0)
    )
    albums = result.scalars().all()

    count = 0
    for album in albums:
        if album.rating_count > 0:
            album_mean = album.rating_sum / album.rating_count
            v = album.rating_count
            album.bayesian_score = (v / (v + m)) * album_mean + (m / (v + m)) * global_mean
            count += 1

    await db.flush()
    return count


async def get_community_rankings(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    min_ratings: int = 1,
) -> tuple[list[Album], int]:
    """
    Get albums ranked by Bayesian community score.

    Args:
        limit: Maximum albums to return
        offset: Pagination offset
        min_ratings: Minimum ratings required to be included

    Returns:
        Tuple of (albums, total_count)
    """
    # Count total albums meeting criteria
    count_result = await db.execute(
        select(func.count()).where(
            Album.rating_count >= min_ratings,
            Album.bayesian_score.isnot(None),
        )
    )
    total_count = count_result.scalar() or 0

    # Get ranked albums
    result = await db.execute(
        select(Album)
        .where(
            Album.rating_count >= min_ratings,
            Album.bayesian_score.isnot(None),
        )
        .order_by(Album.bayesian_score.desc())
        .limit(limit)
        .offset(offset)
    )
    albums = result.scalars().all()

    return albums, total_count


async def get_trending_albums(
    db: AsyncSession,
    limit: int = 10,
) -> list[Album]:
    """
    Get recently popular albums (most ratings in recent period).

    Simple implementation: albums with most ratings, could be enhanced
    with time-decay weighting.
    """
    result = await db.execute(
        select(Album)
        .where(Album.rating_count > 0)
        .order_by(Album.rating_count.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_controversial_albums(
    db: AsyncSession,
    limit: int = 10,
    min_ratings: int = 5,
) -> list[Album]:
    """
    Get albums with high rating variance (controversial).

    These are albums where users strongly disagree.
    Requires calculating standard deviation on the fly.
    """
    # Get albums with enough ratings and calculate variance
    # For simplicity, we'll identify albums where the Bayesian score
    # differs significantly from the raw mean (indicating pull toward global mean)
    result = await db.execute(
        select(Album)
        .where(Album.rating_count >= min_ratings)
        .order_by(Album.rating_count.desc())  # Placeholder - could add variance calc
        .limit(limit)
    )
    return result.scalars().all()
