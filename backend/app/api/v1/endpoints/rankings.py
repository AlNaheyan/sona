"""Personal rankings endpoints - CWPR-based album rankings."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.album import Album
from backend.app.models.rating import UserAlbumPreference
from backend.app.models.user import User
from backend.app.schemas.rating import RankedAlbumOut, PersonalRankingsResponse

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("", response_model=PersonalRankingsResponse)
async def get_my_rankings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PersonalRankingsResponse:
    """
    Get your personal album rankings based on CWPR scores.

    Albums are ranked by their score (μ - λσ), which balances
    preference strength with confidence.

    Requires authentication.
    """
    # Get all user preferences, ordered by score descending
    result = await db.execute(
        select(UserAlbumPreference)
        .where(UserAlbumPreference.user_id == current_user.id)
        .order_by(UserAlbumPreference.score.desc())
        .limit(limit)
        .offset(offset)
    )
    preferences = result.scalars().all()

    rankings = []
    for i, pref in enumerate(preferences, start=offset + 1):
        # Fetch album details
        album_result = await db.execute(select(Album).where(Album.id == pref.album_id))
        album = album_result.scalar_one_or_none()
        if not album:
            continue

        artist_name = album.artists[0].name if album.artists else None

        rankings.append(
            RankedAlbumOut(
                rank=i,
                album_id=pref.album_id,
                album_title=album.title,
                album_artist=artist_name,
                album_cover_url=album.cover_url,
                mu=round(pref.mu, 3),
                sigma=round(pref.sigma, 3),
                score=round(pref.score, 3),
                numeric_count=pref.numeric_count,
                pairwise_count=pref.pairwise_count,
                tier_count=pref.tier_count,
            )
        )

    return PersonalRankingsResponse(rankings=rankings, count=len(rankings))


@router.get("/stats")
async def get_ranking_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get statistics about your rankings.

    Returns counts of albums, ratings, comparisons, and tier placements.
    """
    from sqlalchemy import func
    from backend.app.models.rating import NumericRating, PairwiseComparison, TierPlacement

    # Count preferences
    pref_result = await db.execute(
        select(func.count()).where(UserAlbumPreference.user_id == current_user.id)
    )
    album_count = pref_result.scalar() or 0

    # Count numeric ratings
    rating_result = await db.execute(
        select(func.count()).where(NumericRating.user_id == current_user.id)
    )
    rating_count = rating_result.scalar() or 0

    # Count comparisons
    comparison_result = await db.execute(
        select(func.count()).where(PairwiseComparison.user_id == current_user.id)
    )
    comparison_count = comparison_result.scalar() or 0

    # Count tier placements
    tier_result = await db.execute(
        select(func.count()).where(TierPlacement.user_id == current_user.id)
    )
    tier_count = tier_result.scalar() or 0

    # Get average confidence (inverse of sigma)
    avg_sigma_result = await db.execute(
        select(func.avg(UserAlbumPreference.sigma)).where(
            UserAlbumPreference.user_id == current_user.id
        )
    )
    avg_sigma = avg_sigma_result.scalar() or 2.5

    return {
        "ranked_albums": album_count,
        "numeric_ratings": rating_count,
        "pairwise_comparisons": comparison_count,
        "tier_placements": tier_count,
        "average_uncertainty": round(avg_sigma, 3),
    }
