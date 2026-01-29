"""Sentry error tracking integration."""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from backend.app.core.config import settings


def init_sentry() -> bool:
    """
    Initialize Sentry error tracking.

    Returns True if Sentry was initialized, False if disabled.
    Sentry is disabled when sentry_dsn is empty.
    """
    if not settings.sentry_dsn:
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        # Performance monitoring
        traces_sample_rate=settings.sentry_traces_sample_rate,
        # Profiling (requires traces)
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        # Release tracking (set via environment variable SENTRY_RELEASE)
        release=None,
        # Don't send PII by default
        send_default_pii=False,
        # Attach stack traces to messages
        attach_stacktrace=True,
        # Filter sensitive data
        before_send=_before_send,
    )
    return True


def _before_send(event: dict, hint: dict) -> dict | None:
    """
    Process events before sending to Sentry.

    Use this to:
    - Filter out certain exceptions
    - Scrub sensitive data
    - Add custom context
    """
    # Don't send 404 errors (too noisy)
    if "exc_info" in hint:
        exc_type, exc_value, _ = hint["exc_info"]
        if exc_type.__name__ == "HTTPException":
            if hasattr(exc_value, "status_code") and exc_value.status_code == 404:
                return None

    # Scrub sensitive headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[Filtered]"

    return event


def set_user_context(user_id: str, email: str | None = None, username: str | None = None) -> None:
    """
    Set user context for Sentry events.

    Call this after authentication to associate errors with users.
    """
    sentry_sdk.set_user(
        {
            "id": user_id,
            "email": email,
            "username": username,
        }
    )


def clear_user_context() -> None:
    """Clear user context (e.g., after logout)."""
    sentry_sdk.set_user(None)


def capture_exception(error: Exception, **extra_context) -> str | None:
    """
    Capture an exception with optional extra context.

    Returns the Sentry event ID if captured, None if Sentry is disabled.
    """
    if not settings.sentry_dsn:
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in extra_context.items():
            scope.set_extra(key, value)
        return sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **extra_context) -> str | None:
    """
    Capture a message with optional extra context.

    Level can be: "fatal", "error", "warning", "info", "debug"
    Returns the Sentry event ID if captured, None if Sentry is disabled.
    """
    if not settings.sentry_dsn:
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in extra_context.items():
            scope.set_extra(key, value)
        return sentry_sdk.capture_message(message, level=level)


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: dict | None = None,
) -> None:
    """
    Add a breadcrumb for debugging context.

    Breadcrumbs are shown in Sentry to understand what happened before an error.
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )
