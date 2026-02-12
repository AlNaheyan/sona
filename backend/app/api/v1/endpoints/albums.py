"""Album search and retrieval endpoints."""

import asyncio

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.rate_limit import limiter, RateLimits
from backend.app.models.album import Album
from backend.app.schemas.album import AlbumSearchResult, AlbumSearchResponse, AlbumOut, AlbumListResponse
from backend.app.services.musicbrainz import musicbrainz_client

router = APIRouter(prefix="/albums", tags=["albums"])

COVER_ART_URL = "https://coverartarchive.org/release-group/{mbid}/front-250"


def _cover_url_for(mbid: str, existing_url: str | None = None) -> str | None:
    """Return existing cover URL or a deterministic Cover Art Archive URL."""
    return existing_url or COVER_ART_URL.format(mbid=mbid)


@router.get("/search", response_model=AlbumSearchResponse)
@limiter.limit(RateLimits.SEARCH)
async def search_albums(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query (album name)"),
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
    search_pattern = f"%{q}%"
    local_query = (
        select(Album)
        .options(selectinload(Album.artists))
        .where(func.lower(Album.title).like(func.lower(search_pattern)))
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
