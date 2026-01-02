"""Request ID middleware for tracing requests across components.

Provides:
- Automatic request ID generation
- Header extraction (X-Request-ID)
- Propagation through async context
- Logging integration

Usage in logs:
    logger.info("processing request", request_id=get_request_id())
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Context variable for request ID
_request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to handle request ID extraction and generation."""

    async def dispatch(self, request: Request, call_next):
        """Process request and inject request ID.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with X-Request-ID header
        """
        # Try to get request ID from header, or generate new one
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = generate_request_id()

        # Set in context var for async propagation
        _request_id_ctx_var.set(request_id)

        # Store on request state for easy access
        request.state.request_id = request_id

        # Process request
        response: Response = await call_next(request)

        # Add request ID to response headers
        response.headers[REQUEST_ID_HEADER] = request_id

        return response


def generate_request_id() -> str:
    """Generate a unique request ID.

    Returns:
        UUID4 string in hex format
    """
    return uuid.uuid4().hex


def get_request_id() -> Optional[str]:
    """Get current request ID from async context.

    Returns:
        Request ID if available, None otherwise
    """
    return _request_id_ctx_var.get()


def set_request_id(request_id: str) -> None:
    """Manually set request ID in context.

    Args:
        request_id: Request ID to set

    Usage:
        # When spawning background tasks
        request_id = get_request_id()
        asyncio.create_task(background_task(request_id))

        # In background task:
        set_request_id(request_id)
    """
    _request_id_ctx_var.set(request_id)
