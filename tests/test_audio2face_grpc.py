"""Tests for Audio2Face gRPC Client.

Tests the gRPC client for Audio2Face integration.
"""

import pytest
import asyncio

from src.animation.grpc.client import (
    Audio2FaceClient,
    Audio2FaceClientConfig,
    BlendshapeFrame,
    ConnectionState,
    create_audio2face_client,
)
from src.animation.base import ARKIT_52_BLENDSHAPES


class TestAudio2FaceClientConfig:
    """Tests for Audio2FaceClientConfig."""

    def test_default_config(self):
        """Default config has sensible values."""
        config = Audio2FaceClientConfig()
        assert config.host == "localhost"
        assert config.port == 50051
        assert config.sample_rate == 16000
        assert config.target_fps == 30
        assert config.style == "NEUTRAL"
        assert config.enable_emotion is False
        assert config.blendshape_format == "arkit52"

    def test_custom_config(self):
        """Custom config values are applied."""
        config = Audio2FaceClientConfig(
            host="192.168.1.100",
            port=50052,
            target_fps=60,
            style="NEUTRAL",
        )
        assert config.host == "192.168.1.100"
        assert config.port == 50052
        assert config.target_fps == 60


class TestConnectionState:
    """Tests for ConnectionState enum."""

    def test_all_states_exist(self):
        """All connection states exist."""
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.RECONNECTING.value == "reconnecting"
        assert ConnectionState.FAILED.value == "failed"


class TestBlendshapeFrame:
    """Tests for BlendshapeFrame dataclass."""

    def test_create_frame(self):
        """Create a blendshape frame."""
        frame = BlendshapeFrame(
            session_id="test-session",
            sequence=1,
            timestamp_ms=1000,
            blendshapes={"jawOpen": 0.5},
        )
        assert frame.session_id == "test-session"
        assert frame.sequence == 1
        assert frame.timestamp_ms == 1000
        assert frame.blendshapes["jawOpen"] == 0.5
        assert frame.fps == 30
        assert frame.heartbeat is False

    def test_heartbeat_frame(self):
        """Create a heartbeat frame."""
        frame = BlendshapeFrame(
            session_id="test-session",
            sequence=2,
            timestamp_ms=2000,
            blendshapes={},
            heartbeat=True,
        )
        assert frame.heartbeat is True


class TestAudio2FaceClient:
    """Tests for Audio2FaceClient."""

    @pytest.fixture
    def client(self):
        """Create client instance with short timeout for testing."""
        config = Audio2FaceClientConfig(
            host="localhost",
            port=50051,
            connect_timeout_s=0.5,  # Short timeout for tests
        )
        return Audio2FaceClient(config)

    def test_init(self, client):
        """Client initializes with correct state."""
        assert client.state == ConnectionState.DISCONNECTED
        assert client.is_connected is False
        assert client.session_id is None

    @pytest.mark.asyncio
    async def test_connect_mock_mode(self, client):
        """Connect succeeds in mock mode."""
        connected = await client.connect("test-session")
        assert connected is True
        assert client.state == ConnectionState.CONNECTED
        assert client.is_connected is True
        assert client.session_id == "test-session"
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """Disconnect clears state."""
        await client.connect("test-session")
        await client.disconnect()
        assert client.state == ConnectionState.DISCONNECTED
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_state_change_callback(self, client):
        """State change callback is called."""
        states = []

        def callback(state):
            states.append(state)

        client.on_state_change(callback)
        await client.connect("test-session")
        await client.disconnect()

        assert ConnectionState.CONNECTING in states
        assert ConnectionState.CONNECTED in states
        assert ConnectionState.DISCONNECTED in states

    @pytest.mark.asyncio
    async def test_get_status(self, client):
        """Get status returns mock status."""
        await client.connect("test-session")
        status = await client.get_status()
        assert status is not None
        assert status["ready"] is True
        assert "version" in status
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_send_heartbeat(self, client):
        """Send heartbeat returns frame."""
        await client.connect("test-session")
        frame = await client.send_heartbeat()
        assert frame is not None
        assert frame.heartbeat is True
        assert frame.session_id == "test-session"
        await client.disconnect()


class TestAudio2FaceClientStreaming:
    """Tests for Audio2Face streaming."""

    @pytest.fixture
    def client(self):
        """Create client instance with short timeout."""
        config = Audio2FaceClientConfig(
            host="localhost",
            port=50051,
            connect_timeout_s=0.5,
        )
        return Audio2FaceClient(config)

    @pytest.mark.asyncio
    async def test_process_audio_stream_not_connected(self, client):
        """Processing without connection yields nothing."""
        async def audio_gen():
            yield b"\x00" * 640

        frames = []
        async for frame in client.process_audio_stream(audio_gen()):
            frames.append(frame)

        assert len(frames) == 0

    @pytest.mark.asyncio
    async def test_process_audio_stream_mock(self, client):
        """Process audio stream in mock mode."""
        await client.connect("test-session")

        async def audio_gen():
            # Generate 3 audio chunks
            for _ in range(3):
                yield b"\x00" * 640

        frames = []
        async for frame in client.process_audio_stream(audio_gen()):
            frames.append(frame)

        assert len(frames) == 3
        for frame in frames:
            assert frame.session_id == "test-session"
            assert isinstance(frame.blendshapes, dict)

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_process_audio_generates_blendshapes(self, client):
        """Audio processing generates blendshapes."""
        await client.connect("test-session")

        # Generate audio with some energy
        audio = bytes([0x7F, 0x00] * 320)  # Non-silent audio

        async def audio_gen():
            yield audio

        frames = []
        async for frame in client.process_audio_stream(audio_gen()):
            frames.append(frame)

        assert len(frames) >= 1
        # Should have some mouth movement from audio energy
        frame = frames[0]
        assert "jawOpen" in frame.blendshapes

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_sequence_numbers_increment(self, client):
        """Sequence numbers increment correctly."""
        await client.connect("test-session")

        async def audio_gen():
            for _ in range(5):
                yield b"\x00" * 640

        sequences = []
        async for frame in client.process_audio_stream(audio_gen()):
            sequences.append(frame.sequence)

        assert sequences == [1, 2, 3, 4, 5]
        await client.disconnect()


class TestAudio2FaceClientMockBlendshapes:
    """Tests for mock blendshape generation."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        return Audio2FaceClient()

    def test_silent_audio_neutral(self, client):
        """Silent audio generates near-neutral pose."""
        # Silent audio (zeros)
        audio = b"\x00" * 640
        blendshapes = client._generate_mock_blendshapes(audio)

        # Silent audio should have minimal mouth movement
        assert blendshapes["jawOpen"] < 0.1
        # Most blendshapes should be near zero
        mouth_shapes = ["jawOpen", "mouthClose", "mouthPucker", "mouthFunnel"]
        for name, value in blendshapes.items():
            if name not in mouth_shapes:
                assert value == 0.0, f"{name} should be 0.0"

    def test_loud_audio_opens_jaw(self, client):
        """Loud audio opens jaw."""
        # Loud audio (high values)
        audio = bytes([0xFF, 0x7F] * 320)  # High amplitude samples
        blendshapes = client._generate_mock_blendshapes(audio)

        assert blendshapes["jawOpen"] > 0.0

    def test_all_arkit_blendshapes(self, client):
        """All ARKit-52 blendshapes are present."""
        audio = b"\x00" * 640
        blendshapes = client._generate_mock_blendshapes(audio)

        for name in ARKIT_52_BLENDSHAPES:
            assert name in blendshapes


class TestCreateAudio2FaceClient:
    """Tests for factory function."""

    def test_creates_client(self):
        """Factory creates client instance."""
        client = create_audio2face_client()
        assert isinstance(client, Audio2FaceClient)

    def test_factory_accepts_kwargs(self):
        """Factory accepts config kwargs."""
        client = create_audio2face_client(
            host="192.168.1.100",
            port=50052,
            target_fps=60,
        )
        assert client._config.host == "192.168.1.100"
        assert client._config.port == 50052
        assert client._config.target_fps == 60
