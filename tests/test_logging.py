"""Tests for Structured Logging.

Tests cover:
- configure_logging with JSON and console formats
- get_logger function
- bind_session and unbind_session
- SessionLogger events
- CancelLogger events
- ContextLogger events
- AnimationLogger events
- BackpressureLogger events
- init_logging function
"""

import pytest
from unittest.mock import patch, MagicMock

import structlog

from src.observability.logging import (
    configure_logging,
    get_logger,
    bind_session,
    unbind_session,
    SessionLogger,
    CancelLogger,
    ContextLogger,
    AnimationLogger,
    BackpressureLogger,
    init_logging,
)


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_json_format(self):
        """Configure logging with JSON format."""
        # Should not raise
        configure_logging(level="INFO", json_format=True)

    def test_configure_console_format(self):
        """Configure logging with console format."""
        # Should not raise
        configure_logging(level="DEBUG", json_format=False)

    def test_configure_different_levels(self):
        """Configure logging with different levels."""
        configure_logging(level="WARNING")
        configure_logging(level="ERROR")
        configure_logging(level="DEBUG")


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_with_name(self):
        """Get logger with specific name."""
        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_without_name(self):
        """Get logger without name."""
        logger = get_logger()
        assert logger is not None

    def test_get_logger_returns_bound_logger(self):
        """get_logger returns BoundLogger."""
        logger = get_logger("test")
        # Should be a bound logger (has bind method)
        assert hasattr(logger, "bind")


class TestBindSession:
    """Tests for bind_session and unbind_session."""

    def test_bind_session(self):
        """Bind session to context."""
        # Should not raise
        bind_session("test-session-123")

    def test_unbind_session(self):
        """Unbind session from context."""
        bind_session("test-session")
        # Should not raise
        unbind_session()

    def test_bind_unbind_cycle(self):
        """Bind and unbind in sequence."""
        bind_session("session-1")
        unbind_session()
        bind_session("session-2")
        unbind_session()


class TestSessionLogger:
    """Tests for SessionLogger class."""

    @pytest.fixture
    def logger(self):
        """Create session logger."""
        return SessionLogger("test-session")

    def test_init(self, logger):
        """Initialize session logger."""
        assert logger._session_id == "test-session"
        assert logger._log is not None

    def test_session_started_no_metadata(self, logger):
        """Log session started without metadata."""
        logger.session_started()

    def test_session_started_with_metadata(self, logger):
        """Log session started with metadata."""
        logger.session_started({"user_id": "user-123", "client": "web"})

    def test_session_ended(self, logger):
        """Log session ended."""
        logger.session_ended(reason="normal", duration_s=120.5)

    def test_state_change(self, logger):
        """Log state change."""
        logger.state_change(
            old_state="idle",
            new_state="listening",
            reason="user_spoke",
            t_ms=1000,
        )

    def test_turn_started(self, logger):
        """Log turn started."""
        logger.turn_started(turn_id=1)

    def test_turn_completed(self, logger):
        """Log turn completed."""
        logger.turn_completed(
            turn_id=1,
            ttfa_ms=150.0,
            total_ms=2500.0,
        )

    def test_turn_timeout(self, logger):
        """Log turn timeout."""
        logger.turn_timeout(turn_id=2, latency_ms=550.0)


class TestCancelLogger:
    """Tests for CancelLogger class."""

    @pytest.fixture
    def logger(self):
        """Create cancel logger."""
        return CancelLogger("test-session")

    def test_init(self, logger):
        """Initialize cancel logger."""
        assert logger._session_id == "test-session"
        assert logger._log is not None

    def test_cancel_initiated(self, logger):
        """Log cancel initiation."""
        logger.cancel_initiated(reason="barge_in", t_event_ms=1500)

    def test_cancel_propagated(self, logger):
        """Log cancel propagation."""
        logger.cancel_propagated(
            handlers_count=5,
            completed_count=5,
            elapsed_ms=45.0,
        )

    def test_cancel_timeout(self, logger):
        """Log cancel timeout."""
        logger.cancel_timeout(pending_handlers=2, elapsed_ms=155.0)


class TestContextLogger:
    """Tests for ContextLogger class."""

    @pytest.fixture
    def logger(self):
        """Create context logger."""
        return ContextLogger("test-session")

    def test_init(self, logger):
        """Initialize context logger."""
        assert logger._session_id == "test-session"
        assert logger._log is not None

    def test_rollover_triggered(self, logger):
        """Log rollover triggered."""
        logger.rollover_triggered(token_count=3500, threshold=3000)

    def test_rollover_completed(self, logger):
        """Log rollover completed."""
        logger.rollover_completed(
            evicted_tokens=2000,
            summary_tokens=500,
            elapsed_ms=120.0,
        )

    def test_rollover_failed(self, logger):
        """Log rollover failed."""
        logger.rollover_failed(error="LLM timeout", elapsed_ms=5000.0)


class TestAnimationLogger:
    """Tests for AnimationLogger class."""

    @pytest.fixture
    def logger(self):
        """Create animation logger."""
        return AnimationLogger("test-session")

    def test_init(self, logger):
        """Initialize animation logger."""
        assert logger._session_id == "test-session"
        assert logger._log is not None

    def test_yield_triggered(self, logger):
        """Log animation yield triggered."""
        logger.yield_triggered(lag_ms=50.0)

    def test_heartbeat_sent(self, logger):
        """Log heartbeat sent."""
        logger.heartbeat_sent(t_audio_ms=2500)

    def test_slow_freeze_started(self, logger):
        """Log slow freeze started."""
        logger.slow_freeze_started(t_audio_ms=3000)


class TestBackpressureLogger:
    """Tests for BackpressureLogger class."""

    def test_init_without_session(self):
        """Initialize without session ID."""
        logger = BackpressureLogger()
        assert logger._log is not None

    def test_init_with_session(self):
        """Initialize with session ID."""
        logger = BackpressureLogger("test-session")
        assert logger._log is not None

    def test_level_activated(self):
        """Log backpressure level activated."""
        logger = BackpressureLogger("test-session")
        logger.level_activated(level="animation_yield", trigger="high_lag")

    def test_session_queued(self):
        """Log session queued."""
        logger = BackpressureLogger()
        logger.session_queued(queue_depth=5)

    def test_session_rejected(self):
        """Log session rejected."""
        logger = BackpressureLogger()
        logger.session_rejected(reason="max_sessions_reached")


class TestInitLogging:
    """Tests for init_logging function."""

    def test_init_logging_default(self):
        """Initialize logging with defaults."""
        # Should not raise
        init_logging()

    def test_init_logging_json_false(self):
        """Initialize logging with console format."""
        init_logging(json_format=False)

    def test_init_logging_different_level(self):
        """Initialize logging with different level."""
        init_logging(level="DEBUG")
        init_logging(level="WARNING")


class TestLoggerMethods:
    """Tests for logger method behavior."""

    def test_session_logger_multiple_events(self):
        """Log multiple events in sequence."""
        logger = SessionLogger("multi-event-session")
        logger.session_started()
        logger.turn_started(1)
        logger.state_change("idle", "listening", "user_spoke", 100)
        logger.turn_completed(1, 150.0, 2000.0)
        logger.session_ended("normal", 60.0)

    def test_cancel_logger_full_sequence(self):
        """Log full cancel sequence."""
        logger = CancelLogger("cancel-session")
        logger.cancel_initiated("barge_in", 1000)
        logger.cancel_propagated(4, 4, 50.0)

    def test_context_logger_rollover_flow(self):
        """Log rollover flow."""
        logger = ContextLogger("rollover-session")
        logger.rollover_triggered(4000, 3500)
        logger.rollover_completed(2500, 400, 150.0)

    def test_animation_logger_sequence(self):
        """Log animation events in sequence."""
        logger = AnimationLogger("animation-session")
        logger.heartbeat_sent(1000)
        logger.yield_triggered(60.0)
        logger.slow_freeze_started(2000)

    def test_backpressure_logger_escalation(self):
        """Log backpressure escalation."""
        logger = BackpressureLogger("bp-session")
        logger.level_activated("animation_yield", "lag_detected")
        logger.level_activated("verbosity_reduce", "sustained_lag")
        logger.session_queued(3)
        logger.session_rejected("overloaded")
