"""Pydantic schemas for rating operations."""

from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# Numeric Rating Schemas
# ============================================================================

class RatingCreate(BaseModel):
    """Request to rate an album."""
    mbid: str = Field(..., description="MusicBrainz release-group ID of the album")
    value: float = Field(..., ge=1.0, le=10.0, description="Rating from 1 to 10")
    notes: str | None = Field(None, max_length=1000, description="Optional notes about the rating")


class RatingOut(BaseModel):
    """A user's rating for an album."""
    id: str
    album_id: str
    album_title: str
    album_artist: str | None
    album_cover_url: str | None
    value: float
    notes: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class RatingListResponse(BaseModel):
    """Response for listing user's ratings."""
    ratings: list[RatingOut]
    count: int


# ============================================================================
# Pairwise Comparison Schemas
# ============================================================================

class ComparisonCreate(BaseModel):
    """Request to create a pairwise comparison between two albums."""
    mbid_a: str = Field(..., description="MusicBrainz ID of album A")
    mbid_b: str = Field(..., description="MusicBrainz ID of album B")
    winner: Literal["a", "b", "tie"] = Field(..., description="Which album is preferred: 'a', 'b', or 'tie'")


class ComparisonOut(BaseModel):
    """A pairwise comparison between two albums."""
    id: str
    album_a_id: str
    album_a_title: str
    album_a_artist: str | None
    album_a_cover_url: str | None
    album_b_id: str
    album_b_title: str
    album_b_artist: str | None
    album_b_cover_url: str | None
    winner: Literal["a", "b", "tie"]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ComparisonListResponse(BaseModel):
    """Response for listing user's comparisons."""
    comparisons: list[ComparisonOut]
    count: int


# ============================================================================
# Tier List Schemas
# ============================================================================

TierValue = Literal["S", "A", "B", "C", "D", "F"]


class TierPlacementCreate(BaseModel):
    """Request to place an album in a tier."""
    mbid: str = Field(..., description="MusicBrainz ID of the album")
    tier: TierValue = Field(..., description="Tier: S, A, B, C, D, or F")
    position: int = Field(0, ge=0, description="Position within the tier (0 = first)")


class TierPlacementOut(BaseModel):
    """An album's placement in a tier list."""
    id: str
    album_id: str
    album_title: str
    album_artist: str | None
    album_cover_url: str | None
    tier: TierValue
    position: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TierGroup(BaseModel):
    """A group of albums in a single tier."""
    tier: TierValue
    albums: list[TierPlacementOut]


class TierListResponse(BaseModel):
    """User's complete tier list grouped by tier."""
    tiers: list[TierGroup]
    total_count: int


# ============================================================================
# Personal Rankings Schemas (CWPR-based)
# ============================================================================

class RankedAlbumOut(BaseModel):
    """An album with its CWPR ranking information."""
    rank: int
    album_id: str
    album_title: str
    album_artist: str | None
    album_cover_url: str | None
    mu: float = Field(..., description="Mean preference estimate (μ)")
    sigma: float = Field(..., description="Uncertainty (σ)")
    score: float = Field(..., description="CWPR score (μ - λσ)")
    numeric_count: int = Field(..., description="Number of numeric ratings")
    pairwise_count: int = Field(..., description="Number of pairwise comparisons")
    tier_count: int = Field(..., description="Number of tier placements")

    model_config = {"from_attributes": True}


class PersonalRankingsResponse(BaseModel):
    """User's personal album rankings based on CWPR scores."""
    rankings: list[RankedAlbumOut]
    count: int
