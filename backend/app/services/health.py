"""Health check service for monitoring system components."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

import redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings


class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component."""
    name: str
    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None
    details: dict | None = None


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    timestamp: str
    version: str
    components: list[ComponentHealth]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "version": self.version,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.components
            ],
        }


async def check_database(db: AsyncSession) -> ComponentHealth:
    """Check PostgreSQL database connectivity and performance."""
    start = asyncio.get_event_loop().time()
    try:
        # Simple query to verify connection
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        # Get database version
        version_result = await db.execute(text("SELECT version()"))
        version = version_result.scalar()

        latency = (asyncio.get_event_loop().time() - start) * 1000

        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency, 2),
            message="PostgreSQL connection OK",
            details={"version": version[:50] if version else None},
        )
    except Exception as e:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(latency, 2),
            message=f"Database error: {str(e)[:100]}",
        )


def check_redis() -> ComponentHealth:
    """Check Redis connectivity and performance."""
    start = asyncio.get_event_loop().time()
    try:
        client = redis.from_url(settings.redis_url, socket_timeout=5)

        # Ping Redis
        client.ping()

        # Get Redis info
        info = client.info("server")
        redis_version = info.get("redis_version", "unknown")

        # Get memory info
        memory_info = client.info("memory")
        used_memory_human = memory_info.get("used_memory_human", "unknown")

        latency = (asyncio.get_event_loop().time() - start) * 1000

        client.close()

        return ComponentHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency, 2),
            message="Redis connection OK",
            details={
                "version": redis_version,
                "used_memory": used_memory_human,
            },
        )
    except Exception as e:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(latency, 2),
            message=f"Redis error: {str(e)[:100]}",
        )


def check_celery() -> ComponentHealth:
    """Check Celery worker status via Redis."""
    start = asyncio.get_event_loop().time()
    try:
        from backend.app.worker.celery_app import celery_app

        # Inspect active workers
        inspector = celery_app.control.inspect(timeout=2)
        active_workers = inspector.active()

        latency = (asyncio.get_event_loop().time() - start) * 1000

        if active_workers is None:
            return ComponentHealth(
                name="celery",
                status=HealthStatus.DEGRADED,
                latency_ms=round(latency, 2),
                message="No Celery workers responding",
                details={"workers": 0},
            )

        worker_count = len(active_workers)
        active_tasks = sum(len(tasks) for tasks in active_workers.values())

        # Get registered tasks
        registered = inspector.registered()
        task_count = len(registered.get(list(registered.keys())[0], [])) if registered else 0

        return ComponentHealth(
            name="celery",
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency, 2),
            message=f"{worker_count} worker(s) active",
            details={
                "workers": worker_count,
                "active_tasks": active_tasks,
                "registered_tasks": task_count,
            },
        )
    except Exception as e:
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ComponentHealth(
            name="celery",
            status=HealthStatus.DEGRADED,
            latency_ms=round(latency, 2),
            message=f"Celery check failed: {str(e)[:100]}",
        )


async def get_system_health(db: AsyncSession | None = None) -> SystemHealth:
    """
    Get comprehensive system health status.

    Checks:
    - PostgreSQL database (if db session provided)
    - Redis cache
    - Celery workers
    """
    components: list[ComponentHealth] = []

    # Check database (if session provided)
    if db:
        db_health = await check_database(db)
        components.append(db_health)

    # Check Redis
    redis_health = check_redis()
    components.append(redis_health)

    # Check Celery
    celery_health = check_celery()
    components.append(celery_health)

    # Determine overall status
    statuses = [c.status for c in components]
    if HealthStatus.UNHEALTHY in statuses:
        overall_status = HealthStatus.UNHEALTHY
    elif HealthStatus.DEGRADED in statuses:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    return SystemHealth(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        components=components,
    )


async def get_liveness() -> dict:
    """
    Simple liveness check - just confirms the app is running.

    Used by Kubernetes/Docker for liveness probes.
    """
    return {"status": "alive"}


async def get_readiness(db: AsyncSession) -> dict:
    """
    Readiness check - confirms the app can handle requests.

    Checks critical dependencies (database) are available.
    Used by Kubernetes/Docker for readiness probes.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}
