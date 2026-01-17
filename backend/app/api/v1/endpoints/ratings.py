"""Rating endpoints - numeric album rating (1-10), weak Elo signal."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.core.rate_limit import limiter, RateLimits
from backend.app.models.album import Album, Artist
from backend.app.models.rating import NumericRating
from backend.app.models.user import User
from backend.app.schemas.rating import RatingCreate, RatingOut, RatingListResponse
from backend.app.services.musicbrainz import musicbrainz_client
from backend.app.services.elo import update_elo_from_rating, recalculate_elo_from_rating_change
from backend.app.services.community import update_album_community_stats

router = APIRouter(prefix="/ratings", tags=["ratings"])


async def get_or_create_album(db: AsyncSession, mbid: str) -> Album:
    """Get album from DB or create it from MusicBrainz data."""
    # Check if album exists (eagerly load artists)
    result = await db.execute(
        select(Album)
        .where(Album.mbid == mbid)
        .options(selectinload(Album.artists))
    )
    album = result.scalar_one_or_none()

    if album:
        return album

    # Fetch from MusicBrainz and create
    mb_album = await musicbrainz_client.get_album_by_mbid(mbid)
    if not mb_album:
        raise HTTPException(status_code=404, detail="Album not found in MusicBrainz")

    # Create or get artist
    artist = None
    if mb_album.artist_mbid:
        result = await db.execute(select(Artist).where(Artist.mbid == mb_album.artist_mbid))
        artist = result.scalar_one_or_none()
        if not artist:
            artist = Artist(name=mb_album.artist_name, mbid=mb_album.artist_mbid)
            db.add(artist)

    # Create album
    album = Album(
        mbid=mb_album.mbid,
        title=mb_album.title,
        release_year=mb_album.release_year,
        cover_url=mb_album.cover_url,
    )
    if artist:
        album.artists.append(artist)
    db.add(album)
    await db.flush()

    return album


@router.post("", response_model=RatingOut)
@limiter.limit(RateLimits.RATING)
async def rate_album(
    request: Request,
    rating: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RatingOut:
    """
    Rate an album (1-10).

    This is a weak Elo signal (K=16). The rating is interpreted relative
    to your average rating to update the album's Elo score.

    Requires authentication.
    If the album doesn't exist in our database, it will be fetched from MusicBrainz.
    If you've already rated this album, your rating will be updated.
    """
    # Get or create album
    album = await get_or_create_album(db, rating.mbid)

    # Check for existing rating
    result = await db.execute(
        select(NumericRating).where(
            NumericRating.user_id == current_user.id,
            NumericRating.album_id == album.id,
        )
    )
    existing_rating = result.scalar_one_or_none()

    if existing_rating:
        # Update existing rating
        existing_rating.value = rating.value
        existing_rating.notes = rating.notes
        db_rating = existing_rating
    else:
        # Create new rating
        db_rating = NumericRating(
            user_id=current_user.id,
            album_id=album.id,
            value=rating.value,
            notes=rating.notes,
        )
        db.add(db_rating)

    await db.flush()
    await db.refresh(db_rating)

    # Update Elo score (weak signal for personal ranking)
    await update_elo_from_rating(db, current_user.id, album.id, rating.value)

    # Update community stats (Bayesian score)
    await update_album_community_stats(db, album.id)

    # Get artist name for response
    artist_name = None
    if album.artists:
        artist_name = album.artists[0].name

    return RatingOut(
        id=db_rating.id,
        album_id=album.id,
        album_title=album.title,
        album_artist=artist_name,
        album_cover_url=album.cover_url,
        value=db_rating.value,
        notes=db_rating.notes,
        created_at=db_rating.created_at.isoformat(),
        updated_at=db_rating.updated_at.isoformat(),
    )


@router.get("", response_model=RatingListResponse)
async def get_my_ratings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> RatingListResponse:
    """
    Get all your album ratings.

    Requires authentication.
    """
    result = await db.execute(
        select(NumericRating)
        .where(NumericRating.user_id == current_user.id)
        .order_by(NumericRating.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    ratings = result.scalars().all()

    rating_list = []
    for r in ratings:
        # Fetch album details (eagerly load artists)
        album_result = await db.execute(
            select(Album)
            .where(Album.id == r.album_id)
            .options(selectinload(Album.artists))
        )
        album = album_result.scalar_one_or_none()
        if not album:
            continue

        artist_name = None
        if album.artists:
            artist_name = album.artists[0].name

        rating_list.append(
            RatingOut(
                id=r.id,
                album_id=r.album_id,
                album_title=album.title,
                album_artist=artist_name,
                album_cover_url=album.cover_url,
                value=r.value,
                notes=r.notes,
                created_at=r.created_at.isoformat(),
                updated_at=r.updated_at.isoformat(),
            )
        )

    return RatingListResponse(ratings=rating_list, count=len(rating_list))


@router.delete("/{rating_id}")
async def delete_rating(
    rating_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Delete a rating.

    Requires authentication. You can only delete your own ratings.
    """
    result = await db.execute(
        select(NumericRating).where(
            NumericRating.id == rating_id,
            NumericRating.user_id == current_user.id,
        )
    )
    rating = result.scalar_one_or_none()

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    album_id = rating.album_id
    await db.delete(rating)

    # Update Elo record (decrement rating count)
    await recalculate_elo_from_rating_change(db, current_user.id, album_id, None, None)

    # Update community stats (Bayesian score)
    await update_album_community_stats(db, album_id)

    return {"status": "deleted"}
