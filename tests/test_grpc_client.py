"""Tests for Audio2Face gRPC Client.

Tests cover:
- Client configuration
- Connection state management
- Mock mode fallback
- Audio processing stream
- Heartbeat functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.animation.grpc.client import (
    Audio2FaceClient,
    Audio2FaceClientConfig,
    BlendshapeFrame,
    ConnectionState,
    create_audio2face_client,
)


class TestAudio2FaceClientConfig:
    """Tests for Audio2FaceClientConfig dataclass."""

    def test_default_values(self):
        """Default config has sensible values."""
        config = Audio2FaceClientConfig()
        assert config.host == "localhost"
        assert config.port == 50051
        assert config.sample_rate == 16000
        assert config.target_fps == 30
        assert config.style == "NEUTRAL"
        assert config.enable_emotion is False
        assert config.blendshape_format == "arkit52"
        assert config.connect_timeout_s == 5.0
        assert config.max_retries == 3

    def test_custom_values(self):
        """Custom config values are applied."""
        config = Audio2FaceClientConfig(
            host="192.168.1.100",
            port=50052,
            target_fps=60,
            connect_timeout_s=10.0,
        )
        assert config.host == "192.168.1.100"
        assert config.port == 50052
        assert config.target_fps == 60
        assert config.connect_timeout_s == 10.0


class TestBlendshapeFrame:
    """Tests for BlendshapeFrame dataclass."""

    def test_create_frame(self):
        """Create a blendshape frame."""
        frame = BlendshapeFrame(
            session_id="test-session",
            sequence=1,
            timestamp_ms=100,
            blendshapes={"jawOpen": 0.5},
        )
        assert frame.session_id == "test-session"
        assert frame.sequence == 1
        assert frame.timestamp_ms == 100
        assert frame.blendshapes == {"jawOpen": 0.5}
        assert frame.fps == 30
        assert frame.heartbeat is False
        assert frame.latency_ms == 0

    def test_heartbeat_frame(self):
        """Create a heartbeat frame."""
        frame = BlendshapeFrame(
            session_id="test",
            sequence=5,
            timestamp_ms=500,
            blendshapes={},
            heartbeat=True,
        )
        assert frame.heartbeat is True


class TestConnectionState:
    """Tests for ConnectionState enum."""

    def test_all_states_exist(self):
        """All connection states exist."""
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.RECONNECTING.value == "reconnecting"
        assert ConnectionState.FAILED.value == "failed"

    def test_state_count(self):
        """Exactly 5 states exist."""
        assert len(ConnectionState) == 5


class TestAudio2FaceClientInit:
    """Tests for Audio2Face client initialization."""

    def test_init_default_config(self):
        """Client initializes with default config."""
        client = Audio2FaceClient()
        assert client._config.host == "localhost"
        assert client._config.port == 50051
        assert client.state == ConnectionState.DISCONNECTED
        assert client.is_connected is False

    def test_init_custom_config(self):
        """Client uses custom config."""
        config = Audio2FaceClientConfig(host="test-host", port=12345)
        client = Audio2FaceClient(config)
        assert client._config.host == "test-host"
        assert client._config.port == 12345

    def test_session_id_none_initially(self):
        """Session ID is None before connect."""
        client = Audio2FaceClient()
        assert client.session_id is None


class TestAudio2FaceClientStateChange:
    """Tests for connection state management."""

    def test_state_change_callback(self):
        """State change callback is invoked."""
        client = Audio2FaceClient()
        states = []

        def callback(state):
            states.append(state)

        client.on_state_change(callback)
        client._set_state(ConnectionState.CONNECTING)
        client._set_state(ConnectionState.CONNECTED)

        assert states == [ConnectionState.CONNECTING, ConnectionState.CONNECTED]

    def test_state_change_callback_not_called_for_same_state(self):
        """Callback not invoked when state unchanged."""
        client = Audio2FaceClient()
        states = []

        def callback(state):
            states.append(state)

        client.on_state_change(callback)
        client._set_state(ConnectionState.CONNECTING)
        client._set_state(ConnectionState.CONNECTING)  # Same state

        assert len(states) == 1

    def test_state_change_callback_error_handled(self):
        """Callback errors are handled gracefully."""
        client = Audio2FaceClient()

        def failing_callback(state):
            raise ValueError("Test error")

        client.on_state_change(failing_callback)

        # Should not raise
        client._set_state(ConnectionState.CONNECTING)


class TestAudio2FaceClientConnect:
    """Tests for client connection."""

    @pytest.mark.asyncio
    async def test_connect_mock_mode(self):
        """Connect uses mock mode when grpc unavailable."""
        client = Audio2FaceClient()
        client._grpc_available = False

        result = await client.connect("test-session")

        assert result is True
        assert client.is_connected is True
        assert client.session_id == "test-session"
        assert client.state == ConnectionState.CONNECTED

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        """Connect returns True if already connected."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect("session-1")
        result = await client.connect("session-2")

        assert result is True
        # Session ID shouldn't change
        assert client.session_id == "session-1"

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_connect_generates_session_id(self):
        """Connect generates session ID if not provided."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect()

        assert client.session_id is not None
        assert client.session_id.startswith("a2f-")

        await client.disconnect()


class TestAudio2FaceClientDisconnect:
    """Tests for client disconnection."""

    @pytest.mark.asyncio
    async def test_disconnect_clears_state(self):
        """Disconnect clears connection state."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect("test-session")
        await client.disconnect()

        assert client.state == ConnectionState.DISCONNECTED
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_cancels_keepalive(self):
        """Disconnect cancels keepalive task."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect("test-session")

        # Mock keepalive task
        async def mock_keepalive():
            await asyncio.sleep(100)

        client._keepalive_task = asyncio.create_task(mock_keepalive())

        await client.disconnect()

        assert client._keepalive_task is None


class TestAudio2FaceClientStatus:
    """Tests for status retrieval."""

    @pytest.mark.asyncio
    async def test_get_status_mock_mode(self):
        """Get status returns mock data without stub."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect("test-session")
        status = await client.get_status()

        assert status is not None
        assert status["ready"] is True
        assert status["version"] == "mock"

        await client.disconnect()


class TestAudio2FaceClientMockProcessing:
    """Tests for mock audio processing."""

    @pytest.mark.asyncio
    async def test_process_audio_stream_mock(self):
        """Process audio stream in mock mode."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect("test-session")

        async def audio_stream():
            yield b"\x00" * 640
            yield b"\x00" * 640

        frames = []
        async for frame in client.process_audio_stream(audio_stream()):
            frames.append(frame)
            if len(frames) >= 2:
                break

        assert len(frames) >= 2
        assert frames[0].session_id == "test-session"
        assert frames[0].sequence == 1
        assert frames[1].sequence == 2

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_process_audio_stream_not_connected(self):
        """Process audio stream returns nothing when not connected."""
        client = Audio2FaceClient()

        async def audio_stream():
            yield b"\x00" * 640

        frames = []
        async for frame in client.process_audio_stream(audio_stream()):
            frames.append(frame)

        assert len(frames) == 0

    @pytest.mark.asyncio
    async def test_process_audio_stream_with_timestamp_fn(self):
        """Process audio stream uses timestamp function."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect("test-session")

        timestamp_counter = [0]

        def get_timestamp():
            timestamp_counter[0] += 100
            return timestamp_counter[0]

        async def audio_stream():
            yield b"\x00" * 640

        frames = []
        async for frame in client.process_audio_stream(audio_stream(), get_timestamp):
            frames.append(frame)

        assert len(frames) >= 1
        assert frames[0].timestamp_ms == 100

        await client.disconnect()


class TestAudio2FaceClientMockBlendshapes:
    """Tests for mock blendshape generation."""

    def test_generate_mock_blendshapes_silent(self):
        """Generate mock blendshapes from silent audio."""
        client = Audio2FaceClient()
        audio = b"\x00" * 640

        blendshapes = client._generate_mock_blendshapes(audio)

        assert isinstance(blendshapes, dict)
        assert "jawOpen" in blendshapes
        assert blendshapes["jawOpen"] < 0.1  # Silent = minimal jaw

    def test_generate_mock_blendshapes_loud(self):
        """Generate mock blendshapes from loud audio."""
        client = Audio2FaceClient()
        # Max amplitude 16-bit samples
        audio = b"\xff\x7f" * 160

        blendshapes = client._generate_mock_blendshapes(audio)

        assert isinstance(blendshapes, dict)
        assert "jawOpen" in blendshapes
        assert blendshapes["jawOpen"] > 0.1  # Loud = more jaw

    def test_generate_mock_blendshapes_empty(self):
        """Generate mock blendshapes from empty audio."""
        client = Audio2FaceClient()

        blendshapes = client._generate_mock_blendshapes(b"")

        assert isinstance(blendshapes, dict)
        # Should return neutral pose


class TestAudio2FaceClientHeartbeat:
    """Tests for heartbeat functionality."""

    @pytest.mark.asyncio
    async def test_send_heartbeat(self):
        """Send heartbeat returns neutral frame."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect("test-session")

        frame = await client.send_heartbeat()

        assert frame is not None
        assert frame.heartbeat is True
        assert frame.session_id == "test-session"
        assert "jawOpen" in frame.blendshapes

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_send_heartbeat_not_connected(self):
        """Send heartbeat returns None when not connected."""
        client = Audio2FaceClient()

        frame = await client.send_heartbeat()

        assert frame is None

    @pytest.mark.asyncio
    async def test_send_heartbeat_increments_sequence(self):
        """Send heartbeat increments sequence number."""
        client = Audio2FaceClient()
        client._grpc_available = False

        await client.connect("test-session")

        frame1 = await client.send_heartbeat()
        frame2 = await client.send_heartbeat()

        assert frame2.sequence == frame1.sequence + 1

        await client.disconnect()


class TestCreateAudio2FaceClientFactory:
    """Tests for factory function."""

    def test_factory_creates_client(self):
        """Factory creates Audio2FaceClient instance."""
        client = create_audio2face_client()
        assert isinstance(client, Audio2FaceClient)

    def test_factory_accepts_host_port(self):
        """Factory accepts host and port."""
        client = create_audio2face_client(host="test-host", port=12345)
        assert client._config.host == "test-host"
        assert client._config.port == 12345

    def test_factory_accepts_kwargs(self):
        """Factory passes kwargs to config."""
        client = create_audio2face_client(target_fps=60, max_retries=5)
        assert client._config.target_fps == 60
        assert client._config.max_retries == 5
