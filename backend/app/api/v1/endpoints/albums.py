"""Album search and retrieval endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.album import Album
from backend.app.schemas.album import AlbumSearchResult, AlbumSearchResponse, AlbumOut, AlbumListResponse
from backend.app.services.musicbrainz import musicbrainz_client

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get("/search", response_model=AlbumSearchResponse)
async def search_albums(
    q: str = Query(..., min_length=1, description="Search query (album name)"),
    limit: int = Query(10, ge=1, le=25, description="Maximum number of results"),
    include_covers: bool = Query(False, description="Fetch cover art (slower)"),
    db: AsyncSession = Depends(get_db),
) -> AlbumSearchResponse:
    """
    Search for albums - checks local database first, then MusicBrainz.

    Returns album metadata including title, artist, release year.
    Local DB results are prioritized to reduce external API calls.
    Set include_covers=true to also fetch cover art URLs (makes request slower).
    """
    results: list[AlbumSearchResult] = []
    seen_mbids: set[str] = set()

    # 1. Search local database first (case-insensitive title/artist match)
    search_pattern = f"%{q}%"
    local_query = (
        select(Album)
        .options(selectinload(Album.artists))
        .where(
            func.lower(Album.title).like(func.lower(search_pattern))
        )
        .limit(limit)
    )
    local_result = await db.execute(local_query)
    local_albums = local_result.scalars().all()

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
                cover_url=album.cover_url,
            )
        )

    # 2. If we need more results, fetch from MusicBrainz
    if len(results) < limit:
        remaining = limit - len(results)
        try:
            if include_covers:
                mb_results = await musicbrainz_client.search_albums_with_covers(q, remaining + 5)
            else:
                mb_results = await musicbrainz_client.search_albums(q, remaining + 5)

            # Add MusicBrainz results, skipping duplicates
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
                        cover_url=r.cover_url,
                    )
                )
        except Exception as e:
            # If MusicBrainz fails but we have local results, return those
            if not results:
                raise HTTPException(status_code=503, detail=f"MusicBrainz API error: {str(e)}")

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
