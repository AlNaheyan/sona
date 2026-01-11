"""Pairwise comparison endpoints - compare two albums (A vs B), strong Elo signal."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.album import Album
from backend.app.models.rating import PairwiseComparison, UserAlbumElo
from backend.app.models.user import User
from backend.app.schemas.rating import ComparisonCreate, ComparisonOut, ComparisonListResponse

# Reuse the get_or_create_album helper from ratings
from backend.app.api.v1.endpoints.ratings import get_or_create_album
from backend.app.services.elo import update_elo_from_comparison

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


@router.post("", response_model=ComparisonOut)
async def create_comparison(
    comparison: ComparisonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComparisonOut:
    """
    Create a pairwise comparison between two albums.

    This is a strong Elo signal (K=32). Both albums' Elo scores
    will be updated based on the comparison result.

    Requires authentication.
    If albums don't exist in our database, they will be fetched from MusicBrainz.
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
        # Fetch album details
        album_a_result = await db.execute(select(Album).where(Album.id == c.album_a_id))
        album_a = album_a_result.scalar_one_or_none()
        album_b_result = await db.execute(select(Album).where(Album.id == c.album_b_id))
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
