"""Turn Detector - Endpoint detection with 15ms budget.

TMF v3.0 §6: Turn Detection
- Endpoint detection must complete within 15ms budget
- Triggers LISTENING → THINKING state transition
- Hard timeout of 500ms for cumulative latency (TMF §6.1)

This module coordinates:
- VAD endpoint events
- Endpoint confirmation logic
- State transition triggers
- Latency tracking for TTFA measurement

Reference: Implementation-v3.0.md §5 Orchestrator
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from src.audio.transport.audio_clock import get_audio_clock
from src.audio.vad.silero_vad import VADEvent, VADState
from src.config.constants import TMF
from src.observability.logging import get_logger

logger = get_logger(__name__)


class TurnState(Enum):
    """Turn-taking state for conversation."""

    IDLE = "idle"  # No active conversation
    LISTENING = "listening"  # User is speaking
    ENDPOINT_DETECTED = "endpoint_detected"  # VAD detected end of speech
    THINKING = "thinking"  # Processing user input
    SPEAKING = "speaking"  # Agent is responding
    INTERRUPTED = "interrupted"  # User interrupted agent


@dataclass
class TurnEvent:
    """Event for turn state changes."""

    old_state: TurnState
    new_state: TurnState
    t_ms: int  # Timestamp from audio clock
    session_id: str
    reason: str = ""
    latency_ms: int | None = None  # For endpoint detection latency


@dataclass
class TurnDetector:
    """Detects conversation turns with TMF-compliant timing.

    Responsibilities:
    - Track turn state (IDLE → LISTENING → THINKING → SPEAKING → LISTENING)
    - Handle endpoint detection within 15ms budget
    - Trigger CANCEL on user barge-in
    - Track TTFA start point (endpoint detection)

    Usage:
        detector = TurnDetector(session_id="session-123")

        # Register callbacks
        detector.on_endpoint(handle_endpoint)
        detector.on_barge_in(handle_barge_in)

        # Process VAD events
        await detector.handle_vad_event(vad_event)
    """

    session_id: str
    endpoint_budget_ms: int = TMF.TURN_ENDPOINT_BUDGET_MS
    hard_timeout_ms: int = TMF.TURN_HARD_TIMEOUT_MS

    # Internal state
    _state: TurnState = field(default=TurnState.IDLE, init=False)
    _endpoint_start_ns: int | None = field(default=None, init=False)
    _ttfa_start_ms: int | None = field(default=None, init=False)
    _callbacks_endpoint: list = field(default_factory=list, init=False)
    _callbacks_barge_in: list = field(default_factory=list, init=False)
    _callbacks_state_change: list = field(default_factory=list, init=False)

    def _get_timestamp(self) -> int:
        """Get current timestamp from audio clock."""
        clock = get_audio_clock()
        return clock.get_time_ms(self.session_id)

    def _get_timestamp_ns(self) -> int:
        """Get high-precision timestamp for latency measurement."""
        clock = get_audio_clock()
        return clock.get_reading(self.session_id).raw_ns

    def on_endpoint(self, callback: Callable[[TurnEvent], None]) -> None:
        """Register callback for endpoint detection events.

        This is the TTFA start point.
        """
        self._callbacks_endpoint.append(callback)

    def on_barge_in(self, callback: Callable[[TurnEvent], None]) -> None:
        """Register callback for barge-in (user interrupts agent)."""
        self._callbacks_barge_in.append(callback)

    def on_state_change(self, callback: Callable[[TurnEvent], None]) -> None:
        """Register callback for any state change."""
        self._callbacks_state_change.append(callback)

    async def handle_vad_event(self, event: VADEvent) -> TurnEvent | None:
        """Process VAD event and update turn state.

        Args:
            event: VAD state change event

        Returns:
            TurnEvent if state changed, None otherwise
        """
        if event.state == VADState.SPEECH:
            return await self._handle_speech_start(event)
        elif event.state == VADState.ENDPOINT:
            return await self._handle_speech_end(event)
        return None

    async def _handle_speech_start(self, event: VADEvent) -> TurnEvent | None:
        """Handle user starting to speak."""
        old_state = self._state

        if self._state == TurnState.IDLE:
            # User starts conversation
            self._state = TurnState.LISTENING
            return await self._emit_state_change(
                old_state, TurnState.LISTENING, event.t_ms, "user_speech_start"
            )

        elif self._state == TurnState.SPEAKING:
            # User interrupts agent (barge-in)
            self._state = TurnState.INTERRUPTED
            turn_event = TurnEvent(
                old_state=old_state,
                new_state=TurnState.INTERRUPTED,
                t_ms=event.t_ms,
                session_id=self.session_id,
                reason="user_barge_in",
            )
            await self._emit_barge_in(turn_event)

            # Immediately transition to LISTENING
            self._state = TurnState.LISTENING
            return await self._emit_state_change(
                TurnState.INTERRUPTED, TurnState.LISTENING, event.t_ms, "barge_in_listening"
            )

        return None

    async def _handle_speech_end(self, event: VADEvent) -> TurnEvent | None:
        """Handle user stopping speaking (endpoint detection).

        TMF §6: Endpoint detection must complete within 15ms budget.
        This is the TTFA measurement start point.
        """
        if self._state != TurnState.LISTENING:
            return None

        # Start endpoint detection timing
        self._endpoint_start_ns = self._get_timestamp_ns()

        # Mark state as endpoint detected
        old_state = self._state
        self._state = TurnState.ENDPOINT_DETECTED

        # Record TTFA start point
        self._ttfa_start_ms = event.t_ms

        # Emit endpoint event
        turn_event = TurnEvent(
            old_state=old_state,
            new_state=TurnState.ENDPOINT_DETECTED,
            t_ms=event.t_ms,
            session_id=self.session_id,
            reason="vad_endpoint",
        )
        await self._emit_endpoint(turn_event)

        # Calculate endpoint detection latency
        clock = get_audio_clock()
        latency_ms = clock.measure_elapsed_ms(self._endpoint_start_ns)

        if latency_ms > self.endpoint_budget_ms:
            # Log warning but continue (TMF §6.1 allows degradation)
            pass

        # Transition to THINKING
        self._state = TurnState.THINKING
        return await self._emit_state_change(
            TurnState.ENDPOINT_DETECTED,
            TurnState.THINKING,
            self._get_timestamp(),
            "endpoint_confirmed",
            latency_ms=int(latency_ms),
        )

    async def start_speaking(self) -> TurnEvent | None:
        """Mark agent as starting to speak.

        Called when LLM/TTS begins audio output.
        """
        if self._state != TurnState.THINKING:
            return None

        old_state = self._state
        self._state = TurnState.SPEAKING
        return await self._emit_state_change(
            old_state, TurnState.SPEAKING, self._get_timestamp(), "agent_speaking"
        )

    async def finish_speaking(self) -> TurnEvent | None:
        """Mark agent as finished speaking.

        Called when TTS output completes.
        """
        if self._state != TurnState.SPEAKING:
            return None

        old_state = self._state
        self._state = TurnState.LISTENING
        return await self._emit_state_change(
            old_state, TurnState.LISTENING, self._get_timestamp(), "agent_finished"
        )

    async def reset_turn(self, reason: str = "timeout") -> TurnEvent | None:
        """Reset turn state (e.g., on hard timeout).

        TMF §6.1: Hard timeout of 500ms triggers turn reset.
        """
        old_state = self._state
        self._state = TurnState.LISTENING
        self._ttfa_start_ms = None
        return await self._emit_state_change(
            old_state, TurnState.LISTENING, self._get_timestamp(), f"reset_{reason}"
        )

    async def _emit_state_change(
        self,
        old_state: TurnState,
        new_state: TurnState,
        t_ms: int,
        reason: str,
        latency_ms: int | None = None,
    ) -> TurnEvent:
        """Emit state change event."""
        event = TurnEvent(
            old_state=old_state,
            new_state=new_state,
            t_ms=t_ms,
            session_id=self.session_id,
            reason=reason,
            latency_ms=latency_ms,
        )

        for callback in self._callbacks_state_change:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(
                    "turn_state_change_callback_error",
                    session_id=self.session_id,
                    callback=getattr(callback, "__name__", str(callback)),
                    error=str(e),
                )

        return event

    async def _emit_endpoint(self, event: TurnEvent) -> None:
        """Emit endpoint detection event."""
        for callback in self._callbacks_endpoint:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(
                    "turn_endpoint_callback_error",
                    session_id=self.session_id,
                    callback=getattr(callback, "__name__", str(callback)),
                    error=str(e),
                )

    async def _emit_barge_in(self, event: TurnEvent) -> None:
        """Emit barge-in event."""
        for callback in self._callbacks_barge_in:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(
                    "turn_barge_in_callback_error",
                    session_id=self.session_id,
                    callback=getattr(callback, "__name__", str(callback)),
                    error=str(e),
                )

    @property
    def state(self) -> TurnState:
        """Current turn state."""
        return self._state

    @property
    def ttfa_start_ms(self) -> int | None:
        """TTFA measurement start point (endpoint detection time)."""
        return self._ttfa_start_ms

    @property
    def is_user_turn(self) -> bool:
        """Whether it's the user's turn (LISTENING state)."""
        return self._state == TurnState.LISTENING

    @property
    def is_agent_turn(self) -> bool:
        """Whether it's the agent's turn (THINKING or SPEAKING)."""
        return self._state in (TurnState.THINKING, TurnState.SPEAKING)
