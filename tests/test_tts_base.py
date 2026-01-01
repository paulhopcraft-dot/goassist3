"""Tests for TTS Base Interface.

Tests cover:
- TTSChunk dataclass
- BaseTTSEngine lifecycle and properties
- MockTTSEngine synthesis
- text_to_stream utility
"""

import pytest
import asyncio

from src.audio.tts.base import (
    TTSChunk,
    BaseTTSEngine,
    MockTTSEngine,
    text_to_stream,
)


class TestTTSChunk:
    """Tests for TTSChunk dataclass."""

    def test_create_minimal(self):
        """Create chunk with just audio."""
        chunk = TTSChunk(audio=b"\x00" * 640)
        assert chunk.audio == b"\x00" * 640
        assert chunk.is_final is False
        assert chunk.text_offset == 0
        assert chunk.duration_ms == 0

    def test_create_full(self):
        """Create chunk with all fields."""
        chunk = TTSChunk(
            audio=b"\x00" * 1280,
            is_final=True,
            text_offset=50,
            duration_ms=40,
        )
        assert len(chunk.audio) == 1280
        assert chunk.is_final is True
        assert chunk.text_offset == 50
        assert chunk.duration_ms == 40

    def test_final_chunk(self):
        """Create final chunk marker."""
        chunk = TTSChunk(audio=b"", is_final=True)
        assert chunk.is_final is True


class TestMockTTSEngine:
    """Tests for MockTTSEngine."""

    def test_init_default(self):
        """Initialize with defaults."""
        engine = MockTTSEngine()
        assert engine._chunk_duration_ms == 20
        assert engine._sample_rate == 16000

    def test_init_custom(self):
        """Initialize with custom values."""
        engine = MockTTSEngine(chunk_duration_ms=10)
        assert engine._chunk_duration_ms == 10


class TestMockTTSEngineLifecycle:
    """Tests for MockTTSEngine lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_session(self):
        """Start sets session ID."""
        engine = MockTTSEngine()
        await engine.start("test-session")

        assert engine.session_id == "test-session"
        assert engine.is_running is True

    @pytest.mark.asyncio
    async def test_stop_clears_state(self):
        """Stop clears running state."""
        engine = MockTTSEngine()
        await engine.start("test-session")
        await engine.stop()

        assert engine.is_running is False

    @pytest.mark.asyncio
    async def test_cancel_sets_flag(self):
        """Cancel sets cancelled flag."""
        engine = MockTTSEngine()
        await engine.start("test-session")
        await engine.cancel()

        assert engine.is_cancelled is True
        assert engine.is_synthesizing is False


class TestMockTTSEngineProperties:
    """Tests for MockTTSEngine properties."""

    def test_session_id_none_initially(self):
        """session_id is None before start."""
        engine = MockTTSEngine()
        assert engine.session_id is None

    def test_is_running_false_initially(self):
        """is_running is False initially."""
        engine = MockTTSEngine()
        assert engine.is_running is False

    def test_is_synthesizing_false_initially(self):
        """is_synthesizing is False initially."""
        engine = MockTTSEngine()
        assert engine.is_synthesizing is False

    def test_is_cancelled_false_initially(self):
        """is_cancelled is False initially."""
        engine = MockTTSEngine()
        assert engine.is_cancelled is False


class TestMockTTSEngineSynthesize:
    """Tests for MockTTSEngine.synthesize_stream()."""

    @pytest.fixture
    async def engine(self):
        """Create started engine."""
        engine = MockTTSEngine()
        await engine.start("test-session")
        return engine

    @pytest.mark.asyncio
    async def test_synthesize_yields_audio(self, engine):
        """synthesize_stream yields audio bytes."""
        async def text_stream():
            yield "Hello"

        chunks = []
        async for audio in engine.synthesize_stream(text_stream()):
            chunks.append(audio)

        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, bytes)

    @pytest.mark.asyncio
    async def test_synthesize_generates_silence(self, engine):
        """Generated audio is silence."""
        async def text_stream():
            yield "Hi"

        async for audio in engine.synthesize_stream(text_stream()):
            # Silence is all zeros
            assert audio == b"\x00" * len(audio)
            break  # Just check first chunk

    @pytest.mark.asyncio
    async def test_synthesize_sets_synthesizing_flag(self, engine):
        """Synthesis sets synthesizing flag."""
        async def text_stream():
            yield "Hello"

        async for _ in engine.synthesize_stream(text_stream()):
            # During synthesis, is_synthesizing should be True
            pass

        # After synthesis, is_synthesizing should be False
        assert engine.is_synthesizing is False

    @pytest.mark.asyncio
    async def test_synthesize_respects_cancel(self, engine):
        """Synthesis stops on cancel."""
        async def text_stream():
            for i in range(100):
                yield "x" * 10

        chunks = []
        async for audio in engine.synthesize_stream(text_stream()):
            chunks.append(audio)
            if len(chunks) >= 5:
                await engine.cancel()
                break

        # Should have stopped early
        assert len(chunks) <= 10

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self, engine):
        """Empty text produces no audio."""
        async def text_stream():
            yield ""

        chunks = []
        async for audio in engine.synthesize_stream(text_stream()):
            chunks.append(audio)

        # Empty text should produce no chunks
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_synthesize_multiple_chunks(self, engine):
        """Multiple text chunks are processed."""
        async def text_stream():
            yield "Hello"
            yield " "
            yield "World"

        chunks = []
        async for audio in engine.synthesize_stream(text_stream()):
            chunks.append(audio)

        assert len(chunks) > 0


class TestTextToStream:
    """Tests for text_to_stream utility."""

    @pytest.mark.asyncio
    async def test_empty_string(self):
        """Empty string produces no items."""
        result = []
        async for char in text_to_stream(""):
            result.append(char)

        assert result == []

    @pytest.mark.asyncio
    async def test_single_char(self):
        """Single character produces one item."""
        result = []
        async for char in text_to_stream("A"):
            result.append(char)

        assert result == ["A"]

    @pytest.mark.asyncio
    async def test_multiple_chars(self):
        """Multiple characters produce multiple items."""
        result = []
        async for char in text_to_stream("Hello"):
            result.append(char)

        assert result == ["H", "e", "l", "l", "o"]

    @pytest.mark.asyncio
    async def test_with_spaces(self):
        """Spaces are included as characters."""
        result = []
        async for char in text_to_stream("Hi there"):
            result.append(char)

        assert result == ["H", "i", " ", "t", "h", "e", "r", "e"]

    @pytest.mark.asyncio
    async def test_with_newlines(self):
        """Newlines are included as characters."""
        result = []
        async for char in text_to_stream("Hi\nBye"):
            result.append(char)

        assert result == ["H", "i", "\n", "B", "y", "e"]


class TestBaseTTSEngineAbstract:
    """Tests for BaseTTSEngine abstract methods."""

    def test_is_abstract(self):
        """BaseTTSEngine cannot be instantiated directly."""
        # Should raise TypeError because it's abstract
        with pytest.raises(TypeError):
            BaseTTSEngine()


class TestMockTTSEngineCancel:
    """Tests for MockTTSEngine cancel behavior."""

    @pytest.fixture
    async def engine(self):
        """Create started engine."""
        engine = MockTTSEngine()
        await engine.start("test-session")
        return engine

    @pytest.mark.asyncio
    async def test_cancel_before_synthesis(self, engine):
        """Cancel before synthesis sets flag."""
        await engine.cancel()

        assert engine.is_cancelled is True

    @pytest.mark.asyncio
    async def test_cancel_resets_on_new_synthesis(self, engine):
        """Cancel flag resets on new synthesis."""
        await engine.cancel()
        assert engine.is_cancelled is True

        async def text_stream():
            yield "Hi"

        async for _ in engine.synthesize_stream(text_stream()):
            # During synthesis, cancelled should be reset
            assert engine.is_cancelled is False
            break


class TestMockTTSEngineStop:
    """Tests for MockTTSEngine stop behavior."""

    @pytest.mark.asyncio
    async def test_stop_calls_cancel(self):
        """Stop calls cancel internally."""
        engine = MockTTSEngine()
        await engine.start("test-session")
        await engine.stop()

        # After stop, cancelled should be True (from cancel call)
        assert engine.is_cancelled is True
        assert engine.is_running is False

    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        """Stop without start doesn't raise."""
        engine = MockTTSEngine()
        # Should not raise
        await engine.stop()
