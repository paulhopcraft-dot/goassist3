"""Tests for WebRTC Gateway."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.webrtc.gateway import (
    AudioTrackSink,
    PeerConnectionState,
    WebRTCConfig,
    WebRTCGateway,
    create_webrtc_gateway,
)


class TestWebRTCConfig:
    """Tests for WebRTCConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = WebRTCConfig()

        assert len(config.stun_servers) == 2
        assert "stun:stun.l.google.com:19302" in config.stun_servers
        assert config.turn_servers == []
        assert config.enable_data_channel is True
        assert config.data_channel_ordered is False
        assert config.data_channel_max_retransmits == 0
        assert config.audio_sample_rate == 16000
        assert config.audio_channels == 1

    def test_custom_config(self):
        """Test custom configuration."""
        config = WebRTCConfig(
            stun_servers=["stun:custom.stun.server:3478"],
            turn_servers=[{
                "urls": "turn:custom.turn.server:3478",
                "username": "user",
                "credential": "pass",
            }],
            enable_data_channel=False,
            data_channel_ordered=True,
            data_channel_max_retransmits=3,
            audio_sample_rate=48000,
            audio_channels=2,
        )

        assert config.stun_servers == ["stun:custom.stun.server:3478"]
        assert len(config.turn_servers) == 1
        assert config.turn_servers[0]["urls"] == "turn:custom.turn.server:3478"
        assert config.enable_data_channel is False
        assert config.data_channel_ordered is True
        assert config.data_channel_max_retransmits == 3
        assert config.audio_sample_rate == 48000
        assert config.audio_channels == 2


class TestPeerConnectionState:
    """Tests for PeerConnectionState dataclass."""

    def test_default_state(self):
        """Test default state values."""
        pc_mock = MagicMock()
        state = PeerConnectionState(session_id="test-123", pc=pc_mock)

        assert state.session_id == "test-123"
        assert state.pc is pc_mock
        assert state.audio_track is None
        assert state.data_channel is None
        assert state.is_connected is False
        assert state.is_audio_active is False


class TestAudioTrackSink:
    """Tests for AudioTrackSink."""

    @pytest.mark.asyncio
    async def test_audio_callback_called(self):
        """Test audio callback is invoked with received data."""
        received_audio = []

        def on_audio(audio: bytes, timestamp: int):
            received_audio.append((audio, timestamp))

        sink = AudioTrackSink(session_id="test-123", on_audio=on_audio)

        # Create mock track that yields one frame then stops
        mock_frame = MagicMock()
        mock_frame.to_ndarray.return_value = MagicMock(tobytes=lambda: b"audio_data")
        mock_frame.pts = 1000
        mock_frame.sample_rate = 16000

        mock_track = AsyncMock()
        mock_track.recv.side_effect = [mock_frame, Exception("End of stream")]

        await sink.start(mock_track)

        assert len(received_audio) == 1
        assert received_audio[0][0] == b"audio_data"

    def test_stop_sets_flag(self):
        """Test stop sets running flag to False."""
        sink = AudioTrackSink(session_id="test-123", on_audio=lambda a, t: None)
        sink._running = True

        sink.stop()

        assert sink._running is False


class TestWebRTCGateway:
    """Tests for WebRTCGateway."""

    def test_creation_with_default_config(self):
        """Test gateway creation with default config."""
        with patch("src.api.webrtc.gateway.get_settings") as mock_settings:
            mock_settings.return_value.turn_url = None
            mock_settings.return_value.turn_username = None
            mock_settings.return_value.turn_credential = None

            gateway = WebRTCGateway()

            assert gateway._config is not None
            assert gateway.active_connections == 0

    def test_creation_with_custom_config(self):
        """Test gateway creation with custom config."""
        config = WebRTCConfig(
            stun_servers=["stun:custom:3478"],
            enable_data_channel=False,
        )

        gateway = WebRTCGateway(config)

        assert gateway._config.stun_servers == ["stun:custom:3478"]
        assert gateway._config.enable_data_channel is False

    def test_on_audio_registers_callback(self):
        """Test on_audio registers callback for session."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        callback = MagicMock()
        gateway.on_audio("session-123", callback)

        assert "session-123" in gateway._audio_callbacks
        assert gateway._audio_callbacks["session-123"] is callback

    def test_is_connected_returns_false_for_unknown_session(self):
        """Test is_connected returns False for unknown session."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        assert gateway.is_connected("unknown-session") is False

    def test_get_connection_state_returns_none_for_unknown_session(self):
        """Test get_connection_state returns None for unknown session."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        assert gateway.get_connection_state("unknown-session") is None

    @pytest.mark.asyncio
    async def test_close_connection_removes_session(self):
        """Test close_connection removes session from tracking."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        # Simulate a connection
        mock_pc = AsyncMock()
        state = PeerConnectionState(session_id="test-123", pc=mock_pc)
        gateway._connections["test-123"] = state
        gateway._audio_callbacks["test-123"] = MagicMock()

        await gateway.close_connection("test-123")

        assert "test-123" not in gateway._connections
        assert "test-123" not in gateway._audio_callbacks
        mock_pc.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_all_closes_all_connections(self):
        """Test close_all closes all active connections."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        # Add multiple connections
        for i in range(3):
            mock_pc = AsyncMock()
            state = PeerConnectionState(session_id=f"session-{i}", pc=mock_pc)
            gateway._connections[f"session-{i}"] = state

        await gateway.close_all()

        assert gateway.active_connections == 0

    @pytest.mark.asyncio
    async def test_send_blendshapes_returns_false_for_unknown_session(self):
        """Test send_blendshapes returns False for unknown session."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        result = await gateway.send_blendshapes("unknown", {"frame": 1})

        assert result is False

    @pytest.mark.asyncio
    async def test_send_blendshapes_returns_false_when_no_data_channel(self):
        """Test send_blendshapes returns False when no data channel."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        # Add connection without data channel
        mock_pc = AsyncMock()
        state = PeerConnectionState(session_id="test-123", pc=mock_pc)
        gateway._connections["test-123"] = state

        result = await gateway.send_blendshapes("test-123", {"frame": 1})

        assert result is False

    @pytest.mark.asyncio
    async def test_send_blendshapes_returns_false_when_channel_not_open(self):
        """Test send_blendshapes returns False when channel not open."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        # Add connection with closed data channel
        mock_pc = AsyncMock()
        mock_channel = MagicMock()
        mock_channel.readyState = "closed"
        state = PeerConnectionState(
            session_id="test-123",
            pc=mock_pc,
            data_channel=mock_channel,
        )
        gateway._connections["test-123"] = state

        result = await gateway.send_blendshapes("test-123", {"frame": 1})

        assert result is False

    @pytest.mark.asyncio
    async def test_send_blendshapes_success(self):
        """Test send_blendshapes successfully sends data."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        # Add connection with open data channel
        mock_pc = AsyncMock()
        mock_channel = MagicMock()
        mock_channel.readyState = "open"
        state = PeerConnectionState(
            session_id="test-123",
            pc=mock_pc,
            data_channel=mock_channel,
        )
        gateway._connections["test-123"] = state

        blendshapes = {"jawOpen": 0.5, "mouthSmile_L": 0.3}
        result = await gateway.send_blendshapes("test-123", blendshapes)

        assert result is True
        mock_channel.send.assert_called_once()
        sent_data = mock_channel.send.call_args[0][0]
        assert json.loads(sent_data) == blendshapes

    @pytest.mark.asyncio
    async def test_handle_ice_candidate_ignored_for_unknown_session(self):
        """Test handle_ice_candidate is ignored for unknown session."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        # Should not raise
        await gateway.handle_ice_candidate("unknown", {"candidate": "test"})


class TestFactoryFunction:
    """Tests for factory function."""

    def test_create_webrtc_gateway_with_default_config(self):
        """Test factory creates gateway with default config."""
        config = WebRTCConfig()
        gateway = create_webrtc_gateway(config)

        assert isinstance(gateway, WebRTCGateway)

    def test_create_webrtc_gateway_with_none_config(self):
        """Test factory creates gateway when config is None."""
        with patch("src.api.webrtc.gateway.get_settings") as mock_settings:
            mock_settings.return_value.turn_url = None
            mock_settings.return_value.turn_username = None
            mock_settings.return_value.turn_credential = None

            gateway = create_webrtc_gateway(None)

            assert isinstance(gateway, WebRTCGateway)


class TestWebRTCGatewayHandleOffer:
    """Tests for handle_offer method."""

    def _create_mock_pc(self, answer_sdp: str = "answer"):
        """Create a properly mocked RTCPeerConnection."""
        mock_pc = MagicMock()
        mock_pc.connectionState = "new"

        # Mock async methods
        mock_pc.setRemoteDescription = AsyncMock()
        mock_pc.createAnswer = AsyncMock()
        mock_pc.setLocalDescription = AsyncMock()
        mock_pc.addIceCandidate = AsyncMock()
        mock_pc.close = AsyncMock()

        # Mock local description
        mock_local_desc = MagicMock()
        mock_local_desc.sdp = answer_sdp
        mock_pc.localDescription = mock_local_desc

        # Mock data channel with proper on decorator
        mock_channel = MagicMock()
        mock_channel.on = MagicMock(side_effect=lambda event: lambda fn: fn)
        mock_pc.createDataChannel.return_value = mock_channel

        # Mock on decorator to return identity function
        mock_pc.on = MagicMock(side_effect=lambda event: lambda fn: fn)

        return mock_pc

    @pytest.mark.asyncio
    async def test_handle_offer_creates_answer(self):
        """Test handle_offer creates valid answer."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        # Mock RTCPeerConnection
        with patch("src.api.webrtc.gateway.RTCPeerConnection") as mock_pc_class:
            mock_pc = self._create_mock_pc("v=0\r\no=- 1234 answer\r\n")
            mock_pc_class.return_value = mock_pc

            offer_sdp = "v=0\r\no=- 1234 offer\r\n"
            answer = await gateway.handle_offer("session-123", offer_sdp)

            assert answer == "v=0\r\no=- 1234 answer\r\n"
            assert "session-123" in gateway._connections
            mock_pc.setRemoteDescription.assert_called_once()
            mock_pc.createAnswer.assert_called_once()
            mock_pc.setLocalDescription.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_offer_creates_data_channel_when_enabled(self):
        """Test handle_offer creates data channel when enabled."""
        config = WebRTCConfig(enable_data_channel=True)
        gateway = WebRTCGateway(config)

        with patch("src.api.webrtc.gateway.RTCPeerConnection") as mock_pc_class:
            mock_pc = self._create_mock_pc("answer")
            mock_pc_class.return_value = mock_pc

            await gateway.handle_offer("session-123", "offer")

            mock_pc.createDataChannel.assert_called_once_with(
                "blendshapes",
                ordered=False,
                maxRetransmits=0,
            )

    @pytest.mark.asyncio
    async def test_handle_offer_skips_data_channel_when_disabled(self):
        """Test handle_offer skips data channel when disabled."""
        config = WebRTCConfig(enable_data_channel=False)
        gateway = WebRTCGateway(config)

        with patch("src.api.webrtc.gateway.RTCPeerConnection") as mock_pc_class:
            mock_pc = self._create_mock_pc("answer")
            mock_pc_class.return_value = mock_pc

            await gateway.handle_offer("session-123", "offer")

            mock_pc.createDataChannel.assert_not_called()


class TestWebRTCGatewayIntegration:
    """Integration-style tests for WebRTC gateway."""

    def _create_mock_pc(self, answer_sdp: str = "answer"):
        """Create a properly mocked RTCPeerConnection."""
        mock_pc = MagicMock()
        mock_pc.connectionState = "new"

        # Mock async methods
        mock_pc.setRemoteDescription = AsyncMock()
        mock_pc.createAnswer = AsyncMock()
        mock_pc.setLocalDescription = AsyncMock()
        mock_pc.addIceCandidate = AsyncMock()
        mock_pc.close = AsyncMock()

        # Mock local description
        mock_local_desc = MagicMock()
        mock_local_desc.sdp = answer_sdp
        mock_pc.localDescription = mock_local_desc

        # Mock data channel with proper on decorator and readyState
        mock_channel = MagicMock()
        mock_channel.on = MagicMock(side_effect=lambda event: lambda fn: fn)
        mock_channel.readyState = "open"
        mock_pc.createDataChannel.return_value = mock_channel

        # Mock on decorator to return identity function
        mock_pc.on = MagicMock(side_effect=lambda event: lambda fn: fn)

        return mock_pc

    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle: create, use, close."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        with patch("src.api.webrtc.gateway.RTCPeerConnection") as mock_pc_class:
            mock_pc = self._create_mock_pc("answer")
            mock_pc_class.return_value = mock_pc

            # Step 1: Handle offer
            answer = await gateway.handle_offer("session-1", "offer")
            assert answer == "answer"
            assert gateway.active_connections == 1

            # Step 2: Send blendshapes
            result = await gateway.send_blendshapes("session-1", {"test": 1})
            assert result is True

            # Step 3: Close connection
            await gateway.close_connection("session-1")
            assert gateway.active_connections == 0

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self):
        """Test gateway handles multiple concurrent sessions."""
        config = WebRTCConfig()
        gateway = WebRTCGateway(config)

        with patch("src.api.webrtc.gateway.RTCPeerConnection") as mock_pc_class:
            mock_pcs = [self._create_mock_pc(f"answer-{i}") for i in range(3)]
            mock_pc_class.side_effect = mock_pcs

            # Create 3 connections
            for i in range(3):
                await gateway.handle_offer(f"session-{i}", f"offer-{i}")

            assert gateway.active_connections == 3

            # Close one
            await gateway.close_connection("session-1")
            assert gateway.active_connections == 2

            # Close all
            await gateway.close_all()
            assert gateway.active_connections == 0
