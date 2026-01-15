"""Integration tests for ratings API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.album import Album
from backend.app.models.rating import NumericRating, UserAlbumElo
from backend.app.models.user import User


class TestCreateRatingEndpoint:
    """Tests for POST /api/v1/ratings."""

    @pytest.mark.asyncio
    async def test_rate_album_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
    ):
        """Should create a rating and return rating data."""
        response = await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={
                "mbid": test_album.mbid,
                "value": 8.5,
                "notes": "Great album!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["album_id"] == test_album.id
        assert data["album_title"] == test_album.title
        assert data["value"] == 8.5
        assert data["notes"] == "Great album!"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_rate_album_creates_elo_record(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Rating should create/update Elo record."""
        response = await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={
                "mbid": test_album.mbid,
                "value": 9.0,
            },
        )
        assert response.status_code == 200

        # Check Elo record was created
        result = await db_session.execute(
            select(UserAlbumElo).where(
                UserAlbumElo.user_id == test_user.id,
                UserAlbumElo.album_id == test_album.id,
            )
        )
        elo = result.scalar_one_or_none()

        assert elo is not None
        assert elo.rating_count == 1

    @pytest.mark.asyncio
    async def test_rate_album_updates_existing(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
    ):
        """Rating same album again should update existing rating."""
        # First rating
        response1 = await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 7.0},
        )
        assert response1.status_code == 200
        rating_id = response1.json()["id"]

        # Second rating (update)
        response2 = await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 9.0},
        )
        assert response2.status_code == 200

        # Should be same rating ID (updated, not new)
        assert response2.json()["id"] == rating_id
        assert response2.json()["value"] == 9.0

    @pytest.mark.asyncio
    async def test_rate_album_without_auth(
        self,
        client: AsyncClient,
        test_album: Album,
    ):
        """Should reject rating without authentication."""
        response = await client.post(
            "/api/v1/ratings",
            json={"mbid": test_album.mbid, "value": 8.0},
        )

        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_rate_album_invalid_value_too_high(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
    ):
        """Should reject rating value above 10."""
        response = await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 11.0},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rate_album_invalid_value_too_low(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
    ):
        """Should reject rating value below 1."""
        response = await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 0.5},
        )

        assert response.status_code == 422


class TestGetRatingsEndpoint:
    """Tests for GET /api/v1/ratings."""

    @pytest.mark.asyncio
    async def test_get_ratings_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Should return empty list when user has no ratings."""
        response = await client.get("/api/v1/ratings", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["ratings"] == []
        assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_get_ratings_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
    ):
        """Should return user's ratings."""
        # Create a rating first
        await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 8.0},
        )

        response = await client.get("/api/v1/ratings", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["ratings"]) == 1
        assert data["count"] == 1
        assert data["ratings"][0]["value"] == 8.0

    @pytest.mark.asyncio
    async def test_get_ratings_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
        test_album_2: Album,
    ):
        """Should support pagination."""
        # Create two ratings
        await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 8.0},
        )
        await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album_2.mbid, "value": 7.0},
        )

        # Get with limit=1
        response = await client.get(
            "/api/v1/ratings",
            headers=auth_headers,
            params={"limit": 1},
        )

        assert response.status_code == 200
        assert len(response.json()["ratings"]) == 1

    @pytest.mark.asyncio
    async def test_get_ratings_without_auth(self, client: AsyncClient):
        """Should reject request without authentication."""
        response = await client.get("/api/v1/ratings")

        assert response.status_code in (401, 403)


class TestDeleteRatingEndpoint:
    """Tests for DELETE /api/v1/ratings/{rating_id}."""

    @pytest.mark.asyncio
    async def test_delete_rating_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
    ):
        """Should delete rating and return success."""
        # Create rating
        create_response = await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 8.0},
        )
        rating_id = create_response.json()["id"]

        # Delete it
        delete_response = await client.delete(
            f"/api/v1/ratings/{rating_id}",
            headers=auth_headers,
        )

        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"

        # Verify it's gone
        list_response = await client.get("/api/v1/ratings", headers=auth_headers)
        assert list_response.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_delete_rating_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Should return 404 for non-existent rating."""
        response = await client.delete(
            "/api/v1/ratings/nonexistent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_user_rating(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user_2: User,
        test_album: Album,
        db_session: AsyncSession,
    ):
        """Should not be able to delete another user's rating."""
        # Create rating for user 2 directly in DB
        from uuid import uuid4

        rating = NumericRating(
            id=str(uuid4()),
            user_id=test_user_2.id,
            album_id=test_album.id,
            value=7.0,
        )
        db_session.add(rating)
        await db_session.commit()

        # Try to delete as user 1
        response = await client.delete(
            f"/api/v1/ratings/{rating.id}",
            headers=auth_headers,  # This is user 1's token
        )

        assert response.status_code == 404  # Not found because it's not user 1's rating

    @pytest.mark.asyncio
    async def test_delete_rating_without_auth(
        self,
        client: AsyncClient,
        test_rating: NumericRating,
    ):
        """Should reject deletion without authentication."""
        response = await client.delete(f"/api/v1/ratings/{test_rating.id}")

        assert response.status_code in (401, 403)


class TestRatingEloIntegration:
    """Tests verifying Elo updates from ratings via rankings API."""

    @pytest.mark.asyncio
    async def test_rating_creates_ranking_entry(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
    ):
        """Rating an album should create a ranking entry."""
        # Initially no rankings
        rankings_before = await client.get("/api/v1/rankings", headers=auth_headers)
        assert rankings_before.json()["count"] == 0

        # Rate album
        response = await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 8.0},
        )
        assert response.status_code == 200

        # Should now have a ranking
        rankings_after = await client.get("/api/v1/rankings", headers=auth_headers)
        assert rankings_after.json()["count"] == 1
        assert rankings_after.json()["rankings"][0]["rating_count"] == 1

    @pytest.mark.asyncio
    async def test_high_vs_low_rating_elo_ordering(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_album: Album,
        test_album_2: Album,
    ):
        """Higher rated album should have higher Elo than lower rated album."""
        # Rate first album low
        await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album.mbid, "value": 2.0},
        )

        # Rate second album high
        await client.post(
            "/api/v1/ratings",
            headers=auth_headers,
            json={"mbid": test_album_2.mbid, "value": 9.0},
        )

        # Check rankings - higher rated should be first
        rankings = await client.get("/api/v1/rankings", headers=auth_headers)
        data = rankings.json()["rankings"]

        assert len(data) == 2
        # Album 2 (high rating) should rank first (higher Elo)
        assert data[0]["album_title"] == test_album_2.title
        assert data[1]["album_title"] == test_album.title
        assert data[0]["elo"] > data[1]["elo"]
