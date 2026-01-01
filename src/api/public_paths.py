"""Public Paths Registry - Centralized registry of public/exempt endpoints.

Provides a single source of truth for paths that should bypass various
security middleware (authentication, CSRF, rate limiting).

Usage:
    from src.api.public_paths import is_health_path, is_public_path

    if is_health_path(request.url.path):
        # Skip authentication
        return

Categories:
    - HEALTH_PATHS: Kubernetes probes, bypass all security
    - DOCS_PATHS: API documentation, bypass CSRF but may need auth
    - PUBLIC_PATHS: Union of all paths that bypass authentication

Reference: TODO-IMPROVEMENTS.md Phase 1
"""

from typing import Final

# Health probe endpoints - bypass ALL security (auth, CSRF, rate limiting)
# Used by Kubernetes liveness/readiness probes
HEALTH_PATHS: Final[frozenset[str]] = frozenset({
    "/health",
    "/healthz",
    "/readyz",
})

# API documentation endpoints - bypass CSRF but may require auth in production
DOCS_PATHS: Final[frozenset[str]] = frozenset({
    "/docs",
    "/redoc",
    "/openapi.json",
})

# Metrics endpoint - bypass auth for Prometheus scraping
METRICS_PATHS: Final[frozenset[str]] = frozenset({
    "/metrics",
})

# All paths that bypass authentication
PUBLIC_PATHS: Final[frozenset[str]] = HEALTH_PATHS | METRICS_PATHS

# All paths that bypass CSRF validation
CSRF_EXEMPT_PATHS: Final[frozenset[str]] = HEALTH_PATHS | DOCS_PATHS | METRICS_PATHS


def is_health_path(path: str) -> bool:
    """Check if path is a health probe endpoint.

    Args:
        path: Request URL path

    Returns:
        True if path is a health endpoint

    Example:
        >>> is_health_path("/health")
        True
        >>> is_health_path("/api/sessions")
        False
    """
    return path in HEALTH_PATHS


def is_public_path(path: str) -> bool:
    """Check if path is publicly accessible (no authentication required).

    Args:
        path: Request URL path

    Returns:
        True if path is public

    Example:
        >>> is_public_path("/healthz")
        True
        >>> is_public_path("/sessions")
        False
    """
    return path in PUBLIC_PATHS


def is_csrf_exempt(path: str) -> bool:
    """Check if path is exempt from CSRF validation.

    Args:
        path: Request URL path

    Returns:
        True if path should skip CSRF validation

    Example:
        >>> is_csrf_exempt("/health")
        True
        >>> is_csrf_exempt("/docs")
        True
        >>> is_csrf_exempt("/sessions")
        False
    """
    return path in CSRF_EXEMPT_PATHS


def is_docs_path(path: str) -> bool:
    """Check if path is an API documentation endpoint.

    Args:
        path: Request URL path

    Returns:
        True if path is a documentation endpoint

    Example:
        >>> is_docs_path("/docs")
        True
        >>> is_docs_path("/health")
        False
    """
    return path in DOCS_PATHS


def register_public_path(path: str) -> None:
    """Register a new public path at runtime.

    Note: This modifies the module-level sets. Use sparingly,
    primarily for testing or plugin systems.

    Args:
        path: Path to register as public
    """
    global PUBLIC_PATHS, CSRF_EXEMPT_PATHS
    # Convert to mutable set, add, convert back to frozenset
    PUBLIC_PATHS = frozenset(PUBLIC_PATHS | {path})
    CSRF_EXEMPT_PATHS = frozenset(CSRF_EXEMPT_PATHS | {path})


def get_all_public_paths() -> list[str]:
    """Get all registered public paths.

    Returns:
        Sorted list of all public paths

    Useful for documentation and debugging.
    """
    return sorted(PUBLIC_PATHS)


def get_all_csrf_exempt_paths() -> list[str]:
    """Get all CSRF-exempt paths.

    Returns:
        Sorted list of all CSRF-exempt paths

    Useful for documentation and debugging.
    """
    return sorted(CSRF_EXEMPT_PATHS)
