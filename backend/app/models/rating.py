"""
CWPR (Confidence-Weighted Preference Ranking) Rating Models

Supports three input types that are unified into a preference score:
1. Numeric ratings (1-10)
2. Pairwise comparisons (A vs B)
3. Tier placements (S, A, B, C, D, F)

Each input type updates the UserAlbumPreference which stores:
- mu (μ): mean preference score
- sigma (σ): uncertainty/confidence
- score: μ - λσ (the ranking score)
"""

from enum import Enum

from sqlalchemy import String, Integer, Float, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, UUIDMixin


class Tier(str, Enum):
    S = "S"  # 10.0
    A = "A"  # 8.0
    B = "B"  # 6.0
    C = "C"  # 4.0
    D = "D"  # 2.0
    F = "F"  # 0.0

    def to_numeric(self) -> float:
        mapping = {"S": 10.0, "A": 8.0, "B": 6.0, "C": 4.0, "D": 2.0, "F": 0.0}
        return mapping[self.value]


class NumericRating(Base, UUIDMixin, TimestampMixin):
    """Direct 1-10 rating of an album."""

    __tablename__ = "numeric_ratings"
    __table_args__ = (UniqueConstraint("user_id", "album_id", name="uq_numeric_rating_user_album"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    album_id: Mapped[str] = mapped_column(ForeignKey("albums.id"), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)  # 1.0 to 10.0

    # Optional context capture
    mood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="numeric_ratings")
    album: Mapped["Album"] = relationship("Album")

    def __repr__(self) -> str:
        return f"<NumericRating user={self.user_id} album={self.album_id} value={self.value}>"


class PairwiseComparison(Base, UUIDMixin, TimestampMixin):
    """Comparison between two albums: which does the user prefer?"""

    __tablename__ = "pairwise_comparisons"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    album_a_id: Mapped[str] = mapped_column(ForeignKey("albums.id"), nullable=False)
    album_b_id: Mapped[str] = mapped_column(ForeignKey("albums.id"), nullable=False)

    # True = album_a wins, False = album_b wins, None = tie/skip
    winner_is_a: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="pairwise_comparisons")
    album_a: Mapped["Album"] = relationship("Album", foreign_keys=[album_a_id])
    album_b: Mapped["Album"] = relationship("Album", foreign_keys=[album_b_id])

    def __repr__(self) -> str:
        winner = "A" if self.winner_is_a else "B" if self.winner_is_a is False else "tie"
        return f"<PairwiseComparison {self.album_a_id} vs {self.album_b_id} winner={winner}>"


class TierPlacement(Base, UUIDMixin, TimestampMixin):
    """Placement of an album in a tier list."""

    __tablename__ = "tier_placements"
    __table_args__ = (UniqueConstraint("user_id", "album_id", name="uq_tier_placement_user_album"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    album_id: Mapped[str] = mapped_column(ForeignKey("albums.id"), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(1), nullable=False)  # S, A, B, C, D, F

    # Position within tier (for ordering)
    position: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tier_placements")
    album: Mapped["Album"] = relationship("Album")

    def __repr__(self) -> str:
        return f"<TierPlacement user={self.user_id} album={self.album_id} tier={self.tier}>"


class UserAlbumPreference(Base, UUIDMixin, TimestampMixin):
    """
    Computed CWPR preference for a user-album pair.

    This aggregates all input types (numeric, pairwise, tier) into:
    - mu (μ): mean preference estimate
    - sigma (σ): uncertainty in the estimate
    - score: μ - λσ (used for ranking)

    Updated whenever any rating input changes.
    """

    __tablename__ = "user_album_preferences"
    __table_args__ = (UniqueConstraint("user_id", "album_id", name="uq_preference_user_album"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    album_id: Mapped[str] = mapped_column(ForeignKey("albums.id"), nullable=False, index=True)

    # CWPR values
    mu: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)  # Mean preference
    sigma: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)  # Uncertainty
    score: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)  # mu - lambda*sigma

    # Input counts (for debugging/transparency)
    numeric_count: Mapped[int] = mapped_column(Integer, default=0)
    pairwise_count: Mapped[int] = mapped_column(Integer, default=0)
    tier_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")
    album: Mapped["Album"] = relationship("Album")

    def __repr__(self) -> str:
        return f"<UserAlbumPreference user={self.user_id} album={self.album_id} μ={self.mu:.2f} σ={self.sigma:.2f}>"


# Import User and Album for relationship resolution
from backend.app.models.user import User
from backend.app.models.album import Album
