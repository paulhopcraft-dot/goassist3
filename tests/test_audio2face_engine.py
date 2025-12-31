"""Tests for Audio2Face Engine.

Tests cover:
- Audio2FaceConfig defaults
- Audio2FaceEngine initialization
- Engine lifecycle (start/stop)
- TMF compliance (NEUTRAL style)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.animation.audio2face_engine import (
    Audio2FaceConfig,
    Audio2FaceEngine,
)
from src.config.constants import TMF


class TestAudio2FaceConfig:
    """Tests for Audio2FaceConfig dataclass."""

    def test_default_values(self):
        """Default config has sensible values."""
        config = Audio2FaceConfig()
        assert config.grpc_host == "localhost"
        assert config.grpc_port == 50051
        assert config.target_fps == 30
        assert config.style == "NEUTRAL"
        assert config.enable_emotion is False
        assert config.batch_audio_ms == 20
        assert config.timeout_s == 1.0

    def test_custom_values(self):
        """Custom config values are applied."""
        config = Audio2FaceConfig(
            grpc_host="192.168.1.100",
            grpc_port=50052,
            target_fps=60,
            timeout_s=5.0,
        )
        assert config.grpc_host == "192.168.1.100"
        assert config.grpc_port == 50052
        assert config.target_fps == 60
        assert config.timeout_s == 5.0

    def test_neutral_style_is_default(self):
        """NEUTRAL style is default per TMF Addendum A."""
        config = Audio2FaceConfig()
        assert config.style == "NEUTRAL"

    def test_emotion_disabled_by_default(self):
        """Emotion inference is disabled by default per TMF."""
        config = Audio2FaceConfig()
        assert config.enable_emotion is False


class TestAudio2FaceEngine:
    """Tests for Audio2FaceEngine class."""

    def test_init_default_config(self):
        """Engine initializes with default config."""
        engine = Audio2FaceEngine()
        assert engine._config.style == "NEUTRAL"
        assert engine._config.target_fps == 30

    def test_init_custom_config(self):
        """Engine uses custom config."""
        config = Audio2FaceConfig(target_fps=60)
        engine = Audio2FaceEngine(config=config)
        assert engine._config.target_fps == 60

    def test_init_sets_yield_threshold(self):
        """Engine sets yield threshold from TMF constants."""
        engine = Audio2FaceEngine()
        assert engine._yield_threshold_ms == TMF.ANIMATION_YIELD_THRESHOLD_MS


class TestAudio2FaceEngineLifecycle:
    """Tests for engine start/stop lifecycle."""

    @pytest.fixture
    def engine(self):
        """Create engine for testing."""
        return Audio2FaceEngine()

    @pytest.mark.asyncio
    async def test_stop_without_start(self, engine):
        """Stop without start is safe."""
        # Should not raise
        await engine.stop()


class TestAudio2FaceEngineTMFCompliance:
    """Tests for TMF compliance."""

    def test_default_style_is_neutral(self):
        """Default style must be NEUTRAL per TMF Addendum A §A3.3."""
        engine = Audio2FaceEngine()
        assert engine._config.style == "NEUTRAL"

    def test_emotion_disabled(self):
        """Emotion inference must be disabled per TMF."""
        engine = Audio2FaceEngine()
        assert engine._config.enable_emotion is False

    def test_yield_threshold_matches_tmf(self):
        """Yield threshold matches TMF constant."""
        engine = Audio2FaceEngine()
        assert engine._yield_threshold_ms == 120  # TMF specifies 120ms


class TestAudio2FaceEngineStart:
    """Tests for engine start with mocked gRPC."""

    @pytest.fixture
    def engine(self):
        """Create engine for testing."""
        return Audio2FaceEngine()

    @pytest.mark.asyncio
    async def test_start_initializes_components(self, engine):
        """Start initializes yield controller and heartbeat."""
        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await engine.start("test-session")

            assert engine._session_id == "test-session"
            assert engine._yield_controller is not None
            assert engine._heartbeat is not None
            assert engine._grpc_client is not None

            await engine.stop()

    @pytest.mark.asyncio
    async def test_start_connects_grpc(self, engine):
        """Start attempts gRPC connection."""
        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.is_connected = True
            mock_client_cls.return_value = mock_client

            await engine.start("grpc-test")

            mock_client.connect.assert_awaited_once_with("grpc-test")

            await engine.stop()

    @pytest.mark.asyncio
    async def test_start_handles_grpc_failure(self, engine):
        """Start handles gRPC connection failure gracefully."""
        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client.is_connected = False
            mock_client_cls.return_value = mock_client

            # Should not raise
            await engine.start("fallback-test")
            assert engine._running is True

            await engine.stop()


class TestAudio2FaceEngineCancel:
    """Tests for engine cancel functionality."""

    @pytest.fixture
    def engine(self):
        """Create engine for testing."""
        return Audio2FaceEngine()

    @pytest.mark.asyncio
    async def test_cancel_stops_heartbeat(self, engine):
        """Cancel stops the heartbeat emitter."""
        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await engine.start("cancel-test")
            assert engine._heartbeat is not None

            await engine.cancel()

            assert engine._cancelled is True
            await engine.stop()

    @pytest.mark.asyncio
    async def test_cancel_clears_audio_buffer(self, engine):
        """Cancel clears the audio buffer."""
        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await engine.start("buffer-test")
            engine._audio_buffer.extend(b"\x00" * 1000)

            await engine.cancel()

            assert len(engine._audio_buffer) == 0
            await engine.stop()


class TestAudio2FaceEngineProperties:
    """Tests for engine properties."""

    def test_yield_controller_none_before_start(self):
        """Yield controller is None before start."""
        engine = Audio2FaceEngine()
        assert engine.yield_controller is None

    def test_grpc_client_none_before_start(self):
        """gRPC client is None before start."""
        engine = Audio2FaceEngine()
        assert engine.grpc_client is None

    def test_is_grpc_connected_false_before_start(self):
        """is_grpc_connected is False before start."""
        engine = Audio2FaceEngine()
        assert engine.is_grpc_connected is False

    @pytest.mark.asyncio
    async def test_yield_controller_available_after_start(self):
        """Yield controller is available after start."""
        engine = Audio2FaceEngine()

        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await engine.start("props-test")

            assert engine.yield_controller is not None

            await engine.stop()


class TestAudio2FaceEngineMockBlendshapes:
    """Tests for mock blendshape generation."""

    def test_generate_mock_blendshapes_silent_audio(self):
        """Generate mock blendshapes from silent audio."""
        engine = Audio2FaceEngine()
        audio = b"\x00" * 640  # Silent audio

        blendshapes = engine._generate_mock_blendshapes(audio)

        assert isinstance(blendshapes, dict)
        assert "jawOpen" in blendshapes
        # Silent audio should have minimal jaw movement
        assert blendshapes["jawOpen"] < 0.1

    def test_generate_mock_blendshapes_loud_audio(self):
        """Generate mock blendshapes from loud audio."""
        engine = Audio2FaceEngine()
        # Create loud audio (high amplitude samples)
        audio = b"\xff\x7f" * 160  # Max positive 16-bit samples

        blendshapes = engine._generate_mock_blendshapes(audio)

        assert isinstance(blendshapes, dict)
        assert "jawOpen" in blendshapes
        # Loud audio should have more jaw movement
        assert blendshapes["jawOpen"] > 0

    def test_generate_mock_blendshapes_empty_audio(self):
        """Generate mock blendshapes from empty audio."""
        engine = Audio2FaceEngine()

        blendshapes = engine._generate_mock_blendshapes(b"")

        assert isinstance(blendshapes, dict)
        # Should return neutral blendshapes

    def test_generate_mock_blendshapes_short_audio(self):
        """Generate mock blendshapes from very short audio."""
        engine = Audio2FaceEngine()

        blendshapes = engine._generate_mock_blendshapes(b"\x00")

        assert isinstance(blendshapes, dict)


class TestAudio2FaceEngineLocalGeneration:
    """Tests for local frame generation fallback."""

    @pytest.fixture
    def engine(self):
        """Create engine for testing."""
        return Audio2FaceEngine()

    @pytest.fixture(autouse=True)
    def setup_audio_clock(self):
        """Register session with audio clock."""
        from src.audio.transport.audio_clock import get_audio_clock
        clock = get_audio_clock()
        clock.start_session("local-test")
        clock.start_session("cancel-gen-test")
        yield
        try:
            clock.end_session("local-test")
        except KeyError:
            pass
        try:
            clock.end_session("cancel-gen-test")
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_generate_frames_local_fallback(self, engine):
        """Generate frames uses local fallback when gRPC unavailable."""
        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client.is_connected = False
            mock_client_cls.return_value = mock_client

            await engine.start("local-test")

            # Create audio stream
            async def audio_stream():
                yield b"\x00" * 640
                yield b"\x00" * 640

            frames = []
            async for frame in engine.generate_frames(audio_stream()):
                frames.append(frame)
                if len(frames) >= 2:
                    break

            assert len(frames) >= 1
            assert frames[0].session_id == "local-test"

            await engine.stop()

    @pytest.mark.asyncio
    async def test_generate_frames_cancelled(self, engine):
        """Generate frames stops when cancelled."""
        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client.is_connected = False
            mock_client_cls.return_value = mock_client

            await engine.start("cancel-gen-test")

            async def audio_stream():
                yield b"\x00" * 640
                engine._cancelled = True
                yield b"\x00" * 640

            frames = []
            async for frame in engine.generate_frames(audio_stream()):
                frames.append(frame)

            # Should have stopped early due to cancellation
            assert len(frames) <= 2

            await engine.stop()


class TestAudio2FaceEngineBufferedStream:
    """Tests for buffered audio stream."""

    @pytest.mark.asyncio
    async def test_buffered_stream_batches_audio(self):
        """Buffered stream batches audio correctly."""
        engine = Audio2FaceEngine()

        with patch("src.animation.audio2face_engine.Audio2FaceClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await engine.start("buffer-test")

            async def audio_stream():
                # Send small chunks
                yield b"\x00" * 100
                yield b"\x00" * 100
                yield b"\x00" * 100

            batches = []
            async for batch in engine._buffered_audio_stream(audio_stream()):
                batches.append(batch)

            # Should have received batched output
            assert len(batches) >= 1

            await engine.stop()


class TestCreateAudio2FaceFactory:
    """Tests for create_audio2face_engine factory."""

    def test_factory_creates_engine(self):
        """Factory creates Audio2FaceEngine instance."""
        from src.animation.audio2face_engine import create_audio2face_engine

        engine = create_audio2face_engine()
        assert isinstance(engine, Audio2FaceEngine)

    def test_factory_accepts_config(self):
        """Factory accepts custom config."""
        from src.animation.audio2face_engine import create_audio2face_engine

        config = Audio2FaceConfig(target_fps=60)
        engine = create_audio2face_engine(config)

        assert engine._config.target_fps == 60
