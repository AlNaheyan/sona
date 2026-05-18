"""Pairwise comparison endpoints - compare two albums (A vs B), strong Elo signal."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.core.rate_limit import limiter, RateLimits
from backend.app.models.album import Album
from backend.app.models.rating import PairwiseComparison, UserAlbumElo
from backend.app.models.user import User
from backend.app.schemas.rating import (
    ComparisonCreate,
    ComparisonOut,
    ComparisonListResponse,
    ComparisonSuggestionOut,
    ComparisonSuggestionsResponse,
    ComparisonStatsResponse,
    SuggestedAlbum,
)

# Reuse the get_or_create_album helper from ratings
from backend.app.api.v1.endpoints.ratings import get_or_create_album
from backend.app.services.elo import update_elo_from_comparison
from backend.app.services.comparison_suggestions import (
    get_comparison_suggestions,
    get_comparison_stats,
)

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


def _winner_to_db(winner: str) -> bool | None:
    """Convert winner string to database boolean."""
    if winner == "a":
        return True
    elif winner == "b":
        return False
    return None  # tie


def _db_to_winner(winner_is_a: bool | None) -> str:
    """Convert database boolean to winner string."""
    if winner_is_a is True:
        return "a"
    elif winner_is_a is False:
        return "b"
    return "tie"


@router.post(
    "",
    response_model=ComparisonOut,
    responses={
        400: {
            "description": "Invalid comparison",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot compare an album to itself"}
                }
            },
        },
        401: {"description": "Not authenticated"},
        404: {"description": "One or both albums not found in MusicBrainz"},
        429: {"description": "Rate limit exceeded (60/minute)"},
    },
)
@limiter.limit(RateLimits.COMPARISON)
async def create_comparison(
    request: Request,
    comparison: ComparisonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComparisonOut:
    """
    Create a pairwise comparison between two albums.

    This is a **strong Elo signal (K=32)** - the most impactful way to
    refine your rankings. Declare which album you prefer (or a tie).

    **Elo updates**:
    - Winner gains points, loser loses points
    - Point exchange depends on expected outcome (upset = bigger swing)
    - Ties result in small adjustments toward each other

    **Behavior**:
    - Albums are fetched from MusicBrainz if not in local database
    - You can compare the same pair multiple times (each affects Elo)

    **Rate limit**: 60 requests per minute
    """
    # Validate that albums are different
    if comparison.mbid_a == comparison.mbid_b:
        raise HTTPException(status_code=400, detail="Cannot compare an album to itself")

    # Get or create both albums
    album_a = await get_or_create_album(db, comparison.mbid_a)
    album_b = await get_or_create_album(db, comparison.mbid_b)

    # Create the comparison
    db_comparison = PairwiseComparison(
        user_id=current_user.id,
        album_a_id=album_a.id,
        album_b_id=album_b.id,
        winner_is_a=_winner_to_db(comparison.winner),
    )
    db.add(db_comparison)
    await db.flush()
    await db.refresh(db_comparison)

    # Update Elo scores for both albums (strong signal)
    await update_elo_from_comparison(
        db,
        current_user.id,
        album_a.id,
        album_b.id,
        db_comparison.winner_is_a,
    )

    # Get artist names for response
    artist_a_name = album_a.artists[0].name if album_a.artists else None
    artist_b_name = album_b.artists[0].name if album_b.artists else None

    return ComparisonOut(
        id=db_comparison.id,
        album_a_id=album_a.id,
        album_a_title=album_a.title,
        album_a_artist=artist_a_name,
        album_a_cover_url=album_a.cover_url,
        album_b_id=album_b.id,
        album_b_title=album_b.title,
        album_b_artist=artist_b_name,
        album_b_cover_url=album_b.cover_url,
        winner=comparison.winner,
        created_at=db_comparison.created_at.isoformat(),
        updated_at=db_comparison.updated_at.isoformat(),
    )


@router.get("", response_model=ComparisonListResponse)
async def get_my_comparisons(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ComparisonListResponse:
    """
    Get all your pairwise comparisons.

    Requires authentication.
    """
    result = await db.execute(
        select(PairwiseComparison)
        .where(PairwiseComparison.user_id == current_user.id)
        .order_by(PairwiseComparison.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    comparisons = result.scalars().all()

    comparison_list = []
    for c in comparisons:
        # Fetch album details (eagerly load artists)
        album_a_result = await db.execute(
            select(Album)
            .where(Album.id == c.album_a_id)
            .options(selectinload(Album.artists))
        )
        album_a = album_a_result.scalar_one_or_none()
        album_b_result = await db.execute(
            select(Album)
            .where(Album.id == c.album_b_id)
            .options(selectinload(Album.artists))
        )
        album_b = album_b_result.scalar_one_or_none()

        if not album_a or not album_b:
            continue

        artist_a_name = album_a.artists[0].name if album_a.artists else None
        artist_b_name = album_b.artists[0].name if album_b.artists else None

        comparison_list.append(
            ComparisonOut(
                id=c.id,
                album_a_id=c.album_a_id,
                album_a_title=album_a.title,
                album_a_artist=artist_a_name,
                album_a_cover_url=album_a.cover_url,
                album_b_id=c.album_b_id,
                album_b_title=album_b.title,
                album_b_artist=artist_b_name,
                album_b_cover_url=album_b.cover_url,
                winner=_db_to_winner(c.winner_is_a),
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
        )

    return ComparisonListResponse(comparisons=comparison_list, count=len(comparison_list))


@router.delete("/{comparison_id}")
async def delete_comparison(
    comparison_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Delete a comparison.

    Note: Deleting a comparison does not reverse the Elo changes.
    The comparison count will be decremented for both albums.

    Requires authentication. You can only delete your own comparisons.
    """
    result = await db.execute(
        select(PairwiseComparison).where(
            PairwiseComparison.id == comparison_id,
            PairwiseComparison.user_id == current_user.id,
        )
    )
    comparison = result.scalar_one_or_none()

    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    album_a_id = comparison.album_a_id
    album_b_id = comparison.album_b_id
    await db.delete(comparison)

    # Decrement comparison counts (we don't reverse Elo changes)
    for album_id in [album_a_id, album_b_id]:
        elo_result = await db.execute(
            select(UserAlbumElo).where(
                UserAlbumElo.user_id == current_user.id,
                UserAlbumElo.album_id == album_id,
            )
        )
        elo_record = elo_result.scalar_one_or_none()
        if elo_record and elo_record.comparison_count > 0:
            elo_record.comparison_count -= 1

    await db.flush()
    return {"status": "deleted"}


@router.get(
    "/suggestions",
    response_model=ComparisonSuggestionsResponse,
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(5, ge=1, le=10, description="Number of suggestions"),
) -> ComparisonSuggestionsResponse:
    """
    Get smart suggestions for which albums to compare next.

    The algorithm prioritizes pairs that will most improve your ranking accuracy:

    | Priority | Reason | Weight |
    |----------|--------|--------|
    | 1 | Close Elo scores (need refinement) | 3.0x |
    | 2 | Low comparison counts (uncertain) | 2.0x |
    | 3 | Never compared before | 1.5x |
    | 4 | Exploration (different genres) | 0.5x |

    Returns empty list if you have fewer than 3 ranked albums.
    """
    from backend.app.services.comparison_suggestions import SuggestionConfig

    config = SuggestionConfig(max_suggestions=limit)
    suggestions = await get_comparison_suggestions(db, current_user.id, config)

    # Get Elo data for response
    elo_result = await db.execute(
        select(UserAlbumElo).where(UserAlbumElo.user_id == current_user.id)
    )
    elo_by_album = {e.album_id: e for e in elo_result.scalars().all()}

    suggestion_list = []
    for s in suggestions:
        elo_a = elo_by_album.get(s.album_a.id)
        elo_b = elo_by_album.get(s.album_b.id)

        artist_a = s.album_a.artists[0].name if s.album_a.artists else None
        artist_b = s.album_b.artists[0].name if s.album_b.artists else None

        suggestion_list.append(
            ComparisonSuggestionOut(
                album_a=SuggestedAlbum(
                    id=s.album_a.id,
                    mbid=s.album_a.mbid,
                    title=s.album_a.title,
                    artist_name=artist_a,
                    cover_url=s.album_a.cover_url,
                    elo=round(elo_a.elo, 1) if elo_a else 1500.0,
                    comparison_count=elo_a.comparison_count if elo_a else 0,
                ),
                album_b=SuggestedAlbum(
                    id=s.album_b.id,
                    mbid=s.album_b.mbid,
                    title=s.album_b.title,
                    artist_name=artist_b,
                    cover_url=s.album_b.cover_url,
                    elo=round(elo_b.elo, 1) if elo_b else 1500.0,
                    comparison_count=elo_b.comparison_count if elo_b else 0,
                ),
                reason=s.reason,
                priority_score=round(s.priority_score, 2),
            )
        )

    return ComparisonSuggestionsResponse(
        suggestions=suggestion_list,
        count=len(suggestion_list),
    )


@router.get(
    "/stats",
    response_model=ComparisonStatsResponse,
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_my_comparison_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComparisonStatsResponse:
    """
    Get statistics about your comparison coverage.

    Shows progress toward complete ranking refinement:
    - **ranked_albums**: Total albums in your rankings
    - **possible_pairs**: n*(n-1)/2 possible comparisons
    - **unique_pairs_compared**: How many pairs you've actually compared
    - **coverage_percentage**: Your comparison completeness

    Higher coverage = more accurate rankings, but diminishing returns after ~30%.
    """
    stats = await get_comparison_stats(db, current_user.id)
    return ComparisonStatsResponse(**stats)
