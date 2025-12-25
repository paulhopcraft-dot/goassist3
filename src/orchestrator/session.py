"""Session Container - Manages individual voice session lifecycle.

Coordinates all components for a single voice conversation:
- State machine (FSM)
- Context window
- Cancellation controller
- Component references (VAD, ASR, LLM, TTS, Animation)

Reference: Implementation-v3.0.md §5 Orchestrator
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from src.audio.transport.audio_clock import get_audio_clock
from src.config.constants import TMF
from src.orchestrator.cancellation import CancellationController, create_cancel_handler
from src.orchestrator.context_rollover import ContextWindow, create_context_window
from src.orchestrator.state_machine import SessionState, SessionStateMachine
from src.observability.logging import SessionLogger
from src.observability.metrics import (
    record_session_end,
    record_session_start,
    record_ttfa,
    record_turn_complete,
    update_context_tokens,
)


@dataclass
class SessionConfig:
    """Configuration for a voice session."""

    system_prompt: str = "You are a helpful voice assistant."
    max_context_tokens: int = TMF.LLM_MAX_CONTEXT_TOKENS
    rollover_threshold: int = TMF.CONTEXT_ROLLOVER_THRESHOLD
    enable_avatar: bool = True
    enable_metrics: bool = True


@dataclass
class SessionMetrics:
    """Runtime metrics for a session."""

    turns_completed: int = 0
    total_ttfa_ms: float = 0.0
    min_ttfa_ms: float = float("inf")
    max_ttfa_ms: float = 0.0
    barge_ins: int = 0
    context_rollovers: int = 0
    start_time_ms: int = 0
    last_turn_time_ms: int = 0

    @property
    def avg_ttfa_ms(self) -> float:
        """Average TTFA in milliseconds."""
        if self.turns_completed == 0:
            return 0.0
        return self.total_ttfa_ms / self.turns_completed

    @property
    def is_warmup(self) -> bool:
        """Whether session is still in warmup period.

        TMF: Steady-state = 3 turns OR 60 seconds since start.
        """
        clock = get_audio_clock()
        elapsed_ms = clock.get_absolute_ms() - self.start_time_ms
        return self.turns_completed < 3 and elapsed_ms < 60_000


class Session:
    """Voice session container.

    Manages all components and state for a single voice conversation.

    Usage:
        session = Session(session_id="session-123")
        await session.start()

        # Process audio
        await session.process_audio(audio_bytes, t_audio_ms)

        # Handle events
        await session.on_speech_start()
        await session.on_endpoint_detected()
        await session.on_response_complete()

        await session.stop()
    """

    def __init__(
        self,
        session_id: str | None = None,
        config: SessionConfig | None = None,
    ) -> None:
        self._session_id = session_id or str(uuid.uuid4())
        self._config = config or SessionConfig()

        # Core components
        self._cancellation = CancellationController(self._session_id)
        self._state_machine = SessionStateMachine(
            session_id=self._session_id,
            cancellation=self._cancellation,
        )
        self._context: ContextWindow | None = None

        # Component references (set during start)
        self._vad: Any = None
        self._asr: Any = None
        self._llm: Any = None
        self._tts: Any = None
        self._animation: Any = None

        # Session state
        self._running: bool = False
        self._metrics = SessionMetrics()
        self._logger = SessionLogger(self._session_id)

        # Turn tracking
        self._current_turn_id: int = 0
        self._turn_start_ms: int = 0

        # Callbacks
        self._on_audio_output: Callable[[bytes], None] | None = None
        self._on_blendshapes: Callable[[dict], None] | None = None

    @property
    def session_id(self) -> str:
        """Session identifier."""
        return self._session_id

    @property
    def state(self) -> SessionState:
        """Current session state."""
        return self._state_machine.state

    @property
    def is_running(self) -> bool:
        """Whether session is active."""
        return self._running

    @property
    def metrics(self) -> SessionMetrics:
        """Session metrics."""
        return self._metrics

    @property
    def context_tokens(self) -> int:
        """Current context token count."""
        if self._context:
            return self._context.total_tokens
        return 0

    async def start(
        self,
        vad: Any = None,
        asr: Any = None,
        llm: Any = None,
        tts: Any = None,
        animation: Any = None,
    ) -> None:
        """Start the session.

        Args:
            vad: VAD instance
            asr: ASR engine
            llm: LLM client
            tts: TTS engine
            animation: Animation engine (optional)
        """
        if self._running:
            return

        # Store component references
        self._vad = vad
        self._asr = asr
        self._llm = llm
        self._tts = tts
        self._animation = animation

        # Initialize context window
        self._context = create_context_window(
            system_prompt=self._config.system_prompt,
            llm_client=llm,
            max_tokens=self._config.max_context_tokens,
            rollover_threshold=self._config.rollover_threshold,
        )

        # Register cancel handlers
        if tts:
            self._cancellation.register(create_cancel_handler("tts", tts.cancel))
        if llm:
            self._cancellation.register(create_cancel_handler("llm", llm.abort))
        if animation:
            self._cancellation.register(create_cancel_handler("animation", animation.stop))

        # Register audio clock
        clock = get_audio_clock()
        clock.register_session(self._session_id)

        # Record metrics
        self._metrics.start_time_ms = clock.get_absolute_ms()
        self._running = True

        if self._config.enable_metrics:
            record_session_start()

        self._logger.session_started({
            "config": {
                "max_context_tokens": self._config.max_context_tokens,
                "enable_avatar": self._config.enable_avatar,
            }
        })

    async def stop(self, reason: str = "normal") -> None:
        """Stop the session.

        Args:
            reason: Reason for stopping (normal, timeout, error)
        """
        if not self._running:
            return

        # Cancel any in-progress operations
        await self._cancellation.cancel()

        # Reset state machine
        await self._state_machine.reset()

        # Unregister from audio clock
        clock = get_audio_clock()
        try:
            clock.unregister_session(self._session_id)
        except KeyError:
            pass

        # Calculate session duration
        duration_s = (clock.get_absolute_ms() - self._metrics.start_time_ms) / 1000.0

        self._running = False

        if self._config.enable_metrics:
            record_session_end(reason)

        self._logger.session_ended(reason=reason, duration_s=duration_s)

    async def on_speech_start(self) -> None:
        """Handle user speech start (VAD onset)."""
        if not self._running:
            return

        transition = await self._state_machine.handle_user_speech_start()
        if transition:
            self._logger.state_change(
                old_state=transition.old_state.value,
                new_state=transition.new_state.value,
                reason=transition.reason,
                t_ms=transition.t_ms,
            )

    async def on_endpoint_detected(self, t_ms: int) -> None:
        """Handle speech endpoint detection.

        Args:
            t_ms: Timestamp of endpoint
        """
        if not self._running:
            return

        # Start new turn
        self._current_turn_id += 1
        self._turn_start_ms = t_ms

        self._logger.turn_started(self._current_turn_id)

        transition = await self._state_machine.handle_user_speech_end()
        if transition:
            self._logger.state_change(
                old_state=transition.old_state.value,
                new_state=transition.new_state.value,
                reason=transition.reason,
                t_ms=transition.t_ms,
            )

    async def on_first_audio_byte(self, t_ms: int) -> None:
        """Handle first audio byte output.

        Called when TTS emits first audio byte.
        Used to calculate TTFA.

        Args:
            t_ms: Timestamp of first audio byte
        """
        if self._turn_start_ms == 0:
            return

        ttfa_ms = t_ms - self._turn_start_ms

        # Update metrics
        self._metrics.total_ttfa_ms += ttfa_ms
        self._metrics.min_ttfa_ms = min(self._metrics.min_ttfa_ms, ttfa_ms)
        self._metrics.max_ttfa_ms = max(self._metrics.max_ttfa_ms, ttfa_ms)

        if self._config.enable_metrics:
            record_ttfa(ttfa_ms)

    async def on_response_ready(self) -> None:
        """Handle LLM response ready, transition to speaking."""
        if not self._running:
            return

        transition = await self._state_machine.handle_response_ready()
        if transition:
            self._logger.state_change(
                old_state=transition.old_state.value,
                new_state=transition.new_state.value,
                reason=transition.reason,
                t_ms=transition.t_ms,
            )

    async def on_response_complete(self) -> None:
        """Handle TTS output complete."""
        if not self._running:
            return

        clock = get_audio_clock()
        t_ms = clock.get_time_ms(self._session_id)

        # Calculate turn duration
        total_ms = t_ms - self._turn_start_ms

        self._metrics.turns_completed += 1
        self._metrics.last_turn_time_ms = t_ms

        if self._config.enable_metrics:
            record_turn_complete()
            update_context_tokens(self._session_id, self.context_tokens)

        self._logger.turn_completed(
            turn_id=self._current_turn_id,
            ttfa_ms=self._metrics.max_ttfa_ms,  # Use last recorded TTFA
            total_ms=total_ms,
        )

        transition = await self._state_machine.handle_response_complete()
        if transition:
            self._logger.state_change(
                old_state=transition.old_state.value,
                new_state=transition.new_state.value,
                reason=transition.reason,
                t_ms=transition.t_ms,
            )

    async def on_barge_in(self) -> None:
        """Handle user barge-in (interruption)."""
        if not self._running:
            return

        self._metrics.barge_ins += 1

        transition = await self._state_machine.handle_barge_in()
        if transition:
            self._logger.state_change(
                old_state=transition.old_state.value,
                new_state=transition.new_state.value,
                reason=transition.reason,
                t_ms=transition.t_ms,
            )

    def add_user_message(self, content: str) -> None:
        """Add user message to context.

        Args:
            content: User message content
        """
        if self._context:
            self._context.add_user_message(content)

    def add_assistant_message(self, content: str) -> None:
        """Add assistant message to context.

        Args:
            content: Assistant message content
        """
        if self._context:
            self._context.add_assistant_message(content)

    async def get_context_messages(self) -> list[dict[str, str]]:
        """Get messages for LLM.

        Returns:
            List of message dicts
        """
        if self._context:
            return await self._context.get_messages()
        return []

    def set_audio_output_callback(
        self, callback: Callable[[bytes], None]
    ) -> None:
        """Set callback for audio output.

        Args:
            callback: Function to call with audio bytes
        """
        self._on_audio_output = callback

    def set_blendshapes_callback(
        self, callback: Callable[[dict], None]
    ) -> None:
        """Set callback for blendshape output.

        Args:
            callback: Function to call with blendshape dict
        """
        self._on_blendshapes = callback


class SessionManager:
    """Manages multiple concurrent sessions.

    Provides:
    - Session creation and lookup
    - Concurrent session limits
    - Session cleanup

    Usage:
        manager = SessionManager(max_sessions=10)

        session = await manager.create_session()
        # ... use session ...
        await manager.end_session(session.session_id)
    """

    def __init__(
        self,
        max_sessions: int = TMF.MAX_CONCURRENT_SESSIONS,
        default_config: SessionConfig | None = None,
    ) -> None:
        self._max_sessions = max_sessions
        self._default_config = default_config or SessionConfig()
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        """Number of active sessions."""
        return len(self._sessions)

    @property
    def available_slots(self) -> int:
        """Number of available session slots."""
        return self._max_sessions - len(self._sessions)

    async def create_session(
        self,
        session_id: str | None = None,
        config: SessionConfig | None = None,
    ) -> Session | None:
        """Create a new session.

        Args:
            session_id: Optional session ID (generated if not provided)
            config: Session configuration

        Returns:
            New Session, or None if at capacity
        """
        async with self._lock:
            if len(self._sessions) >= self._max_sessions:
                return None

            session = Session(
                session_id=session_id,
                config=config or self._default_config,
            )

            self._sessions[session.session_id] = session
            return session

    def get_session(self, session_id: str) -> Session | None:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, else None
        """
        return self._sessions.get(session_id)

    async def end_session(
        self,
        session_id: str,
        reason: str = "normal",
    ) -> bool:
        """End and remove a session.

        Args:
            session_id: Session identifier
            reason: Reason for ending

        Returns:
            True if session was found and ended
        """
        async with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                await session.stop(reason)
                return True
            return False

    async def end_all_sessions(self, reason: str = "shutdown") -> int:
        """End all active sessions.

        Args:
            reason: Reason for ending

        Returns:
            Number of sessions ended
        """
        async with self._lock:
            count = len(self._sessions)
            for session in list(self._sessions.values()):
                await session.stop(reason)
            self._sessions.clear()
            return count

    def list_sessions(self) -> list[str]:
        """List all active session IDs."""
        return list(self._sessions.keys())

    def get_sessions_by_state(self, state: SessionState) -> list[Session]:
        """Get sessions in a specific state.

        Args:
            state: Session state to filter by

        Returns:
            List of sessions in that state
        """
        return [s for s in self._sessions.values() if s.state == state]
