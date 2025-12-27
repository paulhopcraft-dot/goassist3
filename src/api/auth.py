"""API Authentication - API key middleware for protected endpoints.

Provides authentication for the GoAssist API:
- API key validation via X-API-Key header
- Skips auth in development mode when no key configured
- Always skips auth for health endpoints

Reference: Implementation-v3.0.md §4.4
"""

import hashlib
import secrets
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from src.config.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)

# API key header extractor
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return secrets.compare_digest(a.encode(), b.encode())


async def verify_api_key(
    request: Request,
    api_key: str | None = Depends(api_key_header),
) -> None:
    """Verify API key from request header.

    Raises:
        HTTPException: 401 if authentication fails

    Note:
        - Skips auth for health endpoints (/health, /healthz, /readyz)
        - Skips auth in development if no API key is configured
        - Uses constant-time comparison to prevent timing attacks
    """
    settings = get_settings()

    # Skip auth for health endpoints
    if request.url.path in ["/health", "/healthz", "/readyz"]:
        return

    # Skip if auth is disabled
    if not settings.auth_enabled:
        return

    # In development without configured key, skip auth with warning
    if settings.environment == "development" and not settings.api_key:
        logger.debug(
            "auth_skipped",
            reason="development_no_key",
            path=request.url.path,
        )
        return

    # Check if API key is provided
    if not api_key:
        logger.warning(
            "auth_failed",
            reason="missing_api_key",
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key with constant-time comparison
    if not _constant_time_compare(api_key, settings.api_key or ""):
        logger.warning(
            "auth_failed",
            reason="invalid_api_key",
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug(
        "auth_success",
        path=request.url.path,
    )


def get_auth_dependency():
    """Get authentication dependency based on settings.

    Returns dependency that can be used with FastAPI's Depends().

    Usage:
        app = FastAPI(dependencies=[Depends(get_auth_dependency())])

    Or for specific routes:
        @router.get("/protected", dependencies=[Depends(verify_api_key)])
        async def protected():
            ...
    """
    return verify_api_key


def generate_api_key() -> str:
    """Generate a secure random API key.

    Returns:
        32-byte hex-encoded API key (64 characters)
    """
    return secrets.token_hex(32)
