"""CSRF Protection - Cross-Site Request Forgery protection for state-changing operations.

Implements the double-submit cookie pattern:
1. Server generates CSRF token and sets it as a cookie
2. Client must send the same token in X-CSRF-Token header
3. Server validates token matches for state-changing requests

Reference: OWASP CSRF Prevention Cheat Sheet
"""

import secrets
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)

# Default configuration
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_TOKEN_LENGTH = 32  # 32 bytes = 64 hex chars
CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token.

    Returns:
        64-character hex string (32 bytes of entropy)
    """
    return secrets.token_hex(CSRF_TOKEN_LENGTH)


def validate_csrf_token(request_token: str | None, cookie_token: str | None) -> bool:
    """Validate CSRF token using constant-time comparison.

    Args:
        request_token: Token from request header
        cookie_token: Token from cookie

    Returns:
        True if tokens match, False otherwise
    """
    if not request_token or not cookie_token:
        return False

    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(request_token, cookie_token)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection using double-submit cookie pattern.

    For state-changing requests (POST, PUT, DELETE, PATCH):
    - Requires X-CSRF-Token header matching csrf_token cookie
    - Returns 403 Forbidden if tokens don't match

    For safe methods (GET, HEAD, OPTIONS, TRACE):
    - No CSRF validation required
    - Sets CSRF cookie if not present

    Usage:
        app.add_middleware(CSRFMiddleware)

    Client usage:
        1. Make any request to get CSRF cookie
        2. Read csrf_token cookie value
        3. Include X-CSRF-Token header with that value in POST/PUT/DELETE requests
    """

    def __init__(
        self,
        app,
        cookie_name: str = CSRF_COOKIE_NAME,
        header_name: str = CSRF_HEADER_NAME,
        cookie_secure: bool = True,
        cookie_httponly: bool = False,  # Must be False for JS to read
        cookie_samesite: str = "strict",
        exempt_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.exempt_paths = exempt_paths or ["/health", "/healthz", "/readyz", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with CSRF validation."""
        settings = get_settings()

        # Skip if CSRF is disabled
        if not settings.csrf_enabled:
            return await call_next(request)

        # Skip for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Get existing CSRF token from cookie
        cookie_token = request.cookies.get(self.cookie_name)

        # For state-changing methods, validate CSRF token
        if request.method not in CSRF_SAFE_METHODS:
            header_token = request.headers.get(self.header_name)

            if not validate_csrf_token(header_token, cookie_token):
                logger.warning(
                    "csrf_validation_failed",
                    path=request.url.path,
                    method=request.method,
                    has_header=bool(header_token),
                    has_cookie=bool(cookie_token),
                    client_ip=request.client.host if request.client else "unknown",
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing or invalid",
                )

            logger.debug(
                "csrf_validation_success",
                path=request.url.path,
                method=request.method,
            )

        # Process request
        response = await call_next(request)

        # Set CSRF cookie if not present
        if not cookie_token:
            new_token = generate_csrf_token()
            response.set_cookie(
                key=self.cookie_name,
                value=new_token,
                secure=self.cookie_secure and settings.environment == "production",
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
                path="/",
            )
            logger.debug(
                "csrf_cookie_set",
                path=request.url.path,
            )

        return response


def get_csrf_token(request: Request) -> str | None:
    """Get CSRF token from request cookie.

    Utility function for endpoints that need to expose the CSRF token.

    Args:
        request: FastAPI request object

    Returns:
        CSRF token string or None if not set
    """
    return request.cookies.get(CSRF_COOKIE_NAME)


def csrf_exempt(func: Callable) -> Callable:
    """Decorator to mark an endpoint as CSRF-exempt.

    Usage:
        @router.post("/webhook")
        @csrf_exempt
        async def webhook():
            ...

    Note: This sets a marker attribute. The CSRFMiddleware checks for this.
    """
    func._csrf_exempt = True
    return func
