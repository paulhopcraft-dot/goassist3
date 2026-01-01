"""Tests for Public Paths Registry.

Tests cover:
- Health path detection
- Public path detection
- CSRF exempt path detection
- Documentation path detection
- Path registration
- Path listing utilities
"""

import pytest

from src.api.public_paths import (
    HEALTH_PATHS,
    DOCS_PATHS,
    METRICS_PATHS,
    PUBLIC_PATHS,
    CSRF_EXEMPT_PATHS,
    is_health_path,
    is_public_path,
    is_csrf_exempt,
    is_docs_path,
    get_all_public_paths,
    get_all_csrf_exempt_paths,
)


class TestHealthPaths:
    """Tests for health path constants and detection."""

    def test_health_paths_contains_standard_endpoints(self):
        """Standard health endpoints are included."""
        assert "/health" in HEALTH_PATHS
        assert "/healthz" in HEALTH_PATHS
        assert "/readyz" in HEALTH_PATHS

    def test_health_paths_is_frozenset(self):
        """Health paths are immutable frozenset."""
        assert isinstance(HEALTH_PATHS, frozenset)

    def test_is_health_path_returns_true_for_health(self):
        """is_health_path returns True for health endpoints."""
        assert is_health_path("/health") is True
        assert is_health_path("/healthz") is True
        assert is_health_path("/readyz") is True

    def test_is_health_path_returns_false_for_other(self):
        """is_health_path returns False for non-health endpoints."""
        assert is_health_path("/") is False
        assert is_health_path("/api") is False
        assert is_health_path("/sessions") is False
        assert is_health_path("/docs") is False

    def test_is_health_path_exact_match_only(self):
        """is_health_path only matches exact paths."""
        assert is_health_path("/health/") is False
        assert is_health_path("/health/check") is False
        assert is_health_path("/api/health") is False


class TestDocsPaths:
    """Tests for documentation path constants and detection."""

    def test_docs_paths_contains_standard_endpoints(self):
        """Standard documentation endpoints are included."""
        assert "/docs" in DOCS_PATHS
        assert "/redoc" in DOCS_PATHS
        assert "/openapi.json" in DOCS_PATHS

    def test_docs_paths_is_frozenset(self):
        """Docs paths are immutable frozenset."""
        assert isinstance(DOCS_PATHS, frozenset)

    def test_is_docs_path_returns_true_for_docs(self):
        """is_docs_path returns True for documentation endpoints."""
        assert is_docs_path("/docs") is True
        assert is_docs_path("/redoc") is True
        assert is_docs_path("/openapi.json") is True

    def test_is_docs_path_returns_false_for_other(self):
        """is_docs_path returns False for non-docs endpoints."""
        assert is_docs_path("/health") is False
        assert is_docs_path("/api") is False
        assert is_docs_path("/sessions") is False


class TestMetricsPaths:
    """Tests for metrics path constants."""

    def test_metrics_paths_contains_standard_endpoint(self):
        """Standard metrics endpoint is included."""
        assert "/metrics" in METRICS_PATHS

    def test_metrics_paths_is_frozenset(self):
        """Metrics paths are immutable frozenset."""
        assert isinstance(METRICS_PATHS, frozenset)


class TestPublicPaths:
    """Tests for public path detection."""

    def test_public_paths_includes_health(self):
        """Public paths include all health paths."""
        for path in HEALTH_PATHS:
            assert path in PUBLIC_PATHS

    def test_public_paths_includes_metrics(self):
        """Public paths include metrics paths."""
        for path in METRICS_PATHS:
            assert path in PUBLIC_PATHS

    def test_public_paths_excludes_docs(self):
        """Public paths do NOT include docs (may need auth)."""
        for path in DOCS_PATHS:
            assert path not in PUBLIC_PATHS

    def test_is_public_path_returns_true_for_health(self):
        """is_public_path returns True for health endpoints."""
        assert is_public_path("/health") is True
        assert is_public_path("/healthz") is True
        assert is_public_path("/readyz") is True

    def test_is_public_path_returns_true_for_metrics(self):
        """is_public_path returns True for metrics endpoint."""
        assert is_public_path("/metrics") is True

    def test_is_public_path_returns_false_for_protected(self):
        """is_public_path returns False for protected endpoints."""
        assert is_public_path("/sessions") is False
        assert is_public_path("/api/v1/chat") is False
        assert is_public_path("/docs") is False  # Docs may need auth


class TestCSRFExemptPaths:
    """Tests for CSRF exempt path detection."""

    def test_csrf_exempt_includes_health(self):
        """CSRF exempt paths include all health paths."""
        for path in HEALTH_PATHS:
            assert path in CSRF_EXEMPT_PATHS

    def test_csrf_exempt_includes_docs(self):
        """CSRF exempt paths include documentation paths."""
        for path in DOCS_PATHS:
            assert path in CSRF_EXEMPT_PATHS

    def test_csrf_exempt_includes_metrics(self):
        """CSRF exempt paths include metrics paths."""
        for path in METRICS_PATHS:
            assert path in CSRF_EXEMPT_PATHS

    def test_is_csrf_exempt_returns_true_for_health(self):
        """is_csrf_exempt returns True for health endpoints."""
        assert is_csrf_exempt("/health") is True
        assert is_csrf_exempt("/healthz") is True
        assert is_csrf_exempt("/readyz") is True

    def test_is_csrf_exempt_returns_true_for_docs(self):
        """is_csrf_exempt returns True for documentation endpoints."""
        assert is_csrf_exempt("/docs") is True
        assert is_csrf_exempt("/redoc") is True
        assert is_csrf_exempt("/openapi.json") is True

    def test_is_csrf_exempt_returns_false_for_api(self):
        """is_csrf_exempt returns False for API endpoints."""
        assert is_csrf_exempt("/sessions") is False
        assert is_csrf_exempt("/api/chat") is False


class TestPathListingUtilities:
    """Tests for path listing utilities."""

    def test_get_all_public_paths_returns_sorted_list(self):
        """get_all_public_paths returns sorted list."""
        paths = get_all_public_paths()
        assert isinstance(paths, list)
        assert paths == sorted(paths)

    def test_get_all_public_paths_contains_health(self):
        """get_all_public_paths includes health paths."""
        paths = get_all_public_paths()
        assert "/health" in paths
        assert "/healthz" in paths
        assert "/readyz" in paths

    def test_get_all_csrf_exempt_paths_returns_sorted_list(self):
        """get_all_csrf_exempt_paths returns sorted list."""
        paths = get_all_csrf_exempt_paths()
        assert isinstance(paths, list)
        assert paths == sorted(paths)

    def test_get_all_csrf_exempt_paths_contains_all(self):
        """get_all_csrf_exempt_paths includes health and docs."""
        paths = get_all_csrf_exempt_paths()
        assert "/health" in paths
        assert "/docs" in paths
        assert "/metrics" in paths


class TestPathSetRelationships:
    """Tests for relationships between path sets."""

    def test_health_is_subset_of_public(self):
        """Health paths are subset of public paths."""
        assert HEALTH_PATHS.issubset(PUBLIC_PATHS)

    def test_health_is_subset_of_csrf_exempt(self):
        """Health paths are subset of CSRF exempt paths."""
        assert HEALTH_PATHS.issubset(CSRF_EXEMPT_PATHS)

    def test_docs_is_subset_of_csrf_exempt(self):
        """Docs paths are subset of CSRF exempt paths."""
        assert DOCS_PATHS.issubset(CSRF_EXEMPT_PATHS)

    def test_metrics_is_subset_of_public(self):
        """Metrics paths are subset of public paths."""
        assert METRICS_PATHS.issubset(PUBLIC_PATHS)

    def test_public_is_subset_of_csrf_exempt(self):
        """Public paths are subset of CSRF exempt paths."""
        assert PUBLIC_PATHS.issubset(CSRF_EXEMPT_PATHS)
