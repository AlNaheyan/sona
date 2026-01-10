"""Tier list endpoints - place albums in S/A/B/C/D/F tiers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.album import Album
from backend.app.models.rating import TierPlacement
from backend.app.models.user import User
from backend.app.schemas.rating import (
    TierPlacementCreate,
    TierPlacementOut,
    TierGroup,
    TierListResponse,
)

# Reuse the get_or_create_album helper from ratings
from backend.app.api.v1.endpoints.ratings import get_or_create_album

router = APIRouter(prefix="/tiers", tags=["tiers"])

# Tier order for grouping
TIER_ORDER = ["S", "A", "B", "C", "D", "F"]


@router.post("", response_model=TierPlacementOut)
async def place_album_in_tier(
    placement: TierPlacementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TierPlacementOut:
    """
    Place an album in a tier (S/A/B/C/D/F).

    Requires authentication.
    If the album doesn't exist in our database, it will be fetched from MusicBrainz.
    If you've already placed this album, it will be updated.
    """
    # Get or create album
    album = await get_or_create_album(db, placement.mbid)

    # Check for existing placement
    result = await db.execute(
        select(TierPlacement).where(
            TierPlacement.user_id == current_user.id,
            TierPlacement.album_id == album.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing placement
        existing.tier = placement.tier
        existing.position = placement.position
        db_placement = existing
    else:
        # Create new placement
        db_placement = TierPlacement(
            user_id=current_user.id,
            album_id=album.id,
            tier=placement.tier,
            position=placement.position,
        )
        db.add(db_placement)

    await db.flush()
    await db.refresh(db_placement)

    # Get artist name for response
    artist_name = album.artists[0].name if album.artists else None

    return TierPlacementOut(
        id=db_placement.id,
        album_id=album.id,
        album_title=album.title,
        album_artist=artist_name,
        album_cover_url=album.cover_url,
        tier=db_placement.tier,
        position=db_placement.position,
        created_at=db_placement.created_at.isoformat(),
        updated_at=db_placement.updated_at.isoformat(),
    )


@router.get("", response_model=TierListResponse)
async def get_my_tier_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TierListResponse:
    """
    Get your complete tier list grouped by tier.

    Requires authentication.
    """
    result = await db.execute(
        select(TierPlacement)
        .where(TierPlacement.user_id == current_user.id)
        .order_by(TierPlacement.tier, TierPlacement.position)
    )
    placements = result.scalars().all()

    # Group by tier
    tier_groups: dict[str, list[TierPlacementOut]] = {t: [] for t in TIER_ORDER}

    for p in placements:
        # Fetch album details
        album_result = await db.execute(select(Album).where(Album.id == p.album_id))
        album = album_result.scalar_one_or_none()
        if not album:
            continue

        artist_name = album.artists[0].name if album.artists else None

        tier_groups[p.tier].append(
            TierPlacementOut(
                id=p.id,
                album_id=p.album_id,
                album_title=album.title,
                album_artist=artist_name,
                album_cover_url=album.cover_url,
                tier=p.tier,
                position=p.position,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
        )

    # Build response with non-empty tiers
    tiers = [
        TierGroup(tier=t, albums=tier_groups[t])
        for t in TIER_ORDER
        if tier_groups[t]
    ]

    return TierListResponse(
        tiers=tiers,
        total_count=len(placements),
    )


@router.delete("/{placement_id}")
async def remove_from_tier_list(
    placement_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Remove an album from your tier list.

    Requires authentication. You can only delete your own placements.
    """
    result = await db.execute(
        select(TierPlacement).where(
            TierPlacement.id == placement_id,
            TierPlacement.user_id == current_user.id,
        )
    )
    placement = result.scalar_one_or_none()

    if not placement:
        raise HTTPException(status_code=404, detail="Tier placement not found")

    await db.delete(placement)
    return {"status": "deleted"}
