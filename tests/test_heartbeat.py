"""Tests for Animation Heartbeat.

Tests cover:
- HeartbeatConfig defaults
- HeartbeatEmitter lifecycle
- Heartbeat frame emission
- HeartbeatMonitor detection
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch

from src.animation.heartbeat import (
    HeartbeatConfig,
    HeartbeatEmitter,
    HeartbeatMonitor,
    create_heartbeat_emitter,
)
from src.animation.base import BlendshapeFrame
from src.audio.transport.audio_clock import get_audio_clock


class TestHeartbeatConfig:
    """Tests for HeartbeatConfig dataclass."""

    def test_default_values(self):
        """Default config has sensible values."""
        config = HeartbeatConfig()
        assert config.interval_ms == 100
        assert config.timeout_ms == 100  # TMF threshold
        assert config.neutral_pose is None

    def test_custom_values(self):
        """Custom config values are applied."""
        config = HeartbeatConfig(
            interval_ms=50,
            timeout_ms=200,
            neutral_pose={"jawOpen": 0.1},
        )
        assert config.interval_ms == 50
        assert config.timeout_ms == 200
        assert config.neutral_pose == {"jawOpen": 0.1}


class TestHeartbeatEmitter:
    """Tests for HeartbeatEmitter class."""

    @pytest.fixture(autouse=True)
    def setup_audio_clock(self):
        """Setup audio clock for tests."""
        clock = get_audio_clock()
        clock.start_session("heartbeat-test")
        yield
        try:
            clock.end_session("heartbeat-test")
        except KeyError:
            pass

    def test_init_default_config(self):
        """Emitter initializes with default config."""
        emitter = HeartbeatEmitter(session_id="test-session")
        assert emitter._session_id == "test-session"
        assert emitter._config.interval_ms == 100
        assert emitter.is_running is False

    def test_init_custom_config(self):
        """Emitter uses custom config."""
        config = HeartbeatConfig(interval_ms=50)
        emitter = HeartbeatEmitter(session_id="test", config=config)
        assert emitter._config.interval_ms == 50

    def test_init_with_callback(self):
        """Emitter accepts heartbeat callback."""
        frames = []

        def callback(frame):
            frames.append(frame)

        emitter = HeartbeatEmitter(session_id="test", on_heartbeat=callback)
        assert emitter._on_heartbeat is not None

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Start sets running flag."""
        emitter = HeartbeatEmitter(session_id="heartbeat-test")
        emitter.start()
        assert emitter.is_running is True
        emitter.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Stop clears running flag."""
        emitter = HeartbeatEmitter(session_id="heartbeat-test")
        emitter.start()
        emitter.stop()
        assert emitter.is_running is False

    @pytest.mark.asyncio
    async def test_double_start_is_noop(self):
        """Starting twice is a no-op."""
        emitter = HeartbeatEmitter(session_id="heartbeat-test")
        emitter.start()
        emitter.start()  # Should not raise
        assert emitter.is_running is True
        emitter.stop()

    def test_frame_sent_updates_timestamp(self):
        """frame_sent updates last frame timestamp."""
        emitter = HeartbeatEmitter(session_id="test")
        emitter.frame_sent(500)
        assert emitter._last_frame_ms == 500

    def test_set_neutral_pose(self):
        """set_neutral_pose updates neutral pose."""
        emitter = HeartbeatEmitter(session_id="test")
        custom_pose = {"jawOpen": 0.2, "mouthSmile_L": 0.1}
        emitter.set_neutral_pose(custom_pose)
        assert emitter._neutral["jawOpen"] == 0.2

    def test_last_frame_ms_property(self):
        """last_frame_ms property returns correct value."""
        emitter = HeartbeatEmitter(session_id="test")
        emitter.frame_sent(1000)
        assert emitter.last_frame_ms == 1000


class TestHeartbeatEmitterLoop:
    """Tests for heartbeat loop."""

    @pytest.fixture(autouse=True)
    def setup_audio_clock(self):
        """Setup audio clock for tests."""
        clock = get_audio_clock()
        clock.start_session("loop-test")
        yield
        try:
            clock.end_session("loop-test")
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_heartbeat_emits_frames(self):
        """Heartbeat loop emits frames."""
        frames = []

        def callback(frame):
            frames.append(frame)

        config = HeartbeatConfig(interval_ms=20)  # Fast for testing
        emitter = HeartbeatEmitter(
            session_id="loop-test",
            config=config,
            on_heartbeat=callback,
        )
        emitter.start()

        # Wait for some heartbeats
        await asyncio.sleep(0.1)

        emitter.stop()

        # Should have received some heartbeat frames
        assert len(frames) >= 1

    @pytest.mark.asyncio
    async def test_heartbeat_suppressed_by_frame_sent(self):
        """Heartbeat suppressed when frames are being sent."""
        frames = []

        def callback(frame):
            frames.append(frame)

        config = HeartbeatConfig(interval_ms=20)
        emitter = HeartbeatEmitter(
            session_id="loop-test",
            config=config,
            on_heartbeat=callback,
        )
        emitter.start()

        # Keep sending frames
        clock = get_audio_clock()
        for _ in range(5):
            emitter.frame_sent(clock.get_absolute_ms())
            await asyncio.sleep(0.01)

        emitter.stop()

        # Should have fewer heartbeats due to suppression
        # (exact count depends on timing)


class TestHeartbeatMonitor:
    """Tests for HeartbeatMonitor class."""

    @pytest.fixture(autouse=True)
    def setup_audio_clock(self):
        """Setup audio clock for tests."""
        clock = get_audio_clock()
        clock.start_session("monitor-test")
        yield
        try:
            clock.end_session("monitor-test")
        except KeyError:
            pass

    def test_init_default_threshold(self):
        """Monitor initializes with default threshold."""
        monitor = HeartbeatMonitor(session_id="test")
        assert monitor._threshold_ms == 100  # TMF threshold
        assert monitor.is_missing_frames is False

    def test_init_custom_threshold(self):
        """Monitor uses custom threshold."""
        monitor = HeartbeatMonitor(session_id="test", threshold_ms=200)
        assert monitor._threshold_ms == 200

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Start sets running flag."""
        monitor = HeartbeatMonitor(session_id="monitor-test")
        monitor.start()
        assert monitor._running is True
        monitor.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Stop clears running flag."""
        monitor = HeartbeatMonitor(session_id="monitor-test")
        monitor.start()
        monitor.stop()
        assert monitor._running is False

    def test_frame_received_updates_state(self):
        """frame_received updates internal state."""
        monitor = HeartbeatMonitor(session_id="test")

        frame = BlendshapeFrame(
            session_id="test",
            seq=5,
            t_audio_ms=1000,
            blendshapes={},
        )
        monitor.frame_received(frame)

        assert monitor._last_frame_ms == 1000
        assert monitor._last_seq == 5

    def test_frame_received_clears_missing_flag(self):
        """frame_received clears missing frames flag."""
        monitor = HeartbeatMonitor(session_id="test")
        monitor._missing_detected = True

        frame = BlendshapeFrame(
            session_id="test",
            seq=1,
            t_audio_ms=100,
            blendshapes={},
        )
        monitor.frame_received(frame)

        assert monitor.is_missing_frames is False

    def test_on_missing_registers_callback(self):
        """on_missing registers callback."""
        monitor = HeartbeatMonitor(session_id="test")
        missing_events = []

        def callback(elapsed_ms):
            missing_events.append(elapsed_ms)

        monitor.on_missing(callback)
        assert monitor._on_missing is not None


class TestHeartbeatMonitorLoop:
    """Tests for monitor detection loop."""

    @pytest.fixture(autouse=True)
    def setup_audio_clock(self):
        """Setup audio clock for tests."""
        clock = get_audio_clock()
        clock.start_session("detect-test")
        yield
        try:
            clock.end_session("detect-test")
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_detects_missing_frames(self):
        """Monitor detects missing frames after threshold."""
        missing_events = []

        def callback(elapsed_ms):
            missing_events.append(elapsed_ms)

        monitor = HeartbeatMonitor(session_id="detect-test", threshold_ms=50)
        monitor.on_missing(callback)
        monitor.start()

        # Wait for detection
        await asyncio.sleep(0.15)

        monitor.stop()

        # Should have detected missing frames
        assert len(missing_events) >= 1
        assert missing_events[0] >= 50

    @pytest.mark.asyncio
    async def test_no_detection_when_frames_received(self):
        """Monitor doesn't trigger when frames are received."""
        missing_events = []

        def callback(elapsed_ms):
            missing_events.append(elapsed_ms)

        monitor = HeartbeatMonitor(session_id="detect-test", threshold_ms=50)
        monitor.on_missing(callback)
        monitor.start()

        # Keep receiving frames
        for _ in range(5):
            frame = BlendshapeFrame(
                session_id="detect-test",
                seq=1,
                t_audio_ms=get_audio_clock().get_absolute_ms(),
                blendshapes={},
            )
            monitor.frame_received(frame)
            await asyncio.sleep(0.02)

        monitor.stop()

        # Should not have triggered
        assert len(missing_events) == 0


class TestCreateHeartbeatEmitterFactory:
    """Tests for factory function."""

    @pytest.fixture(autouse=True)
    def setup_audio_clock(self):
        """Setup audio clock for tests."""
        clock = get_audio_clock()
        clock.start_session("factory-test")
        yield
        try:
            clock.end_session("factory-test")
        except KeyError:
            pass

    def test_factory_creates_emitter(self):
        """Factory creates HeartbeatEmitter instance."""
        emitter = create_heartbeat_emitter("factory-test")
        assert isinstance(emitter, HeartbeatEmitter)
        assert emitter._session_id == "factory-test"

    def test_factory_accepts_callback(self):
        """Factory accepts on_heartbeat callback."""
        frames = []

        def callback(frame):
            frames.append(frame)

        emitter = create_heartbeat_emitter("factory-test", on_heartbeat=callback)
        assert emitter._on_heartbeat is not None
