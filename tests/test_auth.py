"""Tests for API Authentication."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.auth import verify_api_key, generate_api_key, _constant_time_compare


class TestGenerateApiKey:
    """Tests for API key generation."""

    def test_generate_api_key_length(self):
        """Test generated key is 64 characters (32 bytes hex)."""
        key = generate_api_key()
        assert len(key) == 64

    def test_generate_api_key_is_hex(self):
        """Test generated key is valid hex."""
        key = generate_api_key()
        # Should not raise
        int(key, 16)

    def test_generate_api_key_unique(self):
        """Test generated keys are unique."""
        keys = [generate_api_key() for _ in range(10)]
        assert len(set(keys)) == 10


class TestConstantTimeCompare:
    """Tests for constant-time comparison."""

    def test_equal_strings(self):
        """Test equal strings return True."""
        assert _constant_time_compare("test123", "test123") is True

    def test_unequal_strings(self):
        """Test unequal strings return False."""
        assert _constant_time_compare("test123", "test456") is False

    def test_empty_strings(self):
        """Test empty strings."""
        assert _constant_time_compare("", "") is True
        assert _constant_time_compare("a", "") is False


class TestAuthEndpoint:
    """Tests for authentication endpoint behavior."""

    @pytest.fixture
    def app_with_auth(self):
        """Create test app with authenticated route."""
        from fastapi import Depends
        from src.api.auth import verify_api_key

        app = FastAPI()

        @app.get("/protected")
        async def protected(auth=Depends(verify_api_key)):
            return {"status": "ok"}

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        return app

    def test_health_endpoint_no_auth_required(self, app_with_auth):
        """Test health endpoints don't require auth."""
        client = TestClient(app_with_auth)
        response = client.get("/health")
        assert response.status_code == 200

    @patch("src.api.auth.get_settings")
    def test_auth_disabled_allows_access(self, mock_settings, app_with_auth):
        """Test auth disabled allows all access."""
        mock_settings.return_value.auth_enabled = False
        mock_settings.return_value.api_key = "test-key"

        client = TestClient(app_with_auth)
        response = client.get("/protected")
        assert response.status_code == 200

    @patch("src.api.auth.get_settings")
    def test_development_no_key_allows_access(self, mock_settings, app_with_auth):
        """Test development mode without key allows access."""
        mock_settings.return_value.auth_enabled = True
        mock_settings.return_value.environment = "development"
        mock_settings.return_value.api_key = None

        client = TestClient(app_with_auth)
        response = client.get("/protected")
        assert response.status_code == 200

    @patch("src.api.auth.get_settings")
    def test_missing_key_returns_401(self, mock_settings, app_with_auth):
        """Test missing API key returns 401."""
        mock_settings.return_value.auth_enabled = True
        mock_settings.return_value.environment = "production"
        mock_settings.return_value.api_key = "valid-key"

        client = TestClient(app_with_auth)
        response = client.get("/protected")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    @patch("src.api.auth.get_settings")
    def test_invalid_key_returns_401(self, mock_settings, app_with_auth):
        """Test invalid API key returns 401."""
        mock_settings.return_value.auth_enabled = True
        mock_settings.return_value.environment = "production"
        mock_settings.return_value.api_key = "valid-key"

        client = TestClient(app_with_auth)
        response = client.get("/protected", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @patch("src.api.auth.get_settings")
    def test_valid_key_allows_access(self, mock_settings, app_with_auth):
        """Test valid API key allows access."""
        mock_settings.return_value.auth_enabled = True
        mock_settings.return_value.environment = "production"
        mock_settings.return_value.api_key = "valid-key"

        client = TestClient(app_with_auth)
        response = client.get("/protected", headers={"X-API-Key": "valid-key"})
        assert response.status_code == 200
