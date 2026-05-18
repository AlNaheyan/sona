"""Request logging middleware — logs every request with context and timing."""

import re
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.app.core.logging import (
    api_logger,
    clear_request_context,
    new_request_id,
    set_request_context,
)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    - Assigns a unique request ID to every request
    - Sets request context for structured logging
    - Logs request/response with timing
    - Returns request ID in X-Request-ID header
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_id = request.headers.get("X-Request-ID", "")
        request_id = client_id if _UUID_RE.match(client_id) else new_request_id()
        start_time = time.monotonic()

        # Set request context for all logs within this request
        set_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            api_logger.error(
                "Unhandled exception: %s %s → 500 (%sms)",
                request.method,
                request.url.path,
                duration_ms,
                exc_info=exc,
            )
            raise
        else:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)

            log_method = api_logger.info if response.status_code < 400 else api_logger.warning
            if response.status_code >= 500:
                log_method = api_logger.error

            log_method(
                "%s %s → %d (%sms)",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )

            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_request_context()
