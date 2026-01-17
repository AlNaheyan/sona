"""Celery application configuration."""

from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "ratemyalbum",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "backend.app.worker.tasks.community",
        "backend.app.worker.tasks.recommendations",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,  # Tasks acknowledged after completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies

    # Result settings
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=1,  # Prevent task hoarding

    # Beat schedule for periodic tasks
    beat_schedule={
        "recalculate-community-scores-daily": {
            "task": "backend.app.worker.tasks.community.recalculate_all_community_scores",
            "schedule": 86400.0,  # Run daily (24 hours)
        },
    },
)
