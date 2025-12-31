"""Tests for TTS Backends.

Tests cover:
- MockBackend implementation
- TTSRequest/TTSResult/TTSStreamChunk dataclasses
- TTSHealthStatus
- Backend interface compliance
"""

import asyncio

import pytest

from src.audio.tts.backends.interface import (
    TTSBackend,
    TTSHealthStatus,
    TTSRequest,
    TTSResult,
    TTSStreamChunk,
)
from src.audio.tts.backends.mock_backend import MockBackend


class TestTTSRequest:
    """Tests for TTSRequest dataclass."""

    def test_create_simple(self):
        """Create request with just text."""
        request = TTSRequest(text="Hello world")
        assert request.text == "Hello world"
        assert request.voice_id is None
        assert request.language is None
        assert request.prosody is None

    def test_create_full(self):
        """Create request with all fields."""
        request = TTSRequest(
            text="Hello",
            voice_id="voice-1",
            language="en-US",
            prosody={"speed": 1.2, "pitch": 0.9},
        )
        assert request.text == "Hello"
        assert request.voice_id == "voice-1"
        assert request.language == "en-US"
        assert request.prosody == {"speed": 1.2, "pitch": 0.9}


class TestTTSResult:
    """Tests for TTSResult dataclass."""

    def test_create_result(self):
        """Create TTS result."""
        result = TTSResult(
            audio=b"\x00" * 1000,
            sample_rate=24000,
            latency_ms=50.0,
        )
        assert len(result.audio) == 1000
        assert result.sample_rate == 24000
        assert result.latency_ms == 50.0

    def test_default_values(self):
        """Default values are applied."""
        result = TTSResult(audio=b"")
        assert result.sample_rate == 24000
        assert result.latency_ms == 0.0


class TestTTSStreamChunk:
    """Tests for TTSStreamChunk dataclass."""

    def test_create_chunk(self):
        """Create stream chunk."""
        chunk = TTSStreamChunk(
            chunk=b"\x00" * 480,
            is_final=False,
            latency_ms=10.0,
        )
        assert len(chunk.chunk) == 480
        assert chunk.is_final is False
        assert chunk.latency_ms == 10.0

    def test_final_chunk(self):
        """Create final chunk."""
        chunk = TTSStreamChunk(chunk=b"", is_final=True)
        assert chunk.is_final is True


class TestTTSHealthStatus:
    """Tests for TTSHealthStatus dataclass."""

    def test_healthy_status(self):
        """Create healthy status."""
        status = TTSHealthStatus(ok=True, backend="mock")
        assert status.ok is True
        assert status.backend == "mock"
        assert status.last_error is None

    def test_unhealthy_status(self):
        """Create unhealthy status."""
        status = TTSHealthStatus(
            ok=False,
            backend="mock",
            last_error="Connection failed",
        )
        assert status.ok is False
        assert status.last_error == "Connection failed"


class TestMockBackend:
    """Tests for MockBackend implementation."""

    def test_init_default(self):
        """Initialize with defaults."""
        backend = MockBackend()
        assert backend.name == "mock"
        assert backend._sample_rate == 24000
        assert backend._chunk_duration_ms == 20
        assert backend._chars_per_second == 15.0

    def test_init_custom(self):
        """Initialize with custom values."""
        backend = MockBackend(
            sample_rate=16000,
            chunk_duration_ms=10,
            chars_per_second=20.0,
        )
        assert backend._sample_rate == 16000
        assert backend._chunk_duration_ms == 10
        assert backend._chars_per_second == 20.0

    @pytest.mark.asyncio
    async def test_init_method(self):
        """Init method marks as initialized."""
        backend = MockBackend()
        assert backend._initialized is False

        await backend.init()
        assert backend._initialized is True


class TestMockBackendSynthesize:
    """Tests for MockBackend.synthesize()."""

    @pytest.fixture
    async def backend(self):
        """Create initialized backend."""
        backend = MockBackend()
        await backend.init()
        return backend

    @pytest.mark.asyncio
    async def test_synthesize_returns_result(self, backend):
        """Synthesize returns TTSResult."""
        request = TTSRequest(text="Hello")
        result = await backend.synthesize(request)

        assert isinstance(result, TTSResult)
        assert result.sample_rate == 24000
        assert result.latency_ms == 0.0

    @pytest.mark.asyncio
    async def test_synthesize_audio_length(self, backend):
        """Audio length based on text length."""
        # 15 chars at 15 chars/second = 1 second
        # 1 second at 24kHz = 24000 samples
        # 16-bit audio = 2 bytes per sample = 48000 bytes
        request = TTSRequest(text="a" * 15)
        result = await backend.synthesize(request)

        expected_bytes = 24000 * 2  # 1 second of 16-bit mono
        assert len(result.audio) == expected_bytes

    @pytest.mark.asyncio
    async def test_synthesize_produces_silence(self, backend):
        """Audio is silence (zeros)."""
        request = TTSRequest(text="Hello")
        result = await backend.synthesize(request)

        # All bytes should be zero
        assert result.audio == b"\x00" * len(result.audio)

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self, backend):
        """Empty text produces empty audio."""
        request = TTSRequest(text="")
        result = await backend.synthesize(request)

        assert len(result.audio) == 0


class TestMockBackendStream:
    """Tests for MockBackend.stream()."""

    @pytest.fixture
    async def backend(self):
        """Create initialized backend with fast timing."""
        backend = MockBackend(
            chunk_duration_ms=1,  # Fast for testing
            chars_per_second=100.0,  # Fast for testing
        )
        await backend.init()
        return backend

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self, backend):
        """Stream yields TTSStreamChunk objects."""
        request = TTSRequest(text="Hello")
        chunks = []

        async for chunk in backend.stream(request):
            chunks.append(chunk)

        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, TTSStreamChunk)

    @pytest.mark.asyncio
    async def test_stream_last_chunk_is_final(self, backend):
        """Last chunk has is_final=True."""
        request = TTSRequest(text="Hello")
        chunks = []

        async for chunk in backend.stream(request):
            chunks.append(chunk)

        # All but last should be non-final
        for chunk in chunks[:-1]:
            assert chunk.is_final is False

        # Last should be final
        assert chunks[-1].is_final is True

    @pytest.mark.asyncio
    async def test_stream_chunks_have_audio(self, backend):
        """Each chunk has audio bytes."""
        request = TTSRequest(text="Hello")

        async for chunk in backend.stream(request):
            assert len(chunk.chunk) > 0

    @pytest.mark.asyncio
    async def test_stream_latency_increases(self, backend):
        """Latency increases with each chunk."""
        request = TTSRequest(text="Hello world test")
        latencies = []

        async for chunk in backend.stream(request):
            latencies.append(chunk.latency_ms)

        # Should be monotonically increasing from 0
        assert latencies[0] == 0.0
        for i in range(1, len(latencies)):
            assert latencies[i] >= latencies[i - 1]

    @pytest.mark.asyncio
    async def test_stream_at_least_one_chunk(self, backend):
        """Stream produces at least one chunk even for short text."""
        request = TTSRequest(text="H")
        chunks = []

        async for chunk in backend.stream(request):
            chunks.append(chunk)

        assert len(chunks) >= 1


class TestMockBackendHealth:
    """Tests for MockBackend.health()."""

    @pytest.mark.asyncio
    async def test_health_before_init(self):
        """Health returns not-ok before init."""
        backend = MockBackend()
        status = await backend.health()

        assert status.ok is False
        assert status.backend == "mock"
        assert status.last_error == "Not initialized"

    @pytest.mark.asyncio
    async def test_health_after_init(self):
        """Health returns ok after init."""
        backend = MockBackend()
        await backend.init()
        status = await backend.health()

        assert status.ok is True
        assert status.backend == "mock"
        assert status.last_error is None


class TestMockBackendInterface:
    """Tests for TTSBackend interface compliance."""

    def test_is_tts_backend(self):
        """MockBackend is a TTSBackend."""
        backend = MockBackend()
        assert isinstance(backend, TTSBackend)

    def test_has_name_property(self):
        """Has name property."""
        backend = MockBackend()
        assert hasattr(backend, "name")
        assert backend.name == "mock"

    @pytest.mark.asyncio
    async def test_has_init_method(self):
        """Has init method."""
        backend = MockBackend()
        assert hasattr(backend, "init")
        await backend.init()

    @pytest.mark.asyncio
    async def test_has_synthesize_method(self):
        """Has synthesize method."""
        backend = MockBackend()
        await backend.init()
        assert hasattr(backend, "synthesize")
        result = await backend.synthesize(TTSRequest(text="test"))
        assert isinstance(result, TTSResult)

    @pytest.mark.asyncio
    async def test_has_stream_method(self):
        """Has stream method."""
        backend = MockBackend()
        await backend.init()
        assert hasattr(backend, "stream")

    @pytest.mark.asyncio
    async def test_has_health_method(self):
        """Has health method."""
        backend = MockBackend()
        assert hasattr(backend, "health")
        status = await backend.health()
        assert isinstance(status, TTSHealthStatus)
