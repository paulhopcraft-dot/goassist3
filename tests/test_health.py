"""Tests for health endpoints - Ops-Runbook-v3.0.md §9.2 compliance."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_healthz_always_returns_alive(self, client: TestClient):
        """Liveness probe should always return 200."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_readyz_returns_component_status(self, client: TestClient):
        """Readiness probe should include component status."""
        response = client.get("/readyz")
        data = response.json()

        assert "status" in data
        assert "components" in data
        assert isinstance(data["components"], dict)

    def test_health_combined_endpoint(self, client: TestClient):
        """Combined health endpoint should provide full status."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "ready" in data
        assert "components" in data

    def test_health_module_state_management(self):
        """Health module should correctly track component states."""
        from src.api.routes import health

        # Reset state
        health.set_ready(False)
        for component in health._components:
            health.set_component_health(component, False)

        # Test state changes
        health.set_component_health("vad", True)
        components = health.get_component_health()
        assert components["vad"] is True

        health.set_ready(True)
        # Note: readyz still returns 503 because not all critical components are ready

    def test_readyz_503_when_critical_components_down(self, client: TestClient):
        """Readiness should return 503 when critical components are down."""
        from src.api.routes import health

        # Ensure critical components are marked as down
        for component in ["asr", "tts", "llm"]:
            health.set_component_health(component, False)

        response = client.get("/readyz")
        # Should be 503 because critical components are not ready
        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"
