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
    rating_count: int = 0
    bayesian_score: float | None = None

    model_config = {"from_attributes": True}


class AlbumListResponse(BaseModel):
    """Response for album listing endpoint."""
    albums: list[AlbumOut]
    total: int
    limit: int
    offset: int


# ============================================================================
# Community Rankings Schemas
# ============================================================================

class CommunityRankedAlbum(BaseModel):
    """Album with community ranking information."""
    rank: int
    id: str
    mbid: str | None
    title: str
    artist_name: str | None
    cover_url: str | None
    release_year: int | None
    rating_count: int
    average_rating: float = Field(..., description="Raw average of all ratings")
    bayesian_score: float = Field(..., description="Bayesian-weighted score")

    model_config = {"from_attributes": True}


class CommunityRankingsResponse(BaseModel):
    """Response for community rankings endpoint."""
    rankings: list[CommunityRankedAlbum]
    total: int
    limit: int
    offset: int
