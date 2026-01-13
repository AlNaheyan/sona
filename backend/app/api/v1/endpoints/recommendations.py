"""Personalized recommendation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.recommendations import (
    RecommendationsResponse,
    RecommendedAlbum,
    ContentScoreBreakdown,
    SimilarAlbumsResponse,
    SimilarAlbum,
)
from backend.app.services.recommendations import (
    get_hybrid_recommendations,
    get_similar_albums,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationsResponse)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50, description="Number of recommendations"),
    include_reasons: bool = Query(
        False, description="Include explanation for each recommendation"
    ),
) -> RecommendationsResponse:
    """
    Get personalized album recommendations.

    Uses a hybrid approach combining:
    - **Content-based**: Albums similar to your top-rated albums (genre, artist, era)
    - **Collaborative**: Albums loved by users with similar taste

    Weights adapt based on your ranking history:
    - New users (<10 albums): 90% content, 10% collaborative
    - Experienced users (30+ albums): 60% content, 40% collaborative

    ~15% of recommendations are "exploration" picks outside your usual taste.

    For users with fewer than 5 ranked albums, returns community top albums.

    Requires authentication.
    """
    output = await get_hybrid_recommendations(
        db,
        user_id=current_user.id,
        limit=limit,
        include_reasons=include_reasons,
    )

    # Transform results to response schema
    recommendations = []
    for result in output.recommendations:
        album = result.album
        artist_name = album.artists[0].name if album.artists else None

        raw_scores = None
        if result.raw_scores:
            raw_scores = ContentScoreBreakdown(
                genre=round(result.raw_scores.get("genre", 0), 4),
                artist=round(result.raw_scores.get("artist", 0), 4),
                era=round(result.raw_scores.get("era", 0), 4),
            )

        recommendations.append(
            RecommendedAlbum(
                album_id=album.id,
                mbid=album.mbid,
                title=album.title,
                artist_name=artist_name,
                cover_url=album.cover_url,
                release_year=album.release_year,
                genres=album.genres,
                final_score=round(result.final_score, 4),
                content_score=round(result.content_score, 4),
                collaborative_score=round(result.collaborative_score, 4),
                raw_scores=raw_scores,
                is_exploration=result.is_exploration,
                reasons=result.reasons if include_reasons else [],
                community_rating_count=album.rating_count,
                community_bayesian_score=(
                    round(album.bayesian_score, 2) if album.bayesian_score else None
                ),
            )
        )

    return RecommendationsResponse(
        recommendations=recommendations,
        count=len(recommendations),
        user_ranked_albums=output.user_album_count,
        recommendation_type=output.recommendation_type,
        content_weight=round(output.content_weight, 2),
        collaborative_weight=round(output.collaborative_weight, 2),
        similar_users_found=output.similar_users_found,
        exploration_count=output.exploration_count,
    )


@router.get("/similar/{album_id}", response_model=SimilarAlbumsResponse)
async def get_similar_albums_endpoint(
    album_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=30, description="Number of similar albums"),
) -> SimilarAlbumsResponse:
    """
    Get albums similar to a specific album.

    Uses content-based similarity only (genre, artist, era).
    Does not require authentication.
    """
    target_album, similar = await get_similar_albums(db, album_id, limit)

    if not target_album:
        raise HTTPException(status_code=404, detail="Album not found")

    target_artist = target_album.artists[0].name if target_album.artists else None

    similar_albums = []
    for album, score in similar:
        artist_name = album.artists[0].name if album.artists else None
        similar_albums.append(
            SimilarAlbum(
                album_id=album.id,
                mbid=album.mbid,
                title=album.title,
                artist_name=artist_name,
                cover_url=album.cover_url,
                release_year=album.release_year,
                similarity_score=round(score, 4),
            )
        )

    return SimilarAlbumsResponse(
        target_album={
            "id": target_album.id,
            "title": target_album.title,
            "artist_name": target_artist,
        },
        similar_albums=similar_albums,
        count=len(similar_albums),
    )
