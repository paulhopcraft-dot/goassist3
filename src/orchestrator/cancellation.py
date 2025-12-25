"""CANCEL Control-Plane Message Propagation.

TMF v3.0 §4.2: Barge-in requires CANCEL to propagate within 150ms.

CANCEL must stop:
- TTS emission immediately
- Audio playback
- Animation emission
- Return orchestrator to LISTENING state

Reference: Implementation-v3.0.md §3.2 CANCEL Schema
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from src.audio.transport.audio_clock import get_audio_clock
from src.config.constants import TMF


class CancelReason(Enum):
    """Reasons for cancel events."""

    USER_BARGE_IN = "USER_BARGE_IN"
    USER_STOP = "USER_STOP"
    SYSTEM_OVERLOAD = "SYSTEM_OVERLOAD"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


@dataclass
class CancelMessage:
    """CANCEL control-plane message per Implementation v3.0 §3.2.

    Schema:
    {
        "session_id": "uuid",
        "type": "CANCEL",
        "reason": "USER_BARGE_IN|USER_STOP|SYSTEM_OVERLOAD",
        "t_event_ms": 987654400
    }
    """

    session_id: str
    reason: CancelReason
    t_event_ms: int

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "type": "CANCEL",
            "reason": self.reason.value,
            "t_event_ms": self.t_event_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CancelMessage":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            reason=CancelReason(data["reason"]),
            t_event_ms=data["t_event_ms"],
        )


CancelHandler = Callable[[CancelMessage], None]
AsyncCancelHandler = Callable[[CancelMessage], asyncio.Future]


class CancellationController:
    """Manages CANCEL message propagation across components.

    Ensures CANCEL reaches all components within the 150ms barge-in budget.

    Usage:
        controller = CancellationController(session_id="session-123")

        # Register handlers
        controller.register(tts.cancel)
        controller.register(llm.abort)
        controller.register(animation.stop)

        # On barge-in
        await controller.cancel(CancelReason.USER_BARGE_IN)
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._handlers: list[CancelHandler | AsyncCancelHandler] = []
        self._cancelled: bool = False
        self._last_cancel: CancelMessage | None = None

    def register(self, handler: CancelHandler | AsyncCancelHandler) -> None:
        """Register a component to receive CANCEL messages.

        Args:
            handler: Sync or async function to call on cancel
        """
        self._handlers.append(handler)

    def unregister(self, handler: CancelHandler | AsyncCancelHandler) -> None:
        """Unregister a cancel handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    async def cancel(
        self,
        reason: CancelReason = CancelReason.USER_BARGE_IN,
        timeout_ms: int | None = None,
    ) -> bool:
        """Propagate CANCEL to all registered handlers.

        Args:
            reason: Reason for cancellation
            timeout_ms: Max time to wait for handlers (default: TMF barge-in contract)

        Returns:
            True if all handlers completed within timeout

        Note:
            All handlers are called concurrently to minimize latency.
            Handlers that don't complete within timeout are abandoned.
        """
        if timeout_ms is None:
            timeout_ms = TMF.BARGE_IN_MS

        clock = get_audio_clock()
        t_event_ms = clock.get_time_ms(self._session_id)

        message = CancelMessage(
            session_id=self._session_id,
            reason=reason,
            t_event_ms=t_event_ms,
        )

        self._last_cancel = message
        self._cancelled = True

        # Call all handlers concurrently
        tasks = []
        for handler in self._handlers:
            if asyncio.iscoroutinefunction(handler):
                tasks.append(asyncio.create_task(handler(message)))
            else:
                # Wrap sync handler
                try:
                    handler(message)
                except Exception:
                    pass

        if not tasks:
            return True

        # Wait for all async handlers with timeout
        try:
            done, pending = await asyncio.wait(
                tasks,
                timeout=timeout_ms / 1000.0,
                return_when=asyncio.ALL_COMPLETED,
            )

            # Cancel any pending tasks
            for task in pending:
                task.cancel()

            return len(pending) == 0

        except asyncio.CancelledError:
            # Cancel all tasks on external cancellation
            for task in tasks:
                task.cancel()
            raise

    def reset(self) -> None:
        """Reset cancellation state for new turn."""
        self._cancelled = False

    @property
    def is_cancelled(self) -> bool:
        """Whether cancellation is in effect."""
        return self._cancelled

    @property
    def last_cancel(self) -> CancelMessage | None:
        """Last CANCEL message sent."""
        return self._last_cancel

    @property
    def session_id(self) -> str:
        """Session ID for this controller."""
        return self._session_id


def create_cancel_handler(
    name: str,
    cancel_fn: Callable,
) -> AsyncCancelHandler:
    """Create a cancel handler wrapper with logging.

    Args:
        name: Component name for logging
        cancel_fn: Actual cancel function to call

    Returns:
        Async handler that logs and calls the cancel function
    """

    async def handler(message: CancelMessage) -> None:
        try:
            if asyncio.iscoroutinefunction(cancel_fn):
                await cancel_fn()
            else:
                cancel_fn()
        except Exception:
            # Log but don't fail cancel propagation
            pass

    return handler
