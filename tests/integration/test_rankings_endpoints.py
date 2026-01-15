"""Integration tests for rankings API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.album import Album
from backend.app.models.rating import UserAlbumElo, NumericRating, PairwiseComparison
from backend.app.models.user import User


class TestGetRankingsEndpoint:
    """Tests for GET /api/v1/rankings."""

    @pytest.mark.asyncio
    async def test_get_rankings_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Should return empty list when user has no rankings."""
        response = await client.get("/api/v1/rankings", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["rankings"] == []
        assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_get_rankings_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        test_album: Album,
        db_session: AsyncSession,
    ):
        """Should return user's rankings sorted by Elo."""
        # Create Elo record directly
        elo = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album.id,
            elo=1600.0,
            rating_count=1,
            comparison_count=0,
        )
        db_session.add(elo)
        await db_session.commit()

        response = await client.get("/api/v1/rankings", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["rankings"]) == 1
        assert data["rankings"][0]["elo"] == 1600.0
        assert data["rankings"][0]["rank"] == 1

    @pytest.mark.asyncio
    async def test_get_rankings_ordered_by_elo(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        test_album: Album,
        test_album_2: Album,
        db_session: AsyncSession,
    ):
        """Rankings should be ordered by Elo descending."""
        # Create two Elo records with different scores
        elo1 = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album.id,
            elo=1400.0,  # Lower
            rating_count=1,
            comparison_count=0,
        )
        elo2 = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album_2.id,
            elo=1700.0,  # Higher
            rating_count=1,
            comparison_count=0,
        )
        db_session.add_all([elo1, elo2])
        await db_session.commit()

        response = await client.get("/api/v1/rankings", headers=auth_headers)

        assert response.status_code == 200
        rankings = response.json()["rankings"]

        # Higher Elo should be first
        assert rankings[0]["elo"] == 1700.0
        assert rankings[0]["rank"] == 1
        assert rankings[1]["elo"] == 1400.0
        assert rankings[1]["rank"] == 2

    @pytest.mark.asyncio
    async def test_get_rankings_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        test_album: Album,
        test_album_2: Album,
        db_session: AsyncSession,
    ):
        """Should support pagination with limit and offset."""
        # Create two Elo records
        elo1 = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album.id,
            elo=1600.0,
            rating_count=1,
            comparison_count=0,
        )
        elo2 = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album_2.id,
            elo=1500.0,
            rating_count=1,
            comparison_count=0,
        )
        db_session.add_all([elo1, elo2])
        await db_session.commit()

        # Get with limit=1
        response = await client.get(
            "/api/v1/rankings",
            headers=auth_headers,
            params={"limit": 1},
        )

        assert response.status_code == 200
        assert len(response.json()["rankings"]) == 1

        # Get with offset=1
        response2 = await client.get(
            "/api/v1/rankings",
            headers=auth_headers,
            params={"limit": 1, "offset": 1},
        )

        assert response2.status_code == 200
        rankings = response2.json()["rankings"]
        assert len(rankings) == 1
        assert rankings[0]["rank"] == 2  # Second album

    @pytest.mark.asyncio
    async def test_get_rankings_without_auth(self, client: AsyncClient):
        """Should reject request without authentication."""
        response = await client.get("/api/v1/rankings")

        assert response.status_code in (401, 403)


class TestGetRankingStatsEndpoint:
    """Tests for GET /api/v1/rankings/stats."""

    @pytest.mark.asyncio
    async def test_get_stats_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Should return zero counts when user has no data."""
        response = await client.get("/api/v1/rankings/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["ranked_albums"] == 0
        assert data["numeric_ratings"] == 0
        assert data["pairwise_comparisons"] == 0
        assert data["average_elo"] == 1500.0  # Default

    @pytest.mark.asyncio
    async def test_get_stats_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        test_album: Album,
        test_album_2: Album,
        db_session: AsyncSession,
    ):
        """Should return correct counts."""
        # Create Elo records
        elo1 = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album.id,
            elo=1600.0,
            rating_count=1,
            comparison_count=1,
        )
        elo2 = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album_2.id,
            elo=1400.0,
            rating_count=1,
            comparison_count=1,
        )

        # Create a rating
        rating = NumericRating(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album.id,
            value=8.0,
        )

        # Create a comparison
        comparison = PairwiseComparison(
            id=str(uuid4()),
            user_id=test_user.id,
            album_a_id=test_album.id,
            album_b_id=test_album_2.id,
            winner_is_a=True,
        )

        db_session.add_all([elo1, elo2, rating, comparison])
        await db_session.commit()

        response = await client.get("/api/v1/rankings/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["ranked_albums"] == 2
        assert data["numeric_ratings"] == 1
        assert data["pairwise_comparisons"] == 1
        assert data["average_elo"] == 1500.0  # (1600 + 1400) / 2

    @pytest.mark.asyncio
    async def test_get_stats_elo_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        test_album: Album,
        test_album_2: Album,
        db_session: AsyncSession,
    ):
        """Should return correct Elo range."""
        elo1 = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album.id,
            elo=1800.0,  # Max
            rating_count=1,
            comparison_count=0,
        )
        elo2 = UserAlbumElo(
            id=str(uuid4()),
            user_id=test_user.id,
            album_id=test_album_2.id,
            elo=1200.0,  # Min
            rating_count=1,
            comparison_count=0,
        )
        db_session.add_all([elo1, elo2])
        await db_session.commit()

        response = await client.get("/api/v1/rankings/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["elo_range"]["min"] == 1200.0
        assert data["elo_range"]["max"] == 1800.0

    @pytest.mark.asyncio
    async def test_get_stats_without_auth(self, client: AsyncClient):
        """Should reject request without authentication."""
        response = await client.get("/api/v1/rankings/stats")

        assert response.status_code in (401, 403)


class TestRankingsAfterRating:
    """Tests verifying rankings update after rating."""

    @pytest.mark.asyncio
    async def test_ranking_appears_after_rating(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
    ):
        """Album should appear in rankings after being rated."""
        # Initially no rankings
        rankings_before = await client.get("/api/v1/rankings", headers=auth_headers)
        assert rankings_before.json()["count"] == 0

        # Rate album
        await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 8.0},
        )

        # Now should have one ranking
        rankings_after = await client.get("/api/v1/rankings", headers=auth_headers)
        assert rankings_after.json()["count"] == 1
        assert rankings_after.json()["rankings"][0]["album_title"] == test_album.title

    @pytest.mark.asyncio
    async def test_rankings_reflect_elo_from_ratings(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
        test_album_2: Album,
    ):
        """Higher-rated album should rank higher."""
        # Rate album 1 lower
        await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 3.0},  # Below avg
        )

        # Rate album 2 higher
        await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album_2.mbid, "value": 9.0},  # Above avg
        )

        # Check rankings
        response = await client.get("/api/v1/rankings", headers=auth_headers)
        rankings = response.json()["rankings"]

        # Album 2 (higher rating) should be ranked first
        assert rankings[0]["album_title"] == test_album_2.title
        assert rankings[1]["album_title"] == test_album.title
