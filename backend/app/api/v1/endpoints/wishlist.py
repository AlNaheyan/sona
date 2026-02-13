"""Want to Listen (wishlist) endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.album import Album
from backend.app.models.wishlist import WantToListen
from backend.app.models.user import User
from backend.app.api.v1.endpoints.ratings import get_or_create_album
from backend.app.schemas.wishlist import (
    WishlistAdd,
    WishlistOut,
    WishlistCheckResponse,
    WishlistListResponse,
)

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.post("", response_model=WishlistOut)
async def add_to_wishlist(
    body: WishlistAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WishlistOut:
    """Add an album to your Want to Listen list. Idempotent."""
    album = await get_or_create_album(db, body.mbid)

    # Check if already exists
    result = await db.execute(
        select(WantToListen).where(
            WantToListen.user_id == current_user.id,
            WantToListen.album_id == album.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Idempotent — return existing entry
        artist_name = album.artists[0].name if album.artists else None
        return WishlistOut(
            id=existing.id,
            album_id=album.id,
            album_mbid=album.mbid or body.mbid,
            album_title=album.title,
            album_artist=artist_name,
            album_cover_url=album.cover_url,
            created_at=existing.created_at.isoformat(),
        )

    entry = WantToListen(
        user_id=current_user.id,
        album_id=album.id,
        album_mbid=album.mbid or body.mbid,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)

    artist_name = album.artists[0].name if album.artists else None

    return WishlistOut(
        id=entry.id,
        album_id=album.id,
        album_mbid=album.mbid or body.mbid,
        album_title=album.title,
        album_artist=artist_name,
        album_cover_url=album.cover_url,
        created_at=entry.created_at.isoformat(),
    )


@router.get("/check", response_model=WishlistCheckResponse)
async def check_wishlist(
    mbid: str = Query(..., description="MusicBrainz release-group ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WishlistCheckResponse:
    """Check if an album is in your Want to Listen list."""
    result = await db.execute(
        select(WantToListen).where(
            WantToListen.user_id == current_user.id,
            WantToListen.album_mbid == mbid,
        )
    )
    entry = result.scalar_one_or_none()

    return WishlistCheckResponse(
        in_wishlist=entry is not None,
        entry_id=entry.id if entry else None,
    )


@router.delete("/{entry_id}")
async def remove_from_wishlist(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Remove an album from your Want to Listen list."""
    result = await db.execute(
        select(WantToListen).where(
            WantToListen.id == entry_id,
            WantToListen.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Wishlist entry not found")

    await db.delete(entry)
    return {"status": "deleted"}


@router.get("", response_model=WishlistListResponse)
async def list_wishlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> WishlistListResponse:
    """List all albums in your Want to Listen list."""
    result = await db.execute(
        select(WantToListen)
        .where(WantToListen.user_id == current_user.id)
        .order_by(WantToListen.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    entries = result.scalars().all()

    items = []
    for entry in entries:
        album_result = await db.execute(
            select(Album)
            .where(Album.id == entry.album_id)
            .options(selectinload(Album.artists))
        )
        album = album_result.scalar_one_or_none()
        if not album:
            continue

        artist_name = album.artists[0].name if album.artists else None
        items.append(
            WishlistOut(
                id=entry.id,
                album_id=album.id,
                album_mbid=entry.album_mbid,
                album_title=album.title,
                album_artist=artist_name,
                album_cover_url=album.cover_url,
                created_at=entry.created_at.isoformat(),
            )
        )

    return WishlistListResponse(items=items, count=len(items))
