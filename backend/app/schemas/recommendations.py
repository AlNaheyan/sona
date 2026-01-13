"""Pydantic schemas for recommendation endpoints."""

from pydantic import BaseModel, Field


class ContentScoreBreakdown(BaseModel):
    """Raw content scores for debugging/tuning."""

    genre: float = Field(..., description="Genre similarity score (0-1)")
    artist: float = Field(..., description="Artist overlap score (0-1)")
    era: float = Field(..., description="Era/temporal similarity score (0-1)")


class RecommendedAlbum(BaseModel):
    """A single album recommendation with scoring breakdown."""

    album_id: str
    mbid: str | None
    title: str
    artist_name: str | None
    cover_url: str | None
    release_year: int | None
    genres: str | None

    # Separate scores (for debugging/ML replacement)
    final_score: float = Field(..., description="Combined recommendation score (0-1)")
    content_score: float = Field(0, description="Content-based similarity score (0-1)")
    collaborative_score: float = Field(
        0, description="Collaborative filtering score (0-1)"
    )
    raw_scores: ContentScoreBreakdown | None = Field(
        None, description="Detailed content score breakdown"
    )

    is_exploration: bool = Field(
        False, description="True if injected for discovery outside user's taste"
    )
    reasons: list[str] = Field(
        default_factory=list, description="Human-readable recommendation reasons"
    )

    community_rating_count: int = Field(0, description="Number of community ratings")
    community_bayesian_score: float | None = Field(
        None, description="Community Bayesian score"
    )

    model_config = {"from_attributes": True}


class RecommendationsResponse(BaseModel):
    """Response for the recommendations endpoint."""

    recommendations: list[RecommendedAlbum]
    count: int

    # User context
    user_ranked_albums: int = Field(
        ..., description="Number of albums the user has ranked"
    )
    recommendation_type: str = Field(
        ..., description="Type: 'hybrid', 'content', 'collaborative', or 'discovery'"
    )

    # Algorithm transparency
    content_weight: float = Field(..., description="Weight given to content-based scoring")
    collaborative_weight: float = Field(
        ..., description="Weight given to collaborative filtering"
    )
    similar_users_found: int = Field(
        0, description="Number of similar users found for collaborative filtering"
    )
    exploration_count: int = Field(
        0, description="Number of exploration recommendations included"
    )


class SimilarAlbum(BaseModel):
    """An album similar to a target album."""

    album_id: str
    mbid: str | None
    title: str
    artist_name: str | None
    cover_url: str | None
    release_year: int | None
    similarity_score: float = Field(..., description="Content similarity score (0-1)")

    model_config = {"from_attributes": True}


class SimilarAlbumsResponse(BaseModel):
    """Response for similar albums endpoint."""

    target_album: dict
    similar_albums: list[SimilarAlbum]
    count: int
