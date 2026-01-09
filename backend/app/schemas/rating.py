"""Pydantic schemas for rating operations."""

from pydantic import BaseModel, Field


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
