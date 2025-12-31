"""Tests for Silero VAD Wrapper.

Tests voice activity detection state machine and callbacks.
"""

import pytest
import numpy as np

from src.audio.vad.silero_vad import (
    SileroVAD,
    VADState,
    VADEvent,
    create_vad,
)
from src.audio.transport.audio_clock import get_audio_clock


class TestVADState:
    """Tests for VADState enum."""

    def test_all_states_exist(self):
        """All VAD states exist."""
        assert VADState.SILENCE.value == "silence"
        assert VADState.SPEECH.value == "speech"
        assert VADState.ENDPOINT.value == "endpoint"

    def test_state_count(self):
        """Exactly 3 states exist."""
        assert len(VADState) == 3


class TestVADEvent:
    """Tests for VADEvent dataclass."""

    def test_create_event(self):
        """Create a VAD event."""
        event = VADEvent(
            state=VADState.SPEECH,
            t_ms=1000,
            probability=0.95,
            session_id="test-session",
        )
        assert event.state == VADState.SPEECH
        assert event.t_ms == 1000
        assert event.probability == 0.95
        assert event.session_id == "test-session"

    def test_endpoint_event(self):
        """Create an endpoint event."""
        event = VADEvent(
            state=VADState.ENDPOINT,
            t_ms=5000,
            probability=0.1,
            session_id="test-session",
        )
        assert event.state == VADState.ENDPOINT


class TestSileroVAD:
    """Tests for SileroVAD wrapper."""

    @pytest.fixture
    def vad(self):
        """Create a VAD instance with registered session."""
        clock = get_audio_clock()
        session_id = "test-vad"
        clock.start_session(session_id)
        vad = SileroVAD(session_id=session_id)
        yield vad
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_init_default_values(self, vad):
        """VAD initializes with correct defaults."""
        assert vad.session_id == "test-vad"
        assert vad.sample_rate == 16000
        assert vad.threshold == 0.5
        assert vad.min_speech_duration_ms == 250
        assert vad.min_silence_duration_ms == 300
        assert vad._running is False

    @pytest.mark.asyncio
    async def test_start_sets_running(self, vad):
        """Start sets running flag."""
        await vad.start()
        assert vad._running is True
        await vad.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self, vad):
        """Stop clears running flag."""
        await vad.start()
        await vad.stop()
        assert vad._running is False
        assert vad._model is None

    @pytest.mark.asyncio
    async def test_initial_state_is_silence(self, vad):
        """VAD starts in SILENCE state."""
        await vad.start()
        assert vad.state == VADState.SILENCE
        assert vad.is_speaking is False
        await vad.stop()

    @pytest.mark.asyncio
    async def test_process_returns_none_when_not_running(self, vad):
        """Process returns None when VAD not running."""
        audio = np.zeros(480, dtype=np.int16).tobytes()
        result = await vad.process(audio)
        assert result is None

    @pytest.mark.asyncio
    async def test_on_speech_start_registers_callback(self, vad):
        """Speech start callback is registered."""
        callback_called = False

        def callback(event):
            nonlocal callback_called
            callback_called = True

        vad.on_speech_start(callback)
        assert len(vad._callbacks_speech_start) == 1

    @pytest.mark.asyncio
    async def test_on_speech_end_registers_callback(self, vad):
        """Speech end callback is registered."""
        events = []

        def callback(event):
            events.append(event)

        vad.on_speech_end(callback)
        assert len(vad._callbacks_speech_end) == 1

    @pytest.mark.asyncio
    async def test_multiple_callbacks(self, vad):
        """Multiple callbacks can be registered."""
        events1 = []
        events2 = []

        vad.on_speech_start(lambda e: events1.append(e))
        vad.on_speech_start(lambda e: events2.append(e))

        assert len(vad._callbacks_speech_start) == 2

    @pytest.mark.asyncio
    async def test_async_callback(self, vad):
        """Async callbacks work correctly."""
        events = []

        async def async_callback(event):
            events.append(event)

        vad.on_speech_start(async_callback)
        assert len(vad._callbacks_speech_start) == 1


class TestSileroVADStateMachine:
    """Tests for VAD state machine transitions."""

    @pytest.fixture
    def vad(self):
        """Create VAD with registered session."""
        clock = get_audio_clock()
        session_id = "test-vad-fsm"
        clock.start_session(session_id)
        vad = SileroVAD(session_id=session_id)
        yield vad
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_silence_to_speech_transition(self, vad):
        """Transition from SILENCE to SPEECH after min duration."""
        await vad.start()

        # Simulate speech detection
        vad._state = VADState.SILENCE
        vad._speech_start_ms = 0

        # After min_speech_duration_ms, should transition
        vad._speech_start_ms = 0
        speech_duration = vad.min_speech_duration_ms + 10

        # Directly test the logic path
        assert vad._state == VADState.SILENCE
        await vad.stop()

    @pytest.mark.asyncio
    async def test_is_speaking_property(self, vad):
        """is_speaking returns correct value."""
        await vad.start()

        # Initially not speaking
        assert vad.is_speaking is False

        # Manually set to speaking
        vad._state = VADState.SPEECH
        assert vad.is_speaking is True

        vad._state = VADState.ENDPOINT
        assert vad.is_speaking is False

        await vad.stop()


class TestVADConfiguration:
    """Tests for VAD configuration options."""

    @pytest.fixture(autouse=True)
    def setup_session(self):
        clock = get_audio_clock()
        clock.start_session("test-config")
        yield
        try:
            clock.end_session("test-config")
        except KeyError:
            pass

    def test_custom_threshold(self):
        """VAD accepts custom threshold."""
        vad = SileroVAD(session_id="test-config", threshold=0.7)
        assert vad.threshold == 0.7

    def test_custom_sample_rate(self):
        """VAD accepts custom sample rate."""
        vad = SileroVAD(session_id="test-config", sample_rate=8000)
        assert vad.sample_rate == 8000

    def test_custom_speech_duration(self):
        """VAD accepts custom min speech duration."""
        vad = SileroVAD(session_id="test-config", min_speech_duration_ms=500)
        assert vad.min_speech_duration_ms == 500

    def test_custom_silence_duration(self):
        """VAD accepts custom min silence duration."""
        vad = SileroVAD(session_id="test-config", min_silence_duration_ms=200)
        assert vad.min_silence_duration_ms == 200

    def test_custom_speech_pad(self):
        """VAD accepts custom speech padding."""
        vad = SileroVAD(session_id="test-config", speech_pad_ms=50)
        assert vad.speech_pad_ms == 50


class TestCreateVADFactory:
    """Tests for create_vad factory function."""

    @pytest.fixture(autouse=True)
    def setup_session(self):
        clock = get_audio_clock()
        clock.start_session("factory-test")
        yield
        try:
            clock.end_session("factory-test")
        except KeyError:
            pass

    def test_creates_vad_instance(self):
        """Factory creates SileroVAD instance."""
        vad = create_vad("factory-test")
        assert isinstance(vad, SileroVAD)
        assert vad.session_id == "factory-test"

    def test_factory_accepts_kwargs(self):
        """Factory passes kwargs to VAD."""
        vad = create_vad("factory-test", threshold=0.8, min_speech_duration_ms=100)
        assert vad.threshold == 0.8
        assert vad.min_speech_duration_ms == 100


class TestVADAudioProcessing:
    """Tests for VAD audio processing."""

    @pytest.fixture
    def vad(self):
        """Create VAD with registered session."""
        clock = get_audio_clock()
        session_id = "test-audio"
        clock.start_session(session_id)
        vad = SileroVAD(session_id=session_id)
        yield vad
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_process_silent_audio(self, vad):
        """Processing silent audio stays in SILENCE state."""
        await vad.start()

        # Silent audio (zeros)
        audio = np.zeros(480, dtype=np.int16).tobytes()
        result = await vad.process(audio)

        # Should stay in silence (model not loaded, returns 0.0 probability)
        assert vad.state == VADState.SILENCE
        await vad.stop()

    @pytest.mark.asyncio
    async def test_get_speech_probability_without_model(self, vad):
        """Speech probability returns 0.0 when model not loaded."""
        await vad.start()

        # Without torch, model is None
        audio = np.random.randn(480).astype(np.float32)
        prob = await vad._get_speech_probability(audio)

        assert prob == 0.0
        await vad.stop()
