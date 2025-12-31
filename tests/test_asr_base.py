"""Tests for ASR Base Interface.

Tests cover:
- ASRResult dataclass
- ASREventType enum
- BaseASREngine callback management
- MockASREngine simulation methods
"""

import pytest

from src.audio.asr.base import (
    ASREventType,
    ASRResult,
    BaseASREngine,
    MockASREngine,
)


class TestASREventType:
    """Tests for ASREventType enum."""

    def test_all_event_types_exist(self):
        """All event types exist."""
        assert ASREventType.PARTIAL.value == "partial"
        assert ASREventType.FINAL.value == "final"
        assert ASREventType.ENDPOINT.value == "endpoint"

    def test_event_type_count(self):
        """Exactly 3 event types exist."""
        assert len(ASREventType) == 3


class TestASRResult:
    """Tests for ASRResult dataclass."""

    def test_create_minimal_result(self):
        """Create result with minimal fields."""
        result = ASRResult(
            event_type=ASREventType.PARTIAL,
            text="Hello",
        )
        assert result.event_type == ASREventType.PARTIAL
        assert result.text == "Hello"
        assert result.start_ms is None
        assert result.end_ms is None
        assert result.confidence == 1.0
        assert result.is_final is False
        assert result.session_id == ""

    def test_create_full_result(self):
        """Create result with all fields."""
        result = ASRResult(
            event_type=ASREventType.FINAL,
            text="Hello world",
            start_ms=100,
            end_ms=500,
            confidence=0.95,
            is_final=True,
            session_id="test-session",
        )
        assert result.event_type == ASREventType.FINAL
        assert result.text == "Hello world"
        assert result.start_ms == 100
        assert result.end_ms == 500
        assert result.confidence == 0.95
        assert result.is_final is True
        assert result.session_id == "test-session"

    def test_partial_result(self):
        """Create partial transcription result."""
        result = ASRResult(
            event_type=ASREventType.PARTIAL,
            text="Hel",
            start_ms=0,
            is_final=False,
        )
        assert result.event_type == ASREventType.PARTIAL
        assert result.is_final is False

    def test_endpoint_result(self):
        """Create endpoint event result."""
        result = ASRResult(
            event_type=ASREventType.ENDPOINT,
            text="",
            end_ms=1000,
        )
        assert result.event_type == ASREventType.ENDPOINT
        assert result.end_ms == 1000


class TestMockASREngine:
    """Tests for MockASREngine."""

    @pytest.fixture
    def engine(self):
        """Create mock ASR engine."""
        return MockASREngine()

    @pytest.mark.asyncio
    async def test_start_initializes_engine(self, engine):
        """Start initializes engine state."""
        await engine.start("test-session")

        assert engine.session_id == "test-session"
        assert engine.is_running is True

    @pytest.mark.asyncio
    async def test_stop_clears_state(self, engine):
        """Stop clears engine state."""
        await engine.start("test-session")
        await engine.stop()

        assert engine.is_running is False

    @pytest.mark.asyncio
    async def test_push_audio_no_op_when_not_running(self, engine):
        """Push audio does nothing when not running."""
        # Should not raise
        await engine.push_audio(b"\x00" * 640, 100)

    @pytest.mark.asyncio
    async def test_push_audio_accepts_audio_when_running(self, engine):
        """Push audio accepts data when running."""
        await engine.start("test-session")

        # Should not raise
        await engine.push_audio(b"\x00" * 640, 100)

        await engine.stop()


class TestMockASREngineCallbacks:
    """Tests for MockASREngine callback handling."""

    @pytest.fixture
    def engine(self):
        """Create mock ASR engine."""
        return MockASREngine()

    @pytest.mark.asyncio
    async def test_on_partial_registers_callback(self, engine):
        """Partial callback is registered."""
        partials = []

        def callback(text, t_ms):
            partials.append((text, t_ms))

        engine.on_partial(callback)
        assert len(engine._callbacks_partial) == 1

    @pytest.mark.asyncio
    async def test_on_final_registers_callback(self, engine):
        """Final callback is registered."""
        finals = []

        def callback(text, start_ms, end_ms):
            finals.append((text, start_ms, end_ms))

        engine.on_final(callback)
        assert len(engine._callbacks_final) == 1

    @pytest.mark.asyncio
    async def test_on_endpoint_registers_callback(self, engine):
        """Endpoint callback is registered."""
        endpoints = []

        def callback(t_ms):
            endpoints.append(t_ms)

        engine.on_endpoint(callback)
        assert len(engine._callbacks_endpoint) == 1

    @pytest.mark.asyncio
    async def test_multiple_callbacks_per_event(self, engine):
        """Multiple callbacks can be registered for same event."""
        results1 = []
        results2 = []

        engine.on_partial(lambda t, m: results1.append(t))
        engine.on_partial(lambda t, m: results2.append(t))

        assert len(engine._callbacks_partial) == 2


class TestMockASREngineSimulation:
    """Tests for MockASREngine simulation methods."""

    @pytest.fixture
    def engine(self):
        """Create mock ASR engine."""
        return MockASREngine()

    @pytest.mark.asyncio
    async def test_simulate_partial_emits_to_callbacks(self, engine):
        """Simulate partial emits to all callbacks."""
        partials = []

        def callback(text, t_ms):
            partials.append((text, t_ms))

        engine.on_partial(callback)
        await engine.start("test-session")

        await engine.simulate_partial("Hello", 100)

        assert len(partials) == 1
        assert partials[0] == ("Hello", 100)

        await engine.stop()

    @pytest.mark.asyncio
    async def test_simulate_final_emits_to_callbacks(self, engine):
        """Simulate final emits to all callbacks."""
        finals = []

        def callback(text, start_ms, end_ms):
            finals.append((text, start_ms, end_ms))

        engine.on_final(callback)
        await engine.start("test-session")

        await engine.simulate_final("Hello world", 100, 500)

        assert len(finals) == 1
        assert finals[0] == ("Hello world", 100, 500)

        await engine.stop()

    @pytest.mark.asyncio
    async def test_simulate_endpoint_emits_to_callbacks(self, engine):
        """Simulate endpoint emits to all callbacks."""
        endpoints = []

        def callback(t_ms):
            endpoints.append(t_ms)

        engine.on_endpoint(callback)
        await engine.start("test-session")

        await engine.simulate_endpoint(1000)

        assert len(endpoints) == 1
        assert endpoints[0] == 1000

        await engine.stop()

    @pytest.mark.asyncio
    async def test_simulate_multiple_partials(self, engine):
        """Simulate multiple partial updates."""
        partials = []

        engine.on_partial(lambda t, m: partials.append(t))
        await engine.start("test-session")

        await engine.simulate_partial("H", 100)
        await engine.simulate_partial("He", 150)
        await engine.simulate_partial("Hel", 200)
        await engine.simulate_partial("Hell", 250)
        await engine.simulate_partial("Hello", 300)

        assert len(partials) == 5
        assert partials == ["H", "He", "Hel", "Hell", "Hello"]

        await engine.stop()

    @pytest.mark.asyncio
    async def test_callback_error_does_not_stop_emission(self, engine):
        """Callback error doesn't prevent other callbacks from running."""
        results = []

        def failing_callback(text, t_ms):
            raise ValueError("Test error")

        def working_callback(text, t_ms):
            results.append(text)

        engine.on_partial(failing_callback)
        engine.on_partial(working_callback)
        await engine.start("test-session")

        # Should not raise, and working callback should still be called
        await engine.simulate_partial("Hello", 100)

        assert len(results) == 1
        assert results[0] == "Hello"

        await engine.stop()


class TestBaseASREngineProperties:
    """Tests for BaseASREngine properties."""

    @pytest.fixture
    def engine(self):
        """Create mock ASR engine (concrete implementation of base)."""
        return MockASREngine()

    @pytest.mark.asyncio
    async def test_session_id_none_before_start(self, engine):
        """Session ID is None before start."""
        assert engine.session_id is None

    @pytest.mark.asyncio
    async def test_session_id_set_after_start(self, engine):
        """Session ID is set after start."""
        await engine.start("my-session")
        assert engine.session_id == "my-session"
        await engine.stop()

    @pytest.mark.asyncio
    async def test_is_running_false_initially(self, engine):
        """is_running is False initially."""
        assert engine.is_running is False

    @pytest.mark.asyncio
    async def test_is_running_true_after_start(self, engine):
        """is_running is True after start."""
        await engine.start("test")
        assert engine.is_running is True
        await engine.stop()

    @pytest.mark.asyncio
    async def test_is_running_false_after_stop(self, engine):
        """is_running is False after stop."""
        await engine.start("test")
        await engine.stop()
        assert engine.is_running is False
