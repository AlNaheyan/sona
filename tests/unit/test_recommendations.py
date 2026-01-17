"""Tests for the recommendation service."""

import pytest
from uuid import uuid4

from backend.app.services.recommendations import (
    RecommendationConfig,
    ContentScorer,
    ContentScore,
    parse_genres,
    extract_genres,
    generate_reasons,
)
from backend.app.models.album import Album, Artist


class TestParseGenres:
    """Tests for the parse_genres utility function."""

    def test_parse_empty_string(self):
        """Empty string returns empty set."""
        assert parse_genres("") == set()

    def test_parse_none(self):
        """None returns empty set."""
        assert parse_genres(None) == set()

    def test_parse_single_genre(self):
        """Single genre is parsed correctly."""
        assert parse_genres("Rock") == {"rock"}

    def test_parse_multiple_genres(self):
        """Multiple genres are parsed and lowercased."""
        result = parse_genres("Rock, Jazz, Electronic")
        assert result == {"rock", "jazz", "electronic"}

    def test_parse_handles_whitespace(self):
        """Extra whitespace is stripped."""
        result = parse_genres("  Rock  ,  Jazz  ")
        assert result == {"rock", "jazz"}

    def test_parse_empty_segments_ignored(self):
        """Empty segments from consecutive commas are ignored."""
        result = parse_genres("Rock,,Jazz")
        assert result == {"rock", "jazz"}


class TestExtractGenres:
    """Tests for extract_genres utility function."""

    def test_extract_from_empty_list(self):
        """Empty album list returns empty set."""
        assert extract_genres([]) == set()

    def test_extract_from_albums(self):
        """Extracts and combines genres from multiple albums."""
        albums = [
            Album(id=str(uuid4()), title="A", genres="Rock, Jazz"),
            Album(id=str(uuid4()), title="B", genres="Electronic, Jazz"),
        ]
        result = extract_genres(albums)
        assert result == {"rock", "jazz", "electronic"}

    def test_extract_with_none_genres(self):
        """Albums with None genres are handled."""
        albums = [
            Album(id=str(uuid4()), title="A", genres="Rock"),
            Album(id=str(uuid4()), title="B", genres=None),
        ]
        result = extract_genres(albums)
        assert result == {"rock"}


class TestRecommendationConfig:
    """Tests for RecommendationConfig."""

    def test_default_values(self):
        """Config has sensible defaults."""
        config = RecommendationConfig()
        assert config.min_albums_for_hybrid == 5
        assert config.max_similar_users == 20
        assert config.exploration_ratio == 0.15

    def test_compute_weights_new_user(self):
        """New users (<10 albums) get 90% content, 10% collab."""
        content, collab = RecommendationConfig.compute_weights(5)
        assert content == 0.9
        assert collab == 0.1

    def test_compute_weights_growing_user(self):
        """Users with 10-30 albums get interpolated weights."""
        content, collab = RecommendationConfig.compute_weights(20)
        # At 20 albums: t = 10/20 = 0.5, content = 0.9 - 0.15 = 0.75
        assert 0.7 <= content <= 0.8
        assert abs(content + collab - 1.0) < 0.01

    def test_compute_weights_experienced_user(self):
        """Experienced users (30+ albums) get 60% content, 40% collab."""
        content, collab = RecommendationConfig.compute_weights(50)
        assert content == 0.6
        assert collab == 0.4

    def test_weights_always_sum_to_one(self):
        """Content + collab weights always sum to 1."""
        for album_count in [1, 5, 10, 15, 20, 25, 30, 50, 100]:
            content, collab = RecommendationConfig.compute_weights(album_count)
            assert abs(content + collab - 1.0) < 0.001


class TestContentScorer:
    """Tests for the ContentScorer class."""

    def test_score_empty_refs(self):
        """Scoring with no reference albums returns zero scores."""
        scorer = ContentScorer()
        candidate = Album(id=str(uuid4()), title="Test", genres="Rock")
        score = scorer.score(candidate, [])
        assert score.final == 0
        assert score.genre == 0
        assert score.artist == 0
        assert score.era == 0

    def test_genre_similarity_exact_match(self):
        """Albums with identical genres have high similarity."""
        scorer = ContentScorer()
        candidate = Album(id=str(uuid4()), title="A", genres="Rock, Jazz")
        ref = Album(id=str(uuid4()), title="B", genres="Rock, Jazz")
        score = scorer.score(candidate, [ref])
        assert score.genre == 1.0

    def test_genre_similarity_partial_match(self):
        """Albums with partial genre overlap have moderate similarity."""
        scorer = ContentScorer()
        candidate = Album(id=str(uuid4()), title="A", genres="Rock, Jazz")
        ref = Album(id=str(uuid4()), title="B", genres="Rock, Electronic")
        score = scorer.score(candidate, [ref])
        # Jaccard: intersection=1 (rock), union=3 (rock, jazz, electronic) = 0.33
        assert 0.3 <= score.genre <= 0.4

    def test_genre_similarity_no_match(self):
        """Albums with no genre overlap have zero similarity."""
        scorer = ContentScorer()
        candidate = Album(id=str(uuid4()), title="A", genres="Classical")
        ref = Album(id=str(uuid4()), title="B", genres="Rock, Jazz")
        score = scorer.score(candidate, [ref])
        assert score.genre == 0.0

    def test_artist_similarity_same_artist(self):
        """Albums with same artist have 1.0 artist similarity."""
        scorer = ContentScorer()
        artist = Artist(id=str(uuid4()), name="Artist")

        candidate = Album(id=str(uuid4()), title="A")
        candidate.artists = [artist]

        ref = Album(id=str(uuid4()), title="B")
        ref.artists = [artist]

        score = scorer.score(candidate, [ref])
        assert score.artist == 1.0

    def test_artist_similarity_different_artist(self):
        """Albums with different artists have 0.0 artist similarity."""
        scorer = ContentScorer()

        candidate = Album(id=str(uuid4()), title="A")
        candidate.artists = [Artist(id=str(uuid4()), name="Artist 1")]

        ref = Album(id=str(uuid4()), title="B")
        ref.artists = [Artist(id=str(uuid4()), name="Artist 2")]

        score = scorer.score(candidate, [ref])
        assert score.artist == 0.0

    def test_era_similarity_same_year(self):
        """Albums from same year have high era similarity."""
        scorer = ContentScorer()
        candidate = Album(id=str(uuid4()), title="A", release_year=2020)
        ref = Album(id=str(uuid4()), title="B", release_year=2020)
        score = scorer.score(candidate, [ref])
        assert score.era == 1.0

    def test_era_similarity_same_decade(self):
        """Albums from same decade have high era similarity."""
        scorer = ContentScorer()
        candidate = Album(id=str(uuid4()), title="A", release_year=2020)
        ref = Album(id=str(uuid4()), title="B", release_year=2025)
        score = scorer.score(candidate, [ref])
        # 5 years apart: 1.0 - 5/40 = 0.875
        assert 0.8 <= score.era <= 0.9

    def test_era_similarity_distant_years(self):
        """Albums 20 years apart have moderate era similarity."""
        scorer = ContentScorer()
        candidate = Album(id=str(uuid4()), title="A", release_year=2000)
        ref = Album(id=str(uuid4()), title="B", release_year=2020)
        score = scorer.score(candidate, [ref])
        # 20 years apart: 1.0 - 20/40 = 0.5
        assert 0.4 <= score.era <= 0.6

    def test_artist_cap_limits_influence(self):
        """Artist influence is capped at 25% of final score."""
        scorer = ContentScorer(artist_cap=0.25)
        artist = Artist(id=str(uuid4()), name="Artist")

        # No genre similarity, only artist match
        candidate = Album(id=str(uuid4()), title="A", genres="ClassicalOnly")
        candidate.artists = [artist]

        ref = Album(id=str(uuid4()), title="B", genres="JazzOnly")
        ref.artists = [artist]

        score = scorer.score(candidate, [ref])
        # Even with full artist match, capped at 0.25
        assert score.final <= 0.35  # Allow some era contribution

    def test_final_score_capped_at_one(self):
        """Final score never exceeds 1.0."""
        scorer = ContentScorer()
        artist = Artist(id=str(uuid4()), name="Artist")

        # Perfect match on everything
        candidate = Album(
            id=str(uuid4()), title="A", genres="Rock, Jazz", release_year=2020
        )
        candidate.artists = [artist]

        ref = Album(
            id=str(uuid4()), title="B", genres="Rock, Jazz", release_year=2020
        )
        ref.artists = [artist]

        score = scorer.score(candidate, [ref])
        assert score.final <= 1.0


class TestGenerateReasons:
    """Tests for the generate_reasons function."""

    def test_same_artist_reason(self):
        """Generates reason when album shares artist."""
        artist = Artist(id=str(uuid4()), name="Artist")

        album = Album(id=str(uuid4()), title="New Album")
        album.artists = [artist]

        top_album = Album(id=str(uuid4()), title="Favorite Album")
        top_album.artists = [artist]

        reasons = generate_reasons(album, [top_album], 0.0)
        assert any("Same artist" in r for r in reasons)

    def test_similar_genre_reason(self):
        """Generates reason when album shares genres."""
        album = Album(id=str(uuid4()), title="New", genres="Rock, Jazz, Blues")
        album.artists = []

        top_album = Album(id=str(uuid4()), title="Fave", genres="Rock, Jazz, Pop")
        top_album.artists = []

        reasons = generate_reasons(album, [top_album], 0.0)
        assert any("Similar genres" in r for r in reasons)

    def test_collaborative_reason(self):
        """Generates reason when collaborative score is high."""
        album = Album(id=str(uuid4()), title="New")
        album.artists = []

        reasons = generate_reasons(album, [], 0.5)
        assert any("similar taste" in r for r in reasons)

    def test_era_reason(self):
        """Generates reason when album is from same era."""
        album = Album(id=str(uuid4()), title="New", release_year=2020)
        album.artists = []

        top_album = Album(id=str(uuid4()), title="Fave", release_year=2022)
        top_album.artists = []

        reasons = generate_reasons(album, [top_album], 0.0)
        assert any("same era" in r for r in reasons)

    def test_max_three_reasons(self):
        """Never returns more than 3 reasons."""
        artist = Artist(id=str(uuid4()), name="Artist")

        album = Album(
            id=str(uuid4()),
            title="New",
            genres="Rock, Jazz, Blues",
            release_year=2020
        )
        album.artists = [artist]

        top_album = Album(
            id=str(uuid4()),
            title="Fave",
            genres="Rock, Jazz, Pop",
            release_year=2022
        )
        top_album.artists = [artist]

        reasons = generate_reasons(album, [top_album], 0.5)
        assert len(reasons) <= 3
