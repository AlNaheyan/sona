from sqlalchemy import String, Integer, Float, ForeignKey, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, UUIDMixin


# Many-to-many relationship between albums and artists
album_artists = Table(
    "album_artists",
    Base.metadata,
    Column("album_id", UUID(as_uuid=False), ForeignKey("albums.id"), primary_key=True),
    Column("artist_id", UUID(as_uuid=False), ForeignKey("artists.id"), primary_key=True),
)


class Artist(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artists"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mbid: Mapped[str | None] = mapped_column(String(36), unique=True, nullable=True)  # MusicBrainz ID

    # Genre tags (comma-separated for simplicity; could normalize)
    genres: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    albums: Mapped[list["Album"]] = relationship(
        "Album", secondary=album_artists, back_populates="artists"
    )

    def __repr__(self) -> str:
        return f"<Artist {self.name}>"


class Album(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "albums"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mbid: Mapped[str | None] = mapped_column(String(36), unique=True, nullable=True)  # MusicBrainz ID
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Genre tags (comma-separated)
    genres: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Community stats (denormalized for performance)
    # Bayesian weighted score: (v/(v+m))*R + (m/(v+m))*C
    # where R=album avg, v=vote count, m=min votes, C=global avg
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_sum: Mapped[float] = mapped_column(Float, default=0.0)  # Sum of all ratings
    bayesian_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)

    # Relationships
    artists: Mapped[list["Artist"]] = relationship(
        "Artist", secondary=album_artists, back_populates="albums"
    )

    def __repr__(self) -> str:
        return f"<Album {self.title}>"
