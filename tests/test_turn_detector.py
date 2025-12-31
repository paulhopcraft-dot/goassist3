"""Tests for Turn Detector.

Tests cover:
- TurnState enum values
- TurnEvent dataclass
- TurnDetector state machine transitions
- VAD event handling
- Barge-in detection
- Callback system
- TTFA tracking
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.turn_detector import (
    TurnDetector,
    TurnEvent,
    TurnState,
)
from src.audio.vad.silero_vad import VADEvent, VADState


class TestTurnState:
    """Tests for TurnState enum."""

    def test_all_states_exist(self):
        """All turn states exist."""
        assert TurnState.IDLE.value == "idle"
        assert TurnState.LISTENING.value == "listening"
        assert TurnState.ENDPOINT_DETECTED.value == "endpoint_detected"
        assert TurnState.THINKING.value == "thinking"
        assert TurnState.SPEAKING.value == "speaking"
        assert TurnState.INTERRUPTED.value == "interrupted"

    def test_state_count(self):
        """Correct number of states."""
        assert len(TurnState) == 6


class TestTurnEvent:
    """Tests for TurnEvent dataclass."""

    def test_create_event(self):
        """Create a turn event."""
        event = TurnEvent(
            old_state=TurnState.IDLE,
            new_state=TurnState.LISTENING,
            t_ms=1000,
            session_id="test-session",
        )
        assert event.old_state == TurnState.IDLE
        assert event.new_state == TurnState.LISTENING
        assert event.t_ms == 1000
        assert event.session_id == "test-session"
        assert event.reason == ""
        assert event.latency_ms is None

    def test_create_event_with_reason(self):
        """Create event with reason."""
        event = TurnEvent(
            old_state=TurnState.LISTENING,
            new_state=TurnState.THINKING,
            t_ms=2000,
            session_id="test-session",
            reason="vad_endpoint",
        )
        assert event.reason == "vad_endpoint"

    def test_create_event_with_latency(self):
        """Create event with latency measurement."""
        event = TurnEvent(
            old_state=TurnState.ENDPOINT_DETECTED,
            new_state=TurnState.THINKING,
            t_ms=3000,
            session_id="test-session",
            reason="endpoint_confirmed",
            latency_ms=12,
        )
        assert event.latency_ms == 12


class TestTurnDetectorInit:
    """Tests for TurnDetector initialization."""

    def test_default_init(self):
        """Test default initialization."""
        detector = TurnDetector(session_id="test-session")
        assert detector.session_id == "test-session"
        assert detector.state == TurnState.IDLE
        assert detector.ttfa_start_ms is None
        assert detector.is_user_turn is False
        assert detector.is_agent_turn is False

    def test_custom_budget(self):
        """Test custom endpoint budget."""
        detector = TurnDetector(
            session_id="test-session",
            endpoint_budget_ms=20,
            hard_timeout_ms=600,
        )
        assert detector.endpoint_budget_ms == 20
        assert detector.hard_timeout_ms == 600


class TestTurnDetectorStateTransitions:
    """Tests for state transitions."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked clock."""
        with patch("src.orchestrator.turn_detector.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 1000
            mock_clock.return_value.get_reading.return_value.raw_ns = 1000000000
            mock_clock.return_value.measure_elapsed_ms.return_value = 5.0
            detector = TurnDetector(session_id="test-session")
            yield detector

    @pytest.mark.asyncio
    async def test_idle_to_listening_on_speech(self, detector):
        """IDLE -> LISTENING on speech start."""
        assert detector.state == TurnState.IDLE

        vad_event = VADEvent(
            state=VADState.SPEECH,
            t_ms=1000,
            probability=0.9,
            session_id="test-session",
        )
        turn_event = await detector.handle_vad_event(vad_event)

        assert detector.state == TurnState.LISTENING
        assert turn_event is not None
        assert turn_event.old_state == TurnState.IDLE
        assert turn_event.new_state == TurnState.LISTENING
        assert turn_event.reason == "user_speech_start"

    @pytest.mark.asyncio
    async def test_listening_to_thinking_on_endpoint(self, detector):
        """LISTENING -> ENDPOINT_DETECTED -> THINKING on speech end."""
        # First transition to LISTENING
        vad_speech = VADEvent(
            state=VADState.SPEECH,
            t_ms=1000,
            probability=0.9,
            session_id="test-session",
        )
        await detector.handle_vad_event(vad_speech)
        assert detector.state == TurnState.LISTENING

        # Then endpoint detected
        vad_endpoint = VADEvent(
            state=VADState.ENDPOINT,
            t_ms=2000,
            probability=0.1,
            session_id="test-session",
        )
        turn_event = await detector.handle_vad_event(vad_endpoint)

        assert detector.state == TurnState.THINKING
        assert turn_event is not None
        assert turn_event.new_state == TurnState.THINKING
        assert turn_event.reason == "endpoint_confirmed"

    @pytest.mark.asyncio
    async def test_thinking_to_speaking(self, detector):
        """THINKING -> SPEAKING on start_speaking."""
        # Setup: get to THINKING state
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2000, probability=0.1, session_id="test-session"
        ))
        assert detector.state == TurnState.THINKING

        # Start speaking
        turn_event = await detector.start_speaking()

        assert detector.state == TurnState.SPEAKING
        assert turn_event is not None
        assert turn_event.new_state == TurnState.SPEAKING
        assert turn_event.reason == "agent_speaking"

    @pytest.mark.asyncio
    async def test_speaking_to_listening_on_finish(self, detector):
        """SPEAKING -> LISTENING on finish_speaking."""
        # Setup: get to SPEAKING state
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2000, probability=0.1, session_id="test-session"
        ))
        await detector.start_speaking()
        assert detector.state == TurnState.SPEAKING

        # Finish speaking
        turn_event = await detector.finish_speaking()

        assert detector.state == TurnState.LISTENING
        assert turn_event is not None
        assert turn_event.new_state == TurnState.LISTENING
        assert turn_event.reason == "agent_finished"


class TestTurnDetectorBargeIn:
    """Tests for barge-in handling."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked clock."""
        with patch("src.orchestrator.turn_detector.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 1000
            mock_clock.return_value.get_reading.return_value.raw_ns = 1000000000
            mock_clock.return_value.measure_elapsed_ms.return_value = 5.0
            detector = TurnDetector(session_id="test-session")
            yield detector

    @pytest.mark.asyncio
    async def test_barge_in_during_speaking(self, detector):
        """Barge-in when agent is speaking."""
        # Setup: get to SPEAKING state
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2000, probability=0.1, session_id="test-session"
        ))
        await detector.start_speaking()
        assert detector.state == TurnState.SPEAKING

        # User interrupts
        vad_speech = VADEvent(
            state=VADState.SPEECH,
            t_ms=3000,
            probability=0.9,
            session_id="test-session",
        )
        turn_event = await detector.handle_vad_event(vad_speech)

        # Should transition to LISTENING after interruption
        assert detector.state == TurnState.LISTENING
        assert turn_event is not None
        assert turn_event.reason == "barge_in_listening"

    @pytest.mark.asyncio
    async def test_barge_in_callback_called(self, detector):
        """Barge-in callback is invoked."""
        barge_in_events = []

        def on_barge_in(event):
            barge_in_events.append(event)

        detector.on_barge_in(on_barge_in)

        # Setup: get to SPEAKING state
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2000, probability=0.1, session_id="test-session"
        ))
        await detector.start_speaking()

        # Trigger barge-in
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=3000, probability=0.9, session_id="test-session"
        ))

        assert len(barge_in_events) == 1
        assert barge_in_events[0].reason == "user_barge_in"


class TestTurnDetectorCallbacks:
    """Tests for callback system."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked clock."""
        with patch("src.orchestrator.turn_detector.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 1000
            mock_clock.return_value.get_reading.return_value.raw_ns = 1000000000
            mock_clock.return_value.measure_elapsed_ms.return_value = 5.0
            detector = TurnDetector(session_id="test-session")
            yield detector

    @pytest.mark.asyncio
    async def test_endpoint_callback(self, detector):
        """Endpoint callback is invoked."""
        endpoint_events = []

        def on_endpoint(event):
            endpoint_events.append(event)

        detector.on_endpoint(on_endpoint)

        # Trigger endpoint
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2000, probability=0.1, session_id="test-session"
        ))

        assert len(endpoint_events) == 1
        assert endpoint_events[0].reason == "vad_endpoint"

    @pytest.mark.asyncio
    async def test_state_change_callback(self, detector):
        """State change callback is invoked for all transitions."""
        state_changes = []

        def on_state_change(event):
            state_changes.append(event)

        detector.on_state_change(on_state_change)

        # Trigger transitions
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2000, probability=0.1, session_id="test-session"
        ))

        # Should have: IDLE->LISTENING, ENDPOINT_DETECTED->THINKING
        assert len(state_changes) == 2

    @pytest.mark.asyncio
    async def test_async_callback(self, detector):
        """Async callbacks are properly awaited."""
        events = []

        async def async_callback(event):
            await asyncio.sleep(0.001)
            events.append(event)

        detector.on_state_change(async_callback)

        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))

        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_callback_error_handling(self, detector):
        """Callback errors don't break the detector."""
        def bad_callback(event):
            raise ValueError("Test error")

        detector.on_state_change(bad_callback)

        # Should not raise
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))

        assert detector.state == TurnState.LISTENING


class TestTurnDetectorTTFA:
    """Tests for TTFA tracking."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked clock."""
        with patch("src.orchestrator.turn_detector.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 1000
            mock_clock.return_value.get_reading.return_value.raw_ns = 1000000000
            mock_clock.return_value.measure_elapsed_ms.return_value = 5.0
            detector = TurnDetector(session_id="test-session")
            yield detector

    @pytest.mark.asyncio
    async def test_ttfa_start_recorded(self, detector):
        """TTFA start point is recorded on endpoint."""
        assert detector.ttfa_start_ms is None

        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2500, probability=0.1, session_id="test-session"
        ))

        assert detector.ttfa_start_ms == 2500

    @pytest.mark.asyncio
    async def test_ttfa_reset_on_turn_reset(self, detector):
        """TTFA is reset when turn is reset."""
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2000, probability=0.1, session_id="test-session"
        ))
        assert detector.ttfa_start_ms is not None

        await detector.reset_turn("timeout")

        assert detector.ttfa_start_ms is None
        assert detector.state == TurnState.LISTENING


class TestTurnDetectorEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked clock."""
        with patch("src.orchestrator.turn_detector.get_audio_clock") as mock_clock:
            mock_clock.return_value.get_time_ms.return_value = 1000
            mock_clock.return_value.get_reading.return_value.raw_ns = 1000000000
            mock_clock.return_value.measure_elapsed_ms.return_value = 5.0
            detector = TurnDetector(session_id="test-session")
            yield detector

    @pytest.mark.asyncio
    async def test_endpoint_ignored_when_not_listening(self, detector):
        """Endpoint is ignored if not in LISTENING state."""
        assert detector.state == TurnState.IDLE

        result = await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=1000, probability=0.1, session_id="test-session"
        ))

        assert result is None
        assert detector.state == TurnState.IDLE

    @pytest.mark.asyncio
    async def test_start_speaking_ignored_when_not_thinking(self, detector):
        """start_speaking is ignored if not in THINKING state."""
        assert detector.state == TurnState.IDLE

        result = await detector.start_speaking()

        assert result is None
        assert detector.state == TurnState.IDLE

    @pytest.mark.asyncio
    async def test_finish_speaking_ignored_when_not_speaking(self, detector):
        """finish_speaking is ignored if not in SPEAKING state."""
        assert detector.state == TurnState.IDLE

        result = await detector.finish_speaking()

        assert result is None
        assert detector.state == TurnState.IDLE

    @pytest.mark.asyncio
    async def test_speech_during_listening_is_noop(self, detector):
        """Speech event during LISTENING is a no-op."""
        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        assert detector.state == TurnState.LISTENING

        # Another speech event
        result = await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1500, probability=0.9, session_id="test-session"
        ))

        assert result is None
        assert detector.state == TurnState.LISTENING

    @pytest.mark.asyncio
    async def test_is_user_turn_property(self, detector):
        """is_user_turn reflects LISTENING state."""
        assert detector.is_user_turn is False

        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))

        assert detector.is_user_turn is True

    @pytest.mark.asyncio
    async def test_is_agent_turn_property(self, detector):
        """is_agent_turn reflects THINKING or SPEAKING state."""
        assert detector.is_agent_turn is False

        await detector.handle_vad_event(VADEvent(
            state=VADState.SPEECH, t_ms=1000, probability=0.9, session_id="test-session"
        ))
        await detector.handle_vad_event(VADEvent(
            state=VADState.ENDPOINT, t_ms=2000, probability=0.1, session_id="test-session"
        ))

        assert detector.is_agent_turn is True  # THINKING

        await detector.start_speaking()

        assert detector.is_agent_turn is True  # SPEAKING
