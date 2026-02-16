"""
Genre Embedding Cache

Three-tier loading chain: in-process memory → Redis → rebuild from DB.
Ensures embeddings are built once and shared across requests.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select

from backend.app.ml.genre_embeddings import (
    GenreEmbeddingModel,
    build_genre_embeddings,
    _parse_genre_list,
)
from backend.app.models.album import Album
from backend.app.services.cache import CacheKeys, CacheTTL, cache_service

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class GenreEmbeddingCache:
    """In-process → Redis → rebuild-from-DB loading chain for genre embeddings."""

    def __init__(self) -> None:
        self._model: GenreEmbeddingModel | None = None

    async def get_model(self, db: AsyncSession) -> GenreEmbeddingModel | None:
        """
        Get genre embedding model, loading from cache tiers as needed.

        Returns None if there aren't enough genres to build a model.
        """
        # Tier 1: in-process memory
        if self._model is not None and self._model.vectors:
            return self._model

        # Tier 2: Redis
        try:
            cached = await cache_service.get(CacheKeys.genre_embeddings())
            if cached:
                self._model = GenreEmbeddingModel.from_dict(cached)
                if self._model.vectors:
                    logger.info(
                        f"Loaded genre embeddings from Redis: {len(self._model.vectors)} genres"
                    )
                    return self._model
        except Exception as e:
            logger.warning(f"Failed to load genre embeddings from Redis: {e}")

        # Tier 3: rebuild from DB
        return await self.rebuild(db)

    async def rebuild(self, db: AsyncSession) -> GenreEmbeddingModel | None:
        """Rebuild embeddings from all albums in the database."""
        result = await db.execute(select(Album.genres).where(Album.genres.isnot(None)))
        genre_strings = [row[0] for row in result.all()]

        album_genre_lists = [_parse_genre_list(gs) for gs in genre_strings]
        album_genre_lists = [gl for gl in album_genre_lists if gl]

        if len(album_genre_lists) < 5:
            logger.info("Too few albums with genres to build embeddings")
            return None

        model = build_genre_embeddings(album_genre_lists)

        if not model.vectors:
            return None

        self._model = model

        # Store in Redis
        try:
            await cache_service.set(
                CacheKeys.genre_embeddings(),
                model.to_dict(),
                ttl_seconds=CacheTTL.GENRE_EMBEDDINGS,
            )
            logger.info(f"Cached genre embeddings in Redis: {len(model.vectors)} genres")
        except Exception as e:
            logger.warning(f"Failed to cache genre embeddings in Redis: {e}")

        return model

    async def invalidate(self) -> None:
        """Clear both in-process and Redis caches."""
        self._model = None
        try:
            await cache_service.delete(CacheKeys.genre_embeddings())
        except Exception as e:
            logger.warning(f"Failed to invalidate genre embeddings in Redis: {e}")


# Singleton
genre_embedding_cache = GenreEmbeddingCache()
