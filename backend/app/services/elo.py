"""
Elo Rating Service

Implements Elo-based ranking updates for personal album rankings.
Elo is the canonical ranking score - albums are ranked by Elo descending.

Signal hierarchy:
- Pairwise comparisons: K=32 (strong signal)
- Numeric ratings: K=16 (weak signal, relative to user's average)
"""

import math
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.rating import (
    NumericRating,
    PairwiseComparison,
    UserAlbumElo,
    DEFAULT_ELO,
)

# K-factors for different input types
K_PAIRWISE = 32  # Strong signal
K_RATING = 16    # Weak signal


async def get_user_elo_range(
    db: AsyncSession, user_id: str
) -> tuple[float, float]:
    """Return (min_elo, max_elo) for a user. Defaults to (DEFAULT_ELO, DEFAULT_ELO)."""
    result = await db.execute(
        select(
            func.min(UserAlbumElo.elo),
            func.max(UserAlbumElo.elo),
        ).where(UserAlbumElo.user_id == user_id)
    )
    row = result.one()
    min_elo = row[0] if row[0] is not None else DEFAULT_ELO
    max_elo = row[1] if row[1] is not None else DEFAULT_ELO
    return min_elo, max_elo


def normalize_elo(raw_elo: float, min_elo: float, max_elo: float) -> float:
    """
    Normalize a raw Elo score to a 0-100 display scale.

    Uses min-max normalization across the user's personal Elo range.
    Returns a value rounded to the nearest integer.
    If all albums share the same Elo, returns 50.
    """
    if max_elo == min_elo:
        return 50.0
    normalized = ((raw_elo - min_elo) / (max_elo - min_elo)) * 100
    return round(normalized, 1)


def expected_score(elo_a: float, elo_b: float) -> float:
    """
    Calculate expected score for player A against player B.
    Returns value between 0 and 1.
    """
    return 1 / (1 + math.pow(10, (elo_b - elo_a) / 400))


async def get_or_create_elo(
    db: AsyncSession,
    user_id: str,
    album_id: str,
) -> UserAlbumElo:
    """Get existing Elo record or create a new one with default rating."""
    result = await db.execute(
        select(UserAlbumElo).where(
            UserAlbumElo.user_id == user_id,
            UserAlbumElo.album_id == album_id,
        )
    )
    elo_record = result.scalar_one_or_none()

    if not elo_record:
        elo_record = UserAlbumElo(
            user_id=user_id,
            album_id=album_id,
            elo=DEFAULT_ELO,
            rating_count=0,
            comparison_count=0,
        )
        db.add(elo_record)
        await db.flush()

    return elo_record


async def get_user_average_rating(db: AsyncSession, user_id: str) -> float:
    """Get the user's average numeric rating, or 5.5 if no ratings exist."""
    result = await db.execute(
        select(func.avg(NumericRating.value)).where(
            NumericRating.user_id == user_id
        )
    )
    avg = result.scalar()
    return avg if avg is not None else 5.5


async def update_elo_from_rating(
    db: AsyncSession,
    user_id: str,
    album_id: str,
    rating_value: float,
) -> UserAlbumElo:
    """
    Update Elo based on a numeric rating.

    Ratings are interpreted relative to the user's average:
    - Rating above average → Elo increases
    - Rating below average → Elo decreases

    This is a weak signal (K=16).
    """
    elo_record = await get_or_create_elo(db, user_id, album_id)
    user_avg = await get_user_average_rating(db, user_id)

    # Normalize rating to 0-1 scale relative to user's average
    # rating_value is 1-10, user_avg is typically 5-7
    # We treat it as: did this album "win" against the average?
    if rating_value > user_avg:
        # Album is above average - it "won"
        actual_score = 0.5 + (rating_value - user_avg) / 10  # 0.5 to 1.0
    else:
        # Album is below average - it "lost"
        actual_score = 0.5 - (user_avg - rating_value) / 10  # 0.0 to 0.5

    # Clamp to valid range
    actual_score = max(0.0, min(1.0, actual_score))

    # Expected score against "average album" (Elo 1500)
    expected = expected_score(elo_record.elo, DEFAULT_ELO)

    # Update Elo
    elo_record.elo += K_RATING * (actual_score - expected)
    elo_record.rating_count += 1

    await db.flush()
    return elo_record


async def update_elo_from_comparison(
    db: AsyncSession,
    user_id: str,
    album_a_id: str,
    album_b_id: str,
    winner_is_a: bool | None,
) -> tuple[UserAlbumElo, UserAlbumElo]:
    """
    Update Elo for both albums based on a pairwise comparison.

    This is a strong signal (K=32).

    Args:
        winner_is_a: True if A wins, False if B wins, None if tie
    """
    elo_a = await get_or_create_elo(db, user_id, album_a_id)
    elo_b = await get_or_create_elo(db, user_id, album_b_id)

    # Calculate expected scores
    expected_a = expected_score(elo_a.elo, elo_b.elo)
    expected_b = 1 - expected_a

    # Determine actual scores
    if winner_is_a is True:
        actual_a, actual_b = 1.0, 0.0
    elif winner_is_a is False:
        actual_a, actual_b = 0.0, 1.0
    else:  # tie
        actual_a, actual_b = 0.5, 0.5

    # Update both Elos
    elo_a.elo += K_PAIRWISE * (actual_a - expected_a)
    elo_b.elo += K_PAIRWISE * (actual_b - expected_b)

    elo_a.comparison_count += 1
    elo_b.comparison_count += 1

    await db.flush()
    return elo_a, elo_b


async def recalculate_elo_from_rating_change(
    db: AsyncSession,
    user_id: str,
    album_id: str,
    old_value: float | None,
    new_value: float | None,
) -> UserAlbumElo | None:
    """
    Recalculate Elo when a rating is updated or deleted.

    For simplicity, we adjust based on the change in rating value.
    If deleted (new_value is None), we reduce the rating count but
    don't reverse the Elo (would require storing history).
    """
    if new_value is not None:
        # Rating created or updated - apply the new rating's effect
        return await update_elo_from_rating(db, user_id, album_id, new_value)

    # Rating deleted - just decrement the count
    # (We don't reverse Elo changes for simplicity)
    result = await db.execute(
        select(UserAlbumElo).where(
            UserAlbumElo.user_id == user_id,
            UserAlbumElo.album_id == album_id,
        )
    )
    elo_record = result.scalar_one_or_none()
    if elo_record and elo_record.rating_count > 0:
        elo_record.rating_count -= 1
        await db.flush()

    return elo_record
