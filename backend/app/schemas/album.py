"""Pydantic schemas for album-related operations."""

from pydantic import BaseModel, Field


class AlbumSearchResult(BaseModel):
    """Album from MusicBrainz search."""
    mbid: str = Field(..., description="MusicBrainz release-group ID")
    title: str
    artist_name: str
    artist_mbid: str | None = None
    release_year: int | None = None
    cover_url: str | None = None


class AlbumSearchResponse(BaseModel):
    """Response for album search endpoint."""
    query: str
    results: list[AlbumSearchResult]
    count: int


class AlbumOut(BaseModel):
    """Album stored in our database."""
    id: str
    mbid: str | None
    title: str
    release_year: int | None
    cover_url: str | None
    artist_name: str | None = None
    community_mean: float | None = None
    rating_count: int = 0

    model_config = {"from_attributes": True}
