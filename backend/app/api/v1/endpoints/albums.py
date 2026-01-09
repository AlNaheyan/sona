"""Album search and retrieval endpoints."""

from fastapi import APIRouter, Query, HTTPException

from backend.app.schemas.album import AlbumSearchResult, AlbumSearchResponse
from backend.app.services.musicbrainz import musicbrainz_client

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get("/search", response_model=AlbumSearchResponse)
async def search_albums(
    q: str = Query(..., min_length=1, description="Search query (album name)"),
    limit: int = Query(10, ge=1, le=25, description="Maximum number of results"),
    include_covers: bool = Query(False, description="Fetch cover art (slower)"),
) -> AlbumSearchResponse:
    """
    Search for albums using MusicBrainz.

    Returns album metadata including title, artist, release year.
    Set include_covers=true to also fetch cover art URLs (makes request slower).
    """
    try:
        if include_covers:
            results = await musicbrainz_client.search_albums_with_covers(q, limit)
        else:
            results = await musicbrainz_client.search_albums(q, limit)

        return AlbumSearchResponse(
            query=q,
            results=[
                AlbumSearchResult(
                    mbid=r.mbid,
                    title=r.title,
                    artist_name=r.artist_name,
                    artist_mbid=r.artist_mbid,
                    release_year=r.release_year,
                    cover_url=r.cover_url,
                )
                for r in results
            ],
            count=len(results),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MusicBrainz API error: {str(e)}")


@router.get("/{mbid}", response_model=AlbumSearchResult)
async def get_album(mbid: str) -> AlbumSearchResult:
    """
    Get album details by MusicBrainz ID.

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
