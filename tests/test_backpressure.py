"""Tests for Backpressure Policy.

Tests the graceful degradation system.
Reference: TMF v3.0 §5.2, Implementation §5.3
"""

import pytest

from src.llm.backpressure import (
    BackpressureLevel,
    BackpressureState,
    BackpressureController,
    SystemMetrics,
    THRESHOLDS,
    create_backpressure_controller,
)
from src.config.constants import TMF


class TestBackpressureLevel:
    """Tests for BackpressureLevel enum."""

    def test_levels_in_order(self):
        """Levels are in correct severity order."""
        assert BackpressureLevel.NORMAL < BackpressureLevel.ANIMATION_YIELD
        assert BackpressureLevel.ANIMATION_YIELD < BackpressureLevel.VERBOSITY_REDUCE
        assert BackpressureLevel.VERBOSITY_REDUCE < BackpressureLevel.TOOL_REFUSE
        assert BackpressureLevel.TOOL_REFUSE < BackpressureLevel.SESSION_QUEUE
        assert BackpressureLevel.SESSION_QUEUE < BackpressureLevel.SESSION_REJECT

    def test_level_values(self):
        """Level integer values are correct."""
        assert BackpressureLevel.NORMAL == 0
        assert BackpressureLevel.ANIMATION_YIELD == 1
        assert BackpressureLevel.VERBOSITY_REDUCE == 2
        assert BackpressureLevel.TOOL_REFUSE == 3
        assert BackpressureLevel.SESSION_QUEUE == 4
        assert BackpressureLevel.SESSION_REJECT == 5


class TestBackpressureState:
    """Tests for BackpressureState dataclass."""

    def test_default_state(self):
        """Default state is normal with no degradation."""
        state = BackpressureState()
        assert state.level == BackpressureLevel.NORMAL
        assert not state.animation_yield_active
        assert state.verbosity_factor == 1.0
        assert state.max_tokens_override is None
        assert not state.tools_disabled
        assert state.queue_depth == 0
        assert not state.rejecting_sessions

    def test_is_degraded_normal(self):
        """is_degraded is False for NORMAL level."""
        state = BackpressureState(level=BackpressureLevel.NORMAL)
        assert not state.is_degraded

    def test_is_degraded_animation(self):
        """is_degraded is True for any non-NORMAL level."""
        state = BackpressureState(level=BackpressureLevel.ANIMATION_YIELD)
        assert state.is_degraded

    def test_custom_state(self):
        """Custom state values are applied."""
        state = BackpressureState(
            level=BackpressureLevel.VERBOSITY_REDUCE,
            animation_yield_active=True,
            verbosity_factor=0.7,
            max_tokens_override=384,
        )
        assert state.level == BackpressureLevel.VERBOSITY_REDUCE
        assert state.animation_yield_active
        assert state.verbosity_factor == 0.7
        assert state.max_tokens_override == 384


class TestSystemMetrics:
    """Tests for SystemMetrics dataclass."""

    def test_default_metrics(self):
        """Default metrics are zero."""
        metrics = SystemMetrics()
        assert metrics.vram_usage_pct == 0.0
        assert metrics.cpu_usage_pct == 0.0
        assert metrics.active_sessions == 0
        assert metrics.queue_depth == 0
        assert metrics.avg_ttfa_ms == 0.0
        assert metrics.animation_lag_ms == 0.0
        assert metrics.error_rate_pct == 0.0

    def test_custom_metrics(self):
        """Custom metrics are applied."""
        metrics = SystemMetrics(
            vram_usage_pct=85.0,
            avg_ttfa_ms=200.0,
            animation_lag_ms=130.0,
        )
        assert metrics.vram_usage_pct == 85.0
        assert metrics.avg_ttfa_ms == 200.0
        assert metrics.animation_lag_ms == 130.0


class TestThresholds:
    """Tests for backpressure thresholds."""

    def test_animation_yield_thresholds(self):
        """Animation yield has correct thresholds."""
        thresholds = THRESHOLDS[BackpressureLevel.ANIMATION_YIELD]
        assert thresholds["animation_lag_ms"] == 120  # TMF §4.3
        assert thresholds["vram_usage_pct"] == 85

    def test_verbosity_reduce_thresholds(self):
        """Verbosity reduce has correct thresholds."""
        thresholds = THRESHOLDS[BackpressureLevel.VERBOSITY_REDUCE]
        assert thresholds["avg_ttfa_ms"] == 200  # 80% of 250ms
        assert thresholds["vram_usage_pct"] == 90

    def test_session_reject_thresholds(self):
        """Session reject has correct thresholds."""
        thresholds = THRESHOLDS[BackpressureLevel.SESSION_REJECT]
        assert thresholds["avg_ttfa_ms"] == 250  # At contract limit
        assert thresholds["vram_usage_pct"] == 98
        assert thresholds["error_rate_pct"] == 5


class TestBackpressureController:
    """Tests for BackpressureController."""

    @pytest.fixture
    def controller(self):
        """Create a controller."""
        return BackpressureController(session_id="test-session")

    def test_init(self, controller):
        """Controller initializes with normal state."""
        assert controller.level == BackpressureLevel.NORMAL
        assert controller.state.level == BackpressureLevel.NORMAL
        assert not controller.state.is_degraded

    def test_update_metrics_normal(self, controller):
        """Normal metrics keep NORMAL level."""
        metrics = SystemMetrics(
            vram_usage_pct=50.0,
            avg_ttfa_ms=100.0,
            animation_lag_ms=50.0,
        )
        level = controller.update_metrics(metrics)
        assert level == BackpressureLevel.NORMAL

    def test_update_metrics_animation_yield(self, controller):
        """High animation lag triggers ANIMATION_YIELD."""
        metrics = SystemMetrics(animation_lag_ms=130.0)
        level = controller.update_metrics(metrics)
        assert level == BackpressureLevel.ANIMATION_YIELD
        assert controller.state.animation_yield_active

    def test_update_metrics_verbosity_reduce(self, controller):
        """High TTFA triggers VERBOSITY_REDUCE."""
        metrics = SystemMetrics(avg_ttfa_ms=210.0)
        level = controller.update_metrics(metrics)
        assert level == BackpressureLevel.VERBOSITY_REDUCE
        assert controller.state.verbosity_factor == 0.7
        assert controller.state.max_tokens_override == 384

    def test_update_metrics_tool_refuse(self, controller):
        """Very high TTFA triggers TOOL_REFUSE."""
        metrics = SystemMetrics(avg_ttfa_ms=230.0)
        level = controller.update_metrics(metrics)
        assert level == BackpressureLevel.TOOL_REFUSE
        assert controller.state.tools_disabled
        assert controller.state.verbosity_factor == 0.5
        assert controller.state.max_tokens_override == 256

    def test_update_metrics_session_reject(self, controller):
        """Critical metrics trigger SESSION_REJECT."""
        metrics = SystemMetrics(
            avg_ttfa_ms=260.0,
            vram_usage_pct=99.0,
        )
        level = controller.update_metrics(metrics)
        assert level == BackpressureLevel.SESSION_REJECT
        assert controller.state.rejecting_sessions

    def test_get_max_tokens_normal(self, controller):
        """Normal level returns default max tokens."""
        assert controller.get_max_tokens() == 512

    def test_get_max_tokens_reduced(self, controller):
        """Reduced level returns lower max tokens."""
        metrics = SystemMetrics(avg_ttfa_ms=210.0)
        controller.update_metrics(metrics)
        assert controller.get_max_tokens() == 384

    def test_should_allow_tool_call_normal(self, controller):
        """Normal level allows all tools."""
        assert controller.should_allow_tool_call("any_tool")
        assert controller.should_allow_tool_call("search")

    def test_should_allow_tool_call_disabled(self, controller):
        """Tool refuse level blocks non-essential tools."""
        metrics = SystemMetrics(avg_ttfa_ms=230.0)
        controller.update_metrics(metrics)

        assert not controller.should_allow_tool_call("search")
        assert not controller.should_allow_tool_call("web_request")

    def test_should_allow_tool_call_essential(self, controller):
        """Essential tools always allowed."""
        metrics = SystemMetrics(avg_ttfa_ms=230.0)
        controller.update_metrics(metrics)

        assert controller.should_allow_tool_call("cancel")
        assert controller.should_allow_tool_call("end_session")
        assert controller.should_allow_tool_call("emergency_stop")

    def test_should_allow_new_session_normal(self, controller):
        """Normal level allows new sessions."""
        assert controller.should_allow_new_session()

    def test_should_allow_new_session_reject(self, controller):
        """Session reject level blocks new sessions."""
        metrics = SystemMetrics(avg_ttfa_ms=260.0)
        controller.update_metrics(metrics)
        assert not controller.should_allow_new_session()

    def test_get_queue_position_normal(self, controller):
        """Normal level doesn't queue."""
        assert controller.get_queue_position() is None

    def test_get_queue_position_queuing(self, controller):
        """Queue level returns position."""
        metrics = SystemMetrics(avg_ttfa_ms=245.0)
        controller.update_metrics(metrics)

        pos1 = controller.get_queue_position()
        pos2 = controller.get_queue_position()

        assert pos1 == 1
        assert pos2 == 2

    def test_on_level_change_callback(self, controller):
        """Level change triggers callback."""
        received_levels = []

        def callback(level):
            received_levels.append(level)

        controller.on_level_change(callback)
        controller.update_metrics(SystemMetrics(animation_lag_ms=130.0))

        assert len(received_levels) == 1
        assert received_levels[0] == BackpressureLevel.ANIMATION_YIELD

    def test_reset(self, controller):
        """Reset returns to normal state."""
        metrics = SystemMetrics(avg_ttfa_ms=260.0)
        controller.update_metrics(metrics)
        assert controller.level == BackpressureLevel.SESSION_REJECT

        controller.reset()

        assert controller.level == BackpressureLevel.NORMAL
        assert not controller.state.is_degraded

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, controller):
        """Can start and stop monitoring."""
        await controller.start_monitoring()
        assert controller._running

        await controller.stop_monitoring()
        assert not controller._running


class TestCreateBackpressureController:
    """Tests for factory function."""

    def test_creates_controller(self):
        """Factory creates controller."""
        controller = create_backpressure_controller()
        assert isinstance(controller, BackpressureController)
        assert controller.level == BackpressureLevel.NORMAL

    def test_with_session_id(self):
        """Factory accepts session ID."""
        controller = create_backpressure_controller(session_id="test-123")
        assert controller._session_id == "test-123"


class TestDegradationOrder:
    """Tests for correct degradation order per TMF spec."""

    @pytest.fixture
    def controller(self):
        return BackpressureController()

    def test_animation_degrades_first(self, controller):
        """Animation is first to degrade."""
        # Just above animation threshold
        controller.update_metrics(SystemMetrics(animation_lag_ms=125))

        assert controller.state.animation_yield_active
        assert controller.state.verbosity_factor == 1.0  # Not reduced yet
        assert not controller.state.tools_disabled

    def test_verbosity_after_animation(self, controller):
        """Verbosity reduces after animation."""
        # Above verbosity threshold
        controller.update_metrics(SystemMetrics(avg_ttfa_ms=205))

        assert controller.state.animation_yield_active  # Still active
        assert controller.state.verbosity_factor < 1.0  # Reduced
        assert not controller.state.tools_disabled

    def test_tools_after_verbosity(self, controller):
        """Tools disable after verbosity."""
        # Above tool threshold
        controller.update_metrics(SystemMetrics(avg_ttfa_ms=230))

        assert controller.state.animation_yield_active
        assert controller.state.verbosity_factor < 1.0
        assert controller.state.tools_disabled

    def test_audio_never_degrades(self, controller):
        """Audio continuity always wins - no audio degradation field."""
        # Even at max backpressure
        controller.update_metrics(SystemMetrics(
            avg_ttfa_ms=300,
            vram_usage_pct=100,
            error_rate_pct=10,
        ))

        # BackpressureState has no audio_disabled field
        # This is by design - audio is never degraded
        assert not hasattr(controller.state, 'audio_disabled')


class TestBackpressureControllerCallbackErrors:
    """Tests for callback error handling."""

    @pytest.fixture
    def controller(self):
        return BackpressureController(session_id="callback-test")

    def test_callback_error_does_not_break_controller(self, controller):
        """Callback errors don't break the controller."""
        errors_caught = []

        def failing_callback(level):
            errors_caught.append(True)
            raise ValueError("Callback error")

        def working_callback(level):
            errors_caught.append(level)

        controller.on_level_change(failing_callback)
        controller.on_level_change(working_callback)

        # Should not raise
        controller.update_metrics(SystemMetrics(animation_lag_ms=130.0))

        # Both callbacks were called
        assert len(errors_caught) == 2
        assert errors_caught[0] is True  # Failing callback ran
        assert errors_caught[1] == BackpressureLevel.ANIMATION_YIELD

    def test_callback_error_logged(self, controller):
        """Callback errors are logged."""
        def failing_callback(level):
            raise RuntimeError("Test error")

        controller.on_level_change(failing_callback)

        # Should not raise - error is caught and logged
        controller.update_metrics(SystemMetrics(animation_lag_ms=130.0))
        assert controller.level == BackpressureLevel.ANIMATION_YIELD


class TestBackpressureControllerTriggerReasons:
    """Tests for trigger reason generation."""

    @pytest.fixture
    def controller(self):
        return BackpressureController(session_id="trigger-test")

    def test_trigger_reason_animation_lag(self, controller):
        """Animation lag reason is reported."""
        controller.update_metrics(SystemMetrics(animation_lag_ms=130.0))
        reason = controller._get_trigger_reason()
        assert "animation_lag" in reason

    def test_trigger_reason_vram(self, controller):
        """VRAM reason is reported."""
        controller.update_metrics(SystemMetrics(vram_usage_pct=90.0))
        reason = controller._get_trigger_reason()
        assert "vram" in reason

    def test_trigger_reason_ttfa(self, controller):
        """TTFA reason is reported."""
        controller.update_metrics(SystemMetrics(avg_ttfa_ms=210.0))
        reason = controller._get_trigger_reason()
        assert "ttfa" in reason

    def test_trigger_reason_sessions(self, controller):
        """Sessions reason is reported when at limit."""
        controller.update_metrics(SystemMetrics(
            active_sessions=TMF.MAX_CONCURRENT_SESSIONS - 1,
            avg_ttfa_ms=210.0,
        ))
        reason = controller._get_trigger_reason()
        assert "sessions" in reason

    def test_trigger_reason_default(self, controller):
        """Default reason when no specific trigger."""
        controller._metrics = SystemMetrics()  # All zeros
        reason = controller._get_trigger_reason()
        assert reason == "threshold_exceeded"


class TestBackpressureControllerMonitoring:
    """Tests for monitoring behavior."""

    @pytest.fixture
    def controller(self):
        return BackpressureController(
            session_id="monitor-test",
            check_interval_s=0.01,  # Fast for testing
        )

    @pytest.mark.asyncio
    async def test_double_start_is_noop(self, controller):
        """Starting monitoring twice is a no-op."""
        await controller.start_monitoring()
        task1 = controller._monitor_task

        await controller.start_monitoring()  # Second start
        task2 = controller._monitor_task

        # Same task
        assert task1 is task2
        assert controller._running

        await controller.stop_monitoring()

    @pytest.mark.asyncio
    async def test_stop_without_start(self, controller):
        """Stopping without starting doesn't raise."""
        # Should not raise
        await controller.stop_monitoring()
        assert not controller._running

    @pytest.mark.asyncio
    async def test_monitor_loop_runs(self, controller):
        """Monitor loop evaluates level periodically."""
        import asyncio

        evaluations = []
        original_evaluate = controller._evaluate_level

        def tracking_evaluate():
            evaluations.append(True)
            return original_evaluate()

        controller._evaluate_level = tracking_evaluate

        await controller.start_monitoring()
        await asyncio.sleep(0.05)  # Let it run a few iterations
        await controller.stop_monitoring()

        assert len(evaluations) >= 1

    @pytest.mark.asyncio
    async def test_monitor_loop_handles_exceptions(self, controller):
        """Monitor loop handles exceptions without crashing."""
        import asyncio

        call_count = [0]
        original_evaluate = controller._evaluate_level

        def failing_evaluate():
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Simulated error")
            return original_evaluate()

        controller._evaluate_level = failing_evaluate

        await controller.start_monitoring()
        await asyncio.sleep(0.05)  # Let it run through the error
        await controller.stop_monitoring()

        # Should have recovered and continued
        assert call_count[0] >= 2
