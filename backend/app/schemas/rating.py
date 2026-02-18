"""Pydantic schemas for rating operations."""

from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# Numeric Rating Schemas
# ============================================================================


class RatingCreate(BaseModel):
    """Request to rate an album (1-10 scale)."""

    mbid: str = Field(..., description="MusicBrainz release-group ID of the album")
    value: float = Field(..., ge=1.0, le=10.0, description="Rating from 1.0 to 10.0")
    notes: str | None = Field(None, max_length=1000, description="Optional notes about the rating")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mbid": "a4864e94-6d75-4ade-bc93-0b389f5c1b8a",
                    "value": 9.5,
                    "notes": "One of the best albums of the 90s",
                }
            ]
        }
    }


class NearbyAlbum(BaseModel):
    """An album near the just-rated album in Elo space, for comparison prompts."""

    album_id: str = Field(..., description="Internal album ID")
    mbid: str = Field(..., description="MusicBrainz release-group ID")
    title: str = Field(..., description="Album title")
    artist_name: str | None = Field(None, description="Primary artist name")
    cover_url: str | None = Field(None, description="Cover art URL")
    elo: float = Field(..., description="Current Elo score")


class RatingOut(BaseModel):
    """A user's rating for an album."""

    id: str = Field(..., description="Rating ID (UUID)")
    album_id: str = Field(..., description="Internal album ID")
    album_title: str = Field(..., description="Album title")
    album_artist: str | None = Field(None, description="Primary artist name")
    album_cover_url: str | None = Field(None, description="Cover art URL")
    value: float = Field(..., description="Rating value (1-10)")
    notes: str | None = Field(None, description="User's notes")
    created_at: str = Field(..., description="When the rating was created (ISO 8601)")
    updated_at: str = Field(..., description="When the rating was last updated (ISO 8601)")
    nearby_albums: list[NearbyAlbum] = Field(default_factory=list, description="Albums with similar Elo for comparison prompts")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440002",
                    "album_id": "550e8400-e29b-41d4-a716-446655440001",
                    "album_title": "OK Computer",
                    "album_artist": "Radiohead",
                    "album_cover_url": "https://coverartarchive.org/...",
                    "value": 9.5,
                    "notes": "One of the best albums of the 90s",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    }


class RatingListResponse(BaseModel):
    """Response for listing user's ratings."""

    ratings: list[RatingOut] = Field(..., description="List of user's ratings")
    count: int = Field(..., description="Number of ratings returned")


# ============================================================================
# Pairwise Comparison Schemas
# ============================================================================


class ComparisonCreate(BaseModel):
    """Request to create a pairwise comparison between two albums."""

    mbid_a: str = Field(..., description="MusicBrainz ID of album A")
    mbid_b: str = Field(..., description="MusicBrainz ID of album B")
    winner: Literal["a", "b", "tie"] = Field(
        ..., description="Which album is preferred: 'a', 'b', or 'tie'"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mbid_a": "a4864e94-6d75-4ade-bc93-0b389f5c1b8a",
                    "mbid_b": "b5dfc4fe-c7b4-4b2e-ae1f-6b37f1e6b8d9",
                    "winner": "a",
                }
            ]
        }
    }


class ComparisonOut(BaseModel):
    """A pairwise comparison between two albums."""

    id: str = Field(..., description="Comparison ID (UUID)")
    album_a_id: str = Field(..., description="Internal ID of album A")
    album_a_title: str = Field(..., description="Title of album A")
    album_a_artist: str | None = Field(None, description="Artist of album A")
    album_a_cover_url: str | None = Field(None, description="Cover URL of album A")
    album_b_id: str = Field(..., description="Internal ID of album B")
    album_b_title: str = Field(..., description="Title of album B")
    album_b_artist: str | None = Field(None, description="Artist of album B")
    album_b_cover_url: str | None = Field(None, description="Cover URL of album B")
    winner: Literal["a", "b", "tie"] = Field(..., description="Which album won")
    created_at: str = Field(..., description="When the comparison was made (ISO 8601)")
    updated_at: str = Field(..., description="When the comparison was last updated (ISO 8601)")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440003",
                    "album_a_id": "550e8400-e29b-41d4-a716-446655440001",
                    "album_a_title": "OK Computer",
                    "album_a_artist": "Radiohead",
                    "album_a_cover_url": "https://coverartarchive.org/...",
                    "album_b_id": "550e8400-e29b-41d4-a716-446655440004",
                    "album_b_title": "Kid A",
                    "album_b_artist": "Radiohead",
                    "album_b_cover_url": "https://coverartarchive.org/...",
                    "winner": "a",
                    "created_at": "2024-01-15T11:00:00Z",
                    "updated_at": "2024-01-15T11:00:00Z",
                }
            ]
        },
    }


class ComparisonListResponse(BaseModel):
    """Response for listing user's comparisons."""

    comparisons: list[ComparisonOut] = Field(..., description="List of comparisons")
    count: int = Field(..., description="Number of comparisons returned")


# ============================================================================
# Personal Rankings Schemas (Elo-based)
# ============================================================================


class RankedAlbumOut(BaseModel):
    """An album with its Elo ranking information."""

    rank: int = Field(..., description="Position in personal ranking (1 = best)")
    album_id: str = Field(..., description="Internal album ID")
    album_mbid: str | None = Field(None, description="MusicBrainz release-group ID")
    album_title: str = Field(..., description="Album title")
    album_artist: str | None = Field(None, description="Primary artist name")
    album_cover_url: str | None = Field(None, description="Cover art URL")
    elo: float = Field(..., description="Raw Elo rating score (internal)")
    elo_normalized: float = Field(..., description="Elo normalized to 0-100 scale")
    rating_count: int = Field(..., description="Number of numeric ratings for this album")
    comparison_count: int = Field(..., description="Number of pairwise comparisons involving this album")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "rank": 1,
                    "album_id": "550e8400-e29b-41d4-a716-446655440001",
                    "album_mbid": "a4864e94-6d75-4ade-bc93-0b389f5c1b8a",
                    "album_title": "OK Computer",
                    "album_artist": "Radiohead",
                    "album_cover_url": "https://coverartarchive.org/...",
                    "elo": 1687.5,
                    "elo_normalized": 85.0,
                    "rating_count": 3,
                    "comparison_count": 12,
                }
            ]
        },
    }


class PersonalRankingsResponse(BaseModel):
    """User's personal album rankings sorted by Elo score."""

    rankings: list[RankedAlbumOut] = Field(..., description="Albums ranked by Elo score (descending)")
    count: int = Field(..., description="Number of ranked albums returned")


# ============================================================================
# Comparison Suggestion Schemas
# ============================================================================


class SuggestedAlbum(BaseModel):
    """Album info for comparison suggestion."""

    id: str = Field(..., description="Internal album ID")
    title: str = Field(..., description="Album title")
    artist_name: str | None = Field(None, description="Primary artist name")
    cover_url: str | None = Field(None, description="Cover art URL")
    elo: float = Field(..., description="Current Elo score")
    comparison_count: int = Field(..., description="Number of comparisons made")


class ComparisonSuggestionOut(BaseModel):
    """A suggested pair of albums to compare."""

    album_a: SuggestedAlbum = Field(..., description="First album in the suggested pair")
    album_b: SuggestedAlbum = Field(..., description="Second album in the suggested pair")
    reason: str = Field(..., description="Why this comparison is suggested")
    priority_score: float = Field(..., description="How important this comparison is (higher = more important)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "album_a": {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "title": "OK Computer",
                        "artist_name": "Radiohead",
                        "cover_url": "https://coverartarchive.org/...",
                        "elo": 1687.5,
                        "comparison_count": 12,
                    },
                    "album_b": {
                        "id": "550e8400-e29b-41d4-a716-446655440004",
                        "title": "Kid A",
                        "artist_name": "Radiohead",
                        "cover_url": "https://coverartarchive.org/...",
                        "elo": 1672.3,
                        "comparison_count": 8,
                    },
                    "reason": "close_elo",
                    "priority_score": 2.85,
                }
            ]
        }
    }


class ComparisonSuggestionsResponse(BaseModel):
    """Response for comparison suggestions."""

    suggestions: list[ComparisonSuggestionOut] = Field(..., description="Suggested album pairs to compare")
    count: int = Field(..., description="Number of suggestions returned")


class ComparisonStatsResponse(BaseModel):
    """Statistics about user's comparison coverage."""

    ranked_albums: int = Field(..., description="Total number of albums in your rankings")
    total_comparisons: int = Field(..., description="Total number of comparisons you've made")
    unique_pairs_compared: int = Field(..., description="Number of unique album pairs compared")
    possible_pairs: int = Field(..., description="Total possible pairs (n*(n-1)/2)")
    coverage_percentage: float = Field(..., description="Percentage of possible pairs compared")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ranked_albums": 25,
                    "total_comparisons": 87,
                    "unique_pairs_compared": 72,
                    "possible_pairs": 300,
                    "coverage_percentage": 24.0,
                }
            ]
        }
    }
