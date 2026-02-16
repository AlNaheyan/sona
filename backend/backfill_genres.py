"""One-time script to backfill genres for albums missing them.

Usage (inside Docker container):
    python -m backend.backfill_genres
"""

import asyncio
import logging

from sqlalchemy import select

from backend.app.core.database import async_session_maker
from backend.app.models.album import Album
from backend.app.services.musicbrainz import musicbrainz_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def backfill() -> None:
    async with async_session_maker() as db:
        result = await db.execute(
            select(Album).where(Album.genres.is_(None))
        )
        albums = list(result.scalars().all())
        logger.info(f"Found {len(albums)} albums without genres")

        updated = 0
        for album in albums:
            if not album.mbid:
                continue
            try:
                mb = await musicbrainz_client.get_album_by_mbid(album.mbid)
                if mb and mb.genres:
                    album.genres = ",".join(mb.genres)
                    updated += 1
                    logger.info(f"  {album.title}: {album.genres}")
                else:
                    logger.info(f"  {album.title}: no genres found on MusicBrainz")
            except Exception as e:
                logger.warning(f"  {album.title}: error fetching genres: {e}")

        await db.commit()
        logger.info(f"Backfill complete: {updated}/{len(albums)} albums updated")


if __name__ == "__main__":
    asyncio.run(backfill())
