# Initialize structured logging FIRST (before any other imports)
from backend.app.core.logging import setup_logging, api_logger
setup_logging()

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import engine, get_db
from backend.app.core.rate_limit import limiter
from backend.app.models.base import Base
from backend.app.models import Album, Artist, User, NumericRating  # noqa: F401 - for table creation
from backend.app.api.v1 import api_router
from backend.app.middleware.request_logging import RequestLoggingMiddleware
from backend.app.middleware.security_headers import SecurityHeadersMiddleware
from backend.app.services.health import get_system_health, get_liveness, get_readiness


# OpenAPI Tags Metadata
tags_metadata = [
    {
        "name": "auth",
        "description": "Authentication operations. Register, login, and manage JWT tokens.",
    },
    {
        "name": "albums",
        "description": "Album search and discovery. Search MusicBrainz catalog and browse local database.",
    },
    {
        "name": "ratings",
        "description": "Numeric album ratings (1-10). Creates weak Elo signal (K=16) for personal rankings.",
    },
    {
        "name": "comparisons",
        "description": "Pairwise album comparisons (A vs B). Creates strong Elo signal (K=32) for personal rankings.",
    },
    {
        "name": "rankings",
        "description": "Personal album rankings based on Elo scores. Your canonical ordered album list.",
    },
    {
        "name": "community",
        "description": "Community-wide rankings using Bayesian-weighted scores. Global album leaderboards.",
    },
    {
        "name": "recommendations",
        "description": "Personalized album recommendations using hybrid content + collaborative filtering.",
    },
    {
        "name": "health",
        "description": "System health checks for monitoring and orchestration.",
    },
]


API_DESCRIPTION = """
## RateMyAlbum API

A ranking-first album recommendation engine that learns your musical taste through explicit preferences.

### Core Concepts

**Personal Rankings (Elo-based)**
- Every user has their own ranking space
- Albums start at Elo 1500 and move based on your feedback
- Higher Elo = better ranked

**Signal Types**
| Type | Strength | Example |
|------|----------|---------|
| Pairwise Comparison | Strong (K=32) | "I prefer OK Computer over Kid A" |
| Numeric Rating | Weak (K=16) | "I give this album 8/10" |

**Community Rankings**
- Global rankings using Bayesian-weighted averages
- Prevents albums with few ratings from dominating
- Separate from personal rankings

### Authentication

Most endpoints require a JWT Bearer token. Get one via `/api/v1/auth/login`.

```
Authorization: Bearer <your_access_token>
```

Access tokens expire in 30 minutes. Use `/api/v1/auth/refresh` with your refresh token to get new tokens.

### Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| Login/Register | 5/min |
| Search | 30/min |
| Ratings | 60/min |
| Comparisons | 60/min |
| Recommendations | 20/min |
"""


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
    description=API_DESCRIPTION,
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    contact={
        "name": "RateMyAlbum",
        "url": "https://github.com/ratemyalbum",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware (adds request ID, timing, structured logs)
app.add_middleware(RequestLoggingMiddleware)
# Security headers on all responses
app.add_middleware(SecurityHeadersMiddleware)

# Include API routes
app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Comprehensive health check for all system components.

    Returns status of:
    - **PostgreSQL database**: Connection status, version, latency
    - **Redis cache**: Connection status, version, memory usage, latency
    - **Celery workers**: Worker count, active tasks, registered tasks

    Overall status is determined by component health:
    - `healthy`: All components operational
    - `degraded`: Some components have issues but system is functional
    - `unhealthy`: Critical components are down
    """
    health = await get_system_health(db)
    return health.to_dict()


@app.get("/health/live", tags=["health"])
async def liveness_check() -> dict:
    """
    Simple liveness probe for container orchestration.

    Returns `{"status": "alive"}` if the application process is running.

    **Use case**: Kubernetes/Docker liveness probes to detect hung processes.
    """
    return await get_liveness()


@app.get("/health/ready", tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Readiness probe for container orchestration.

    Returns `{"status": "ready"}` if the application can handle requests
    (database connection is available).

    **Use case**: Kubernetes/Docker readiness probes to control traffic routing.
    Only route traffic to instances that return ready.
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
