"""
CWPR (Confidence-Weighted Preference Ranking) Service

Computes user preference scores from multiple input types:
- Numeric ratings (1-10)
- Tier placements (S/A/B/C/D/F -> 10/8/6/4/2/0)
- Pairwise comparisons (relative preference adjustments)

Formula: Score = μ - λσ

Where:
- μ (mu): Mean preference estimate
- σ (sigma): Uncertainty in the estimate
- λ (lambda): Confidence penalty factor (default 1.0)
"""

import math
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.rating import (
    NumericRating,
    TierPlacement,
    PairwiseComparison,
    UserAlbumPreference,
)

# Tier to numeric value mapping
TIER_VALUES = {
    "S": 10.0,
    "A": 8.0,
    "B": 6.0,
    "C": 4.0,
    "D": 2.0,
    "F": 0.0,
}

# Default values when no input exists
DEFAULT_MU = 5.0
DEFAULT_SIGMA = 2.5


async def compute_preference(
    db: AsyncSession,
    user_id: str,
    album_id: str,
) -> UserAlbumPreference:
    """
    Compute and update the CWPR preference score for a user-album pair.

    Combines all input types into a single (μ, σ, score) tuple.
    """
    values: list[float] = []
    weights: list[float] = []

    # 1. Get numeric rating
    result = await db.execute(
        select(NumericRating).where(
            NumericRating.user_id == user_id,
            NumericRating.album_id == album_id,
        )
    )
    numeric_rating = result.scalar_one_or_none()
    numeric_count = 0
    if numeric_rating:
        values.append(numeric_rating.value)
        weights.append(1.0)  # Numeric ratings have weight 1.0
        numeric_count = 1

    # 2. Get tier placement
    result = await db.execute(
        select(TierPlacement).where(
            TierPlacement.user_id == user_id,
            TierPlacement.album_id == album_id,
        )
    )
    tier_placement = result.scalar_one_or_none()
    tier_count = 0
    if tier_placement:
        tier_value = TIER_VALUES.get(tier_placement.tier, 5.0)
        values.append(tier_value)
        weights.append(0.8)  # Tier placements have slightly lower weight
        tier_count = 1

    # 3. Count pairwise comparisons involving this album
    result = await db.execute(
        select(func.count()).where(
            PairwiseComparison.user_id == user_id,
            (PairwiseComparison.album_a_id == album_id) |
            (PairwiseComparison.album_b_id == album_id),
        )
    )
    pairwise_count = result.scalar() or 0

    # Calculate pairwise adjustment (wins vs losses)
    pairwise_adjustment = 0.0
    if pairwise_count > 0:
        # Count wins (album is A and winner_is_a=True, or album is B and winner_is_a=False)
        wins_result = await db.execute(
            select(func.count()).where(
                PairwiseComparison.user_id == user_id,
                (
                    (PairwiseComparison.album_a_id == album_id) &
                    (PairwiseComparison.winner_is_a == True)
                ) | (
                    (PairwiseComparison.album_b_id == album_id) &
                    (PairwiseComparison.winner_is_a == False)
                ),
            )
        )
        wins = wins_result.scalar() or 0

        # Count losses
        losses_result = await db.execute(
            select(func.count()).where(
                PairwiseComparison.user_id == user_id,
                (
                    (PairwiseComparison.album_a_id == album_id) &
                    (PairwiseComparison.winner_is_a == False)
                ) | (
                    (PairwiseComparison.album_b_id == album_id) &
                    (PairwiseComparison.winner_is_a == True)
                ),
            )
        )
        losses = losses_result.scalar() or 0

        # Win rate adjustment: scale from -1 to +1 based on win percentage
        if wins + losses > 0:
            win_rate = wins / (wins + losses)
            # Convert 0-1 win rate to -1 to +1 adjustment
            pairwise_adjustment = (win_rate - 0.5) * 2.0

    # Calculate mu (weighted mean)
    if values:
        total_weight = sum(weights)
        mu = sum(v * w for v, w in zip(values, weights)) / total_weight
        # Apply pairwise adjustment (scaled by confidence in pairwise data)
        if pairwise_count > 0:
            pairwise_confidence = min(pairwise_count / 5.0, 1.0)  # Max confidence at 5 comparisons
            mu += pairwise_adjustment * pairwise_confidence * 0.5  # Max ±0.5 adjustment
    else:
        mu = DEFAULT_MU

    # Clamp mu to valid range
    mu = max(0.0, min(10.0, mu))

    # Calculate sigma (uncertainty)
    # Sigma decreases with more inputs: σ = base_σ / sqrt(1 + n)
    total_inputs = len(values) + (1 if pairwise_count > 0 else 0)
    if total_inputs > 0:
        sigma = DEFAULT_SIGMA / math.sqrt(1 + total_inputs)
    else:
        sigma = DEFAULT_SIGMA

    # If we have both numeric and tier, and they disagree, increase uncertainty
    if numeric_rating and tier_placement:
        tier_value = TIER_VALUES.get(tier_placement.tier, 5.0)
        disagreement = abs(numeric_rating.value - tier_value)
        sigma += disagreement * 0.1  # Small penalty for self-disagreement

    # Calculate final score
    score = mu - settings.cwpr_lambda * sigma

    # Get or create preference record
    result = await db.execute(
        select(UserAlbumPreference).where(
            UserAlbumPreference.user_id == user_id,
            UserAlbumPreference.album_id == album_id,
        )
    )
    preference = result.scalar_one_or_none()

    if preference:
        preference.mu = mu
        preference.sigma = sigma
        preference.score = score
        preference.numeric_count = numeric_count
        preference.pairwise_count = pairwise_count
        preference.tier_count = tier_count
    else:
        preference = UserAlbumPreference(
            user_id=user_id,
            album_id=album_id,
            mu=mu,
            sigma=sigma,
            score=score,
            numeric_count=numeric_count,
            pairwise_count=pairwise_count,
            tier_count=tier_count,
        )
        db.add(preference)

    await db.flush()
    await db.refresh(preference)

    return preference


async def recompute_user_preferences(
    db: AsyncSession,
    user_id: str,
) -> int:
    """
    Recompute all preferences for a user.

    Returns the number of preferences updated.
    """
    # Get all albums the user has interacted with
    album_ids = set()

    # From numeric ratings
    result = await db.execute(
        select(NumericRating.album_id).where(NumericRating.user_id == user_id)
    )
    album_ids.update(row[0] for row in result.all())

    # From tier placements
    result = await db.execute(
        select(TierPlacement.album_id).where(TierPlacement.user_id == user_id)
    )
    album_ids.update(row[0] for row in result.all())

    # From pairwise comparisons
    result = await db.execute(
        select(PairwiseComparison.album_a_id, PairwiseComparison.album_b_id).where(
            PairwiseComparison.user_id == user_id
        )
    )
    for row in result.all():
        album_ids.add(row[0])
        album_ids.add(row[1])

    # Recompute each preference
    for album_id in album_ids:
        await compute_preference(db, user_id, album_id)

    return len(album_ids)
