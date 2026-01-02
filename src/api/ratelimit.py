"""Rate Limiting - Protect API endpoints from abuse.

Uses slowapi for FastAPI-compatible rate limiting.

Reference: TODO-IMPROVEMENTS.md Phase 1
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from fastapi import Request
from fastapi.responses import JSONResponse

from src.config.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)


def _get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting.

    Uses API key if present (for authenticated requests),
    otherwise falls back to IP address.

    Args:
        request: FastAPI request object

    Returns:
        Client identifier string
    """
    # Try to get API key from header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Use hash of API key to avoid logging sensitive data
        return f"key:{hash(api_key) % 10000:04d}"

    # Fall back to IP address
    return get_remote_address(request)


# Create the limiter instance
# Uses in-memory storage by default; can be configured for Redis in production
# Note: default_limits is computed at import time from settings
_settings = get_settings()
_default_limits = [
    f"{_settings.rate_limit_per_minute}/minute",
    f"{_settings.rate_limit_per_hour}/hour",
]

# Only create real limiter if rate limiting is enabled
if _settings.rate_limit_enabled:
    limiter = Limiter(
        key_func=_get_client_identifier,
        default_limits=_default_limits,
        headers_enabled=True,  # Include X-RateLimit-* headers in responses
        strategy="fixed-window",  # Simple fixed window strategy
        enabled=True,
    )
else:
    # Create a disabled limiter for testing
    limiter = Limiter(
        key_func=_get_client_identifier,
        default_limits=[],
        enabled=False,
    )


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors.

    Args:
        request: FastAPI request object
        exc: Rate limit exceeded exception

    Returns:
        JSON response with 429 status
    """
    client_id = _get_client_identifier(request)
    logger.warning(
        "rate_limit_exceeded",
        client_id=client_id,
        path=request.url.path,
        method=request.method,
        limit=str(exc.detail),
    )

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down.",
            "retry_after": exc.detail,
        },
        headers={
            "Retry-After": str(exc.detail),
            "X-RateLimit-Limit": str(exc.detail),
        },
    )


# Specific rate limits for different endpoint types
SESSION_CREATE_LIMIT = "5/minute"  # Session creation is expensive
SESSION_CHAT_LIMIT = "30/minute"  # Chat is more frequent
WEBRTC_LIMIT = "10/minute"  # WebRTC signaling


def get_limiter() -> Limiter:
    """Get the global limiter instance.

    Returns:
        Configured Limiter instance
    """
    return limiter
