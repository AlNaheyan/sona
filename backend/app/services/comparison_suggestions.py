"""
Pairwise Comparison Suggestion Service

Smart algorithm to suggest which albums a user should compare next.
Goals:
1. Refine close rankings (albums with similar Elo scores)
2. Prioritize pairs that haven't been compared
3. Boost newly added albums that need more data
4. Occasional exploration (diverse genre pairs)
"""

import random
from dataclasses import dataclass
from itertools import combinations

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.album import Album
from backend.app.models.rating import UserAlbumElo, PairwiseComparison


@dataclass
class ComparisonSuggestion:
    """A suggested pair of albums to compare."""
    album_a: Album
    album_b: Album
    reason: str
    priority_score: float  # Higher = more important to compare


@dataclass
class SuggestionConfig:
    """Configuration for comparison suggestions."""
    # How many suggestions to return
    max_suggestions: int = 5

    # Elo difference thresholds
    close_elo_threshold: int = 100  # Albums within this range are "close"
    medium_elo_threshold: int = 200  # For medium priority comparisons

    # Weight factors for scoring
    close_elo_weight: float = 3.0  # High priority for close rankings
    low_comparison_weight: float = 2.0  # Boost albums with few comparisons
    uncompared_weight: float = 1.5  # Boost pairs never compared
    exploration_weight: float = 0.5  # Lower priority for exploration

    # Minimum albums needed for suggestions
    min_albums_for_suggestions: int = 3


async def get_user_comparison_pairs(
    db: AsyncSession,
    user_id: str,
) -> set[tuple[str, str]]:
    """Get all album pairs the user has already compared."""
    result = await db.execute(
        select(PairwiseComparison.album_a_id, PairwiseComparison.album_b_id)
        .where(PairwiseComparison.user_id == user_id)
    )
    pairs = set()
    for row in result.all():
        # Store both orderings for easy lookup
        pairs.add((row[0], row[1]))
        pairs.add((row[1], row[0]))
    return pairs


async def get_comparison_suggestions(
    db: AsyncSession,
    user_id: str,
    config: SuggestionConfig | None = None,
) -> list[ComparisonSuggestion]:
    """
    Generate smart comparison suggestions for a user.

    Algorithm:
    1. Get all user's ranked albums with Elo scores
    2. Find pairs with close Elo scores (need refinement)
    3. Prioritize pairs that haven't been compared yet
    4. Boost albums with few total comparisons
    5. Add some exploration pairs (different genres)
    6. Score and rank all candidates
    """
    config = config or SuggestionConfig()

    # Get user's albums with Elo scores
    elo_result = await db.execute(
        select(UserAlbumElo)
        .where(UserAlbumElo.user_id == user_id)
        .order_by(UserAlbumElo.elo.desc())
    )
    elo_records = list(elo_result.scalars().all())

    if len(elo_records) < config.min_albums_for_suggestions:
        return []

    # Get album details
    album_ids = [e.album_id for e in elo_records]
    albums_result = await db.execute(
        select(Album)
        .where(Album.id.in_(album_ids))
        .options(selectinload(Album.artists))
    )
    albums_by_id = {a.id: a for a in albums_result.scalars().all()}

    # Build Elo lookup
    elo_by_album = {e.album_id: e for e in elo_records}

    # Get existing comparison pairs
    compared_pairs = await get_user_comparison_pairs(db, user_id)

    # Generate and score candidate pairs
    candidates: list[ComparisonSuggestion] = []

    for elo_a, elo_b in combinations(elo_records, 2):
        album_a = albums_by_id.get(elo_a.album_id)
        album_b = albums_by_id.get(elo_b.album_id)

        if not album_a or not album_b:
            continue

        # Check if already compared
        already_compared = (elo_a.album_id, elo_b.album_id) in compared_pairs

        # Calculate Elo difference
        elo_diff = abs(elo_a.elo - elo_b.elo)

        # Score this pair
        score = 0.0
        reasons = []

        # Factor 1: Close Elo scores (need refinement)
        if elo_diff <= config.close_elo_threshold:
            score += config.close_elo_weight * (1 - elo_diff / config.close_elo_threshold)
            reasons.append("Rankings are very close")
        elif elo_diff <= config.medium_elo_threshold:
            score += config.close_elo_weight * 0.5 * (1 - elo_diff / config.medium_elo_threshold)
            reasons.append("Rankings are similar")

        # Factor 2: Never compared before
        if not already_compared:
            score += config.uncompared_weight
            reasons.append("Never compared before")
        else:
            # Reduce priority for already compared pairs
            score *= 0.3

        # Factor 3: Low comparison count (new albums need data)
        avg_comparisons = (elo_a.comparison_count + elo_b.comparison_count) / 2
        if avg_comparisons < 3:
            score += config.low_comparison_weight * (1 - avg_comparisons / 3)
            if elo_a.comparison_count == 0 or elo_b.comparison_count == 0:
                reasons.append("New album needs comparisons")

        # Factor 4: Exploration (different genres can be interesting)
        if score < 0.5 and not already_compared:
            # Add some exploration pairs
            genres_a = set((album_a.genres or "").lower().split(","))
            genres_b = set((album_b.genres or "").lower().split(","))
            if genres_a and genres_b and not (genres_a & genres_b):
                score += config.exploration_weight
                reasons.append("Discover your preference across genres")

        if score > 0:
            reason = reasons[0] if reasons else "Refine your rankings"
            candidates.append(ComparisonSuggestion(
                album_a=album_a,
                album_b=album_b,
                reason=reason,
                priority_score=score,
            ))

    # Sort by priority score and return top suggestions
    candidates.sort(key=lambda x: x.priority_score, reverse=True)

    # Add some randomization among top candidates to keep it fresh
    top_candidates = candidates[:config.max_suggestions * 2]
    if len(top_candidates) > config.max_suggestions:
        # Weighted random selection favoring higher scores
        selected = []
        remaining = top_candidates.copy()
        while len(selected) < config.max_suggestions and remaining:
            # Weight by score
            weights = [c.priority_score for c in remaining]
            total = sum(weights)
            if total == 0:
                break
            probs = [w / total for w in weights]

            # Select one
            idx = random.choices(range(len(remaining)), weights=probs, k=1)[0]
            selected.append(remaining.pop(idx))

        return selected

    return candidates[:config.max_suggestions]


async def get_next_comparison(
    db: AsyncSession,
    user_id: str,
) -> ComparisonSuggestion | None:
    """Get the single best comparison suggestion for immediate use."""
    suggestions = await get_comparison_suggestions(
        db, user_id, SuggestionConfig(max_suggestions=1)
    )
    return suggestions[0] if suggestions else None


async def get_comparison_stats(
    db: AsyncSession,
    user_id: str,
) -> dict:
    """Get statistics about user's comparison coverage."""
    # Count albums
    album_count_result = await db.execute(
        select(func.count()).where(UserAlbumElo.user_id == user_id)
    )
    album_count = album_count_result.scalar() or 0

    # Count comparisons
    comparison_count_result = await db.execute(
        select(func.count()).where(PairwiseComparison.user_id == user_id)
    )
    comparison_count = comparison_count_result.scalar() or 0

    # Calculate possible pairs
    possible_pairs = album_count * (album_count - 1) // 2 if album_count > 1 else 0

    # Get unique compared pairs
    compared_pairs = await get_user_comparison_pairs(db, user_id)
    unique_pairs_compared = len(compared_pairs) // 2  # Divide by 2 since we store both orderings

    # Coverage percentage
    coverage = (unique_pairs_compared / possible_pairs * 100) if possible_pairs > 0 else 0

    return {
        "ranked_albums": album_count,
        "total_comparisons": comparison_count,
        "unique_pairs_compared": unique_pairs_compared,
        "possible_pairs": possible_pairs,
        "coverage_percentage": round(coverage, 1),
    }
