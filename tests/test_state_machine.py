"""Tests for Session State Machine.

Tests the 5-state FSM for conversation flow.
Reference: TMF v3.0, PRD v3.0 §5.1
"""

import pytest

from src.orchestrator.state_machine import (
    SessionState,
    SessionStateMachine,
    StateTransition,
    VALID_TRANSITIONS,
)
from src.orchestrator.cancellation import CancellationController
from src.audio.transport.audio_clock import get_audio_clock


class TestSessionState:
    """Tests for SessionState enum."""

    def test_all_states_exist(self):
        """All 5 states exist."""
        assert SessionState.IDLE.value == "idle"
        assert SessionState.LISTENING.value == "listening"
        assert SessionState.THINKING.value == "thinking"
        assert SessionState.SPEAKING.value == "speaking"
        assert SessionState.INTERRUPTED.value == "interrupted"

    def test_state_count(self):
        """Exactly 5 states exist."""
        assert len(SessionState) == 5


class TestValidTransitions:
    """Tests for valid state transitions."""

    def test_idle_transitions(self):
        """IDLE can only go to LISTENING."""
        assert VALID_TRANSITIONS[SessionState.IDLE] == {SessionState.LISTENING}

    def test_listening_transitions(self):
        """LISTENING can go to THINKING or IDLE."""
        assert VALID_TRANSITIONS[SessionState.LISTENING] == {
            SessionState.THINKING,
            SessionState.IDLE,
        }

    def test_thinking_transitions(self):
        """THINKING can go to SPEAKING, LISTENING, or IDLE."""
        assert VALID_TRANSITIONS[SessionState.THINKING] == {
            SessionState.SPEAKING,
            SessionState.LISTENING,
            SessionState.IDLE,
        }

    def test_speaking_transitions(self):
        """SPEAKING can go to LISTENING, INTERRUPTED, or IDLE."""
        assert VALID_TRANSITIONS[SessionState.SPEAKING] == {
            SessionState.LISTENING,
            SessionState.INTERRUPTED,
            SessionState.IDLE,
        }

    def test_interrupted_transitions(self):
        """INTERRUPTED can go to LISTENING or IDLE."""
        assert VALID_TRANSITIONS[SessionState.INTERRUPTED] == {
            SessionState.LISTENING,
            SessionState.IDLE,
        }


class TestStateTransition:
    """Tests for StateTransition dataclass."""

    def test_create_transition(self):
        """Create a state transition record."""
        transition = StateTransition(
            old_state=SessionState.IDLE,
            new_state=SessionState.LISTENING,
            t_ms=12345,
            reason="test",
        )
        assert transition.old_state == SessionState.IDLE
        assert transition.new_state == SessionState.LISTENING
        assert transition.t_ms == 12345
        assert transition.reason == "test"
        assert transition.metadata == {}

    def test_transition_with_metadata(self):
        """Transition can include metadata."""
        transition = StateTransition(
            old_state=SessionState.LISTENING,
            new_state=SessionState.THINKING,
            t_ms=0,
            reason="endpoint",
            metadata={"confidence": 0.95},
        )
        assert transition.metadata == {"confidence": 0.95}


class TestSessionStateMachine:
    """Tests for SessionStateMachine."""

    @pytest.fixture
    def fsm(self):
        """Create a state machine with registered session."""
        clock = get_audio_clock()
        session_id = "test-fsm"
        clock.start_session(session_id)
        fsm = SessionStateMachine(session_id)
        yield fsm
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    def test_init(self, fsm):
        """FSM initializes in IDLE state."""
        assert fsm.state == SessionState.IDLE
        assert fsm.session_id == "test-fsm"
        assert len(fsm.history) == 0

    @pytest.mark.asyncio
    async def test_valid_transition(self, fsm):
        """Valid transitions succeed."""
        transition = await fsm.transition_to(SessionState.LISTENING, "test")

        assert transition is not None
        assert transition.old_state == SessionState.IDLE
        assert transition.new_state == SessionState.LISTENING
        assert fsm.state == SessionState.LISTENING

    @pytest.mark.asyncio
    async def test_invalid_transition(self, fsm):
        """Invalid transitions raise ValueError."""
        with pytest.raises(ValueError, match="Invalid transition"):
            # IDLE can't go directly to SPEAKING
            await fsm.transition_to(SessionState.SPEAKING, "invalid")

    @pytest.mark.asyncio
    async def test_transition_records_history(self, fsm):
        """Transitions are recorded in history."""
        await fsm.transition_to(SessionState.LISTENING, "test")

        assert len(fsm.history) == 1
        assert fsm.history[0].new_state == SessionState.LISTENING

    @pytest.mark.asyncio
    async def test_history_limit(self, fsm):
        """History is limited to max_history entries."""
        # Do many transitions
        for _ in range(50):
            await fsm.transition_to(SessionState.LISTENING, "test")
            await fsm.transition_to(SessionState.IDLE, "reset")

        assert len(fsm.history) <= fsm._max_history


class TestStateCallbacks:
    """Tests for state change callbacks."""

    @pytest.fixture
    def fsm(self):
        clock = get_audio_clock()
        session_id = "test-callbacks"
        clock.start_session(session_id)
        fsm = SessionStateMachine(session_id)
        yield fsm
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_on_state_change_callback(self, fsm):
        """State change callback is called."""
        received = []

        def callback(transition):
            received.append(transition)

        fsm.on_state_change(callback)
        await fsm.transition_to(SessionState.LISTENING, "test")

        assert len(received) == 1
        assert received[0].new_state == SessionState.LISTENING

    @pytest.mark.asyncio
    async def test_on_enter_callback(self, fsm):
        """Enter callback is called for specific state."""
        enter_called = False

        def callback(transition):
            nonlocal enter_called
            enter_called = True

        fsm.on_enter(SessionState.LISTENING, callback)
        await fsm.transition_to(SessionState.LISTENING, "test")

        assert enter_called

    @pytest.mark.asyncio
    async def test_on_exit_callback(self, fsm):
        """Exit callback is called when leaving state."""
        exit_called = False

        def callback(transition):
            nonlocal exit_called
            exit_called = True

        fsm.on_exit(SessionState.IDLE, callback)
        await fsm.transition_to(SessionState.LISTENING, "test")

        assert exit_called

    @pytest.mark.asyncio
    async def test_async_callback(self, fsm):
        """Async callbacks work correctly."""
        received = []

        async def callback(transition):
            received.append(transition)

        fsm.on_state_change(callback)
        await fsm.transition_to(SessionState.LISTENING, "test")

        assert len(received) == 1


class TestConversationFlow:
    """Tests for typical conversation flows."""

    @pytest.fixture
    def fsm(self):
        clock = get_audio_clock()
        session_id = "test-flow"
        clock.start_session(session_id)
        fsm = SessionStateMachine(session_id)
        yield fsm
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_normal_turn(self, fsm):
        """Normal conversation turn flow."""
        # User starts speaking
        await fsm.handle_user_speech_start()
        assert fsm.state == SessionState.LISTENING

        # User stops speaking
        await fsm.handle_user_speech_end()
        assert fsm.state == SessionState.THINKING

        # LLM responds
        await fsm.handle_response_ready()
        assert fsm.state == SessionState.SPEAKING

        # TTS completes
        await fsm.handle_response_complete()
        assert fsm.state == SessionState.LISTENING

    @pytest.mark.asyncio
    async def test_barge_in(self, fsm):
        """Barge-in interruption flow."""
        # Get to SPEAKING state
        await fsm.transition_to(SessionState.LISTENING, "start")
        await fsm.transition_to(SessionState.THINKING, "endpoint")
        await fsm.transition_to(SessionState.SPEAKING, "response")

        assert fsm.state == SessionState.SPEAKING

        # User interrupts
        transition = await fsm.handle_barge_in()

        assert transition is not None
        assert fsm.state == SessionState.LISTENING
        # Cancellation should be triggered
        assert fsm.cancellation.is_cancelled

    @pytest.mark.asyncio
    async def test_user_speech_start_from_idle(self, fsm):
        """User speech start from IDLE goes to LISTENING."""
        assert fsm.state == SessionState.IDLE

        await fsm.handle_user_speech_start()

        assert fsm.state == SessionState.LISTENING

    @pytest.mark.asyncio
    async def test_user_speech_start_from_speaking(self, fsm):
        """User speech start from SPEAKING triggers barge-in."""
        # Get to SPEAKING
        await fsm.transition_to(SessionState.LISTENING, "start")
        await fsm.transition_to(SessionState.THINKING, "endpoint")
        await fsm.transition_to(SessionState.SPEAKING, "response")

        # Speech during speaking = barge-in
        await fsm.handle_user_speech_start()

        assert fsm.state == SessionState.LISTENING

    @pytest.mark.asyncio
    async def test_reset(self, fsm):
        """Reset returns to IDLE from any state."""
        await fsm.transition_to(SessionState.LISTENING, "start")
        await fsm.transition_to(SessionState.THINKING, "endpoint")

        await fsm.reset()

        assert fsm.state == SessionState.IDLE

    @pytest.mark.asyncio
    async def test_reset_from_idle(self, fsm):
        """Reset from IDLE does nothing."""
        assert fsm.state == SessionState.IDLE

        result = await fsm.reset()

        assert result is None
        assert fsm.state == SessionState.IDLE


class TestHandlerGuards:
    """Tests for handler state guards."""

    @pytest.fixture
    def fsm(self):
        clock = get_audio_clock()
        session_id = "test-guards"
        clock.start_session(session_id)
        fsm = SessionStateMachine(session_id)
        yield fsm
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_barge_in_only_from_speaking(self, fsm):
        """Barge-in only works from SPEAKING state."""
        # From IDLE
        result = await fsm.handle_barge_in()
        assert result is None

        # From LISTENING
        await fsm.transition_to(SessionState.LISTENING, "start")
        result = await fsm.handle_barge_in()
        assert result is None

    @pytest.mark.asyncio
    async def test_speech_end_only_from_listening(self, fsm):
        """Speech end only works from LISTENING state."""
        # From IDLE
        result = await fsm.handle_user_speech_end()
        assert result is None

    @pytest.mark.asyncio
    async def test_response_ready_only_from_thinking(self, fsm):
        """Response ready only works from THINKING state."""
        # From IDLE
        result = await fsm.handle_response_ready()
        assert result is None

        # From LISTENING
        await fsm.transition_to(SessionState.LISTENING, "start")
        result = await fsm.handle_response_ready()
        assert result is None

    @pytest.mark.asyncio
    async def test_response_complete_only_from_speaking(self, fsm):
        """Response complete only works from SPEAKING state."""
        # From IDLE
        result = await fsm.handle_response_complete()
        assert result is None
