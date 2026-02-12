"""Profile endpoints - user profile CRUD."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.core.rate_limit import limiter, RateLimits
from backend.app.models.profile import UserProfile
from backend.app.models.rating import NumericRating
from backend.app.models.user import User
from backend.app.schemas.profile import ProfileCreate, ProfileOut, PublicProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    """Get the authenticated user's profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return ProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        username=current_user.username,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        spotify_username=profile.spotify_username,
        favorite_genres=profile.favorite_genres,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.put("/me", response_model=ProfileOut)
@limiter.limit(RateLimits.RATING)
async def upsert_my_profile(
    request: Request,
    data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    """Create or update the authenticated user's profile (upsert)."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        profile.display_name = data.display_name
        profile.bio = data.bio
        profile.avatar_url = data.avatar_url
        profile.spotify_username = data.spotify_username
        profile.favorite_genres = data.favorite_genres
    else:
        profile = UserProfile(
            user_id=current_user.id,
            display_name=data.display_name,
            bio=data.bio,
            avatar_url=data.avatar_url,
            spotify_username=data.spotify_username,
            favorite_genres=data.favorite_genres,
        )
        db.add(profile)

    await db.flush()
    await db.refresh(profile)

    return ProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        username=current_user.username,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        spotify_username=profile.spotify_username,
        favorite_genres=profile.favorite_genres,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.get("/{username}", response_model=PublicProfileOut)
async def get_public_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> PublicProfileOut:
    """Get a user's public profile by username."""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Count rated albums
    count_result = await db.execute(
        select(func.count()).where(NumericRating.user_id == user.id)
    )
    rated_albums_count = count_result.scalar() or 0

    return PublicProfileOut(
        username=user.username,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        spotify_username=profile.spotify_username,
        favorite_genres=profile.favorite_genres,
        rated_albums_count=rated_albums_count,
        member_since=user.created_at.isoformat(),
    )
