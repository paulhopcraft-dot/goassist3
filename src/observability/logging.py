"""Structured Logging - JSON logs with correlation.

Provides structured logging for:
- Session events (start, end, state changes)
- CANCEL propagation
- Context rollover
- Animation yield
- Error tracking

All logs include session_id for correlation.
Reference: Ops-Runbook-v3.0.md §3.2
"""

import logging
import sys
from typing import Any

import structlog


def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """Configure structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: If True, output JSON; else human-readable
    """
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a structured logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Bound structlog logger
    """
    return structlog.get_logger(name)


def bind_session(session_id: str) -> None:
    """Bind session_id to all logs in current context.

    Args:
        session_id: Session identifier
    """
    structlog.contextvars.bind_contextvars(session_id=session_id)


def unbind_session() -> None:
    """Remove session_id from log context."""
    structlog.contextvars.unbind_contextvars("session_id")


# -----------------------------------------------------------------------------
# Event-specific logging functions
# -----------------------------------------------------------------------------


class SessionLogger:
    """Logger for session-related events."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._log = get_logger("session").bind(session_id=session_id)

    def session_started(self, metadata: dict[str, Any] | None = None) -> None:
        """Log session start."""
        self._log.info(
            "session_started",
            event_type="session.started",
            **(metadata or {}),
        )

    def session_ended(self, reason: str, duration_s: float) -> None:
        """Log session end."""
        self._log.info(
            "session_ended",
            event_type="session.ended",
            reason=reason,
            duration_s=duration_s,
        )

    def state_change(
        self,
        old_state: str,
        new_state: str,
        reason: str,
        t_ms: int,
    ) -> None:
        """Log state transition."""
        self._log.info(
            "state_change",
            event_type="session.state_change",
            old_state=old_state,
            new_state=new_state,
            reason=reason,
            t_ms=t_ms,
        )

    def turn_started(self, turn_id: int) -> None:
        """Log turn start."""
        self._log.debug(
            "turn_started",
            event_type="turn.started",
            turn_id=turn_id,
        )

    def turn_completed(
        self,
        turn_id: int,
        ttfa_ms: float,
        total_ms: float,
    ) -> None:
        """Log turn completion with metrics."""
        self._log.info(
            "turn_completed",
            event_type="turn.completed",
            turn_id=turn_id,
            ttfa_ms=ttfa_ms,
            total_ms=total_ms,
        )

    def turn_timeout(self, turn_id: int, latency_ms: float) -> None:
        """Log turn timeout (>500ms)."""
        self._log.warning(
            "turn_timeout",
            event_type="turn.timeout",
            turn_id=turn_id,
            latency_ms=latency_ms,
        )


class CancelLogger:
    """Logger for CANCEL control-plane events."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._log = get_logger("cancel").bind(session_id=session_id)

    def cancel_initiated(self, reason: str, t_event_ms: int) -> None:
        """Log CANCEL initiation."""
        self._log.info(
            "cancel_initiated",
            event_type="cancel.initiated",
            reason=reason,
            t_event_ms=t_event_ms,
        )

    def cancel_propagated(
        self,
        handlers_count: int,
        completed_count: int,
        elapsed_ms: float,
    ) -> None:
        """Log CANCEL propagation completion."""
        self._log.info(
            "cancel_propagated",
            event_type="cancel.propagated",
            handlers_count=handlers_count,
            completed_count=completed_count,
            elapsed_ms=elapsed_ms,
        )

    def cancel_timeout(
        self,
        pending_handlers: int,
        elapsed_ms: float,
    ) -> None:
        """Log CANCEL propagation timeout."""
        self._log.warning(
            "cancel_timeout",
            event_type="cancel.timeout",
            pending_handlers=pending_handlers,
            elapsed_ms=elapsed_ms,
        )


class ContextLogger:
    """Logger for context management events."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._log = get_logger("context").bind(session_id=session_id)

    def rollover_triggered(
        self,
        token_count: int,
        threshold: int,
    ) -> None:
        """Log context rollover trigger."""
        self._log.info(
            "rollover_triggered",
            event_type="context.rollover_triggered",
            token_count=token_count,
            threshold=threshold,
        )

    def rollover_completed(
        self,
        evicted_tokens: int,
        summary_tokens: int,
        elapsed_ms: float,
    ) -> None:
        """Log successful rollover."""
        self._log.info(
            "rollover_completed",
            event_type="context.rollover_completed",
            evicted_tokens=evicted_tokens,
            summary_tokens=summary_tokens,
            elapsed_ms=elapsed_ms,
        )

    def rollover_failed(self, error: str, elapsed_ms: float) -> None:
        """Log rollover failure."""
        self._log.error(
            "rollover_failed",
            event_type="context.rollover_failed",
            error=error,
            elapsed_ms=elapsed_ms,
        )


class AnimationLogger:
    """Logger for animation/avatar events."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._log = get_logger("animation").bind(session_id=session_id)

    def yield_triggered(self, lag_ms: float) -> None:
        """Log animation yield due to lag."""
        self._log.warning(
            "animation_yield",
            event_type="animation.yield",
            lag_ms=lag_ms,
        )

    def heartbeat_sent(self, t_audio_ms: int) -> None:
        """Log heartbeat frame sent."""
        self._log.debug(
            "heartbeat_sent",
            event_type="animation.heartbeat",
            t_audio_ms=t_audio_ms,
        )

    def slow_freeze_started(self, t_audio_ms: int) -> None:
        """Log slow-freeze animation started."""
        self._log.info(
            "slow_freeze_started",
            event_type="animation.slow_freeze",
            t_audio_ms=t_audio_ms,
        )


class BackpressureLogger:
    """Logger for backpressure events."""

    def __init__(self, session_id: str | None = None) -> None:
        self._log = get_logger("backpressure")
        if session_id:
            self._log = self._log.bind(session_id=session_id)

    def level_activated(
        self,
        level: str,
        trigger: str,
    ) -> None:
        """Log backpressure level activation."""
        self._log.warning(
            "backpressure_activated",
            event_type="backpressure.activated",
            level=level,
            trigger=trigger,
        )

    def session_queued(self, queue_depth: int) -> None:
        """Log session queued due to backpressure."""
        self._log.warning(
            "session_queued",
            event_type="backpressure.session_queued",
            queue_depth=queue_depth,
        )

    def session_rejected(self, reason: str) -> None:
        """Log session rejected due to overload."""
        self._log.error(
            "session_rejected",
            event_type="backpressure.session_rejected",
            reason=reason,
        )


# Initialize default logging configuration
def init_logging(json_format: bool = True, level: str = "INFO") -> None:
    """Initialize logging with defaults.

    Call this once at application startup.
    """
    configure_logging(level=level, json_format=json_format)
