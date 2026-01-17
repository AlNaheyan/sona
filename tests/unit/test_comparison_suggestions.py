"""Unit tests for comparison suggestion service."""

import pytest
from uuid import uuid4

from backend.app.services.comparison_suggestions import SuggestionConfig


class TestSuggestionConfig:
    """Tests for SuggestionConfig defaults and settings."""

    def test_default_values(self):
        """Config has sensible defaults."""
        config = SuggestionConfig()
        assert config.max_suggestions == 5
        assert config.close_elo_threshold == 100
        assert config.min_albums_for_suggestions == 3

    def test_close_elo_weight_highest(self):
        """Close Elo weight should be highest priority."""
        config = SuggestionConfig()
        assert config.close_elo_weight > config.uncompared_weight
        assert config.close_elo_weight > config.low_comparison_weight
        assert config.close_elo_weight > config.exploration_weight

    def test_exploration_weight_lowest(self):
        """Exploration weight should be lowest priority."""
        config = SuggestionConfig()
        assert config.exploration_weight < config.close_elo_weight
        assert config.exploration_weight < config.uncompared_weight
        assert config.exploration_weight < config.low_comparison_weight

    def test_custom_values(self):
        """Config accepts custom values."""
        config = SuggestionConfig(
            max_suggestions=10,
            close_elo_threshold=50,
            min_albums_for_suggestions=5,
        )
        assert config.max_suggestions == 10
        assert config.close_elo_threshold == 50
        assert config.min_albums_for_suggestions == 5
