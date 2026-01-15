"""Unit tests for Elo ranking service - core business logic."""

import math

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.album import Album
from backend.app.models.user import User
from backend.app.models.rating import UserAlbumElo, NumericRating, DEFAULT_ELO
from backend.app.services.elo import (
    expected_score,
    get_or_create_elo,
    get_user_average_rating,
    update_elo_from_rating,
    update_elo_from_comparison,
    K_PAIRWISE,
    K_RATING,
)


class TestExpectedScore:
    """Tests for Elo expected score calculation."""

    def test_equal_elo_returns_0_5(self):
        """Equal Elo ratings should give 0.5 expected score."""
        result = expected_score(1500, 1500)
        assert result == pytest.approx(0.5, abs=0.001)

    def test_higher_elo_higher_expected(self):
        """Higher Elo player should have higher expected score."""
        higher_expected = expected_score(1600, 1500)
        lower_expected = expected_score(1500, 1600)

        assert higher_expected > 0.5
        assert lower_expected < 0.5
        assert higher_expected + lower_expected == pytest.approx(1.0, abs=0.001)

    def test_400_point_difference(self):
        """400 point difference should give ~0.91 expected score."""
        # 400 points higher means 10^1 = 10x more likely to win
        # Expected = 1 / (1 + 10^(-1)) = 1 / 1.1 ≈ 0.909
        result = expected_score(1900, 1500)
        assert result == pytest.approx(0.909, abs=0.01)

    def test_symmetry(self):
        """Expected scores should sum to 1."""
        elo_a, elo_b = 1700, 1400
        exp_a = expected_score(elo_a, elo_b)
        exp_b = expected_score(elo_b, elo_a)

        assert exp_a + exp_b == pytest.approx(1.0, abs=0.001)

    def test_large_difference(self):
        """Large Elo difference should give near 1.0 expected."""
        result = expected_score(2000, 1000)
        assert result > 0.99


class TestGetOrCreateElo:
    """Tests for Elo record creation/retrieval."""

    @pytest.mark.asyncio
    async def test_creates_new_elo_record(
        self, db_session: AsyncSession, test_user: User, test_album: Album
    ):
        """Should create new Elo record with default values."""
        elo = await get_or_create_elo(db_session, test_user.id, test_album.id)

        assert elo is not None
        assert elo.user_id == test_user.id
        assert elo.album_id == test_album.id
        assert elo.elo == DEFAULT_ELO
        assert elo.rating_count == 0
        assert elo.comparison_count == 0

    @pytest.mark.asyncio
    async def test_returns_existing_elo_record(
        self, db_session: AsyncSession, test_user: User, test_album: Album
    ):
        """Should return existing Elo record if it exists."""
        # Create first record
        elo1 = await get_or_create_elo(db_session, test_user.id, test_album.id)
        elo1.elo = 1600  # Modify it
        await db_session.flush()

        # Get again - should return same record
        elo2 = await get_or_create_elo(db_session, test_user.id, test_album.id)

        assert elo2.id == elo1.id
        assert elo2.elo == 1600


class TestGetUserAverageRating:
    """Tests for user average rating calculation."""

    @pytest.mark.asyncio
    async def test_returns_default_with_no_ratings(
        self, db_session: AsyncSession, test_user: User
    ):
        """Should return 5.5 when user has no ratings."""
        avg = await get_user_average_rating(db_session, test_user.id)
        assert avg == 5.5

    @pytest.mark.asyncio
    async def test_calculates_average(
        self, db_session: AsyncSession, test_user: User, test_album: Album, test_album_2: Album
    ):
        """Should calculate correct average of ratings."""
        # Add two ratings: 8.0 and 6.0 -> avg = 7.0
        rating1 = NumericRating(
            user_id=test_user.id,
            album_id=test_album.id,
            value=8.0,
        )
        rating2 = NumericRating(
            user_id=test_user.id,
            album_id=test_album_2.id,
            value=6.0,
        )
        db_session.add_all([rating1, rating2])
        await db_session.flush()

        avg = await get_user_average_rating(db_session, test_user.id)
        assert avg == pytest.approx(7.0, abs=0.01)


class TestUpdateEloFromRating:
    """Tests for Elo updates from numeric ratings."""

    @pytest.mark.asyncio
    async def test_rating_above_average_increases_elo(
        self, db_session: AsyncSession, test_user: User, test_album: Album
    ):
        """Rating above user average should increase Elo."""
        # No existing ratings, so avg is 5.5
        # Rating of 8.0 is above average
        elo = await update_elo_from_rating(db_session, test_user.id, test_album.id, 8.0)

        assert elo.elo > DEFAULT_ELO
        assert elo.rating_count == 1

    @pytest.mark.asyncio
    async def test_rating_below_average_decreases_elo(
        self, db_session: AsyncSession, test_user: User, test_album: Album
    ):
        """Rating below user average should decrease Elo."""
        # No existing ratings, so avg is 5.5
        # Rating of 3.0 is below average
        elo = await update_elo_from_rating(db_session, test_user.id, test_album.id, 3.0)

        assert elo.elo < DEFAULT_ELO
        assert elo.rating_count == 1

    @pytest.mark.asyncio
    async def test_rating_at_average_minimal_change(
        self, db_session: AsyncSession, test_user: User, test_album: Album
    ):
        """Rating at user average should cause minimal Elo change."""
        # Default avg is 5.5
        elo = await update_elo_from_rating(db_session, test_user.id, test_album.id, 5.5)

        # Should be very close to default
        assert abs(elo.elo - DEFAULT_ELO) < K_RATING * 0.1
        assert elo.rating_count == 1

    @pytest.mark.asyncio
    async def test_uses_k_rating_factor(
        self, db_session: AsyncSession, test_user: User, test_album: Album
    ):
        """Elo change should be bounded by K_RATING."""
        # Maximum possible change is K_RATING (when actual=1, expected=0)
        elo = await update_elo_from_rating(db_session, test_user.id, test_album.id, 10.0)

        # Change should be less than K_RATING
        assert elo.elo - DEFAULT_ELO < K_RATING


class TestUpdateEloFromComparison:
    """Tests for Elo updates from pairwise comparisons."""

    @pytest.mark.asyncio
    async def test_winner_gains_elo(
        self, db_session: AsyncSession, test_user: User, test_album: Album, test_album_2: Album
    ):
        """Winner should gain Elo, loser should lose Elo."""
        elo_a, elo_b = await update_elo_from_comparison(
            db_session,
            test_user.id,
            test_album.id,
            test_album_2.id,
            winner_is_a=True,
        )

        assert elo_a.elo > DEFAULT_ELO
        assert elo_b.elo < DEFAULT_ELO
        assert elo_a.comparison_count == 1
        assert elo_b.comparison_count == 1

    @pytest.mark.asyncio
    async def test_loser_loses_elo(
        self, db_session: AsyncSession, test_user: User, test_album: Album, test_album_2: Album
    ):
        """When A loses, A's Elo should decrease."""
        elo_a, elo_b = await update_elo_from_comparison(
            db_session,
            test_user.id,
            test_album.id,
            test_album_2.id,
            winner_is_a=False,
        )

        assert elo_a.elo < DEFAULT_ELO
        assert elo_b.elo > DEFAULT_ELO

    @pytest.mark.asyncio
    async def test_tie_minimal_change(
        self, db_session: AsyncSession, test_user: User, test_album: Album, test_album_2: Album
    ):
        """Tie between equal Elo albums should result in minimal change."""
        elo_a, elo_b = await update_elo_from_comparison(
            db_session,
            test_user.id,
            test_album.id,
            test_album_2.id,
            winner_is_a=None,  # Tie
        )

        # Both started at 1500, tie gives actual=0.5, expected=0.5
        # Change = K * (0.5 - 0.5) = 0
        assert abs(elo_a.elo - DEFAULT_ELO) < 1
        assert abs(elo_b.elo - DEFAULT_ELO) < 1

    @pytest.mark.asyncio
    async def test_elo_sum_conserved(
        self, db_session: AsyncSession, test_user: User, test_album: Album, test_album_2: Album
    ):
        """Total Elo should be conserved after comparison."""
        initial_total = DEFAULT_ELO * 2

        elo_a, elo_b = await update_elo_from_comparison(
            db_session,
            test_user.id,
            test_album.id,
            test_album_2.id,
            winner_is_a=True,
        )

        final_total = elo_a.elo + elo_b.elo
        assert final_total == pytest.approx(initial_total, abs=0.01)

    @pytest.mark.asyncio
    async def test_uses_k_pairwise_factor(
        self, db_session: AsyncSession, test_user: User, test_album: Album, test_album_2: Album
    ):
        """Elo change should use K_PAIRWISE factor."""
        elo_a, elo_b = await update_elo_from_comparison(
            db_session,
            test_user.id,
            test_album.id,
            test_album_2.id,
            winner_is_a=True,
        )

        # When both start at 1500, expected is 0.5
        # Winner gets K * (1.0 - 0.5) = K * 0.5
        expected_change = K_PAIRWISE * 0.5
        actual_change = elo_a.elo - DEFAULT_ELO

        assert actual_change == pytest.approx(expected_change, abs=0.01)

    @pytest.mark.asyncio
    async def test_underdog_gains_more(
        self, db_session: AsyncSession, test_user: User, test_album: Album, test_album_2: Album
    ):
        """Underdog winning should gain more than favorite winning."""
        # First, make album_a the favorite
        elo_a_initial = await get_or_create_elo(db_session, test_user.id, test_album.id)
        elo_a_initial.elo = 1700
        await db_session.flush()

        elo_b_initial = await get_or_create_elo(db_session, test_user.id, test_album_2.id)
        # elo_b stays at default 1500

        # Underdog (B) beats favorite (A)
        elo_a, elo_b = await update_elo_from_comparison(
            db_session,
            test_user.id,
            test_album.id,
            test_album_2.id,
            winner_is_a=False,
        )

        # B was underdog, so B gains more than if favorite won
        b_gain = elo_b.elo - DEFAULT_ELO

        # Expected score for B was low (underdog), so gain is higher
        # Expected B = 1 / (1 + 10^(200/400)) ≈ 0.24
        # Gain = K * (1.0 - 0.24) = K * 0.76
        expected_b_gain = K_PAIRWISE * (1 - expected_score(DEFAULT_ELO, 1700))
        assert b_gain == pytest.approx(expected_b_gain, abs=0.1)


class TestEloKFactors:
    """Tests to verify K-factor configuration."""

    def test_k_pairwise_is_32(self):
        """Pairwise comparisons should use K=32 (strong signal)."""
        assert K_PAIRWISE == 32

    def test_k_rating_is_16(self):
        """Numeric ratings should use K=16 (weak signal)."""
        assert K_RATING == 16

    def test_k_pairwise_stronger_than_rating(self):
        """Pairwise K should be larger than rating K."""
        assert K_PAIRWISE > K_RATING


class TestDefaultElo:
    """Tests for default Elo value."""

    def test_default_elo_is_1500(self):
        """Default Elo should be 1500."""
        assert DEFAULT_ELO == 1500.0
