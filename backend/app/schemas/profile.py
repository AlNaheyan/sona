"""Pydantic schemas for user profiles."""

from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    """Create or update a user profile (PUT body)."""

    display_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Display name (2-100 chars)",
    )
    bio: str | None = Field(
        None,
        max_length=500,
        description="Short bio (optional, max 500 chars)",
    )
    avatar_url: str | None = Field(
        None,
        max_length=500,
        description="Avatar image URL (optional)",
    )
    spotify_username: str | None = Field(
        None,
        max_length=100,
        description="Spotify username (optional)",
    )
    favorite_genres: str | None = Field(
        None,
        max_length=500,
        description="Comma-separated favorite genres (optional)",
    )


class ProfileOut(BaseModel):
    """Full profile response for the authenticated user."""

    id: str
    user_id: str
    username: str
    display_name: str
    bio: str | None
    avatar_url: str | None
    spotify_username: str | None
    favorite_genres: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PublicProfileOut(BaseModel):
    """Public profile visible to anyone."""

    username: str
    display_name: str
    bio: str | None
    avatar_url: str | None
    spotify_username: str | None
    favorite_genres: str | None
    rated_albums_count: int
    member_since: str
