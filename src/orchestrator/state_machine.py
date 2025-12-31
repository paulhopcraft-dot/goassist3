"""Session State Machine - 5-state FSM for conversation flow.

TMF v3.0: Orchestrator manages session state transitions.
PRD v3.0 §5.1: State machine states

States:
- IDLE: Agent is ready
- LISTENING: User is speaking / agent is capturing
- THINKING: User finished; agent prepares response
- SPEAKING: Agent outputs voice (and avatar if enabled)
- INTERRUPTED: User begins speaking; agent stops

Reference: Implementation-v3.0.md §5 Orchestrator
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from src.audio.transport.audio_clock import get_audio_clock
from src.orchestrator.cancellation import CancellationController, CancelReason


class SessionState(Enum):
    """Session state per PRD v3.0 §5.1."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


# Valid state transitions
VALID_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.IDLE: {SessionState.LISTENING},
    SessionState.LISTENING: {SessionState.THINKING, SessionState.IDLE},
    SessionState.THINKING: {SessionState.SPEAKING, SessionState.LISTENING, SessionState.IDLE},
    SessionState.SPEAKING: {SessionState.LISTENING, SessionState.INTERRUPTED, SessionState.IDLE},
    SessionState.INTERRUPTED: {SessionState.LISTENING, SessionState.IDLE},
}


@dataclass
class StateTransition:
    """Record of a state transition."""

    old_state: SessionState
    new_state: SessionState
    t_ms: int
    reason: str
    metadata: dict = field(default_factory=dict)


StateChangeCallback = Callable[[StateTransition], None]
AsyncStateChangeCallback = Callable[[StateTransition], asyncio.Future]


class SessionStateMachine:
    """5-state FSM for session management.

    Manages conversation flow and coordinates component transitions.

    Usage:
        fsm = SessionStateMachine(session_id="session-123")

        # Register state change handlers
        fsm.on_state_change(handle_state_change)
        fsm.on_enter(SessionState.SPEAKING, handle_speaking_start)
        fsm.on_exit(SessionState.SPEAKING, handle_speaking_end)

        # Transition states
        await fsm.transition_to(SessionState.LISTENING, "user_connected")
    """

    def __init__(
        self,
        session_id: str,
        cancellation: CancellationController | None = None,
    ) -> None:
        self._session_id = session_id
        self._state = SessionState.IDLE
        self._cancellation = cancellation or CancellationController(session_id)

        # Callback registries
        self._on_change_callbacks: list[StateChangeCallback | AsyncStateChangeCallback] = []
        self._on_enter_callbacks: dict[SessionState, list[Callable]] = {
            s: [] for s in SessionState
        }
        self._on_exit_callbacks: dict[SessionState, list[Callable]] = {
            s: [] for s in SessionState
        }

        # Transition history
        self._history: list[StateTransition] = []
        self._max_history = 100

    @property
    def state(self) -> SessionState:
        """Current session state."""
        return self._state

    @property
    def session_id(self) -> str:
        """Session identifier."""
        return self._session_id

    @property
    def cancellation(self) -> CancellationController:
        """Cancellation controller."""
        return self._cancellation

    def on_state_change(
        self, callback: StateChangeCallback | AsyncStateChangeCallback
    ) -> None:
        """Register callback for any state change."""
        self._on_change_callbacks.append(callback)

    def on_enter(self, state: SessionState, callback: Callable) -> None:
        """Register callback for entering a specific state."""
        self._on_enter_callbacks[state].append(callback)

    def on_exit(self, state: SessionState, callback: Callable) -> None:
        """Register callback for exiting a specific state."""
        self._on_exit_callbacks[state].append(callback)

    async def transition_to(
        self,
        new_state: SessionState,
        reason: str = "",
        metadata: dict | None = None,
    ) -> StateTransition | None:
        """Transition to a new state.

        Args:
            new_state: Target state
            reason: Reason for transition
            metadata: Additional context

        Returns:
            StateTransition if successful, None if invalid transition

        Raises:
            ValueError: If transition is not allowed
        """
        old_state = self._state

        # Validate transition
        if new_state not in VALID_TRANSITIONS.get(old_state, set()):
            raise ValueError(
                f"Invalid transition: {old_state.value} → {new_state.value}"
            )

        # Get timestamp
        clock = get_audio_clock()
        try:
            t_ms = clock.get_time_ms(self._session_id)
        except KeyError:
            t_ms = clock.get_absolute_ms()

        # Create transition record
        transition = StateTransition(
            old_state=old_state,
            new_state=new_state,
            t_ms=t_ms,
            reason=reason,
            metadata=metadata or {},
        )

        # Call exit callbacks
        await self._call_callbacks(self._on_exit_callbacks[old_state], transition)

        # Update state
        self._state = new_state

        # Call enter callbacks
        await self._call_callbacks(self._on_enter_callbacks[new_state], transition)

        # Call change callbacks
        await self._call_callbacks(self._on_change_callbacks, transition)

        # Record history
        self._history.append(transition)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        return transition

    async def handle_barge_in(self) -> StateTransition | None:
        """Handle user barge-in (interruption).

        Triggers CANCEL propagation and transitions to LISTENING.
        """
        if self._state != SessionState.SPEAKING:
            return None

        # Propagate CANCEL to all components
        await self._cancellation.cancel(CancelReason.USER_BARGE_IN)

        # Transition through INTERRUPTED to LISTENING
        await self.transition_to(SessionState.INTERRUPTED, "user_barge_in")
        return await self.transition_to(SessionState.LISTENING, "barge_in_complete")

    async def handle_user_speech_start(self) -> StateTransition | None:
        """Handle user starting to speak.

        From IDLE: Start listening
        From SPEAKING: Barge-in
        """
        if self._state == SessionState.IDLE:
            return await self.transition_to(SessionState.LISTENING, "user_speech_start")
        elif self._state == SessionState.SPEAKING:
            return await self.handle_barge_in()
        return None

    async def handle_user_speech_end(self) -> StateTransition | None:
        """Handle user stopping speaking (endpoint detected)."""
        if self._state != SessionState.LISTENING:
            return None

        return await self.transition_to(SessionState.THINKING, "endpoint_detected")

    async def handle_response_ready(self) -> StateTransition | None:
        """Handle LLM response ready, start speaking."""
        if self._state != SessionState.THINKING:
            return None

        self._cancellation.reset()  # Reset for new turn
        return await self.transition_to(SessionState.SPEAKING, "response_ready")

    async def handle_response_complete(self) -> StateTransition | None:
        """Handle TTS output complete."""
        if self._state != SessionState.SPEAKING:
            return None

        return await self.transition_to(SessionState.LISTENING, "response_complete")

    async def reset(self) -> StateTransition | None:
        """Reset to IDLE state."""
        if self._state == SessionState.IDLE:
            return None

        self._cancellation.reset()
        return await self.transition_to(SessionState.IDLE, "session_reset")

    async def _call_callbacks(
        self,
        callbacks: list[Callable],
        transition: StateTransition,
    ) -> None:
        """Call list of callbacks with transition."""
        for callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(transition)
                else:
                    callback(transition)
            except Exception:
                # Don't let callback errors break state machine
                pass

    @property
    def history(self) -> list[StateTransition]:
        """Transition history (most recent last)."""
        return self._history.copy()

    def get_state_duration_ms(self) -> int:
        """Get time spent in current state (ms)."""
        if not self._history:
            return 0

        last_transition = self._history[-1]
        clock = get_audio_clock()

        try:
            current_ms = clock.get_time_ms(self._session_id)
        except KeyError:
            current_ms = clock.get_absolute_ms()

        return current_ms - last_transition.t_ms
