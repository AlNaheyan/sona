"""Pytest fixtures for RateMyAlbum tests."""

import asyncio
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.database import get_db
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.user import User
from backend.app.models.album import Album, Artist
from backend.app.models.rating import NumericRating, PairwiseComparison, UserAlbumElo
from backend.app.services.auth import hash_password, create_access_token


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with rollback after each test."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with database override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=str(uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_2(db_session: AsyncSession) -> User:
    """Create a second test user for comparison tests."""
    user = User(
        id=str(uuid4()),
        email="test2@example.com",
        username="testuser2",
        hashed_password=hash_password("testpassword456"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Create authorization headers for the test user."""
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_artist(db_session: AsyncSession) -> Artist:
    """Create a test artist."""
    artist = Artist(
        id=str(uuid4()),
        name="Test Artist",
        mbid=str(uuid4()),
    )
    db_session.add(artist)
    await db_session.commit()
    await db_session.refresh(artist)
    return artist


@pytest_asyncio.fixture
async def test_album(db_session: AsyncSession, test_artist: Artist) -> Album:
    """Create a test album with artist."""
    album = Album(
        id=str(uuid4()),
        title="Test Album",
        mbid=str(uuid4()),
        release_year=2020,
        cover_url="https://example.com/cover.jpg",
        rating_count=0,
        rating_sum=0.0,
    )
    album.artists.append(test_artist)
    db_session.add(album)
    await db_session.commit()
    await db_session.refresh(album)
    return album


@pytest_asyncio.fixture
async def test_album_2(db_session: AsyncSession, test_artist: Artist) -> Album:
    """Create a second test album for comparison tests."""
    album = Album(
        id=str(uuid4()),
        title="Test Album 2",
        mbid=str(uuid4()),
        release_year=2021,
        cover_url="https://example.com/cover2.jpg",
        rating_count=0,
        rating_sum=0.0,
    )
    album.artists.append(test_artist)
    db_session.add(album)
    await db_session.commit()
    await db_session.refresh(album)
    return album


@pytest_asyncio.fixture
async def test_rating(
    db_session: AsyncSession,
    test_user: User,
    test_album: Album,
) -> NumericRating:
    """Create a test rating."""
    rating = NumericRating(
        id=str(uuid4()),
        user_id=test_user.id,
        album_id=test_album.id,
        value=8.0,
    )
    db_session.add(rating)
    await db_session.commit()
    await db_session.refresh(rating)
    return rating
