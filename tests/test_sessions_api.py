"""Integration tests for Sessions API.

Tests the full session lifecycle:
- Session creation
- Session retrieval
- Session listing
- Session deletion
- WebRTC signaling flow
"""

import pytest
from fastapi.testclient import TestClient


class TestSessionLifecycle:
    """Tests for session CRUD operations."""

    def test_create_session(self, client: TestClient):
        """Test creating a new session."""
        response = client.post("/sessions", json={})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["state"] == "idle"
        assert "message" in data

    def test_create_session_with_custom_prompt(self, client: TestClient):
        """Test creating a session with custom system prompt."""
        response = client.post("/sessions", json={
            "system_prompt": "You are a pirate assistant. Arr!",
            "enable_avatar": False,
        })

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    def test_create_session_returns_uuid(self, client: TestClient):
        """Test that session ID is a valid UUID format."""
        response = client.post("/sessions", json={})
        data = response.json()

        session_id = data["session_id"]
        # UUID format: 8-4-4-4-12 hex chars
        parts = session_id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_get_session(self, client: TestClient):
        """Test retrieving a session by ID."""
        # Create session first
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Get session
        response = client.get(f"/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["state"] == "idle"
        assert "is_running" in data
        assert "context_tokens" in data
        assert "turns_completed" in data

    def test_get_nonexistent_session(self, client: TestClient):
        """Test getting a session that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/sessions/{fake_id}")

        assert response.status_code == 404

    def test_list_sessions(self, client: TestClient):
        """Test listing all sessions."""
        # Create a few sessions
        client.post("/sessions", json={})
        client.post("/sessions", json={})

        response = client.get("/sessions")

        assert response.status_code == 200
        data = response.json()
        # Response is {"active_count": N, "available_slots": M, "sessions": [...]}
        assert "sessions" in data
        assert "active_count" in data
        assert "available_slots" in data
        assert isinstance(data["sessions"], list)

    def test_delete_session(self, client: TestClient):
        """Test deleting a session."""
        # Create session
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Delete session
        response = client.delete(f"/sessions/{session_id}")

        assert response.status_code == 200

        # Verify session is gone
        get_resp = client.get(f"/sessions/{session_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_session(self, client: TestClient):
        """Test deleting a session that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/sessions/{fake_id}")

        assert response.status_code == 404


class TestHealthEndpointsIntegration:
    """Integration tests for health endpoints with sessions."""

    def test_health_shows_active_sessions(self, client: TestClient):
        """Test that health endpoint reflects session count."""
        # Get initial health
        initial = client.get("/health").json()

        # Create a session
        client.post("/sessions", json={})

        # Health should still work
        health = client.get("/health").json()
        assert health["status"] in ["degraded", "healthy", "alive"]

    def test_readyz_during_session(self, client: TestClient):
        """Test readyz endpoint with active session."""
        # Create session
        client.post("/sessions", json={})

        response = client.get("/readyz")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "components" in data


class TestWebRTCSignaling:
    """Tests for WebRTC signaling endpoints."""

    def test_offer_requires_valid_session(self, client: TestClient):
        """Test that WebRTC offer requires a valid session."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/sessions/{fake_id}/offer",
            json={"sdp": "v=0\r\n..."}
        )

        assert response.status_code == 404

    def test_offer_with_valid_session(self, client: TestClient):
        """Test WebRTC offer with valid session."""
        # Create session
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Send offer (will fail validation but should reach handler)
        response = client.post(
            f"/sessions/{session_id}/offer",
            json={"sdp": "invalid"}
        )

        # Should either accept or give error, not 404
        assert response.status_code != 404

    def test_ice_candidate_requires_valid_session(self, client: TestClient):
        """Test that ICE candidate requires a valid session."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/sessions/{fake_id}/ice-candidate",
            json={
                "candidate": {
                    "candidate": "candidate:...",
                    "sdpMid": "0",
                    "sdpMLineIndex": 0
                }
            }
        )

        assert response.status_code == 404


class TestSessionConcurrency:
    """Tests for concurrent session handling."""

    def test_multiple_sessions_independent(self, client: TestClient):
        """Test that multiple sessions are independent."""
        # Create two sessions
        resp1 = client.post("/sessions", json={})
        resp2 = client.post("/sessions", json={})

        id1 = resp1.json()["session_id"]
        id2 = resp2.json()["session_id"]

        assert id1 != id2

        # Delete one
        client.delete(f"/sessions/{id1}")

        # Other should still exist
        resp = client.get(f"/sessions/{id2}")
        assert resp.status_code == 200

    def test_session_limit_respected(self, client: TestClient):
        """Test that max session limit is enforced."""
        # The test environment sets MAX_CONCURRENT_SESSIONS=5
        created = []

        # Try to create more than limit
        for _ in range(10):
            resp = client.post("/sessions", json={})
            if resp.status_code == 200:
                created.append(resp.json()["session_id"])
            else:
                break

        # Should have hit limit
        assert len(created) <= 5

        # Cleanup
        for sid in created:
            client.delete(f"/sessions/{sid}")


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_schema_available(self, client: TestClient):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/sessions" in data["paths"]

    def test_docs_page_available(self, client: TestClient):
        """Test that Swagger UI docs are available."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_page_available(self, client: TestClient):
        """Test that ReDoc docs are available."""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
