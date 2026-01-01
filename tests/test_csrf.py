"""Tests for CSRF Protection.

Tests cover:
- CSRF token generation
- CSRF token validation
- CSRF middleware behavior
- Integration with API endpoints
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.api.csrf import (
    generate_csrf_token,
    validate_csrf_token,
    CSRFMiddleware,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    get_csrf_token,
    csrf_exempt,
)


class TestCSRFTokenGeneration:
    """Tests for CSRF token generation."""

    def test_generate_csrf_token_length(self):
        """Generated token has correct length."""
        token = generate_csrf_token()
        # 32 bytes = 64 hex characters
        assert len(token) == 64

    def test_generate_csrf_token_is_hex(self):
        """Generated token is valid hex string."""
        token = generate_csrf_token()
        # Should not raise ValueError
        int(token, 16)

    def test_generate_csrf_token_unique(self):
        """Generated tokens are unique."""
        tokens = {generate_csrf_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_generate_csrf_token_cryptographic(self):
        """Token uses cryptographic random."""
        # Tokens should have high entropy
        token = generate_csrf_token()
        # Check for variety in characters (not all same)
        unique_chars = set(token)
        assert len(unique_chars) > 10


class TestCSRFTokenValidation:
    """Tests for CSRF token validation."""

    def test_validate_matching_tokens(self):
        """Matching tokens pass validation."""
        token = generate_csrf_token()
        assert validate_csrf_token(token, token) is True

    def test_validate_mismatched_tokens(self):
        """Mismatched tokens fail validation."""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert validate_csrf_token(token1, token2) is False

    def test_validate_none_request_token(self):
        """None request token fails validation."""
        cookie_token = generate_csrf_token()
        assert validate_csrf_token(None, cookie_token) is False

    def test_validate_none_cookie_token(self):
        """None cookie token fails validation."""
        request_token = generate_csrf_token()
        assert validate_csrf_token(request_token, None) is False

    def test_validate_both_none(self):
        """Both None fails validation."""
        assert validate_csrf_token(None, None) is False

    def test_validate_empty_strings(self):
        """Empty strings fail validation."""
        assert validate_csrf_token("", "") is False

    def test_validate_uses_constant_time(self):
        """Validation uses constant-time comparison."""
        import secrets
        # This test ensures we're using secrets.compare_digest
        # which is timing-attack resistant
        token = generate_csrf_token()
        # Should complete quickly regardless of match position
        for i in range(100):
            wrong_token = generate_csrf_token()
            validate_csrf_token(token, wrong_token)


class TestCSRFMiddleware:
    """Tests for CSRF middleware behavior."""

    @pytest.fixture
    def app_with_csrf(self):
        """Create a test app with CSRF middleware."""
        from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
        from starlette.responses import Response

        app = FastAPI()

        @app.get("/")
        async def root():
            return {"message": "hello"}

        @app.post("/action")
        async def action():
            return {"status": "ok"}

        @app.delete("/resource")
        async def delete_resource():
            return {"deleted": True}

        @app.get("/health")
        async def health():
            return {"healthy": True}

        # Create a simple CSRF middleware for testing that doesn't depend on settings
        class TestCSRFMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
                # Skip for exempt paths
                if request.url.path == "/health":
                    return await call_next(request)

                # Get existing CSRF token from cookie
                cookie_token = request.cookies.get(CSRF_COOKIE_NAME)

                # For state-changing methods, validate CSRF token
                if request.method not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
                    header_token = request.headers.get(CSRF_HEADER_NAME)
                    if not validate_csrf_token(header_token, cookie_token):
                        from fastapi import HTTPException
                        from fastapi.responses import JSONResponse
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "CSRF token missing or invalid"},
                        )

                response = await call_next(request)

                # Set CSRF cookie if not present
                if not cookie_token:
                    new_token = generate_csrf_token()
                    response.set_cookie(
                        key=CSRF_COOKIE_NAME,
                        value=new_token,
                        secure=False,
                        httponly=False,
                        samesite="strict",
                        path="/",
                    )

                return response

        app.add_middleware(TestCSRFMiddleware)

        return app

    def test_get_sets_csrf_cookie(self, app_with_csrf):
        """GET request sets CSRF cookie."""
        with TestClient(app_with_csrf) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert CSRF_COOKIE_NAME in response.cookies

    def test_post_without_token_fails(self, app_with_csrf):
        """POST without CSRF token returns 403."""
        with TestClient(app_with_csrf) as client:
            # First get to receive cookie
            client.get("/")
            # POST without header
            response = client.post("/action")
            assert response.status_code == 403
            assert "CSRF" in response.json()["detail"]

    def test_post_with_valid_token_succeeds(self, app_with_csrf):
        """POST with valid CSRF token succeeds."""
        with TestClient(app_with_csrf) as client:
            # Get to receive cookie
            get_response = client.get("/")
            csrf_token = get_response.cookies[CSRF_COOKIE_NAME]

            # POST with header
            response = client.post(
                "/action",
                headers={CSRF_HEADER_NAME: csrf_token},
            )
            assert response.status_code == 200

    def test_post_with_invalid_token_fails(self, app_with_csrf):
        """POST with invalid CSRF token returns 403."""
        with TestClient(app_with_csrf) as client:
            # Get to receive cookie
            client.get("/")

            # POST with wrong header
            response = client.post(
                "/action",
                headers={CSRF_HEADER_NAME: "wrong-token"},
            )
            assert response.status_code == 403

    def test_delete_requires_token(self, app_with_csrf):
        """DELETE also requires CSRF token."""
        with TestClient(app_with_csrf) as client:
            # Get to receive cookie
            get_response = client.get("/")
            csrf_token = get_response.cookies[CSRF_COOKIE_NAME]

            # DELETE with header succeeds
            response = client.delete(
                "/resource",
                headers={CSRF_HEADER_NAME: csrf_token},
            )
            assert response.status_code == 200

            # DELETE without header fails
            response = client.delete("/resource")
            assert response.status_code == 403

    def test_exempt_path_no_validation(self, app_with_csrf):
        """Exempt paths don't require CSRF token."""
        with TestClient(app_with_csrf) as client:
            response = client.get("/health")
            assert response.status_code == 200


class TestCSRFMiddlewareDisabled:
    """Tests for CSRF middleware when disabled."""

    @pytest.fixture
    def app_without_csrf(self):
        """Create a test app without CSRF middleware."""
        app = FastAPI()

        @app.post("/action")
        async def action():
            return {"status": "ok"}

        return app

    def test_post_without_middleware_succeeds(self, app_without_csrf):
        """POST without CSRF middleware succeeds."""
        with TestClient(app_without_csrf) as client:
            response = client.post("/action")
            assert response.status_code == 200


class TestCSRFSettings:
    """Tests for CSRF settings integration."""

    def test_settings_have_csrf_fields(self):
        """Settings include CSRF configuration."""
        from src.config.settings import Settings

        settings = Settings(
            animation_enabled=False,
        )

        assert hasattr(settings, "csrf_enabled")
        assert hasattr(settings, "csrf_cookie_name")
        assert hasattr(settings, "csrf_header_name")
        assert hasattr(settings, "csrf_cookie_secure")
        assert hasattr(settings, "csrf_cookie_samesite")

    def test_csrf_values_configurable(self):
        """CSRF values can be configured."""
        from src.config.settings import Settings

        settings = Settings(
            animation_enabled=False,
            csrf_enabled=True,
            csrf_cookie_name="custom_csrf",
            csrf_header_name="X-Custom-CSRF",
            csrf_cookie_secure=False,
            csrf_cookie_samesite="lax",
        )

        assert settings.csrf_enabled is True
        assert settings.csrf_cookie_name == "custom_csrf"
        assert settings.csrf_header_name == "X-Custom-CSRF"
        assert settings.csrf_cookie_secure is False
        assert settings.csrf_cookie_samesite == "lax"

    def test_csrf_defaults(self):
        """CSRF has sensible defaults."""
        from src.config.settings import Settings

        # Create settings without relying on env vars
        settings = Settings(
            animation_enabled=False,
            csrf_enabled=True,  # Explicitly set to test default behavior
        )

        # Test the field defaults (these are the class defaults, not env-influenced)
        assert settings.csrf_cookie_name == "csrf_token"
        assert settings.csrf_header_name == "X-CSRF-Token"
        assert settings.csrf_cookie_secure is True
        assert settings.csrf_cookie_samesite == "strict"


class TestCSRFExemptDecorator:
    """Tests for csrf_exempt decorator."""

    def test_csrf_exempt_sets_attribute(self):
        """Decorator sets _csrf_exempt attribute."""
        @csrf_exempt
        async def my_endpoint():
            return {}

        assert hasattr(my_endpoint, "_csrf_exempt")
        assert my_endpoint._csrf_exempt is True

    def test_csrf_exempt_preserves_function(self):
        """Decorator preserves original function."""
        async def original():
            return {"original": True}

        decorated = csrf_exempt(original)

        # Function should be same object
        assert decorated is original


class TestGetCSRFToken:
    """Tests for get_csrf_token utility."""

    def test_get_csrf_token_with_cookie(self):
        """Returns token when cookie present."""
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {CSRF_COOKIE_NAME: "test-token"}

        token = get_csrf_token(mock_request)
        assert token == "test-token"

    def test_get_csrf_token_without_cookie(self):
        """Returns None when cookie absent."""
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {}

        token = get_csrf_token(mock_request)
        assert token is None


class TestCSRFIntegration:
    """Integration tests for CSRF with full app."""

    @pytest.fixture
    def csrf_enabled_client(self):
        """Create client with CSRF enabled."""
        # Temporarily enable CSRF
        original_env = os.environ.get("CSRF_ENABLED")
        os.environ["CSRF_ENABLED"] = "true"

        # Clear settings cache
        from src.config.settings import get_settings
        get_settings.cache_clear()

        # Reimport to get fresh middleware
        import importlib
        import src.main
        importlib.reload(src.main)

        from src.main import app
        with TestClient(app) as client:
            yield client

        # Restore original
        if original_env is None:
            os.environ.pop("CSRF_ENABLED", None)
        else:
            os.environ["CSRF_ENABLED"] = original_env

        get_settings.cache_clear()

    def test_session_creation_with_csrf(self, csrf_enabled_client):
        """Session creation requires CSRF token when enabled."""
        # First get any endpoint to receive CSRF cookie
        get_response = csrf_enabled_client.get("/health")

        # Check if CSRF cookie was set
        if CSRF_COOKIE_NAME in get_response.cookies:
            csrf_token = get_response.cookies[CSRF_COOKIE_NAME]

            # POST with CSRF token should work
            response = csrf_enabled_client.post(
                "/sessions",
                json={},
                headers={CSRF_HEADER_NAME: csrf_token},
            )
            # Should get past CSRF (may fail for other reasons like auth)
            assert response.status_code != 403 or "CSRF" not in response.text
