"""
Personalized Recommendation Service

Hybrid recommendation system combining:
1. Content-based filtering (genre, artist, era similarity)
2. Collaborative filtering (similar users' preferences)

Key design principles:
- Dynamic weights based on user history size
- Capped artist influence (max 25%)
- Candidate pruning before scoring
- Graceful fallback for weak collaborative signals
- Exploration injection (15% outside comfort zone)
- Modular scorers for future ML replacement
"""

import random
from dataclasses import dataclass, field

import numpy as np
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.album import Album
from backend.app.models.rating import UserAlbumElo


# ============================================================================
# Configuration
# ============================================================================
@dataclass
class RecommendationConfig:
    """Tunable recommendation parameters."""

    min_albums_for_hybrid: int = 5
    max_similar_users: int = 20
    candidate_limit: int = 300
    exploration_ratio: float = 0.15
    artist_cap: float = 0.25
    min_shared_albums: int = 5
    top_albums_for_content: int = 10

    @staticmethod
    def compute_weights(user_album_count: int) -> tuple[float, float]:
        """Dynamic weights: new users lean content, experienced lean collab."""
        if user_album_count < 10:
            return 0.9, 0.1
        elif user_album_count < 30:
            t = (user_album_count - 10) / 20
            content = 0.9 - (t * 0.3)
            return content, 1 - content
        else:
            return 0.6, 0.4


# ============================================================================
# Score Data Classes
# ============================================================================
@dataclass
class ContentScore:
    """Breakdown of content-based similarity scores."""

    genre: float = 0.0
    artist: float = 0.0
    era: float = 0.0
    final: float = 0.0


@dataclass
class CollabScore:
    """Collaborative filtering score with confidence."""

    raw_score: float = 0.0
    normalized: float = 0.0


@dataclass
class RecommendationResult:
    """A single recommendation with all scoring data."""

    album: Album
    final_score: float = 0.0
    content_score: float = 0.0
    collaborative_score: float = 0.0
    raw_scores: dict = field(default_factory=dict)
    is_exploration: bool = False
    reasons: list[str] = field(default_factory=list)


@dataclass
class RecommendationsOutput:
    """Full recommendation response data."""

    recommendations: list[RecommendationResult]
    user_album_count: int = 0
    content_weight: float = 0.6
    collaborative_weight: float = 0.4
    similar_users_found: int = 0
    exploration_count: int = 0
    recommendation_type: str = "hybrid"


# ============================================================================
# Utility Functions
# ============================================================================
def parse_genres(genres_str: str | None) -> set[str]:
    """Parse comma-separated genre string into a set of lowercase genres."""
    if not genres_str:
        return set()
    return {g.strip().lower() for g in genres_str.split(",") if g.strip()}


def extract_genres(albums: list[Album]) -> set[str]:
    """Extract all genres from a list of albums."""
    genres = set()
    for album in albums:
        genres.update(parse_genres(album.genres))
    return genres


# ============================================================================
# Content-Based Scorer
# ============================================================================
class ContentScorer:
    """
    Content-based similarity scoring.

    Compares candidate albums against user's top-rated albums using:
    - Genre similarity (Jaccard)
    - Artist overlap (soft similarity)
    - Era similarity (temporal decay)

    Artist influence is capped to prevent full discography spam.
    """

    def __init__(self, artist_cap: float = 0.25):
        self.artist_cap = artist_cap
        self.base_weights = {"genre": 0.5, "artist": 0.35, "era": 0.15}

    def score(self, candidate: Album, user_top_albums: list[Album]) -> ContentScore:
        """Compute content similarity score for a candidate album."""
        if not user_top_albums:
            return ContentScore()

        genre_sim = self._genre_similarity(candidate, user_top_albums)
        artist_sim = self._artist_similarity(candidate, user_top_albums)
        era_sim = self._era_similarity(candidate, user_top_albums)

        # Cap artist influence to prevent discography spam
        raw_artist_contribution = artist_sim * self.base_weights["artist"]
        capped_artist = min(raw_artist_contribution, self.artist_cap)

        # Redistribute remaining weight proportionally to genre and era
        remaining = 1 - capped_artist
        genre_weight = self.base_weights["genre"]
        era_weight = self.base_weights["era"]
        total_other = genre_weight + era_weight

        final = (
            (genre_weight / total_other) * remaining * genre_sim
            + capped_artist
            + (era_weight / total_other) * remaining * era_sim
        )

        return ContentScore(
            genre=genre_sim,
            artist=artist_sim,
            era=era_sim,
            final=min(1.0, final),
        )

    def _genre_similarity(self, candidate: Album, refs: list[Album]) -> float:
        """Compute average Jaccard similarity across reference albums."""
        candidate_genres = parse_genres(candidate.genres)
        if not candidate_genres:
            return 0.0

        total_sim = 0.0
        count = 0

        for ref in refs:
            ref_genres = parse_genres(ref.genres)
            if not ref_genres:
                continue

            intersection = len(candidate_genres & ref_genres)
            union = len(candidate_genres | ref_genres)
            if union > 0:
                total_sim += intersection / union
                count += 1

        return total_sim / count if count > 0 else 0.0

    def _artist_similarity(self, candidate: Album, refs: list[Album]) -> float:
        """
        Compute artist overlap.

        Returns 1.0 if candidate shares an artist with any reference album.
        Future: could add 0.3 for shared label/producer/scene.
        """
        candidate_artist_ids = {a.id for a in candidate.artists}
        if not candidate_artist_ids:
            return 0.0

        for ref in refs:
            ref_artist_ids = {a.id for a in ref.artists}
            if candidate_artist_ids & ref_artist_ids:
                return 1.0

        return 0.0

    def _era_similarity(self, candidate: Album, refs: list[Album]) -> float:
        """
        Compute temporal similarity.

        Same decade = ~0.9, 20 years apart = ~0.5.
        """
        if candidate.release_year is None:
            return 0.5

        total_sim = 0.0
        count = 0

        for ref in refs:
            if ref.release_year is None:
                continue

            year_diff = abs(candidate.release_year - ref.release_year)
            sim = max(0.1, 1.0 - (year_diff / 40))
            total_sim += sim
            count += 1

        return total_sim / count if count > 0 else 0.5


# ============================================================================
# Collaborative Scorer
# ============================================================================
class CollaborativeScorer:
    """
    User-based collaborative filtering.

    Finds users with similar Elo rankings and recommends albums they rated highly.
    Uses cosine similarity on Elo vectors for user similarity.
    """

    def __init__(self, elo_cache: dict[str, np.ndarray] | None = None):
        self._elo_cache = elo_cache or {}

    async def find_similar_users(
        self,
        db: AsyncSession,
        target_user_id: str,
        target_album_ids: set[str],
        min_shared: int = 5,
        max_users: int = 20,
        adaptive: bool = True,
    ) -> list[tuple[str, float]]:
        """
        Find users with similar taste based on Elo scores.

        Adaptive thresholds: relaxes min_shared for niche users to avoid empty results.
        """
        if len(target_album_ids) < min_shared:
            return []

        # Try with standard threshold first
        users = await self._find_users_with_threshold(
            db, target_user_id, target_album_ids, min_shared, max_users
        )

        # Adaptive: relax threshold if too few matches
        if len(users) < 3 and adaptive and min_shared > 2:
            users = await self._find_users_with_threshold(
                db, target_user_id, target_album_ids, min_shared=2, max_users=max_users
            )

        return users

    async def _find_users_with_threshold(
        self,
        db: AsyncSession,
        target_user_id: str,
        target_album_ids: set[str],
        min_shared: int,
        max_users: int,
    ) -> list[tuple[str, float]]:
        """Find similar users with a specific shared album threshold."""
        from sklearn.metrics.pairwise import cosine_similarity

        target_album_list = list(target_album_ids)

        # Find candidate users with enough shared albums
        result = await db.execute(
            select(UserAlbumElo.user_id, func.count(UserAlbumElo.album_id))
            .where(
                UserAlbumElo.user_id != target_user_id,
                UserAlbumElo.album_id.in_(target_album_list),
            )
            .group_by(UserAlbumElo.user_id)
            .having(func.count(UserAlbumElo.album_id) >= min_shared)
        )
        candidates = [(row[0], row[1]) for row in result.all()]

        if not candidates:
            return []

        # Build target user's Elo vector
        target_vector = await self._build_elo_vector(
            db, target_user_id, target_album_list
        )

        # Calculate similarity for each candidate
        similarities = []
        for other_user_id, _ in candidates:
            other_vector = await self._build_elo_vector(
                db, other_user_id, target_album_list
            )

            # Only compare on albums both have rated
            mask = (target_vector != 0) & (other_vector != 0)
            if mask.sum() < min_shared:
                continue

            sim = cosine_similarity(
                target_vector[mask].reshape(1, -1),
                other_vector[mask].reshape(1, -1),
            )[0][0]

            similarities.append((other_user_id, float(sim)))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:max_users]

    async def _build_elo_vector(
        self, db: AsyncSession, user_id: str, album_ids: list[str]
    ) -> np.ndarray:
        """Build Elo score vector for specified albums. Uses request-level cache."""
        cache_key = f"{user_id}:{len(album_ids)}"
        if cache_key in self._elo_cache:
            return self._elo_cache[cache_key]

        result = await db.execute(
            select(UserAlbumElo).where(
                UserAlbumElo.user_id == user_id,
                UserAlbumElo.album_id.in_(album_ids),
            )
        )
        elo_records = {r.album_id: r.elo for r in result.scalars().all()}

        vector = np.array([elo_records.get(aid, 0) for aid in album_ids])
        self._elo_cache[cache_key] = vector
        return vector

    async def get_similar_users_albums(
        self,
        db: AsyncSession,
        similar_users: list[tuple[str, float]],
        exclude_album_ids: set[str],
        limit_per_user: int = 30,
    ) -> dict[str, CollabScore]:
        """
        Get albums that similar users rated highly.

        Returns dict of album_id -> CollabScore with aggregated scores.
        """
        album_scores: dict[str, float] = {}

        for user_id, similarity in similar_users:
            result = await db.execute(
                select(UserAlbumElo)
                .where(UserAlbumElo.user_id == user_id)
                .order_by(UserAlbumElo.elo.desc())
                .limit(limit_per_user)
            )
            user_albums = result.scalars().all()

            for i, elo_record in enumerate(user_albums):
                if elo_record.album_id in exclude_album_ids:
                    continue

                # Score = similarity * position_weight * normalized_elo
                position_weight = 1.0 / (i + 1)
                normalized_elo = max(0, (elo_record.elo - 1200) / 600)

                score = similarity * position_weight * normalized_elo
                album_scores[elo_record.album_id] = (
                    album_scores.get(elo_record.album_id, 0) + score
                )

        # Normalize scores
        max_score = max(album_scores.values()) if album_scores else 1.0
        return {
            aid: CollabScore(raw_score=score, normalized=score / max_score if max_score > 0 else 0)
            for aid, score in album_scores.items()
        }


# ============================================================================
# Candidate Pruning
# ============================================================================
async def get_candidate_albums(
    db: AsyncSession,
    user_album_ids: set[str],
    user_genres: set[str],
    similar_user_album_ids: set[str],
    limit: int = 300,
) -> list[Album]:
    """
    Prune candidates BEFORE scoring to avoid O(N*M).

    Priority:
    1. Albums sharing genre with user's top albums
    2. Albums liked by similar users
    3. Albums with high community activity
    """
    candidates: list[Album] = []
    seen_ids: set[str] = set()

    base_query = (
        select(Album)
        .where(~Album.id.in_(user_album_ids) if user_album_ids else True)
        .options(selectinload(Album.artists))
    )

    # Priority 1: Genre overlap
    if user_genres:
        genre_conditions = [
            Album.genres.ilike(f"%{g}%") for g in list(user_genres)[:5]
        ]
        genre_result = await db.execute(
            base_query.where(or_(*genre_conditions)).limit(limit // 2)
        )
        for album in genre_result.scalars().all():
            if album.id not in seen_ids:
                candidates.append(album)
                seen_ids.add(album.id)

    # Priority 2: Similar user recommendations
    if similar_user_album_ids:
        collab_result = await db.execute(
            base_query.where(
                Album.id.in_(similar_user_album_ids),
                ~Album.id.in_(seen_ids) if seen_ids else True,
            ).limit(limit // 3)
        )
        for album in collab_result.scalars().all():
            if album.id not in seen_ids:
                candidates.append(album)
                seen_ids.add(album.id)

    # Priority 3: Community popular (fallback)
    remaining = limit - len(candidates)
    if remaining > 0:
        community_result = await db.execute(
            base_query.where(
                Album.rating_count >= 3,
                ~Album.id.in_(seen_ids) if seen_ids else True,
            )
            .order_by(Album.bayesian_score.desc().nullslast())
            .limit(remaining)
        )
        for album in community_result.scalars().all():
            if album.id not in seen_ids:
                candidates.append(album)
                seen_ids.add(album.id)

    return candidates


# ============================================================================
# Exploration Injection
# ============================================================================
async def inject_exploration(
    db: AsyncSession,
    main_recommendations: list[RecommendationResult],
    user_genres: set[str],
    user_album_ids: set[str],
    exploration_ratio: float = 0.15,
) -> list[RecommendationResult]:
    """
    Replace bottom ~15% of results with albums outside user's usual genres.

    Prevents echo chambers and improves discovery.
    """
    if not main_recommendations:
        return main_recommendations

    num_explore = max(1, int(len(main_recommendations) * exploration_ratio))

    # Find albums with minimal genre overlap
    exclude_conditions = []
    for g in list(user_genres)[:3]:
        exclude_conditions.append(~Album.genres.ilike(f"%{g}%"))

    query = (
        select(Album)
        .where(
            ~Album.id.in_(user_album_ids) if user_album_ids else True,
            Album.rating_count >= 5,
        )
        .order_by(Album.bayesian_score.desc().nullslast())
        .limit(num_explore * 3)
        .options(selectinload(Album.artists))
    )

    if exclude_conditions:
        query = query.where(*exclude_conditions)

    result = await db.execute(query)
    explore_candidates = list(result.scalars().all())

    if not explore_candidates:
        return main_recommendations

    # Randomly sample for variety
    explore_picks = random.sample(
        explore_candidates, min(num_explore, len(explore_candidates))
    )

    # Replace bottom N of main recommendations
    final_results = main_recommendations[:-num_explore] if num_explore < len(main_recommendations) else []

    for album in explore_picks:
        final_results.append(
            RecommendationResult(
                album=album,
                final_score=0.5,
                content_score=0.0,
                collaborative_score=0.0,
                is_exploration=True,
                reasons=["Discover something different"],
            )
        )

    return final_results


# ============================================================================
# Discovery Recommendations (Fallback)
# ============================================================================
async def get_discovery_recommendations(
    db: AsyncSession,
    user_album_ids: set[str],
    limit: int = 20,
) -> RecommendationsOutput:
    """
    Fallback for new users with insufficient data.

    Returns highly-rated community albums.
    """
    query = (
        select(Album)
        .where(
            Album.bayesian_score.isnot(None),
            ~Album.id.in_(user_album_ids) if user_album_ids else True,
        )
        .order_by(Album.bayesian_score.desc())
        .limit(limit)
        .options(selectinload(Album.artists))
    )
    result = await db.execute(query)
    albums = list(result.scalars().all())

    recommendations = [
        RecommendationResult(
            album=album,
            final_score=album.bayesian_score or 0,
            content_score=0,
            collaborative_score=0,
            reasons=["Popular in the community"],
        )
        for album in albums
    ]

    return RecommendationsOutput(
        recommendations=recommendations,
        user_album_count=len(user_album_ids),
        content_weight=0.0,
        collaborative_weight=0.0,
        similar_users_found=0,
        recommendation_type="discovery",
    )


# ============================================================================
# Reason Generation
# ============================================================================
def generate_reasons(
    album: Album,
    user_top_albums: list[Album],
    collab_score: float,
) -> list[str]:
    """Generate human-readable explanation for why an album is recommended."""
    reasons = []

    # Check for shared artists
    album_artist_ids = {a.id for a in album.artists}
    for top_album in user_top_albums:
        top_artist_ids = {a.id for a in top_album.artists}
        if album_artist_ids & top_artist_ids:
            reasons.append(f"Same artist as {top_album.title}")
            break

    # Check for genre similarity
    album_genres = parse_genres(album.genres)
    for top_album in user_top_albums[:3]:
        top_genres = parse_genres(top_album.genres)
        shared = album_genres & top_genres
        if len(shared) >= 2:
            genre_str = ", ".join(list(shared)[:2])
            reasons.append(f"Similar genres ({genre_str})")
            break

    # Collaborative signal
    if collab_score > 0.3:
        reasons.append("Loved by users with similar taste")

    # Era similarity
    if album.release_year:
        for top_album in user_top_albums:
            if top_album.release_year:
                if abs(album.release_year - top_album.release_year) <= 5:
                    reasons.append(f"From the same era as {top_album.title}")
                    break

    return reasons[:3]


# ============================================================================
# Main Entry Point
# ============================================================================
async def get_hybrid_recommendations(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
    include_reasons: bool = False,
    config: RecommendationConfig | None = None,
) -> RecommendationsOutput:
    """
    Generate personalized recommendations using hybrid approach.

    Combines content-based and collaborative filtering with:
    - Dynamic weighting based on user history
    - Candidate pruning before scoring
    - Capped artist influence
    - Graceful collaborative fallback
    - Exploration injection
    """
    config = config or RecommendationConfig()
    elo_cache: dict[str, np.ndarray] = {}

    # 1. Get user's current albums
    user_albums_result = await db.execute(
        select(UserAlbumElo.album_id).where(UserAlbumElo.user_id == user_id)
    )
    user_album_ids = set(row[0] for row in user_albums_result.all())
    user_album_count = len(user_album_ids)

    # 2. Fallback to discovery for new users
    if user_album_count < config.min_albums_for_hybrid:
        return await get_discovery_recommendations(db, user_album_ids, limit)

    # 3. Dynamic weights
    content_weight, collab_weight = config.compute_weights(user_album_count)

    # 4. Get user's top albums for content matching
    top_albums_result = await db.execute(
        select(Album)
        .join(UserAlbumElo, UserAlbumElo.album_id == Album.id)
        .where(UserAlbumElo.user_id == user_id)
        .order_by(UserAlbumElo.elo.desc())
        .limit(config.top_albums_for_content)
        .options(selectinload(Album.artists))
    )
    user_top_albums = list(top_albums_result.scalars().all())
    user_genres = extract_genres(user_top_albums)

    # 5. Find similar users
    collab_scorer = CollaborativeScorer(elo_cache)
    similar_users = await collab_scorer.find_similar_users(
        db,
        user_id,
        user_album_ids,
        min_shared=config.min_shared_albums,
        max_users=config.max_similar_users,
        adaptive=True,
    )

    # 6. Graceful fallback if weak collaborative signal
    if len(similar_users) < 3:
        collab_weight = max(0.1, collab_weight * 0.5)
        content_weight = 1 - collab_weight

    # 7. Get similar users' liked albums
    collab_scores = await collab_scorer.get_similar_users_albums(
        db, similar_users, user_album_ids
    )
    similar_user_album_ids = set(collab_scores.keys())

    # 8. Prune candidates
    candidates = await get_candidate_albums(
        db,
        user_album_ids,
        user_genres,
        similar_user_album_ids,
        limit=config.candidate_limit,
    )

    # 9. Score candidates
    content_scorer = ContentScorer(artist_cap=config.artist_cap)
    results: list[RecommendationResult] = []

    for album in candidates:
        c_score = content_scorer.score(album, user_top_albums)
        col_score = collab_scores.get(album.id, CollabScore())

        final = content_weight * c_score.final + collab_weight * col_score.normalized

        reasons = []
        if include_reasons:
            reasons = generate_reasons(
                album, user_top_albums, col_score.normalized
            )

        results.append(
            RecommendationResult(
                album=album,
                final_score=final,
                content_score=c_score.final,
                collaborative_score=col_score.normalized,
                raw_scores={
                    "genre": c_score.genre,
                    "artist": c_score.artist,
                    "era": c_score.era,
                },
                is_exploration=False,
                reasons=reasons,
            )
        )

    # 10. Sort and limit
    results.sort(key=lambda r: r.final_score, reverse=True)
    results = results[:limit]

    # 11. Inject exploration
    results = await inject_exploration(
        db,
        results,
        user_genres,
        user_album_ids,
        exploration_ratio=config.exploration_ratio,
    )

    exploration_count = sum(1 for r in results if r.is_exploration)

    return RecommendationsOutput(
        recommendations=results,
        user_album_count=user_album_count,
        content_weight=content_weight,
        collaborative_weight=collab_weight,
        similar_users_found=len(similar_users),
        exploration_count=exploration_count,
        recommendation_type="hybrid",
    )


async def get_similar_albums(
    db: AsyncSession,
    album_id: str,
    limit: int = 10,
) -> tuple[Album | None, list[tuple[Album, float]]]:
    """
    Get albums similar to a specific album (content-based only).

    Returns (target_album, list of (similar_album, similarity_score)).
    """
    # Get target album
    target_result = await db.execute(
        select(Album).where(Album.id == album_id).options(selectinload(Album.artists))
    )
    target_album = target_result.scalar_one_or_none()

    if not target_album:
        return None, []

    # Get candidate albums
    candidates_result = await db.execute(
        select(Album)
        .where(Album.id != album_id)
        .options(selectinload(Album.artists))
        .limit(300)
    )
    candidates = list(candidates_result.scalars().all())

    # Score candidates
    scorer = ContentScorer()
    scored: list[tuple[Album, float]] = []

    for candidate in candidates:
        score = scorer.score(candidate, [target_album])
        if score.final > 0.1:
            scored.append((candidate, score.final))

    scored.sort(key=lambda x: x[1], reverse=True)
    return target_album, scored[:limit]
