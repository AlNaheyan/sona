"""Pydantic schemas for recommendation endpoints."""

from pydantic import BaseModel, Field


class ContentScoreBreakdown(BaseModel):
    """Raw content scores for debugging/tuning."""

    genre: float = Field(..., description="Genre similarity score (0-1)")
    artist: float = Field(..., description="Artist overlap score (0-1)")
    era: float = Field(..., description="Era/temporal similarity score (0-1)")


class RecommendedAlbum(BaseModel):
    """A single album recommendation with scoring breakdown."""

    album_id: str = Field(..., description="Internal album ID")
    mbid: str | None = Field(None, description="MusicBrainz release-group ID")
    title: str = Field(..., description="Album title")
    artist_name: str | None = Field(None, description="Primary artist name")
    cover_url: str | None = Field(None, description="Cover art URL")
    release_year: int | None = Field(None, description="Year of first release")
    genres: str | None = Field(None, description="Comma-separated genre tags")

    # Separate scores (for debugging/ML replacement)
    final_score: float = Field(..., description="Combined recommendation score (0-1)")
    content_score: float = Field(0, description="Content-based similarity score (0-1)")
    collaborative_score: float = Field(0, description="Collaborative filtering score (0-1)")
    raw_scores: ContentScoreBreakdown | None = Field(
        None, description="Detailed content score breakdown (genre, artist, era)"
    )

    is_exploration: bool = Field(
        False, description="True if this is an exploration pick outside your usual taste"
    )
    reasons: list[str] = Field(
        default_factory=list, description="Human-readable explanation for this recommendation"
    )

    community_rating_count: int = Field(0, description="Number of community ratings")
    community_bayesian_score: float | None = Field(None, description="Community Bayesian score")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "album_id": "550e8400-e29b-41d4-a716-446655440005",
                    "mbid": "c5dfc4fe-c7b4-4b2e-ae1f-6b37f1e6b8d9",
                    "title": "In Rainbows",
                    "artist_name": "Radiohead",
                    "cover_url": "https://coverartarchive.org/...",
                    "release_year": 2007,
                    "genres": "alternative rock, art rock",
                    "final_score": 0.87,
                    "content_score": 0.82,
                    "collaborative_score": 0.91,
                    "raw_scores": {"genre": 0.85, "artist": 0.95, "era": 0.65},
                    "is_exploration": False,
                    "reasons": [
                        "Same artist as your #1 ranked album",
                        "High ratings from users with similar taste",
                    ],
                    "community_rating_count": 89,
                    "community_bayesian_score": 8.72,
                }
            ]
        },
    }


class RecommendationsResponse(BaseModel):
    """Response for the recommendations endpoint."""

    recommendations: list[RecommendedAlbum] = Field(..., description="List of recommended albums")
    count: int = Field(..., description="Number of recommendations returned")

    # User context
    user_ranked_albums: int = Field(..., description="Number of albums you have ranked")
    recommendation_type: str = Field(
        ..., description="Algorithm type: 'hybrid', 'content', 'collaborative', or 'discovery'"
    )

    # Algorithm transparency
    content_weight: float = Field(..., description="Weight given to content-based scoring (0-1)")
    collaborative_weight: float = Field(..., description="Weight given to collaborative filtering (0-1)")
    similar_users_found: int = Field(0, description="Number of users with similar taste found")
    exploration_count: int = Field(0, description="Number of exploration picks included")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "recommendations": [],
                    "count": 20,
                    "user_ranked_albums": 35,
                    "recommendation_type": "hybrid",
                    "content_weight": 0.65,
                    "collaborative_weight": 0.35,
                    "similar_users_found": 12,
                    "exploration_count": 3,
                }
            ]
        }
    }


class SimilarAlbum(BaseModel):
    """An album similar to a target album."""

    album_id: str = Field(..., description="Internal album ID")
    mbid: str | None = Field(None, description="MusicBrainz release-group ID")
    title: str = Field(..., description="Album title")
    artist_name: str | None = Field(None, description="Primary artist name")
    cover_url: str | None = Field(None, description="Cover art URL")
    release_year: int | None = Field(None, description="Year of first release")
    similarity_score: float = Field(..., description="Content similarity score (0-1, higher = more similar)")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "album_id": "550e8400-e29b-41d4-a716-446655440005",
                    "mbid": "c5dfc4fe-c7b4-4b2e-ae1f-6b37f1e6b8d9",
                    "title": "In Rainbows",
                    "artist_name": "Radiohead",
                    "cover_url": "https://coverartarchive.org/...",
                    "release_year": 2007,
                    "similarity_score": 0.89,
                }
            ]
        },
    }


class SimilarAlbumsResponse(BaseModel):
    """Response for similar albums endpoint."""

    target_album: dict = Field(..., description="The album you requested similar albums for")
    similar_albums: list[SimilarAlbum] = Field(..., description="Albums similar to the target")
    count: int = Field(..., description="Number of similar albums returned")
