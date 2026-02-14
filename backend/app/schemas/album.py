"""Pydantic schemas for album-related operations."""

from pydantic import BaseModel, Field


class AlbumSearchResult(BaseModel):
    """Album from MusicBrainz search."""

    mbid: str = Field(..., description="MusicBrainz release-group ID (UUID format)")
    title: str = Field(..., description="Album title")
    artist_name: str = Field(..., description="Primary artist name")
    artist_mbid: str | None = Field(None, description="MusicBrainz artist ID")
    release_year: int | None = Field(None, description="Year of first release")
    cover_url: str | None = Field(None, description="Cover art URL from Cover Art Archive")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mbid": "a4864e94-6d75-4ade-bc93-0b389f5c1b8a",
                    "title": "OK Computer",
                    "artist_name": "Radiohead",
                    "artist_mbid": "a74b1b7f-71a5-4011-9441-d0b5e4122711",
                    "release_year": 1997,
                    "cover_url": "https://coverartarchive.org/release-group/a4864e94.../front-250.jpg",
                }
            ]
        }
    }


class AlbumSearchResponse(BaseModel):
    """Response for album search endpoint."""

    query: str = Field(..., description="The search query that was executed")
    results: list[AlbumSearchResult] = Field(..., description="List of matching albums")
    count: int = Field(..., description="Number of results returned")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "radiohead",
                    "results": [
                        {
                            "mbid": "a4864e94-6d75-4ade-bc93-0b389f5c1b8a",
                            "title": "OK Computer",
                            "artist_name": "Radiohead",
                            "artist_mbid": "a74b1b7f-71a5-4011-9441-d0b5e4122711",
                            "release_year": 1997,
                            "cover_url": None,
                        }
                    ],
                    "count": 1,
                }
            ]
        }
    }


class AlbumOut(BaseModel):
    """Album stored in our database."""

    id: str = Field(..., description="Internal album ID (UUID)")
    mbid: str | None = Field(None, description="MusicBrainz release-group ID")
    title: str = Field(..., description="Album title")
    release_year: int | None = Field(None, description="Year of first release")
    cover_url: str | None = Field(None, description="Cover art URL")
    artist_name: str | None = Field(None, description="Primary artist name")
    rating_count: int = Field(0, description="Number of user ratings")
    bayesian_score: float | None = Field(None, description="Community Bayesian-weighted score")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "mbid": "a4864e94-6d75-4ade-bc93-0b389f5c1b8a",
                    "title": "OK Computer",
                    "release_year": 1997,
                    "cover_url": "https://coverartarchive.org/...",
                    "artist_name": "Radiohead",
                    "rating_count": 42,
                    "bayesian_score": 8.45,
                }
            ]
        },
    }


class AlbumListResponse(BaseModel):
    """Response for album listing endpoint."""

    albums: list[AlbumOut] = Field(..., description="List of albums")
    total: int = Field(..., description="Total number of albums in database")
    limit: int = Field(..., description="Maximum results requested")
    offset: int = Field(..., description="Number of results skipped")


# ============================================================================
# Album Detail Schema (enriched view for modal)
# ============================================================================


class AlbumDetail(BaseModel):
    """Full album detail combining metadata, community stats, and user data."""

    mbid: str = Field(..., description="MusicBrainz release-group ID")
    title: str = Field(..., description="Album title")
    artist_name: str = Field(..., description="Primary artist name")
    release_year: int | None = Field(None, description="Year of first release")
    cover_url: str | None = Field(None, description="Cover art URL")
    genres: list[str] = Field(default_factory=list, description="Genre tags")

    # Community stats (null if album not yet in local DB)
    community_rating_count: int = Field(0, description="Number of community ratings")
    community_average_rating: float | None = Field(None, description="Community average rating (1-10)")
    community_bayesian_score: float | None = Field(None, description="Bayesian-weighted community score")

    # User-specific data (null if user hasn't interacted)
    user_rating: float | None = Field(None, description="User's 1-10 rating, or null if not rated")
    user_elo: float | None = Field(None, description="User's raw Elo score (internal)")
    user_elo_normalized: float | None = Field(None, description="User's Elo normalized to 0-100 scale")
    user_rank: int | None = Field(None, description="User's rank for this album")


# ============================================================================
# Community Rankings Schemas
# ============================================================================


class CommunityRankedAlbum(BaseModel):
    """Album with community ranking information."""

    rank: int = Field(..., description="Position in community rankings (1 = best)")
    id: str = Field(..., description="Internal album ID")
    mbid: str | None = Field(None, description="MusicBrainz release-group ID")
    title: str = Field(..., description="Album title")
    artist_name: str | None = Field(None, description="Primary artist name")
    cover_url: str | None = Field(None, description="Cover art URL")
    release_year: int | None = Field(None, description="Year of first release")
    rating_count: int = Field(..., description="Number of user ratings")
    average_rating: float = Field(..., description="Raw average of all ratings (1-10)")
    bayesian_score: float = Field(
        ...,
        description="Bayesian-weighted score that accounts for rating count and global average",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "rank": 1,
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "mbid": "a4864e94-6d75-4ade-bc93-0b389f5c1b8a",
                    "title": "OK Computer",
                    "artist_name": "Radiohead",
                    "cover_url": "https://coverartarchive.org/...",
                    "release_year": 1997,
                    "rating_count": 156,
                    "average_rating": 9.12,
                    "bayesian_score": 8.87,
                }
            ]
        },
    }


class CommunityRankingsResponse(BaseModel):
    """Response for community rankings endpoint."""

    rankings: list[CommunityRankedAlbum] = Field(..., description="Ranked list of albums")
    total: int = Field(..., description="Total number of ranked albums")
    limit: int = Field(..., description="Maximum results requested")
    offset: int = Field(..., description="Number of results skipped")
