from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, UUIDMixin


class WantToListen(Base, UUIDMixin, TimestampMixin):
    """Album saved to a user's 'Want to Listen' list."""

    __tablename__ = "want_to_listen"
    __table_args__ = (
        UniqueConstraint("user_id", "album_id", name="uq_want_to_listen_user_album"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    album_id: Mapped[str] = mapped_column(
        ForeignKey("albums.id", ondelete="CASCADE"), nullable=False, index=True
    )
    album_mbid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="want_to_listen")
    album: Mapped["Album"] = relationship("Album")

    def __repr__(self) -> str:
        return f"<WantToListen user={self.user_id} album={self.album_id}>"


# Import for relationship resolution
from backend.app.models.user import User
from backend.app.models.album import Album
