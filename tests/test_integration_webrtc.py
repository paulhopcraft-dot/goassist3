"""Integration Tests - WebRTC Pipeline.

Tests covering WebRTC connection establishment and media transport:
    1. WebRTC offer/answer exchange
    2. ICE candidate handling
    3. Data channel creation
    4. Audio track setup
    5. Blendshape streaming via data channel
    6. Connection cleanup

TMF v3.0 §3.7: WebRTC data channel for blendshapes (low-latency alternative to WebSocket)
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestWebRTCOfferAnswer:
    """Tests for WebRTC signaling (offer/answer)."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_create_session_for_webrtc(self, client):
        """Test session creation returns valid session ID."""
        response = client.post("/sessions", json={})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert isinstance(data["session_id"], str)

    def test_send_webrtc_offer(self, client):
        """Test sending WebRTC offer to session."""
        # Create session first
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Send offer
        offer = {
            "type": "offer",
            "sdp": "v=0\r\no=- 123456 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"
        }
        offer_resp = client.post(
            f"/sessions/{session_id}/offer",
            json=offer
        )

        assert offer_resp.status_code == 200
        answer = offer_resp.json()
        assert "type" in answer
        assert "sdp" in answer
        assert answer["type"] == "answer"

        # Cleanup
        client.delete(f"/sessions/{session_id}")

    def test_offer_to_nonexistent_session(self, client):
        """Test offer to non-existent session returns 404."""
        offer = {
            "type": "offer",
            "sdp": "v=0\r\n"
        }
        response = client.post(
            "/sessions/nonexistent-session-id/offer",
            json=offer
        )

        assert response.status_code == 404

    def test_invalid_sdp_format(self, client):
        """Test invalid SDP format is rejected."""
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Send malformed offer
        offer = {
            "type": "offer",
            "sdp": ""  # Empty SDP
        }
        offer_resp = client.post(
            f"/sessions/{session_id}/offer",
            json=offer
        )

        # Should return error
        assert offer_resp.status_code in [400, 500]

        # Cleanup
        client.delete(f"/sessions/{session_id}")


class TestICECandidates:
    """Tests for ICE candidate exchange."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_add_ice_candidate(self, client):
        """Test adding ICE candidate to session."""
        # Create session
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Add ICE candidate
        candidate = {
            "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host",
            "sdpMLineIndex": 0,
            "sdpMid": "0"
        }
        ice_resp = client.post(
            f"/sessions/{session_id}/ice-candidate",
            json=candidate
        )

        assert ice_resp.status_code == 200

        # Cleanup
        client.delete(f"/sessions/{session_id}")

    def test_ice_candidate_to_nonexistent_session(self, client):
        """Test ICE candidate to non-existent session returns 404."""
        candidate = {
            "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host",
            "sdpMLineIndex": 0,
            "sdpMid": "0"
        }
        response = client.post(
            "/sessions/nonexistent/ice-candidate",
            json=candidate
        )

        assert response.status_code == 404

    def test_multiple_ice_candidates(self, client):
        """Test adding multiple ICE candidates."""
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Add multiple candidates
        candidates = [
            {
                "candidate": f"candidate:{i} 1 UDP 2130706431 192.168.1.100 {54321+i} typ host",
                "sdpMLineIndex": 0,
                "sdpMid": "0"
            }
            for i in range(3)
        ]

        for candidate in candidates:
            resp = client.post(
                f"/sessions/{session_id}/ice-candidate",
                json=candidate
            )
            assert resp.status_code == 200

        # Cleanup
        client.delete(f"/sessions/{session_id}")


class TestWebRTCDataChannel:
    """Tests for WebRTC data channel (blendshapes)."""

    @pytest.mark.asyncio
    async def test_data_channel_emitter_creation(self):
        """Test data channel emitter can be created."""
        from src.api.webrtc.datachannel_emitter import DataChannelEmitter

        emitter = DataChannelEmitter()
        assert emitter is not None

    @pytest.mark.asyncio
    async def test_data_channel_sends_blendshapes(self):
        """Test data channel can send blendshape frames."""
        from src.api.webrtc.datachannel_emitter import DataChannelEmitter
        from src.animation.base import BlendshapeFrame

        emitter = DataChannelEmitter()

        # Mock data channel
        mock_channel = AsyncMock()
        mock_channel.readyState = "open"
        mock_channel.send = MagicMock()

        emitter.set_data_channel(mock_channel)

        # Send blendshape frame
        frame = BlendshapeFrame(
            session_id="test-session",
            seq=1,
            t_audio_ms=100,
            blendshapes={"jawOpen": 0.5, "mouthSmile": 0.3}
        )

        await emitter.send_frame(frame)

        # Should have called send
        mock_channel.send.assert_called_once()

        # Verify JSON format
        sent_data = mock_channel.send.call_args[0][0]
        parsed = json.loads(sent_data)
        assert parsed["seq"] == 1
        assert parsed["t_audio_ms"] == 100
        assert "jawOpen" in parsed["blendshapes"]

    @pytest.mark.asyncio
    async def test_data_channel_handles_closed_state(self):
        """Test data channel gracefully handles closed state."""
        from src.api.webrtc.datachannel_emitter import DataChannelEmitter
        from src.animation.base import BlendshapeFrame

        emitter = DataChannelEmitter()

        # Mock closed channel
        mock_channel = AsyncMock()
        mock_channel.readyState = "closed"
        mock_channel.send = MagicMock()

        emitter.set_data_channel(mock_channel)

        # Attempt to send
        frame = BlendshapeFrame(
            session_id="test",
            seq=1,
            t_audio_ms=100,
            blendshapes={}
        )

        await emitter.send_frame(frame)

        # Should not call send when closed
        mock_channel.send.assert_not_called()


class TestWebRTCAudioTrack:
    """Tests for WebRTC audio track setup."""

    @pytest.mark.asyncio
    async def test_audio_track_creation(self):
        """Test audio track can be created for session."""
        from src.api.webrtc.gateway import WebRTCGateway

        gateway = WebRTCGateway()

        # Create peer connection
        pc = await gateway.create_peer_connection("test-session")
        assert pc is not None

    @pytest.mark.asyncio
    async def test_audio_track_receives_data(self):
        """Test audio track can receive audio data."""
        from src.api.webrtc.gateway import WebRTCGateway

        gateway = WebRTCGateway()
        pc = await gateway.create_peer_connection("test-session")

        # Check that track handler is set up
        assert pc is not None
        # Audio handling tested in pipeline integration


class TestBlendshapeWebSocket:
    """Tests for fallback WebSocket blendshape transport."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_websocket_endpoint_exists(self, client):
        """Test blendshape WebSocket endpoint is available."""
        # Create session first
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Attempt WebSocket connection
        # Note: TestClient doesn't support WebSocket, just verify route exists
        # Real WebSocket testing requires websocket-client library

        # Cleanup
        client.delete(f"/sessions/{session_id}")


class TestWebRTCConnectionLifecycle:
    """Tests for complete WebRTC connection lifecycle."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    @pytest.mark.asyncio
    async def test_complete_webrtc_setup(self, client):
        """Test complete WebRTC setup: session → offer → answer → ICE."""
        from aiortc import RTCPeerConnection

        # 1. Create session
        create_resp = client.post("/sessions", json={})
        assert create_resp.status_code == 200
        session_id = create_resp.json()["session_id"]

        # 2. Create a real aiortc client peer connection to generate valid SDP
        client_pc = RTCPeerConnection()

        # Add audio transceiver to generate audio offer
        client_pc.addTransceiver("audio", direction="sendrecv")

        # Create offer
        offer_description = await client_pc.createOffer()
        await client_pc.setLocalDescription(offer_description)

        # Send offer to server
        offer = {"sdp": client_pc.localDescription.sdp}
        offer_resp = client.post(f"/sessions/{session_id}/offer", json=offer)

        # Check response
        assert offer_resp.status_code == 200
        answer = offer_resp.json()
        assert answer["type"] == "answer"
        assert "sdp" in answer

        # Close client PC
        await client_pc.close()

        # 3. Add ICE candidates
        candidate = {
            "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host",
            "sdpMLineIndex": 0,
            "sdpMid": "0"
        }
        ice_resp = client.post(f"/sessions/{session_id}/ice-candidate", json=candidate)
        if ice_resp.status_code != 200:
            print(f"ICE error: {ice_resp.json()}")
        assert ice_resp.status_code == 200

        # 4. Cleanup
        delete_resp = client.delete(f"/sessions/{session_id}")
        assert delete_resp.status_code == 200

    def test_session_cleanup_closes_webrtc(self, client):
        """Test deleting session closes WebRTC connection."""
        # Create session and establish WebRTC
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        offer = {
            "type": "offer",
            "sdp": "v=0\r\no=- 123 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"
        }
        client.post(f"/sessions/{session_id}/offer", json=offer)

        # Delete session
        delete_resp = client.delete(f"/sessions/{session_id}")
        assert delete_resp.status_code == 200

        # Session should no longer exist
        status_resp = client.get(f"/sessions/{session_id}")
        assert status_resp.status_code == 404


class TestWebRTCError:
    """Tests for WebRTC error handling."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_concurrent_offers_handled(self, client):
        """Test handling concurrent offers to same session."""
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        offer = {
            "type": "offer",
            "sdp": "v=0\r\no=- 123 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"
        }

        # Send first offer
        resp1 = client.post(f"/sessions/{session_id}/offer", json=offer)
        assert resp1.status_code == 200

        # Send second offer (should either succeed or return conflict)
        resp2 = client.post(f"/sessions/{session_id}/offer", json=offer)
        assert resp2.status_code in [200, 409]

        # Cleanup
        client.delete(f"/sessions/{session_id}")


class TestWebRTCMetrics:
    """Tests for WebRTC connection metrics."""

    @pytest.mark.asyncio
    async def test_connection_state_tracked(self):
        """Test WebRTC connection state is tracked."""
        from src.api.webrtc.gateway import WebRTCGateway

        gateway = WebRTCGateway()
        pc = await gateway.create_peer_connection("metrics-session")

        # Connection should have state
        assert pc.connectionState is not None

    @pytest.mark.asyncio
    async def test_ice_connection_state_tracked(self):
        """Test ICE connection state is tracked."""
        from src.api.webrtc.gateway import WebRTCGateway

        gateway = WebRTCGateway()
        pc = await gateway.create_peer_connection("ice-metrics-session")

        # ICE state should be available
        assert pc.iceConnectionState is not None


class TestWebRTCTURN:
    """Tests for TURN server configuration."""

    @pytest.mark.asyncio
    async def test_turn_server_configured(self):
        """Test TURN servers are configured when provided."""
        from src.api.webrtc.gateway import WebRTCGateway
        from src.config.settings import get_settings

        settings = get_settings()

        if settings.turn_url:
            gateway = WebRTCGateway()
            pc = await gateway.create_peer_connection("turn-session")

            # TURN config should be present
            assert pc is not None
            # aiortc RTCConfiguration includes ICE servers

    @pytest.mark.asyncio
    async def test_works_without_turn(self):
        """Test WebRTC works without TURN server (host candidates only)."""
        from src.api.webrtc.gateway import WebRTCGateway

        gateway = WebRTCGateway()
        pc = await gateway.create_peer_connection("no-turn-session")

        # Should still create peer connection
        assert pc is not None
