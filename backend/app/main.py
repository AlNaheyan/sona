from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import engine
from backend.app.models.base import Base
from backend.app.models import Album, Artist, User, NumericRating  # noqa: F401 - for table creation
from backend.app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    # NOTE: Use Alembic migrations for schema changes:
    #   cd backend && alembic upgrade head
    # Auto-create is disabled - all schema changes go through migrations
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="RateMyAlbum API",
    description="Album rating and recommendation engine with CWPR algorithm",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "RateMyAlbum API",
        "docs": "/docs",
        "health": "/health",
    }
