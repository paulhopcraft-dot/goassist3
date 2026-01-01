"""Tests for Animation Yield Controller.

Tests cover:
- YieldState dataclass
- YieldController initialization
- should_yield behavior
- Yield pose interpolation
- Slow-freeze behavior
- Callbacks
- Factory function
"""

import pytest
from unittest.mock import MagicMock, patch

from src.animation.yield_controller import (
    YieldState,
    YieldController,
    create_yield_controller,
)
from src.audio.transport.audio_clock import get_audio_clock


class TestYieldState:
    """Tests for YieldState dataclass."""

    def test_default_values(self):
        """Default state values."""
        state = YieldState()
        assert state.is_yielding is False
        assert state.yield_start_ms == 0
        assert state.frames_skipped == 0
        assert state.in_slow_freeze is False
        assert state.freeze_progress == 0.0
        assert state.last_valid_frame is None

    def test_custom_values(self):
        """Custom state values."""
        state = YieldState(
            is_yielding=True,
            yield_start_ms=1000,
            frames_skipped=5,
            in_slow_freeze=True,
            freeze_progress=0.5,
            last_valid_frame={"blendshapes": {}, "t_ms": 100},
        )
        assert state.is_yielding is True
        assert state.yield_start_ms == 1000
        assert state.frames_skipped == 5
        assert state.in_slow_freeze is True
        assert state.freeze_progress == 0.5


class TestYieldController:
    """Tests for YieldController initialization."""

    @pytest.fixture(autouse=True)
    def setup_clock(self):
        """Setup audio clock."""
        clock = get_audio_clock()
        clock.start_session("yield-test")
        yield
        try:
            clock.end_session("yield-test")
        except KeyError:
            pass

    def test_init_default(self):
        """Initialize with defaults."""
        controller = YieldController(session_id="yield-test")
        assert controller._session_id == "yield-test"
        assert controller._yield_threshold_ms == 120  # TMF default
        assert controller._state.is_yielding is False

    def test_init_custom_thresholds(self):
        """Initialize with custom thresholds."""
        controller = YieldController(
            session_id="yield-test",
            yield_threshold_ms=100,
            freeze_trigger_ms=80,
            freeze_duration_ms=200,
        )
        assert controller._yield_threshold_ms == 100
        assert controller._freeze_trigger_ms == 80
        assert controller._freeze_duration_ms == 200


class TestYieldControllerShouldYield:
    """Tests for should_yield behavior."""

    @pytest.fixture(autouse=True)
    def setup_clock(self):
        """Setup audio clock."""
        clock = get_audio_clock()
        clock.start_session("should-yield-test")
        yield
        try:
            clock.end_session("should-yield-test")
        except KeyError:
            pass

    def test_no_yield_below_threshold(self):
        """No yield when lag below threshold."""
        controller = YieldController(
            session_id="should-yield-test",
            yield_threshold_ms=120,
        )

        result = controller.should_yield(50)

        assert result is False
        assert controller.is_yielding is False

    def test_yield_above_threshold(self):
        """Yield when lag above threshold."""
        controller = YieldController(
            session_id="should-yield-test",
            yield_threshold_ms=120,
        )

        result = controller.should_yield(150)

        assert result is True
        assert controller.is_yielding is True

    def test_yield_ends_when_lag_drops(self):
        """Yield ends when lag drops below threshold."""
        controller = YieldController(
            session_id="should-yield-test",
            yield_threshold_ms=120,
        )

        controller.should_yield(150)  # Start yielding
        assert controller.is_yielding is True

        controller.should_yield(50)  # Lag drops
        assert controller.is_yielding is False


class TestYieldControllerRecordFrame:
    """Tests for record_frame method."""

    def test_record_frame(self):
        """Record frame stores last valid frame."""
        controller = YieldController(session_id="record-test")

        blendshapes = {"jawOpen": 0.5, "mouthSmile_L": 0.3}
        controller.record_frame(blendshapes, 1000)

        assert controller._state.last_valid_frame is not None
        assert controller._state.last_valid_frame["blendshapes"] == blendshapes
        assert controller._state.last_valid_frame["t_ms"] == 1000

    def test_record_frame_copies_dict(self):
        """Record frame copies the blendshape dict."""
        controller = YieldController(session_id="record-test")

        blendshapes = {"jawOpen": 0.5}
        controller.record_frame(blendshapes, 1000)

        # Modify original
        blendshapes["jawOpen"] = 1.0

        # Stored frame should be unchanged
        assert controller._state.last_valid_frame["blendshapes"]["jawOpen"] == 0.5


class TestYieldControllerGetYieldPose:
    """Tests for get_yield_pose method."""

    @pytest.fixture(autouse=True)
    def setup_clock(self):
        """Setup audio clock."""
        clock = get_audio_clock()
        clock.start_session("pose-test")
        yield
        try:
            clock.end_session("pose-test")
        except KeyError:
            pass

    def test_get_yield_pose_returns_last_frame(self):
        """get_yield_pose returns last recorded frame."""
        controller = YieldController(
            session_id="pose-test",
            yield_threshold_ms=50,
            freeze_trigger_ms=1000,  # High to prevent freeze
        )

        blendshapes = {"jawOpen": 0.8}
        controller.record_frame(blendshapes, 500)

        # Start yielding
        controller.should_yield(100)

        pose = controller.get_yield_pose(1000)

        assert pose == blendshapes

    def test_get_yield_pose_returns_neutral_without_last_frame(self):
        """get_yield_pose returns neutral if no last frame."""
        controller = YieldController(
            session_id="pose-test",
            yield_threshold_ms=50,
            freeze_trigger_ms=1000,
        )

        # Start yielding without recording any frames
        controller.should_yield(100)

        pose = controller.get_yield_pose(1000)

        # Should return neutral
        assert "jawOpen" in pose
        assert pose["jawOpen"] == 0.0  # Neutral

    def test_get_yield_pose_increments_skipped(self):
        """get_yield_pose increments frames_skipped."""
        controller = YieldController(
            session_id="pose-test",
            yield_threshold_ms=50,
            freeze_trigger_ms=1000,
        )

        controller.should_yield(100)
        assert controller.frames_skipped == 0

        controller.get_yield_pose(1000)
        assert controller.frames_skipped == 1

        controller.get_yield_pose(1050)
        assert controller.frames_skipped == 2


class TestYieldControllerSlowFreeze:
    """Tests for slow-freeze behavior."""

    @pytest.fixture(autouse=True)
    def setup_clock(self):
        """Setup audio clock."""
        clock = get_audio_clock()
        clock.start_session("freeze-test")
        yield
        try:
            clock.end_session("freeze-test")
        except KeyError:
            pass

    def test_slow_freeze_state_management(self):
        """Slow-freeze state can be set and checked."""
        controller = YieldController(session_id="freeze-test")

        # Initially not freezing
        assert controller.is_freezing is False

        # Manually set state for testing
        controller._state.in_slow_freeze = True
        assert controller.is_freezing is True


class TestYieldControllerInterpolatePose:
    """Tests for pose interpolation during freeze."""

    @pytest.fixture(autouse=True)
    def setup_clock(self):
        """Setup audio clock."""
        clock = get_audio_clock()
        clock.start_session("interp-test")
        yield
        try:
            clock.end_session("interp-test")
        except KeyError:
            pass

    def test_interpolate_to_neutral_start(self):
        """Interpolation at progress 0 returns last pose."""
        controller = YieldController(session_id="interp-test")

        last_pose = {"jawOpen": 0.8, "mouthSmile_L": 0.5}
        controller._state.last_valid_frame = {
            "blendshapes": last_pose,
            "t_ms": 1000,
        }

        result = controller._interpolate_to_neutral(0.0)

        # At progress 0, should be close to last pose
        assert result["jawOpen"] == pytest.approx(0.8, abs=0.01)

    def test_interpolate_to_neutral_end(self):
        """Interpolation at progress 1 returns neutral."""
        controller = YieldController(session_id="interp-test")

        last_pose = {"jawOpen": 0.8, "mouthSmile_L": 0.5}
        controller._state.last_valid_frame = {
            "blendshapes": last_pose,
            "t_ms": 1000,
        }

        result = controller._interpolate_to_neutral(1.0)

        # At progress 1, should be neutral
        assert result["jawOpen"] == 0.0

    def test_interpolate_to_neutral_midpoint(self):
        """Interpolation at midpoint is between pose and neutral."""
        controller = YieldController(session_id="interp-test")

        last_pose = {"jawOpen": 1.0}
        controller._state.last_valid_frame = {
            "blendshapes": last_pose,
            "t_ms": 1000,
        }

        result = controller._interpolate_to_neutral(0.5)

        # At midpoint, should be interpolated
        # With ease-out: 1 - (1-0.5)^2 = 1 - 0.25 = 0.75
        # So value = 1.0 + (0.0 - 1.0) * 0.75 = 0.25
        assert 0.0 < result["jawOpen"] < 1.0

    def test_interpolate_without_last_frame(self):
        """Interpolation without last frame returns neutral."""
        controller = YieldController(session_id="interp-test")

        result = controller._interpolate_to_neutral(0.5)

        assert result["jawOpen"] == 0.0  # Neutral


class TestYieldControllerCallbacks:
    """Tests for yield callbacks."""

    @pytest.fixture(autouse=True)
    def setup_clock(self):
        """Setup audio clock."""
        clock = get_audio_clock()
        clock.start_session("callback-test")
        yield
        try:
            clock.end_session("callback-test")
        except KeyError:
            pass

    def test_on_yield_start_callback(self):
        """on_yield_start callback is called."""
        controller = YieldController(
            session_id="callback-test",
            yield_threshold_ms=50,
        )

        yield_started = []

        def callback():
            yield_started.append(True)

        controller.on_yield_start(callback)
        controller.should_yield(100)

        assert len(yield_started) == 1

    def test_on_slow_freeze_callback_registered(self):
        """on_slow_freeze callback is registered."""
        controller = YieldController(session_id="callback-test")

        freeze_started = []

        def callback():
            freeze_started.append(True)

        controller.on_slow_freeze(callback)

        # Verify callback is registered
        assert controller._on_slow_freeze is not None

        # Manually trigger the callback
        controller._on_slow_freeze()
        assert len(freeze_started) == 1


class TestYieldControllerProperties:
    """Tests for controller properties."""

    def test_state_property(self):
        """state property returns current state."""
        controller = YieldController(session_id="props-test")
        state = controller.state

        assert state.is_yielding is False
        assert state.frames_skipped == 0

    def test_is_yielding_property(self):
        """is_yielding property works."""
        controller = YieldController(session_id="props-test")
        assert controller.is_yielding is False

    def test_is_freezing_property(self):
        """is_freezing property works."""
        controller = YieldController(session_id="props-test")
        assert controller.is_freezing is False

    def test_frames_skipped_property(self):
        """frames_skipped property works."""
        controller = YieldController(session_id="props-test")
        assert controller.frames_skipped == 0


class TestYieldControllerReset:
    """Tests for reset method."""

    def test_reset_clears_state(self):
        """reset() clears all state."""
        controller = YieldController(session_id="reset-test")

        # Set some state
        controller._state.is_yielding = True
        controller._state.frames_skipped = 10
        controller._state.in_slow_freeze = True

        controller.reset()

        assert controller.is_yielding is False
        assert controller.frames_skipped == 0
        assert controller.is_freezing is False


class TestYieldControllerNeutralPose:
    """Tests for neutral pose management."""

    def test_set_neutral_pose(self):
        """set_neutral_pose updates neutral."""
        controller = YieldController(session_id="neutral-test")

        custom_neutral = {"jawOpen": 0.1, "eyesClosed_L": 0.5}
        controller.set_neutral_pose(custom_neutral)

        assert controller._neutral_pose == custom_neutral

    def test_set_neutral_pose_copies(self):
        """set_neutral_pose copies the dict."""
        controller = YieldController(session_id="neutral-test")

        custom_neutral = {"jawOpen": 0.1}
        controller.set_neutral_pose(custom_neutral)

        # Modify original
        custom_neutral["jawOpen"] = 0.9

        # Stored neutral should be unchanged
        assert controller._neutral_pose["jawOpen"] == 0.1


class TestCreateYieldController:
    """Tests for factory function."""

    def test_factory_creates_controller(self):
        """Factory creates YieldController instance."""
        controller = create_yield_controller("factory-test")

        assert isinstance(controller, YieldController)
        assert controller._session_id == "factory-test"
