"""Community rankings endpoints - global Bayesian-weighted album rankings."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.schemas.album import CommunityRankedAlbum, CommunityRankingsResponse
from backend.app.services.community import (
    get_community_rankings,
    get_trending_albums,
    get_global_mean_rating,
)

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/rankings", response_model=CommunityRankingsResponse)
async def get_rankings(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    min_ratings: int = Query(1, ge=1, description="Minimum ratings required"),
) -> CommunityRankingsResponse:
    """
    Get community album rankings based on Bayesian-weighted scores.

    Albums are ranked by their Bayesian score, which accounts for:
    - The album's average rating
    - The number of ratings (more ratings = more confidence)
    - The global average (pulls albums with few ratings toward the mean)

    This prevents albums with 1-2 high ratings from dominating.
    Does not require authentication.
    """
    albums, total = await get_community_rankings(
        db,
        limit=limit,
        offset=offset,
        min_ratings=min_ratings,
    )

    rankings = []
    for i, album in enumerate(albums, start=offset + 1):
        artist_name = album.artists[0].name if album.artists else None
        avg_rating = album.rating_sum / album.rating_count if album.rating_count > 0 else 0

        rankings.append(
            CommunityRankedAlbum(
                rank=i,
                id=album.id,
                mbid=album.mbid,
                title=album.title,
                artist_name=artist_name,
                cover_url=album.cover_url,
                release_year=album.release_year,
                rating_count=album.rating_count,
                average_rating=round(avg_rating, 2),
                bayesian_score=round(album.bayesian_score, 2) if album.bayesian_score else 0,
            )
        )

    return CommunityRankingsResponse(
        rankings=rankings,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/trending")
async def get_trending(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    """
    Get trending albums (most rated recently).

    Does not require authentication.
    """
    albums = await get_trending_albums(db, limit=limit)

    trending = []
    for album in albums:
        artist_name = album.artists[0].name if album.artists else None
        avg_rating = album.rating_sum / album.rating_count if album.rating_count > 0 else 0

        trending.append({
            "id": album.id,
            "mbid": album.mbid,
            "title": album.title,
            "artist_name": artist_name,
            "cover_url": album.cover_url,
            "rating_count": album.rating_count,
            "average_rating": round(avg_rating, 2),
        })

    return {"trending": trending, "count": len(trending)}


@router.get("/stats")
async def get_community_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get community-wide statistics.

    Does not require authentication.
    """
    from sqlalchemy import select, func
    from backend.app.models.album import Album
    from backend.app.models.rating import NumericRating

    # Total ratings
    rating_count_result = await db.execute(select(func.count(NumericRating.id)))
    total_ratings = rating_count_result.scalar() or 0

    # Total rated albums
    album_count_result = await db.execute(
        select(func.count()).where(Album.rating_count > 0)
    )
    rated_albums = album_count_result.scalar() or 0

    # Global mean
    global_mean = await get_global_mean_rating(db)

    # Top rated album
    top_result = await db.execute(
        select(Album)
        .where(Album.bayesian_score.isnot(None))
        .order_by(Album.bayesian_score.desc())
        .limit(1)
    )
    top_album = top_result.scalar_one_or_none()

    top_album_info = None
    if top_album:
        artist_name = top_album.artists[0].name if top_album.artists else None
        top_album_info = {
            "title": top_album.title,
            "artist": artist_name,
            "bayesian_score": round(top_album.bayesian_score, 2) if top_album.bayesian_score else None,
        }

    return {
        "total_ratings": total_ratings,
        "rated_albums": rated_albums,
        "global_mean_rating": round(global_mean, 2),
        "top_album": top_album_info,
    }
