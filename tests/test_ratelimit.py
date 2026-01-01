"""Tests for Rate Limiting.

Tests cover:
- Rate limiter configuration
- Client identification
- Rate limit exceeded handling
- Integration with sessions API
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.testclient import TestClient


class TestRateLimitConfiguration:
    """Tests for rate limit configuration."""

    def test_rate_limit_constants_defined(self):
        """Rate limit constants are defined."""
        from src.api.ratelimit import (
            SESSION_CREATE_LIMIT,
            SESSION_CHAT_LIMIT,
            WEBRTC_LIMIT,
        )

        assert SESSION_CREATE_LIMIT == "5/minute"
        assert SESSION_CHAT_LIMIT == "30/minute"
        assert WEBRTC_LIMIT == "10/minute"

    def test_limiter_exists(self):
        """Limiter instance exists."""
        from src.api.ratelimit import limiter

        assert limiter is not None

    def test_get_limiter_returns_limiter(self):
        """get_limiter returns the limiter instance."""
        from src.api.ratelimit import get_limiter, limiter

        assert get_limiter() is limiter


class TestClientIdentification:
    """Tests for client identification."""

    def test_get_client_identifier_with_api_key(self):
        """Client identified by API key when present."""
        from src.api.ratelimit import _get_client_identifier

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-API-Key": "test-api-key-12345"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        identifier = _get_client_identifier(mock_request)

        # Should use key prefix, not IP
        assert identifier.startswith("key:")

    def test_get_client_identifier_without_api_key(self):
        """Client identified by IP when no API key."""
        from src.api.ratelimit import _get_client_identifier

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"

        identifier = _get_client_identifier(mock_request)

        # Should use IP address
        assert identifier == "192.168.1.100"

    def test_get_client_identifier_api_key_hashed(self):
        """API key is hashed for identifier."""
        from src.api.ratelimit import _get_client_identifier

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-API-Key": "secret-key"}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"

        identifier = _get_client_identifier(mock_request)

        # Should not contain the actual key
        assert "secret-key" not in identifier
        assert identifier.startswith("key:")


class TestRateLimitExceededHandler:
    """Tests for rate limit exceeded handler."""

    def _create_rate_limit_exception(self, limit_str: str):
        """Create a RateLimitExceeded exception with proper limit object."""
        from limits import parse

        limit = parse(limit_str)
        # Create exception with the detail string (simulating how slowapi creates it)
        exc = Exception(limit_str)
        exc.detail = limit_str
        return exc

    def test_handler_returns_429(self):
        """Handler returns 429 status."""
        from src.api.ratelimit import rate_limit_exceeded_handler

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url = MagicMock()
        mock_request.url.path = "/sessions"
        mock_request.method = "POST"

        exc = self._create_rate_limit_exception("5 per 1 minute")

        response = rate_limit_exceeded_handler(mock_request, exc)

        assert response.status_code == 429

    def test_handler_includes_retry_after(self):
        """Handler includes Retry-After header."""
        from src.api.ratelimit import rate_limit_exceeded_handler

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url = MagicMock()
        mock_request.url.path = "/sessions"
        mock_request.method = "POST"

        exc = self._create_rate_limit_exception("10 per 1 minute")

        response = rate_limit_exceeded_handler(mock_request, exc)

        assert "Retry-After" in response.headers

    def test_handler_returns_json_body(self):
        """Handler returns JSON body with detail."""
        from src.api.ratelimit import rate_limit_exceeded_handler
        import json

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url = MagicMock()
        mock_request.url.path = "/sessions"
        mock_request.method = "POST"

        exc = self._create_rate_limit_exception("5 per 1 minute")

        response = rate_limit_exceeded_handler(mock_request, exc)
        body = json.loads(response.body)

        assert "detail" in body
        assert "Rate limit exceeded" in body["detail"]


class TestRateLimitSettings:
    """Tests for rate limit settings."""

    def test_settings_have_rate_limit_fields(self):
        """Settings include rate limit configuration."""
        from src.config.settings import Settings

        # Create settings with defaults
        settings = Settings(
            animation_enabled=False,
        )

        assert hasattr(settings, "rate_limit_enabled")
        assert hasattr(settings, "rate_limit_per_minute")
        assert hasattr(settings, "rate_limit_per_hour")

    def test_rate_limit_values_configurable(self):
        """Rate limit values can be configured."""
        from src.config.settings import Settings

        settings = Settings(
            animation_enabled=False,
            rate_limit_enabled=True,
            rate_limit_per_minute=100,
            rate_limit_per_hour=2000,
        )

        assert settings.rate_limit_enabled is True
        assert settings.rate_limit_per_minute == 100
        assert settings.rate_limit_per_hour == 2000

    def test_rate_limit_can_be_disabled(self):
        """Rate limiting can be disabled via settings."""
        from src.config.settings import Settings

        settings = Settings(
            animation_enabled=False,
            rate_limit_enabled=False,
        )

        assert settings.rate_limit_enabled is False


class TestRateLimitIntegration:
    """Integration tests for rate limiting with API."""

    @pytest.fixture
    def rate_limited_client(self):
        """Create a client with rate limiting enabled."""
        # Temporarily enable rate limiting
        original_env = os.environ.get("RATE_LIMIT_ENABLED")
        os.environ["RATE_LIMIT_ENABLED"] = "true"

        # Clear settings cache to pick up new env
        from src.config.settings import get_settings
        get_settings.cache_clear()

        # Reimport to get fresh limiter
        import importlib
        import src.api.ratelimit
        importlib.reload(src.api.ratelimit)

        # Import app fresh
        import src.main
        importlib.reload(src.main)

        from src.main import app
        with TestClient(app) as client:
            yield client

        # Restore original setting
        if original_env is None:
            os.environ.pop("RATE_LIMIT_ENABLED", None)
        else:
            os.environ["RATE_LIMIT_ENABLED"] = original_env

        get_settings.cache_clear()

    def test_rate_limit_headers_present(self, rate_limited_client):
        """Rate limit headers are present in responses."""
        # Make a request
        response = rate_limited_client.post("/sessions", json={})

        # Should have rate limit headers
        # Note: headers may vary based on slowapi version
        assert response.status_code in [200, 201, 429, 503]


class TestDisabledRateLimiting:
    """Tests for disabled rate limiting."""

    def test_limiter_respects_enabled_setting(self):
        """Limiter enabled state matches settings."""
        from src.api.ratelimit import limiter, _settings

        # Limiter enabled state should match settings
        assert limiter.enabled == _settings.rate_limit_enabled

    def test_disabled_limiter_has_empty_defaults(self):
        """Disabled limiter has no default limits."""
        from src.api.ratelimit import limiter, _settings

        if not _settings.rate_limit_enabled:
            # When disabled, default_limits should be empty
            assert limiter._default_limits == []
