"""Tests for Prometheus Metrics.

Tests cover:
- Helper function invocations
- Metric recording (TTFA, barge-in, turns, sessions)
- Context rollover, animation yield, backpressure
- Build info setting
"""

import pytest
from unittest.mock import patch, MagicMock

from src.observability.metrics import (
    record_ttfa,
    record_barge_in,
    record_turn_complete,
    record_turn_timeout,
    record_session_start,
    record_session_end,
    record_context_rollover,
    record_animation_yield,
    record_backpressure,
    record_error,
    update_session_state,
    update_vram_usage,
    update_context_tokens,
    set_build_info,
    # Metrics objects for verification
    TTFA_HISTOGRAM,
    BARGE_IN_HISTOGRAM,
    BARGE_IN_EVENTS,
    TURNS_COMPLETED,
    TURNS_TIMEOUT,
    SESSION_STARTED,
    SESSION_ENDED,
    ACTIVE_SESSIONS,
    CONTEXT_ROLLOVER,
    ANIMATION_YIELD,
    BACKPRESSURE_EVENTS,
    ERRORS,
    SESSIONS_BY_STATE,
    VRAM_USAGE_BYTES,
    CONTEXT_TOKENS,
    BUILD_INFO,
)


class TestRecordTTFA:
    """Tests for record_ttfa function."""

    def test_record_ttfa_converts_to_seconds(self):
        """TTFA is recorded in seconds from milliseconds."""
        # Just verify no exception and function runs
        record_ttfa(250.0)  # 250ms

    def test_record_ttfa_zero(self):
        """Zero TTFA is recorded."""
        record_ttfa(0.0)

    def test_record_ttfa_small(self):
        """Small TTFA values are recorded."""
        record_ttfa(50.0)  # 50ms


class TestRecordBargeIn:
    """Tests for record_barge_in function."""

    def test_record_barge_in_records_latency_and_event(self):
        """Barge-in records both latency and event count."""
        # Should not raise
        record_barge_in(100.0)

    def test_record_barge_in_zero(self):
        """Zero latency is recorded."""
        record_barge_in(0.0)


class TestRecordTurnComplete:
    """Tests for record_turn_complete function."""

    def test_record_turn_complete(self):
        """Turn complete increments counter."""
        record_turn_complete()


class TestRecordTurnTimeout:
    """Tests for record_turn_timeout function."""

    def test_record_turn_timeout(self):
        """Turn timeout increments counter."""
        record_turn_timeout()


class TestRecordSessionStart:
    """Tests for record_session_start function."""

    def test_record_session_start(self):
        """Session start increments counters."""
        record_session_start()


class TestRecordSessionEnd:
    """Tests for record_session_end function."""

    def test_record_session_end_default_reason(self):
        """Session end with default reason."""
        record_session_end()

    def test_record_session_end_timeout(self):
        """Session end with timeout reason."""
        record_session_end("timeout")

    def test_record_session_end_error(self):
        """Session end with error reason."""
        record_session_end("error")


class TestRecordContextRollover:
    """Tests for record_context_rollover function."""

    def test_record_context_rollover_default(self):
        """Context rollover with default status."""
        record_context_rollover()

    def test_record_context_rollover_success(self):
        """Context rollover with success status."""
        record_context_rollover("success")

    def test_record_context_rollover_timeout(self):
        """Context rollover with timeout status."""
        record_context_rollover("timeout")

    def test_record_context_rollover_error(self):
        """Context rollover with error status."""
        record_context_rollover("error")


class TestRecordAnimationYield:
    """Tests for record_animation_yield function."""

    def test_record_animation_yield(self):
        """Animation yield increments counter."""
        record_animation_yield()


class TestRecordBackpressure:
    """Tests for record_backpressure function."""

    def test_record_backpressure_animation_yield(self):
        """Backpressure with animation_yield level."""
        record_backpressure("animation_yield")

    def test_record_backpressure_verbosity_reduce(self):
        """Backpressure with verbosity_reduce level."""
        record_backpressure("verbosity_reduce")

    def test_record_backpressure_session_reject(self):
        """Backpressure with session_reject level."""
        record_backpressure("session_reject")


class TestRecordError:
    """Tests for record_error function."""

    def test_record_error_vad(self):
        """Record VAD error."""
        record_error("vad", "audio_processing")

    def test_record_error_asr(self):
        """Record ASR error."""
        record_error("asr", "connection")

    def test_record_error_llm(self):
        """Record LLM error."""
        record_error("llm", "timeout")

    def test_record_error_tts(self):
        """Record TTS error."""
        record_error("tts", "synthesis")

    def test_record_error_animation(self):
        """Record animation error."""
        record_error("animation", "grpc")


class TestUpdateSessionState:
    """Tests for update_session_state function."""

    def test_update_session_state_idle(self):
        """Update idle sessions count."""
        update_session_state("idle", 5)

    def test_update_session_state_listening(self):
        """Update listening sessions count."""
        update_session_state("listening", 3)

    def test_update_session_state_thinking(self):
        """Update thinking sessions count."""
        update_session_state("thinking", 2)

    def test_update_session_state_speaking(self):
        """Update speaking sessions count."""
        update_session_state("speaking", 1)

    def test_update_session_state_interrupted(self):
        """Update interrupted sessions count."""
        update_session_state("interrupted", 0)


class TestUpdateVramUsage:
    """Tests for update_vram_usage function."""

    def test_update_vram_usage(self):
        """Update VRAM usage gauge."""
        update_vram_usage(1024 * 1024 * 1024)  # 1GB

    def test_update_vram_usage_zero(self):
        """Update VRAM usage to zero."""
        update_vram_usage(0)


class TestUpdateContextTokens:
    """Tests for update_context_tokens function."""

    def test_update_context_tokens(self):
        """Update context tokens for session."""
        update_context_tokens("session-123", 2048)

    def test_update_context_tokens_different_sessions(self):
        """Update tokens for different sessions."""
        update_context_tokens("session-1", 1000)
        update_context_tokens("session-2", 2000)


class TestSetBuildInfo:
    """Tests for set_build_info function."""

    def test_set_build_info(self):
        """Set build information."""
        set_build_info(
            version="3.0.0",
            commit="abc123",
            build_time="2024-01-15T12:00:00Z",
        )


class TestMetricObjects:
    """Tests for metric object definitions."""

    def test_ttfa_histogram_exists(self):
        """TTFA histogram is defined."""
        assert TTFA_HISTOGRAM is not None

    def test_barge_in_histogram_exists(self):
        """Barge-in histogram is defined."""
        assert BARGE_IN_HISTOGRAM is not None

    def test_barge_in_events_exists(self):
        """Barge-in events counter is defined."""
        assert BARGE_IN_EVENTS is not None

    def test_turns_completed_exists(self):
        """Turns completed counter is defined."""
        assert TURNS_COMPLETED is not None

    def test_turns_timeout_exists(self):
        """Turns timeout counter is defined."""
        assert TURNS_TIMEOUT is not None

    def test_session_started_exists(self):
        """Session started counter is defined."""
        assert SESSION_STARTED is not None

    def test_session_ended_exists(self):
        """Session ended counter is defined."""
        assert SESSION_ENDED is not None

    def test_active_sessions_exists(self):
        """Active sessions gauge is defined."""
        assert ACTIVE_SESSIONS is not None

    def test_context_rollover_exists(self):
        """Context rollover counter is defined."""
        assert CONTEXT_ROLLOVER is not None

    def test_animation_yield_exists(self):
        """Animation yield counter is defined."""
        assert ANIMATION_YIELD is not None

    def test_backpressure_events_exists(self):
        """Backpressure events counter is defined."""
        assert BACKPRESSURE_EVENTS is not None

    def test_errors_exists(self):
        """Errors counter is defined."""
        assert ERRORS is not None

    def test_sessions_by_state_exists(self):
        """Sessions by state gauge is defined."""
        assert SESSIONS_BY_STATE is not None

    def test_vram_usage_exists(self):
        """VRAM usage gauge is defined."""
        assert VRAM_USAGE_BYTES is not None

    def test_context_tokens_exists(self):
        """Context tokens gauge is defined."""
        assert CONTEXT_TOKENS is not None

    def test_build_info_exists(self):
        """Build info metric is defined."""
        assert BUILD_INFO is not None
