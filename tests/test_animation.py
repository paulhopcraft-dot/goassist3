"""Tests for animation pipeline components.

Tests cover:
- BlendshapeFrame creation and serialization
- Animation engine state management
- Yield controller backpressure handling
- Heartbeat emission during silence
- TMF compliance for animation timing

Reference: TMF v3.0 §3.1, §4.3, Implementation §4.3
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.animation.base import (
    ARKIT_52_BLENDSHAPES,
    BaseAnimationEngine,
    BlendshapeFrame,
    MockAnimationEngine,
    get_neutral_blendshapes,
)
from src.animation.yield_controller import YieldController, YieldState
from src.animation.heartbeat import (
    HeartbeatConfig,
    HeartbeatEmitter,
    HeartbeatMonitor,
)
from src.config.constants import TMF


class TestARKit52Blendshapes:
    """Tests for ARKit-52 blendshape constants."""

    def test_arkit_52_has_52_blendshapes(self):
        """Verify we have exactly 52 ARKit blendshapes."""
        assert len(ARKIT_52_BLENDSHAPES) == 52

    def test_arkit_52_includes_eye_blendshapes(self):
        """Verify eye blendshapes are present."""
        assert "eyeBlinkLeft" in ARKIT_52_BLENDSHAPES
        assert "eyeBlinkRight" in ARKIT_52_BLENDSHAPES
        assert "eyeLookUpLeft" in ARKIT_52_BLENDSHAPES

    def test_arkit_52_includes_mouth_blendshapes(self):
        """Verify mouth blendshapes for lip-sync are present."""
        assert "jawOpen" in ARKIT_52_BLENDSHAPES
        assert "mouthFunnel" in ARKIT_52_BLENDSHAPES
        assert "mouthSmileLeft" in ARKIT_52_BLENDSHAPES
        assert "mouthSmileRight" in ARKIT_52_BLENDSHAPES

    def test_arkit_52_no_duplicates(self):
        """Verify no duplicate blendshape names."""
        assert len(ARKIT_52_BLENDSHAPES) == len(set(ARKIT_52_BLENDSHAPES))


class TestNeutralBlendshapes:
    """Tests for neutral blendshape generation."""

    def test_neutral_has_all_blendshapes(self):
        """Neutral pose includes all 52 blendshapes."""
        neutral = get_neutral_blendshapes()
        assert len(neutral) == 52
        for name in ARKIT_52_BLENDSHAPES:
            assert name in neutral

    def test_neutral_all_zeros(self):
        """Neutral pose has all values at 0.0."""
        neutral = get_neutral_blendshapes()
        for value in neutral.values():
            assert value == 0.0

    def test_neutral_returns_new_copy(self):
        """Each call returns a new dictionary."""
        n1 = get_neutral_blendshapes()
        n2 = get_neutral_blendshapes()
        assert n1 is not n2
        n1["jawOpen"] = 0.5
        assert n2["jawOpen"] == 0.0


class TestBlendshapeFrame:
    """Tests for BlendshapeFrame dataclass."""

    def test_frame_creation(self):
        """Test basic frame creation."""
        frame = BlendshapeFrame(
            session_id="test-session",
            seq=1,
            t_audio_ms=1000,
            blendshapes=get_neutral_blendshapes(),
        )
        assert frame.session_id == "test-session"
        assert frame.seq == 1
        assert frame.t_audio_ms == 1000
        assert frame.fps == 30  # default
        assert frame.heartbeat is False

    def test_frame_custom_fps(self):
        """Test frame with custom FPS."""
        frame = BlendshapeFrame(
            session_id="test",
            seq=1,
            t_audio_ms=0,
            blendshapes={},
            fps=60,
        )
        assert frame.fps == 60

    def test_frame_to_dict(self):
        """Test frame serialization to dict."""
        blendshapes = {"jawOpen": 0.5, "mouthSmileLeft": 0.3}
        frame = BlendshapeFrame(
            session_id="test",
            seq=42,
            t_audio_ms=12345,
            blendshapes=blendshapes,
            fps=30,
            heartbeat=False,
        )
        data = frame.to_dict()

        assert data["session_id"] == "test"
        assert data["seq"] == 42
        assert data["t_audio_ms"] == 12345
        assert data["fps"] == 30
        assert data["heartbeat"] is False
        assert data["blendshapes"] == blendshapes

    def test_frame_from_dict(self):
        """Test frame deserialization from dict."""
        data = {
            "session_id": "test",
            "seq": 100,
            "t_audio_ms": 5000,
            "fps": 60,
            "heartbeat": True,
            "blendshapes": {"jawOpen": 0.8},
        }
        frame = BlendshapeFrame.from_dict(data)

        assert frame.session_id == "test"
        assert frame.seq == 100
        assert frame.t_audio_ms == 5000
        assert frame.fps == 60
        assert frame.heartbeat is True
        assert frame.blendshapes["jawOpen"] == 0.8

    def test_heartbeat_frame_factory(self):
        """Test heartbeat frame creation."""
        frame = BlendshapeFrame.heartbeat_frame(
            session_id="test",
            seq=5,
            t_audio_ms=2000,
        )

        assert frame.session_id == "test"
        assert frame.seq == 5
        assert frame.t_audio_ms == 2000
        assert frame.heartbeat is True
        assert frame.blendshapes == get_neutral_blendshapes()


class TestMockAnimationEngine:
    """Tests for MockAnimationEngine."""

    @pytest.fixture
    def engine(self):
        """Create mock animation engine."""
        return MockAnimationEngine(target_fps=30)

    @pytest.mark.asyncio
    async def test_start_initializes_state(self, engine):
        """Test engine start initializes state."""
        await engine.start("test-session")

        assert engine.session_id == "test-session"
        assert engine.is_running is True
        assert engine.is_cancelled is False
        assert engine._seq == 0

    @pytest.mark.asyncio
    async def test_stop_clears_state(self, engine):
        """Test engine stop clears state."""
        await engine.start("test-session")
        await engine.stop()

        assert engine.is_running is False

    @pytest.mark.asyncio
    async def test_cancel_sets_flag(self, engine):
        """Test cancel sets cancelled flag."""
        await engine.start("test-session")
        await engine.cancel()

        assert engine.is_cancelled is True
        assert engine.is_generating is False

    def test_should_yield_below_threshold(self, engine):
        """Test should_yield returns False below threshold."""
        engine.update_lag(50)
        assert engine.should_yield() is False

    def test_should_yield_above_threshold(self, engine):
        """Test should_yield returns True above threshold."""
        engine.update_lag(TMF.ANIMATION_YIELD_THRESHOLD_MS + 10)
        assert engine.should_yield() is True

    def test_next_seq_increments(self, engine):
        """Test sequence number increments correctly."""
        assert engine.next_seq() == 1
        assert engine.next_seq() == 2
        assert engine.next_seq() == 3

    def test_frame_interval_calculation(self, engine):
        """Test frame interval calculation."""
        # 30 FPS = ~33.33ms per frame
        assert engine.frame_interval_ms == pytest.approx(33.33, rel=0.01)

    @pytest.mark.asyncio
    async def test_generate_frames_produces_frames(self, engine):
        """Test that generate_frames produces blendshape frames."""
        await engine.start("test-session")

        async def mock_audio():
            for _ in range(3):
                yield b"\x00" * 640

        frames = []
        async for frame in engine.generate_frames(mock_audio()):
            frames.append(frame)
            if len(frames) >= 3:
                await engine.cancel()

        assert len(frames) == 3
        for frame in frames:
            assert isinstance(frame, BlendshapeFrame)
            assert frame.session_id == "test-session"
            assert frame.fps == 30


class TestYieldController:
    """Tests for YieldController backpressure handling."""

    @pytest.fixture
    def controller(self, audio_clock):
        """Create yield controller with mocked clock."""
        with patch("src.animation.yield_controller.get_audio_clock", return_value=audio_clock):
            return YieldController(
                session_id="test-session",
                yield_threshold_ms=120,
                freeze_trigger_ms=100,
                freeze_duration_ms=150,
            )

    def test_initial_state(self, controller):
        """Test initial yield state."""
        assert controller.is_yielding is False
        assert controller.is_freezing is False
        assert controller.frames_skipped == 0

    def test_should_yield_below_threshold(self, controller):
        """Test no yield below threshold."""
        assert controller.should_yield(100) is False
        assert controller.is_yielding is False

    def test_should_yield_above_threshold(self, controller):
        """Test yield triggered above threshold."""
        assert controller.should_yield(150) is True
        assert controller.is_yielding is True

    def test_yield_ends_when_lag_drops(self, controller):
        """Test yield ends when lag drops below threshold."""
        controller.should_yield(150)  # Start yield
        assert controller.is_yielding is True

        controller.should_yield(50)  # Lag drops
        assert controller.is_yielding is False

    def test_record_frame_stores_last_frame(self, controller):
        """Test frame recording stores blendshapes."""
        blendshapes = {"jawOpen": 0.5}
        controller.record_frame(blendshapes, 1000)

        assert controller.state.last_valid_frame is not None
        assert controller.state.last_valid_frame["blendshapes"]["jawOpen"] == 0.5

    def test_get_yield_pose_returns_last_frame(self, controller, audio_clock):
        """Test yield pose returns last valid frame initially."""
        with patch("src.animation.yield_controller.get_audio_clock", return_value=audio_clock):
            blendshapes = {"jawOpen": 0.5, "mouthSmileLeft": 0.3}
            controller.record_frame(blendshapes, 1000)

            controller.should_yield(150)  # Start yield

            pose = controller.get_yield_pose(1050)
            assert pose["jawOpen"] == 0.5
            assert pose["mouthSmileLeft"] == 0.3

    def test_get_yield_pose_returns_neutral_if_no_frame(self, controller, audio_clock):
        """Test yield pose returns neutral if no last frame."""
        with patch("src.animation.yield_controller.get_audio_clock", return_value=audio_clock):
            controller.should_yield(150)
            pose = controller.get_yield_pose(1000)

            # Should be neutral (all zeros)
            assert all(v == 0.0 for v in pose.values())

    def test_yield_callback_triggered(self, controller):
        """Test yield start callback is triggered."""
        callback = MagicMock()
        controller.on_yield_start(callback)

        controller.should_yield(150)  # Trigger yield

        callback.assert_called_once()

    def test_slow_freeze_callback_triggered(self):
        """Test slow freeze callback after threshold."""
        # Create a mock clock with controllable time
        mock_clock = MagicMock()
        current_time = [0]  # Use list to allow mutation in inner function

        def get_time():
            return current_time[0]

        mock_clock.get_absolute_ms = MagicMock(side_effect=get_time)

        with patch("src.animation.yield_controller.get_audio_clock", return_value=mock_clock):
            controller = YieldController(
                session_id="test-session",
                yield_threshold_ms=120,
                freeze_trigger_ms=100,
                freeze_duration_ms=150,
            )
            callback = MagicMock()
            controller.on_slow_freeze(callback)

            # Start yield at time 0
            current_time[0] = 0
            controller.should_yield(150)

            # Advance clock past freeze trigger (100ms)
            current_time[0] = 150

            # Get pose to trigger freeze check
            controller.get_yield_pose(150)

            callback.assert_called_once()
            assert controller.is_freezing is True

    def test_reset_clears_state(self, controller):
        """Test reset clears all yield state."""
        controller.should_yield(150)
        controller.reset()

        assert controller.is_yielding is False
        assert controller.is_freezing is False
        assert controller.frames_skipped == 0
        assert controller.state.last_valid_frame is None


class TestHeartbeatEmitter:
    """Tests for HeartbeatEmitter."""

    @pytest.fixture
    def emitter(self, audio_clock):
        """Create heartbeat emitter with mocked clock."""
        with patch("src.animation.heartbeat.get_audio_clock", return_value=audio_clock):
            return HeartbeatEmitter(
                session_id="test-session",
                config=HeartbeatConfig(interval_ms=50),
            )

    def test_initial_state(self, emitter):
        """Test emitter initial state."""
        assert emitter.is_running is False

    @pytest.mark.asyncio
    async def test_start_sets_running(self, emitter, audio_clock):
        """Test start sets running flag."""
        with patch("src.animation.heartbeat.get_audio_clock", return_value=audio_clock):
            emitter.start()
            assert emitter.is_running is True
            emitter.stop()
            # Allow task to cancel
            await asyncio.sleep(0.01)

    @pytest.mark.asyncio
    async def test_stop_clears_running(self, emitter, audio_clock):
        """Test stop clears running flag."""
        with patch("src.animation.heartbeat.get_audio_clock", return_value=audio_clock):
            emitter.start()
            emitter.stop()
            assert emitter.is_running is False
            # Allow task to cancel
            await asyncio.sleep(0.01)

    def test_frame_sent_updates_last_frame_ms(self, emitter):
        """Test frame_sent updates timestamp."""
        emitter.frame_sent(5000)
        assert emitter.last_frame_ms == 5000

    def test_set_neutral_pose(self, emitter):
        """Test custom neutral pose setting."""
        custom_pose = {"jawOpen": 0.1}
        emitter.set_neutral_pose(custom_pose)
        assert emitter._neutral == custom_pose


class TestHeartbeatMonitor:
    """Tests for HeartbeatMonitor."""

    @pytest.fixture
    def monitor(self, audio_clock):
        """Create heartbeat monitor with mocked clock."""
        with patch("src.animation.heartbeat.get_audio_clock", return_value=audio_clock):
            return HeartbeatMonitor(
                session_id="test-session",
                threshold_ms=100,
            )

    def test_initial_state(self, monitor):
        """Test monitor initial state."""
        assert monitor.is_missing_frames is False

    def test_frame_received_clears_missing(self, monitor):
        """Test receiving frame clears missing flag."""
        monitor._missing_detected = True
        frame = BlendshapeFrame(
            session_id="test",
            seq=1,
            t_audio_ms=1000,
            blendshapes={},
        )
        monitor.frame_received(frame)

        assert monitor.is_missing_frames is False

    @pytest.mark.asyncio
    async def test_start_sets_running(self, monitor, audio_clock):
        """Test start sets running flag."""
        with patch("src.animation.heartbeat.get_audio_clock", return_value=audio_clock):
            monitor.start()
            assert monitor._running is True
            monitor.stop()
            # Allow task to cancel
            await asyncio.sleep(0.01)

    @pytest.mark.asyncio
    async def test_stop_clears_running(self, monitor, audio_clock):
        """Test stop clears running flag."""
        with patch("src.animation.heartbeat.get_audio_clock", return_value=audio_clock):
            monitor.start()
            monitor.stop()
            assert monitor._running is False
            # Allow task to cancel
            await asyncio.sleep(0.01)


class TestTMFAnimationCompliance:
    """Tests for TMF v3.0 animation timing compliance."""

    def test_yield_threshold_is_120ms(self):
        """TMF §4.3: Animation yield threshold is 120ms."""
        assert TMF.ANIMATION_YIELD_THRESHOLD_MS == 120

    def test_freeze_trigger_is_100ms(self):
        """TMF §4.3: Slow-freeze triggers after 100ms of yield."""
        assert TMF.ANIMATION_FREEZE_THRESHOLD_MS == 100

    def test_freeze_duration_is_150ms(self):
        """TMF §4.3: Slow-freeze completes over 150ms."""
        assert TMF.ANIMATION_FREEZE_DURATION_MS == 150

    def test_frame_schema_matches_spec(self):
        """TMF §3.1: Frame schema must match specification."""
        frame = BlendshapeFrame(
            session_id="uuid-here",
            seq=4321,
            t_audio_ms=987654321,
            blendshapes={"jawOpen": 0.5},
            fps=30,
            heartbeat=False,
        )
        data = frame.to_dict()

        # Required fields per TMF §3.1
        required_fields = [
            "session_id",
            "seq",
            "t_audio_ms",
            "fps",
            "heartbeat",
            "blendshapes",
        ]
        for field in required_fields:
            assert field in data

    def test_arkit_52_is_standard_set(self):
        """Verify ARKit-52 is the standard Apple blendshape set."""
        # Key reference blendshapes that must be present
        required = [
            "jawOpen",  # Essential for lip-sync
            "mouthFunnel",
            "mouthPucker",
            "eyeBlinkLeft",
            "eyeBlinkRight",
            "browInnerUp",
            "cheekPuff",
            "tongueOut",
        ]
        for name in required:
            assert name in ARKIT_52_BLENDSHAPES

    def test_yield_controller_respects_thresholds(self, audio_clock):
        """Test yield controller uses TMF thresholds."""
        with patch("src.animation.yield_controller.get_audio_clock", return_value=audio_clock):
            controller = YieldController(session_id="test")

            # Default thresholds should match TMF
            assert controller._yield_threshold_ms == TMF.ANIMATION_YIELD_THRESHOLD_MS
            assert controller._freeze_trigger_ms == TMF.ANIMATION_FREEZE_THRESHOLD_MS
            assert controller._freeze_duration_ms == TMF.ANIMATION_FREEZE_DURATION_MS
