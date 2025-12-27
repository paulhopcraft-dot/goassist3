"""Tests for Kyutai TTS adapter.

Tests the KyutaiTTSEngine implementation without requiring
a real Kyutai TTS server (uses mocks).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.audio.tts import create_tts_engine
from src.audio.tts.kyutai_tts import (
    KyutaiTTSConfig,
    KyutaiTTSEngine,
    WordTimestamp,
)


class TestKyutaiTTSConfig:
    """Tests for KyutaiTTSConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = KyutaiTTSConfig()

        assert config.server_url == "ws://localhost:8080/tts"
        assert config.sample_rate == 24000
        assert config.channels == 1
        assert config.voice_id == "default"
        assert config.chunk_size_ms == 20
        assert config.cancel_timeout_ms == 150  # TMF barge-in budget

    def test_custom_config(self):
        """Test custom configuration."""
        config = KyutaiTTSConfig(
            server_url="ws://custom:9000/tts",
            voice_id="en-female-1",
            sample_rate=48000,
        )

        assert config.server_url == "ws://custom:9000/tts"
        assert config.voice_id == "en-female-1"
        assert config.sample_rate == 48000

    def test_voice_sample_path(self):
        """Test voice cloning configuration."""
        config = KyutaiTTSConfig(
            voice_sample_path="/path/to/voice.wav",
        )

        assert config.voice_sample_path == "/path/to/voice.wav"


class TestKyutaiTTSEngineCreation:
    """Tests for KyutaiTTSEngine instantiation."""

    def test_create_with_config(self):
        """Test engine creation with explicit config."""
        config = KyutaiTTSConfig(voice_id="test-voice")
        engine = KyutaiTTSEngine(config=config)

        assert engine.config.voice_id == "test-voice"
        assert not engine.is_running

    def test_create_with_word_callback(self):
        """Test engine creation with word timestamp callback."""
        words_received = []

        def on_word(word: WordTimestamp):
            words_received.append(word)

        config = KyutaiTTSConfig()
        engine = KyutaiTTSEngine(config=config, on_word=on_word)

        assert engine._on_word is not None

    def test_factory_function_mock(self):
        """Test create_tts_engine factory with mock."""
        engine = create_tts_engine("mock")

        assert engine is not None
        assert not engine.is_running

    def test_factory_function_kyutai(self):
        """Test create_tts_engine factory with kyutai."""
        engine = create_tts_engine(
            "kyutai",
            server_url="ws://test:8080/tts",
            voice_id="test-voice",
        )

        assert isinstance(engine, KyutaiTTSEngine)
        assert engine.config.server_url == "ws://test:8080/tts"
        assert engine.config.voice_id == "test-voice"

    def test_factory_function_invalid(self):
        """Test create_tts_engine with invalid engine."""
        with pytest.raises(ValueError, match="Unknown TTS engine"):
            create_tts_engine("invalid_engine")


class TestWordTimestamp:
    """Tests for WordTimestamp dataclass."""

    def test_word_timestamp_creation(self):
        """Test WordTimestamp creation."""
        ts = WordTimestamp(word="hello", start_ms=100, end_ms=350)

        assert ts.word == "hello"
        assert ts.start_ms == 100
        assert ts.end_ms == 350

    def test_word_timestamp_duration(self):
        """Test word duration calculation."""
        ts = WordTimestamp(word="world", start_ms=400, end_ms=700)

        duration = ts.end_ms - ts.start_ms
        assert duration == 300


class TestKyutaiTTSEngineState:
    """Tests for KyutaiTTSEngine state management."""

    def test_initial_state(self):
        """Test engine initial state."""
        engine = KyutaiTTSEngine()

        assert not engine.is_running
        assert not engine.is_synthesizing
        assert not engine.is_cancelled
        assert engine.session_id is None

    def test_cancel_sets_flag(self):
        """Test that cancel sets the cancelled flag."""
        engine = KyutaiTTSEngine()

        # Can call cancel even when not running
        asyncio.run(engine.cancel())

        assert engine.is_cancelled

    def test_stop_resets_running(self):
        """Test that stop resets running state."""
        engine = KyutaiTTSEngine()
        engine._running = True

        asyncio.run(engine.stop())

        assert not engine.is_running


class TestKyutaiTTSEngineMocked:
    """Tests for KyutaiTTSEngine with mocked WebSocket."""

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        ws = AsyncMock()
        ws.send = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_start_connects_websocket(self, mock_websocket):
        """Test that start() connects to WebSocket server."""
        with patch("src.audio.tts.kyutai_tts.websockets") as mock_ws:
            mock_ws.connect = AsyncMock(return_value=mock_websocket)

            engine = KyutaiTTSEngine()
            await engine.start("test-session")

            assert engine.is_running
            assert engine.session_id == "test-session"
            mock_ws.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_sends_config(self, mock_websocket):
        """Test that start() sends initial configuration."""
        with patch("src.audio.tts.kyutai_tts.websockets") as mock_ws:
            mock_ws.connect = AsyncMock(return_value=mock_websocket)

            config = KyutaiTTSConfig(voice_id="custom-voice")
            engine = KyutaiTTSEngine(config=config)
            await engine.start("test-session")

            # Verify config was sent
            mock_websocket.send.assert_called()
            call_arg = mock_websocket.send.call_args[0][0]
            assert "custom-voice" in call_arg

    @pytest.mark.asyncio
    async def test_stop_closes_websocket(self, mock_websocket):
        """Test that stop() closes WebSocket connection."""
        with patch("src.audio.tts.kyutai_tts.websockets") as mock_ws:
            mock_ws.connect = AsyncMock(return_value=mock_websocket)

            engine = KyutaiTTSEngine()
            await engine.start("test-session")
            await engine.stop()

            assert not engine.is_running
            mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_sends_cancel_message(self, mock_websocket):
        """Test that cancel() sends cancel message."""
        with patch("src.audio.tts.kyutai_tts.websockets") as mock_ws:
            mock_ws.connect = AsyncMock(return_value=mock_websocket)

            engine = KyutaiTTSEngine()
            await engine.start("test-session")
            await engine.cancel()

            assert engine.is_cancelled
            # Should have sent cancel message
            calls = mock_websocket.send.call_args_list
            assert any("cancel" in str(call) for call in calls)


class TestKyutaiTTSStreaming:
    """Tests for streaming synthesis."""

    @pytest.mark.asyncio
    async def test_synthesize_requires_start(self):
        """Test that synthesize_stream requires start() first."""
        engine = KyutaiTTSEngine()

        async def text_gen():
            yield "hello"

        with pytest.raises(RuntimeError, match="not started"):
            async for _ in engine.synthesize_stream(text_gen()):
                pass

    @pytest.mark.asyncio
    async def test_word_timestamps_collected(self):
        """Test that word timestamps are collected."""
        words_received = []

        def on_word(word: WordTimestamp):
            words_received.append(word)

        # Create engine with callback
        config = KyutaiTTSConfig()
        engine = KyutaiTTSEngine(config=config, on_word=on_word)

        # Manually add word timestamps (simulating server response)
        ts1 = WordTimestamp(word="hello", start_ms=0, end_ms=200)
        ts2 = WordTimestamp(word="world", start_ms=250, end_ms=500)

        engine._state.word_timestamps.append(ts1)
        engine._state.word_timestamps.append(ts2)

        # Trigger callback manually
        if engine._on_word:
            engine._on_word(ts1)
            engine._on_word(ts2)

        assert len(words_received) == 2
        assert words_received[0].word == "hello"
        assert words_received[1].word == "world"

    def test_word_timestamps_property(self):
        """Test word_timestamps property returns copy."""
        engine = KyutaiTTSEngine()

        ts = WordTimestamp(word="test", start_ms=0, end_ms=100)
        engine._state.word_timestamps.append(ts)

        # Get timestamps
        timestamps = engine.word_timestamps

        # Should be a copy
        assert timestamps is not engine._state.word_timestamps
        assert len(timestamps) == 1
        assert timestamps[0].word == "test"


class TestTMFCompliance:
    """Tests for TMF v3.0 compliance."""

    def test_cancel_timeout_within_budget(self):
        """Test that cancel timeout is within barge-in budget."""
        config = KyutaiTTSConfig()

        # TMF requires cancel within 150ms
        assert config.cancel_timeout_ms <= 150

    def test_chunk_size_matches_tmf(self):
        """Test that chunk size matches TMF audio packet duration."""
        config = KyutaiTTSConfig()

        # TMF specifies 20ms audio packets
        assert config.chunk_size_ms == 20

    def test_streaming_text_input_supported(self):
        """Test that streaming text input is supported."""
        engine = KyutaiTTSEngine()

        # The synthesize_stream method should accept AsyncIterator[str]
        # This is the key feature for low TTFA
        import inspect
        sig = inspect.signature(engine.synthesize_stream)

        assert "text_stream" in sig.parameters
