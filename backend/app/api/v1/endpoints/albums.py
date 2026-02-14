"""Album search and retrieval endpoints."""

import asyncio

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.core.rate_limit import limiter, RateLimits
from backend.app.models.album import Album, Artist, album_artists
from backend.app.models.rating import NumericRating, UserAlbumElo
from backend.app.models.user import User
from backend.app.schemas.album import AlbumSearchResult, AlbumSearchResponse, AlbumOut, AlbumListResponse, AlbumDetail
from backend.app.services.musicbrainz import musicbrainz_client
from backend.app.services.elo import get_user_elo_range, normalize_elo

router = APIRouter(prefix="/albums", tags=["albums"])

COVER_ART_URL = "https://coverartarchive.org/release-group/{mbid}/front-250"


def _cover_url_for(mbid: str, existing_url: str | None = None) -> str | None:
    """Return existing cover URL or a deterministic Cover Art Archive URL."""
    return existing_url or COVER_ART_URL.format(mbid=mbid)


@router.get("/search", response_model=AlbumSearchResponse)
@limiter.limit(RateLimits.SEARCH)
async def search_albums(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query (album name or artist)"),
    limit: int = Query(10, ge=1, le=25, description="Maximum number of results"),
    include_covers: bool = Query(False, description="Ignored (kept for backwards compat). Covers are always included via deterministic URLs."),
    db: AsyncSession = Depends(get_db),
) -> AlbumSearchResponse:
    """
    Search for albums - checks local database and MusicBrainz in parallel.

    Returns album metadata including title, artist, release year.
    Cover art URLs are deterministic (Cover Art Archive) and don't require
    extra API calls, so they're always included.
    """

    # Run DB and MusicBrainz searches in parallel
    # Split query into terms — each term must match either title or artist
    terms = q.split()
    term_filters = []
    for term in terms:
        pattern = f"%{term}%"
        term_filters.append(
            or_(
                func.lower(Album.title).like(func.lower(pattern)),
                func.lower(Artist.name).like(func.lower(pattern)),
            )
        )

    local_query = (
        select(Album)
        .options(selectinload(Album.artists))
        .outerjoin(album_artists, Album.id == album_artists.c.album_id)
        .outerjoin(Artist, Artist.id == album_artists.c.artist_id)
        .where(and_(*term_filters))
        .distinct()
        .limit(limit)
    )

    async def db_search() -> list[Album]:
        result = await db.execute(local_query)
        return list(result.scalars().all())

    async def mb_search() -> list:
        try:
            return await musicbrainz_client.search_albums(q, limit + 5)
        except Exception:
            return []

    local_albums, mb_results = await asyncio.gather(db_search(), mb_search())

    # Merge results: local DB first, then MusicBrainz (deduplicated)
    results: list[AlbumSearchResult] = []
    seen_mbids: set[str] = set()

    for album in local_albums:
        if album.mbid:
            seen_mbids.add(album.mbid)
        artist = album.artists[0] if album.artists else None
        results.append(
            AlbumSearchResult(
                mbid=album.mbid,
                title=album.title,
                artist_name=artist.name if artist else None,
                artist_mbid=artist.mbid if artist else None,
                release_year=album.release_year,
                cover_url=_cover_url_for(album.mbid, album.cover_url),
            )
        )

    for r in mb_results:
        if r.mbid in seen_mbids:
            continue
        if len(results) >= limit:
            break
        seen_mbids.add(r.mbid)
        results.append(
            AlbumSearchResult(
                mbid=r.mbid,
                title=r.title,
                artist_name=r.artist_name,
                artist_mbid=r.artist_mbid,
                release_year=r.release_year,
                cover_url=_cover_url_for(r.mbid),
            )
        )

    if not results:
        # Both searches returned nothing
        pass

    return AlbumSearchResponse(
        query=q,
        results=results[:limit],
        count=len(results[:limit]),
    )


@router.get("/db/list", response_model=AlbumListResponse)
async def list_albums(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="Number of albums to return"),
    offset: int = Query(0, ge=0, description="Number of albums to skip"),
    sort_by: str = Query("rating_count", description="Sort by: rating_count, community_mean, title, release_year"),
) -> AlbumListResponse:
    """
    List albums from local database.

    Returns albums that have been rated by users, sorted by popularity or rating.
    """
    # Get total count
    count_result = await db.execute(select(func.count(Album.id)))
    total = count_result.scalar() or 0

    # Build query with sorting
    query = select(Album).options(selectinload(Album.artists))

    if sort_by == "community_mean":
        query = query.order_by(Album.community_mean.desc().nullslast())
    elif sort_by == "title":
        query = query.order_by(Album.title.asc())
    elif sort_by == "release_year":
        query = query.order_by(Album.release_year.desc().nullslast())
    else:  # default: rating_count
        query = query.order_by(Album.rating_count.desc())

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    albums = result.scalars().all()

    return AlbumListResponse(
        albums=[
            AlbumOut(
                id=a.id,
                mbid=a.mbid,
                title=a.title,
                release_year=a.release_year,
                cover_url=a.cover_url,
                artist_name=a.artists[0].name if a.artists else None,
                community_mean=a.community_mean,
                rating_count=a.rating_count,
            )
            for a in albums
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{mbid}/detail", response_model=AlbumDetail)
async def get_album_detail(
    mbid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlbumDetail:
    """
    Get enriched album detail: metadata, genres, community stats, and user data.

    Checks local DB first (fast, has community stats + user data), then
    enriches with MusicBrainz metadata (genres). Never fails if the album
    exists in either source.
    """
    # 1. Check local DB first — fast and has all rating/community data
    result = await db.execute(
        select(Album)
        .where(Album.mbid == mbid)
        .options(selectinload(Album.artists))
    )
    local_album = result.scalar_one_or_none()

    # 2. Try MusicBrainz for enrichment (genres), but don't fail if it errors
    mb_result = None
    try:
        mb_result = await musicbrainz_client.get_album_by_mbid(mbid)
    except Exception:
        pass

    # 3. Must exist in at least one source
    if not local_album and not mb_result:
        raise HTTPException(status_code=404, detail="Album not found")

    # 4. Resolve metadata: prefer local DB (it's authoritative), enrich from MB
    title = local_album.title if local_album else mb_result.title
    artist_name = (
        (local_album.artists[0].name if local_album and local_album.artists else None)
        or (mb_result.artist_name if mb_result else "Unknown Artist")
    )
    release_year = (
        local_album.release_year if local_album and local_album.release_year
        else (mb_result.release_year if mb_result else None)
    )
    cover_url = (
        local_album.cover_url if local_album and local_album.cover_url
        else (mb_result.cover_url if mb_result else None)
    ) or _cover_url_for(mbid)

    # 5. Genres: prefer MusicBrainz (fresh), fall back to local DB
    genres: list[str] = []
    if mb_result and mb_result.genres:
        genres = mb_result.genres
    elif local_album and local_album.genres:
        genres = [g.strip() for g in local_album.genres.split(",") if g.strip()]

    # 6. Community stats from local DB
    community_rating_count = 0
    community_average_rating = None
    community_bayesian_score = None

    if local_album:
        community_rating_count = local_album.rating_count
        if local_album.rating_count > 0:
            community_average_rating = round(local_album.rating_sum / local_album.rating_count, 1)
        community_bayesian_score = local_album.bayesian_score

    # 7. User's personal data
    user_rating = None
    user_elo = None
    user_elo_normalized = None
    user_rank = None

    if local_album:
        # User's numeric rating
        rating_result = await db.execute(
            select(NumericRating.value).where(
                NumericRating.user_id == current_user.id,
                NumericRating.album_id == local_album.id,
            )
        )
        rating_row = rating_result.scalar_one_or_none()
        if rating_row is not None:
            user_rating = rating_row

        # User's Elo and rank
        elo_result = await db.execute(
            select(UserAlbumElo).where(
                UserAlbumElo.user_id == current_user.id,
                UserAlbumElo.album_id == local_album.id,
            )
        )
        elo_record = elo_result.scalar_one_or_none()
        if elo_record:
            user_elo = elo_record.elo
            # Normalize to 0-100
            min_elo, max_elo = await get_user_elo_range(db, current_user.id)
            user_elo_normalized = normalize_elo(elo_record.elo, min_elo, max_elo)
            # Compute rank: count albums with higher Elo
            rank_result = await db.execute(
                select(func.count(UserAlbumElo.id)).where(
                    UserAlbumElo.user_id == current_user.id,
                    UserAlbumElo.elo > elo_record.elo,
                )
            )
            user_rank = (rank_result.scalar() or 0) + 1

    return AlbumDetail(
        mbid=mbid,
        title=title,
        artist_name=artist_name,
        release_year=release_year,
        cover_url=cover_url,
        genres=genres,
        community_rating_count=community_rating_count,
        community_average_rating=community_average_rating,
        community_bayesian_score=community_bayesian_score,
        user_rating=user_rating,
        user_elo=user_elo,
        user_elo_normalized=user_elo_normalized,
        user_rank=user_rank,
    )


@router.get("/{mbid}", response_model=AlbumSearchResult)
async def get_album(mbid: str) -> AlbumSearchResult:
    """
    Get album details by MusicBrainz ID from MusicBrainz API.

    Returns album metadata including cover art URL.
    """
    result = await musicbrainz_client.get_album_by_mbid(mbid)
    if not result:
        raise HTTPException(status_code=404, detail="Album not found")

    return AlbumSearchResult(
        mbid=result.mbid,
        title=result.title,
        artist_name=result.artist_name,
        artist_mbid=result.artist_mbid,
        release_year=result.release_year,
        cover_url=result.cover_url,
    )
