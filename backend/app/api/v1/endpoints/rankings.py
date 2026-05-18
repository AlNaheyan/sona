"""Personal rankings endpoints - Elo-based album rankings."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.album import Album
from backend.app.models.rating import UserAlbumElo, NumericRating, PairwiseComparison
from backend.app.models.user import User
from backend.app.schemas.rating import RankedAlbumOut, PersonalRankingsResponse
from backend.app.services.elo import get_user_elo_range, normalize_elo

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("", response_model=PersonalRankingsResponse)
async def get_my_rankings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PersonalRankingsResponse:
    """
    Get your personal album rankings based on Elo scores.

    Albums are ranked by their Elo score in descending order.
    Higher Elo = better ranked.

    Requires authentication.
    """
    # Get user's Elo range for normalization
    min_elo, max_elo = await get_user_elo_range(db, current_user.id)

    # Get paginated Elo records, ordered by Elo descending
    result = await db.execute(
        select(UserAlbumElo)
        .where(UserAlbumElo.user_id == current_user.id)
        .order_by(UserAlbumElo.elo.desc())
        .limit(limit)
        .offset(offset)
    )
    elo_records = result.scalars().all()

    # Bulk fetch all albums in one query instead of N+1
    album_ids = [elo.album_id for elo in elo_records]
    albums_result = await db.execute(
        select(Album)
        .where(Album.id.in_(album_ids))
        .options(selectinload(Album.artists))
    )
    album_by_id = {a.id: a for a in albums_result.scalars().all()}

    rankings = []
    for i, elo in enumerate(elo_records, start=offset + 1):
        album = album_by_id.get(elo.album_id)
        if not album:
            continue

        artist_name = album.artists[0].name if album.artists else None

        rankings.append(
            RankedAlbumOut(
                rank=i,
                album_id=elo.album_id,
                album_mbid=album.mbid,
                album_title=album.title,
                album_artist=artist_name,
                album_cover_url=album.cover_url,
                elo=round(elo.elo, 1),
                elo_normalized=normalize_elo(elo.elo, min_elo, max_elo),
                rating_count=elo.rating_count,
                comparison_count=elo.comparison_count,
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

    Returns counts of ranked albums, ratings, and comparisons.
    """
    # Count ranked albums (Elo records)
    elo_result = await db.execute(
        select(func.count()).where(UserAlbumElo.user_id == current_user.id)
    )
    album_count = elo_result.scalar() or 0

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

    # Get average Elo
    avg_elo_result = await db.execute(
        select(func.avg(UserAlbumElo.elo)).where(
            UserAlbumElo.user_id == current_user.id
        )
    )
    avg_elo = avg_elo_result.scalar() or 1500.0

    # Get Elo range
    min_elo_result = await db.execute(
        select(func.min(UserAlbumElo.elo)).where(
            UserAlbumElo.user_id == current_user.id
        )
    )
    max_elo_result = await db.execute(
        select(func.max(UserAlbumElo.elo)).where(
            UserAlbumElo.user_id == current_user.id
        )
    )
    min_elo = min_elo_result.scalar() or 1500.0
    max_elo = max_elo_result.scalar() or 1500.0

    return {
        "ranked_albums": album_count,
        "numeric_ratings": rating_count,
        "pairwise_comparisons": comparison_count,
        "average_elo": round(avg_elo, 1),
        "elo_range": {
            "min": round(min_elo, 1),
            "max": round(max_elo, 1),
        },
    }
