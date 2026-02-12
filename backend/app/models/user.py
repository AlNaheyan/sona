from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    numeric_ratings: Mapped[list["NumericRating"]] = relationship(
        "NumericRating", back_populates="user", cascade="all, delete-orphan"
    )
    pairwise_comparisons: Mapped[list["PairwiseComparison"]] = relationship(
        "PairwiseComparison", back_populates="user", cascade="all, delete-orphan"
    )
    album_elos: Mapped[list["UserAlbumElo"]] = relationship(
        "UserAlbumElo", back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"


# Forward references for type hints
from backend.app.models.rating import (
    NumericRating,
    PairwiseComparison,
    UserAlbumElo,
)
from backend.app.models.profile import UserProfile
