"""Integration tests for comparison suggestions endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from backend.app.models.album import Album, Artist
from backend.app.models.rating import UserAlbumElo, PairwiseComparison
from backend.app.models.user import User
from backend.app.services.comparison_suggestions import (
    get_comparison_suggestions,
    get_comparison_stats,
    SuggestionConfig,
)


@pytest.fixture
async def albums_with_elo(
    db_session: AsyncSession,
    test_user: User,
    test_artist: Artist,
) -> list[Album]:
    """Create multiple albums with Elo records for the user."""
    albums = []
    for i in range(5):
        album = Album(
            id=str(uuid4()),
            title=f"Album {i + 1}",
            mbid=str(uuid4()),
            release_year=2020 + i,
            genres=f"Genre{i % 3}",
        )
        album.artists.append(test_artist)
        db_session.add(album)
        albums.append(album)

    await db_session.commit()

    # Create Elo records with varying scores
    for i, album in enumerate(albums):
        elo = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=album.id,
            elo=1500 + (i * 20),  # 1500, 1520, 1540, 1560, 1580
            rating_count=1,
            comparison_count=i,  # 0, 1, 2, 3, 4
        )
        db_session.add(elo)

    await db_session.commit()

    for album in albums:
        await db_session.refresh(album)

    return albums


class TestGetSuggestionsEndpoint:
    """Tests for GET /comparisons/suggestions endpoint."""

    @pytest.mark.asyncio
    async def test_suggestions_without_auth(self, client: AsyncClient):
        """Suggestions endpoint requires authentication."""
        response = await client.get("/api/v1/comparisons/suggestions")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_suggestions_empty_for_new_user(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """New user with no albums gets empty suggestions."""
        response = await client.get(
            "/api/v1/comparisons/suggestions",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == []
        assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_suggestions_with_albums(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        albums_with_elo: list[Album],
    ):
        """User with albums gets comparison suggestions."""
        response = await client.get(
            "/api/v1/comparisons/suggestions",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert len(data["suggestions"]) <= 5

        # Check suggestion structure
        if data["suggestions"]:
            suggestion = data["suggestions"][0]
            assert "album_a" in suggestion
            assert "album_b" in suggestion
            assert "reason" in suggestion
            assert "priority_score" in suggestion

            # Check album structure
            assert "id" in suggestion["album_a"]
            assert "title" in suggestion["album_a"]
            assert "elo" in suggestion["album_a"]

    @pytest.mark.asyncio
    async def test_suggestions_limit_parameter(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        albums_with_elo: list[Album],
    ):
        """Limit parameter controls number of suggestions."""
        response = await client.get(
            "/api/v1/comparisons/suggestions?limit=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] <= 2


class TestGetStatsEndpoint:
    """Tests for GET /comparisons/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_without_auth(self, client: AsyncClient):
        """Stats endpoint requires authentication."""
        response = await client.get("/api/v1/comparisons/stats")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_stats_empty_for_new_user(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """New user gets zero stats."""
        response = await client.get(
            "/api/v1/comparisons/stats",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ranked_albums"] == 0
        assert data["total_comparisons"] == 0
        assert data["unique_pairs_compared"] == 0
        assert data["possible_pairs"] == 0
        assert data["coverage_percentage"] == 0

    @pytest.mark.asyncio
    async def test_stats_with_albums(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        albums_with_elo: list[Album],
    ):
        """User with albums gets accurate stats."""
        response = await client.get(
            "/api/v1/comparisons/stats",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ranked_albums"] == 5
        # 5 albums = 10 possible pairs (5*4/2)
        assert data["possible_pairs"] == 10


class TestSuggestionService:
    """Tests for the comparison suggestion service functions."""

    @pytest.mark.asyncio
    async def test_suggestions_prioritize_close_elo(
        self,
        db_session: AsyncSession,
        test_user: User,
        albums_with_elo: list[Album],
    ):
        """Albums with close Elo scores should be suggested."""
        suggestions = await get_comparison_suggestions(
            db_session, test_user.id
        )

        # Should have suggestions since we have 5 albums
        assert len(suggestions) > 0

        # Top suggestions should have priority scores > 0
        assert all(s.priority_score > 0 for s in suggestions)

    @pytest.mark.asyncio
    async def test_suggestions_with_custom_config(
        self,
        db_session: AsyncSession,
        test_user: User,
        albums_with_elo: list[Album],
    ):
        """Custom config should be respected."""
        config = SuggestionConfig(max_suggestions=2)
        suggestions = await get_comparison_suggestions(
            db_session, test_user.id, config
        )

        assert len(suggestions) <= 2

    @pytest.mark.asyncio
    async def test_stats_coverage_calculation(
        self,
        db_session: AsyncSession,
        test_user: User,
        albums_with_elo: list[Album],
    ):
        """Coverage percentage should be calculated correctly."""
        stats = await get_comparison_stats(db_session, test_user.id)

        assert stats["ranked_albums"] == 5
        assert stats["possible_pairs"] == 10
        # No comparisons made yet
        assert stats["unique_pairs_compared"] == 0
        assert stats["coverage_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_stats_with_comparisons(
        self,
        db_session: AsyncSession,
        test_user: User,
        albums_with_elo: list[Album],
    ):
        """Coverage should update after comparisons."""
        # Add a comparison
        comparison = PairwiseComparison(
            id=str(uuid4()),
            user_id=test_user.id,
            album_a_id=albums_with_elo[0].id,
            album_b_id=albums_with_elo[1].id,
            winner_is_a=True,
        )
        db_session.add(comparison)
        await db_session.commit()

        stats = await get_comparison_stats(db_session, test_user.id)

        assert stats["total_comparisons"] == 1
        assert stats["unique_pairs_compared"] == 1
        assert stats["coverage_percentage"] == 10.0  # 1/10 = 10%
