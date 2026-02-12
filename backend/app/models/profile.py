from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, UUIDMixin


class UserProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    spotify_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    favorite_genres: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile {self.display_name}>"


# Forward reference
from backend.app.models.user import User
