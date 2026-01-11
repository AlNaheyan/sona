"""
Elo-based Personal Ranking Models

The ranking system uses Elo scores as the canonical personal ranking.
Two input types feed into Elo updates:
1. Numeric ratings (1-10) - weak Elo signal
2. Pairwise comparisons (A vs B) - strong Elo signal

Each input type triggers an Elo update on the UserAlbumElo record.
Rankings are determined by sorting albums by their Elo score.
"""

from sqlalchemy import String, Integer, Float, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, UUIDMixin


# Default Elo values
DEFAULT_ELO = 1500.0


class NumericRating(Base, UUIDMixin, TimestampMixin):
    """Direct 1-10 rating of an album (weak Elo signal)."""

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
    """Comparison between two albums (strong Elo signal)."""

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


class UserAlbumElo(Base, UUIDMixin, TimestampMixin):
    """
    Elo rating for a user-album pair.

    This is the canonical personal ranking value.
    Albums are ranked by sorting Elo scores in descending order.

    Elo updates come from:
    - Pairwise comparisons (K=32, strong signal)
    - Numeric ratings (K=16, weak signal, relative to user average)
    """

    __tablename__ = "user_album_elo"
    __table_args__ = (UniqueConstraint("user_id", "album_id", name="uq_elo_user_album"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    album_id: Mapped[str] = mapped_column(ForeignKey("albums.id"), nullable=False, index=True)

    # Elo score (canonical ranking value)
    elo: Mapped[float] = mapped_column(Float, nullable=False, default=DEFAULT_ELO)

    # Input counts (for transparency)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    comparison_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="album_elos")
    album: Mapped["Album"] = relationship("Album")

    def __repr__(self) -> str:
        return f"<UserAlbumElo user={self.user_id} album={self.album_id} elo={self.elo:.0f}>"


# Import User and Album for relationship resolution
from backend.app.models.user import User
from backend.app.models.album import Album
