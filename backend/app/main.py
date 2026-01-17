from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import engine, get_db
from backend.app.core.rate_limit import limiter
from backend.app.models.base import Base
from backend.app.models import Album, Artist, User, NumericRating  # noqa: F401 - for table creation
from backend.app.api.v1 import api_router
from backend.app.services.health import get_system_health, get_liveness, get_readiness


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

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Comprehensive health check for all system components.

    Returns status of:
    - PostgreSQL database
    - Redis cache
    - Celery workers

    Response includes latency metrics and component details.
    """
    health = await get_system_health(db)
    return health.to_dict()


@app.get("/health/live")
async def liveness_check() -> dict:
    """
    Simple liveness probe.

    Returns 200 if the application is running.
    Used by Kubernetes/Docker health checks.
    """
    return await get_liveness()


@app.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Readiness probe.

    Returns 200 if the application can handle requests (database available).
    Used by Kubernetes/Docker to know when to route traffic.
    """
    return await get_readiness(db)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "RateMyAlbum API",
        "docs": "/docs",
        "health": "/health",
        "health_live": "/health/live",
        "health_ready": "/health/ready",
    }
