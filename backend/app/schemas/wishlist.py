"""Pydantic schemas for Want to Listen (wishlist) operations."""

from pydantic import BaseModel, Field


class WishlistAdd(BaseModel):
    """Request to add an album to Want to Listen list."""

    mbid: str = Field(..., description="MusicBrainz release-group ID of the album")


class WishlistOut(BaseModel):
    """A wishlist entry with album info."""

    id: str = Field(..., description="Wishlist entry ID (UUID)")
    album_id: str = Field(..., description="Internal album ID")
    album_mbid: str = Field(..., description="MusicBrainz release-group ID")
    album_title: str = Field(..., description="Album title")
    album_artist: str | None = Field(None, description="Primary artist name")
    album_cover_url: str | None = Field(None, description="Cover art URL")
    created_at: str = Field(..., description="When the entry was created (ISO 8601)")

    model_config = {"from_attributes": True}


class WishlistCheckResponse(BaseModel):
    """Response for checking if an album is in the wishlist."""

    in_wishlist: bool = Field(..., description="Whether the album is in the wishlist")
    entry_id: str | None = Field(None, description="Wishlist entry ID if present")


class WishlistListResponse(BaseModel):
    """Response for listing wishlist entries."""

    items: list[WishlistOut] = Field(..., description="List of wishlist entries")
    count: int = Field(..., description="Number of entries returned")
