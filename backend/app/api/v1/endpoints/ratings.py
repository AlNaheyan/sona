"""Rating endpoints - numeric album rating (1-10), weak Elo signal."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.core.rate_limit import limiter, RateLimits
from backend.app.models.album import Album, Artist
from backend.app.models.rating import NumericRating, UserAlbumElo, PairwiseComparison
from backend.app.models.user import User
from backend.app.schemas.rating import RatingCreate, RatingOut, RatingListResponse, NearbyAlbum
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
        genres=",".join(mb_album.genres) if mb_album.genres else None,
    )
    if artist:
        album.artists.append(artist)
    db.add(album)
    await db.flush()

    return album


async def _get_nearby_albums(
    db: AsyncSession, user_id: str, album_id: str
) -> list[NearbyAlbum]:
    """Return up to 3 albums closest in Elo to the just-rated album, excluding already-compared pairs."""
    # Get the current album's Elo
    result = await db.execute(
        select(UserAlbumElo).where(
            UserAlbumElo.user_id == user_id,
            UserAlbumElo.album_id == album_id,
        )
    )
    current_elo_record = result.scalar_one_or_none()
    if not current_elo_record:
        return []

    # Check total ranked albums — skip if < 3
    count_result = await db.execute(
        select(func.count()).select_from(UserAlbumElo).where(
            UserAlbumElo.user_id == user_id,
        )
    )
    total_ranked = count_result.scalar() or 0
    if total_ranked < 3:
        return []

    current_elo = current_elo_record.elo

    # Get albums already compared against this one (in either direction)
    compared_result = await db.execute(
        select(PairwiseComparison.album_a_id, PairwiseComparison.album_b_id).where(
            PairwiseComparison.user_id == user_id,
            or_(
                PairwiseComparison.album_a_id == album_id,
                PairwiseComparison.album_b_id == album_id,
            ),
        )
    )
    compared_pairs = compared_result.all()
    already_compared_ids = set()
    for row in compared_pairs:
        if row.album_a_id == album_id:
            already_compared_ids.add(row.album_b_id)
        else:
            already_compared_ids.add(row.album_a_id)

    # Get nearby Elo albums sorted by distance from current Elo
    nearby_query = (
        select(UserAlbumElo)
        .where(
            UserAlbumElo.user_id == user_id,
            UserAlbumElo.album_id != album_id,
        )
        .order_by(func.abs(UserAlbumElo.elo - current_elo))
        .limit(3 + len(already_compared_ids))  # fetch extra to filter
    )
    nearby_result = await db.execute(nearby_query)
    nearby_elos = nearby_result.scalars().all()

    # Filter out already-compared and take top 3
    candidates = [e for e in nearby_elos if e.album_id not in already_compared_ids][:3]

    if not candidates:
        return []

    # Fetch album details for these candidates
    candidate_album_ids = [c.album_id for c in candidates]
    albums_result = await db.execute(
        select(Album)
        .where(Album.id.in_(candidate_album_ids))
        .options(selectinload(Album.artists))
    )
    albums_by_id = {a.id: a for a in albums_result.scalars().all()}

    nearby_albums = []
    for candidate in candidates:
        a = albums_by_id.get(candidate.album_id)
        if not a or not a.mbid:
            continue
        nearby_albums.append(NearbyAlbum(
            album_id=a.id,
            mbid=a.mbid,
            title=a.title,
            artist_name=a.artists[0].name if a.artists else None,
            cover_url=a.cover_url,
            elo=candidate.elo,
        ))

    return nearby_albums


@router.post(
    "",
    response_model=RatingOut,
    responses={
        401: {"description": "Not authenticated"},
        404: {
            "description": "Album not found in MusicBrainz",
            "content": {
                "application/json": {
                    "example": {"detail": "Album not found in MusicBrainz"}
                }
            },
        },
        422: {"description": "Invalid rating value (must be 1-10)"},
        429: {"description": "Rate limit exceeded (60/minute)"},
    },
)
@limiter.limit(RateLimits.RATING)
async def rate_album(
    request: Request,
    rating: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RatingOut:
    """
    Rate an album on a 1-10 scale.

    This creates a **weak Elo signal (K=16)** for your personal rankings.
    The rating is interpreted relative to your average rating:
    - Rating above your average → album's Elo increases
    - Rating below your average → album's Elo decreases

    **Behavior**:
    - If the album doesn't exist locally, it's fetched from MusicBrainz
    - If you've already rated this album, your rating is updated
    - Both personal Elo and community Bayesian scores are recalculated

    **Rate limit**: 60 requests per minute
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

    # Find nearby albums for comparison prompt
    nearby_albums = await _get_nearby_albums(db, current_user.id, album.id)

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
        nearby_albums=nearby_albums,
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
