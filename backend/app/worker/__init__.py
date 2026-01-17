"""Celery worker package."""

from backend.app.worker.celery_app import celery_app

__all__ = ["celery_app"]
