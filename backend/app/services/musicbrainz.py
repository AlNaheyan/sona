"""
MusicBrainz API client for album/artist metadata.

Uses:
- MusicBrainz API for album/artist data (no auth required, 1 req/sec limit)
- Cover Art Archive for album artwork (no auth required)
- Redis caching to reduce API calls and respect rate limits
"""

import asyncio
import logging
from dataclasses import dataclass, asdict

import httpx

from backend.app.services.cache import (
    cache_service,
    CacheKeys,
    CacheTTL,
)

logger = logging.getLogger(__name__)

MUSICBRAINZ_BASE_URL = "https://musicbrainz.org/ws/2"
COVER_ART_BASE_URL = "https://coverartarchive.org"

# MusicBrainz requires a User-Agent with contact info
USER_AGENT = "RateMyAlbum/0.1.0 (https://github.com/ratemyalbum)"


@dataclass
class AlbumSearchResult:
    """Album search result from MusicBrainz."""
    mbid: str
    title: str
    artist_name: str
    artist_mbid: str | None
    release_year: int | None
    cover_url: str | None

    def to_dict(self) -> dict:
        """Convert to dictionary for caching."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AlbumSearchResult":
        """Create from dictionary (from cache)."""
        return cls(**data)


class MusicBrainzClient:
    """Async client for MusicBrainz and Cover Art Archive APIs with caching."""

    def __init__(self) -> None:
        self._last_request_time: float = 0
        self._rate_limit_delay: float = 1.0  # 1 request per second

    async def _rate_limit(self) -> None:
        """Ensure we don't exceed MusicBrainz rate limit (1 req/sec)."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def search_albums(self, query: str, limit: int = 10) -> list[AlbumSearchResult]:
        """
        Search for albums by name. Results are cached for 1 hour.

        Args:
            query: Search query (album name, can include artist)
            limit: Maximum number of results (default 10)

        Returns:
            List of album search results
        """
        # Check cache first
        cache_key = CacheKeys.musicbrainz_search(query, limit)
        cached = await cache_service.get(cache_key)
        if cached:
            logger.debug(f"Cache HIT for search: {query}")
            return [AlbumSearchResult.from_dict(item) for item in cached]

        logger.debug(f"Cache MISS for search: {query}")

        # Rate limit and fetch from API
        await self._rate_limit()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MUSICBRAINZ_BASE_URL}/release-group",
                params={
                    "query": query,
                    "type": "album",
                    "limit": limit,
                    "fmt": "json",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

        results: list[AlbumSearchResult] = []
        for rg in data.get("release-groups", []):
            # Get primary artist
            artist_credit = rg.get("artist-credit", [])
            artist_name = ""
            artist_mbid = None
            if artist_credit:
                artist_name = artist_credit[0].get("name", "Unknown Artist")
                artist_info = artist_credit[0].get("artist", {})
                artist_mbid = artist_info.get("id")

            # Parse release year from first-release-date
            release_year = None
            first_release = rg.get("first-release-date", "")
            if first_release and len(first_release) >= 4:
                try:
                    release_year = int(first_release[:4])
                except ValueError:
                    pass

            results.append(
                AlbumSearchResult(
                    mbid=rg["id"],
                    title=rg.get("title", "Unknown Title"),
                    artist_name=artist_name,
                    artist_mbid=artist_mbid,
                    release_year=release_year,
                    cover_url=None,  # Fetched separately if needed
                )
            )

        # Cache results
        await cache_service.set(
            cache_key,
            [r.to_dict() for r in results],
            ttl_seconds=CacheTTL.SEARCH_RESULTS,
        )

        return results

    async def get_cover_art_url(self, mbid: str) -> str | None:
        """
        Get album cover art URL from Cover Art Archive. Cached for 7 days.

        Args:
            mbid: MusicBrainz release-group ID

        Returns:
            URL to cover art image, or None if not found
        """
        # Check cache first
        cache_key = CacheKeys.cover_art(mbid)
        cached = await cache_service.get(cache_key)
        if cached is not None:
            # Empty string means "no cover found" (cached negative result)
            return cached if cached else None

        # Fetch from API
        cover_url = None
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    f"{COVER_ART_BASE_URL}/release-group/{mbid}/front-250",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    cover_url = str(response.url)
        except httpx.HTTPError:
            pass

        # Cache result (including negative results as empty string)
        await cache_service.set(
            cache_key,
            cover_url or "",
            ttl_seconds=CacheTTL.COVER_ART,
        )

        return cover_url

    async def search_albums_with_covers(
        self, query: str, limit: int = 10
    ) -> list[AlbumSearchResult]:
        """
        Search for albums and fetch cover art for each result.

        Note: This makes multiple API calls, so it's slower but provides complete data.
        Cover art URLs are cached individually for 7 days.
        """
        results = await self.search_albums(query, limit)

        # Fetch cover art for each result (in parallel, but respecting rate limits)
        for result in results:
            result.cover_url = await self.get_cover_art_url(result.mbid)

        return results

    async def get_album_by_mbid(self, mbid: str) -> AlbumSearchResult | None:
        """
        Get album details by MusicBrainz ID. Cached for 24 hours.

        Args:
            mbid: MusicBrainz release-group ID

        Returns:
            Album details or None if not found
        """
        # Check cache first
        cache_key = CacheKeys.musicbrainz_album(mbid)
        cached = await cache_service.get(cache_key)
        if cached:
            logger.debug(f"Cache HIT for album: {mbid}")
            return AlbumSearchResult.from_dict(cached)

        logger.debug(f"Cache MISS for album: {mbid}")

        # Rate limit and fetch from API
        await self._rate_limit()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{MUSICBRAINZ_BASE_URL}/release-group/{mbid}",
                    params={"inc": "artist-credits", "fmt": "json"},
                    headers={"User-Agent": USER_AGENT},
                    timeout=10.0,
                )
                response.raise_for_status()
                rg = response.json()
        except httpx.HTTPError:
            return None

        # Get primary artist
        artist_credit = rg.get("artist-credit", [])
        artist_name = ""
        artist_mbid = None
        if artist_credit:
            artist_name = artist_credit[0].get("name", "Unknown Artist")
            artist_info = artist_credit[0].get("artist", {})
            artist_mbid = artist_info.get("id")

        # Parse release year
        release_year = None
        first_release = rg.get("first-release-date", "")
        if first_release and len(first_release) >= 4:
            try:
                release_year = int(first_release[:4])
            except ValueError:
                pass

        cover_url = await self.get_cover_art_url(mbid)

        result = AlbumSearchResult(
            mbid=rg["id"],
            title=rg.get("title", "Unknown Title"),
            artist_name=artist_name,
            artist_mbid=artist_mbid,
            release_year=release_year,
            cover_url=cover_url,
        )

        # Cache result
        await cache_service.set(
            cache_key,
            result.to_dict(),
            ttl_seconds=CacheTTL.ALBUM_METADATA,
        )

        return result


# Singleton instance
musicbrainz_client = MusicBrainzClient()
