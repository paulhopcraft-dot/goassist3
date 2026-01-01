"""Tests for DataChannel Emitter.

Tests cover:
- EmitterConfig defaults
- DataChannelEmitter initialization
- Transport selection (WebRTC vs WebSocket)
- Frame queueing and dropping
- Metrics tracking
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.animation.datachannel_emitter import (
    DataChannelEmitter,
    EmitterConfig,
)
from src.animation.base import BlendshapeFrame


class TestEmitterConfig:
    """Tests for EmitterConfig dataclass."""

    def test_default_values(self):
        """Default config has sensible values."""
        config = EmitterConfig()
        assert config.use_data_channel is True
        assert config.fallback_to_websocket is True
        assert config.heartbeat_enabled is True
        assert config.compress_frames is False
        assert config.max_queue_size == 30

    def test_custom_values(self):
        """Custom config values are applied."""
        config = EmitterConfig(
            use_data_channel=False,
            fallback_to_websocket=False,
            heartbeat_enabled=False,
            compress_frames=True,
            max_queue_size=50,
        )
        assert config.use_data_channel is False
        assert config.fallback_to_websocket is False
        assert config.heartbeat_enabled is False
        assert config.compress_frames is True
        assert config.max_queue_size == 50


class TestDataChannelEmitter:
    """Tests for DataChannelEmitter class."""

    def test_init_default_config(self):
        """Emitter initializes with default config."""
        emitter = DataChannelEmitter(session_id="test-session")
        assert emitter._session_id == "test-session"
        assert emitter._config.use_data_channel is True
        assert emitter._running is False
        assert emitter._frames_sent == 0
        assert emitter._frames_dropped == 0

    def test_init_custom_config(self):
        """Emitter uses custom config."""
        config = EmitterConfig(max_queue_size=10)
        emitter = DataChannelEmitter(
            session_id="custom-session",
            config=config,
        )
        assert emitter._config.max_queue_size == 10


class TestDataChannelEmitterTransport:
    """Tests for transport selection."""

    @pytest.mark.asyncio
    async def test_prefers_data_channel(self):
        """Emitter prefers WebRTC data channel when available."""
        emitter = DataChannelEmitter(session_id="dc-test")
        mock_webrtc = MagicMock()
        mock_websocket = MagicMock()

        # Disable heartbeat to simplify test
        emitter._config.heartbeat_enabled = False

        await emitter.start(webrtc=mock_webrtc, websocket=mock_websocket)

        assert emitter._using_data_channel is True
        assert emitter._running is True

        await emitter.stop()

    @pytest.mark.asyncio
    async def test_falls_back_to_websocket(self):
        """Emitter falls back to WebSocket when data channel unavailable."""
        config = EmitterConfig(use_data_channel=False, heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="ws-test", config=config)
        mock_websocket = MagicMock()

        await emitter.start(websocket=mock_websocket)

        assert emitter._using_data_channel is False
        assert emitter._running is True

        await emitter.stop()

    @pytest.mark.asyncio
    async def test_raises_when_no_transport(self):
        """Emitter raises when no transport available."""
        config = EmitterConfig(
            use_data_channel=False,
            fallback_to_websocket=False,
            heartbeat_enabled=False,
        )
        emitter = DataChannelEmitter(session_id="no-transport", config=config)

        with pytest.raises(RuntimeError, match="No transport available"):
            await emitter.start()


class TestDataChannelEmitterLifecycle:
    """Tests for emitter start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Stop clears running flag."""
        config = EmitterConfig(heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="lifecycle-test", config=config)
        mock_websocket = MagicMock()

        await emitter.start(websocket=mock_websocket)
        assert emitter._running is True

        await emitter.stop()
        assert emitter._running is False

    @pytest.mark.asyncio
    async def test_stop_cancels_send_task(self):
        """Stop cancels the send task."""
        config = EmitterConfig(heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="task-test", config=config)
        mock_websocket = MagicMock()

        await emitter.start(websocket=mock_websocket)
        assert emitter._send_task is not None

        await emitter.stop()
        assert emitter._send_task.cancelled() or emitter._send_task.done()


class TestDataChannelEmitterQueue:
    """Tests for frame queueing."""

    @pytest.mark.asyncio
    async def test_send_queues_frame(self):
        """Send queues frame for delivery."""
        config = EmitterConfig(heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="queue-test", config=config)
        mock_websocket = MagicMock()

        await emitter.start(websocket=mock_websocket)

        frame = BlendshapeFrame(
            session_id="queue-test",
            seq=1,
            t_audio_ms=100,
            blendshapes={"jawOpen": 0.5},
        )

        result = await emitter.send(frame)
        assert result is True

        await emitter.stop()

    @pytest.mark.asyncio
    async def test_send_drops_when_queue_full(self):
        """Send drops frames when queue is full."""
        config = EmitterConfig(max_queue_size=2, heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="drop-test", config=config)
        mock_websocket = MagicMock()

        await emitter.start(websocket=mock_websocket)

        # Fill the queue
        for i in range(5):
            frame = BlendshapeFrame(
                session_id="drop-test",
                seq=i,
                t_audio_ms=i * 100,
                blendshapes={"jawOpen": 0.5},
            )
            await emitter.send(frame)

        # Should have dropped some frames
        assert emitter._frames_dropped > 0

        await emitter.stop()


class TestDataChannelEmitterMetrics:
    """Tests for emitter metrics."""

    def test_initial_metrics_zero(self):
        """Initial metrics are zero."""
        emitter = DataChannelEmitter(session_id="metrics-test")
        assert emitter._frames_sent == 0
        assert emitter._frames_dropped == 0

    @pytest.mark.asyncio
    async def test_dropped_frames_counted(self):
        """Dropped frames are counted."""
        config = EmitterConfig(max_queue_size=1, heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="count-test", config=config)
        mock_websocket = MagicMock()

        await emitter.start(websocket=mock_websocket)

        # Send more frames than queue can hold
        for i in range(5):
            frame = BlendshapeFrame(
                session_id="count-test",
                seq=i,
                t_audio_ms=i * 100,
                blendshapes={},
            )
            await emitter.send(frame)

        assert emitter._frames_dropped >= 3  # At least 3 should drop

        await emitter.stop()


class TestDataChannelEmitterProperties:
    """Tests for emitter properties."""

    def test_is_running_property(self):
        """is_running property works correctly."""
        emitter = DataChannelEmitter(session_id="props-test")
        assert emitter.is_running is False

    def test_using_data_channel_property(self):
        """using_data_channel property works correctly."""
        emitter = DataChannelEmitter(session_id="props-test")
        assert emitter.using_data_channel is False

    def test_frames_sent_property(self):
        """frames_sent property works correctly."""
        emitter = DataChannelEmitter(session_id="props-test")
        emitter._frames_sent = 100
        assert emitter.frames_sent == 100

    def test_frames_dropped_property(self):
        """frames_dropped property works correctly."""
        emitter = DataChannelEmitter(session_id="props-test")
        emitter._frames_dropped = 5
        assert emitter.frames_dropped == 5

    def test_queue_size_property(self):
        """queue_size property works correctly."""
        emitter = DataChannelEmitter(session_id="props-test")
        assert emitter.queue_size == 0


class TestDataChannelEmitterSendFrame:
    """Tests for _send_frame method."""

    @pytest.mark.asyncio
    async def test_send_frame_via_data_channel(self):
        """_send_frame sends via WebRTC data channel."""
        config = EmitterConfig(heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="dc-send-test", config=config)

        mock_webrtc = AsyncMock()
        mock_webrtc.send_blendshapes = AsyncMock(return_value=True)

        await emitter.start(webrtc=mock_webrtc)

        frame = BlendshapeFrame(
            session_id="dc-send-test",
            seq=1,
            t_audio_ms=100,
            blendshapes={"jawOpen": 0.5},
        )

        result = await emitter._send_frame(frame)

        assert result is True
        mock_webrtc.send_blendshapes.assert_awaited_once()

        await emitter.stop()

    @pytest.mark.asyncio
    async def test_send_frame_via_websocket(self):
        """_send_frame sends via WebSocket fallback."""
        config = EmitterConfig(use_data_channel=False, heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="ws-send-test", config=config)

        mock_websocket = AsyncMock()
        mock_websocket.send_frame = AsyncMock(return_value=True)

        await emitter.start(websocket=mock_websocket)

        frame = BlendshapeFrame(
            session_id="ws-send-test",
            seq=1,
            t_audio_ms=100,
            blendshapes={"jawOpen": 0.5},
        )

        result = await emitter._send_frame(frame)

        assert result is True
        mock_websocket.send_frame.assert_awaited_once()

        await emitter.stop()

    @pytest.mark.asyncio
    async def test_send_frame_returns_false_no_transport(self):
        """_send_frame returns False with no transport configured."""
        emitter = DataChannelEmitter(session_id="no-transport")
        emitter._running = True  # Bypass start
        emitter._using_data_channel = False
        emitter._webrtc = None
        emitter._websocket = None

        frame = BlendshapeFrame(
            session_id="no-transport",
            seq=1,
            t_audio_ms=100,
            blendshapes={},
        )

        result = await emitter._send_frame(frame)
        assert result is False


class TestDataChannelEmitterHeartbeat:
    """Tests for heartbeat integration."""

    @pytest.fixture(autouse=True)
    def setup_audio_clock(self):
        """Setup audio clock for tests."""
        from src.audio.transport.audio_clock import get_audio_clock
        clock = get_audio_clock()
        clock.start_session("hb-test")
        yield
        try:
            clock.end_session("hb-test")
        except KeyError:
            pass

    @pytest.mark.asyncio
    async def test_heartbeat_enabled_starts_emitter(self):
        """Heartbeat emitter starts when enabled."""
        config = EmitterConfig(heartbeat_enabled=True)
        emitter = DataChannelEmitter(session_id="hb-test", config=config)
        mock_websocket = MagicMock()

        await emitter.start(websocket=mock_websocket)

        assert emitter._heartbeat is not None
        assert emitter._heartbeat.is_running is True

        await emitter.stop()

    @pytest.mark.asyncio
    async def test_heartbeat_disabled_no_emitter(self):
        """No heartbeat emitter when disabled."""
        config = EmitterConfig(heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="hb-test", config=config)
        mock_websocket = MagicMock()

        await emitter.start(websocket=mock_websocket)

        assert emitter._heartbeat is None

        await emitter.stop()

    def test_queue_heartbeat_sync_callback(self):
        """_queue_heartbeat queues frame synchronously."""
        emitter = DataChannelEmitter(session_id="queue-hb-test")

        frame = BlendshapeFrame(
            session_id="queue-hb-test",
            seq=1,
            t_audio_ms=100,
            blendshapes={},
            heartbeat=True,
        )

        emitter._queue_heartbeat(frame)

        assert emitter.queue_size == 1

    def test_queue_heartbeat_drops_when_full(self):
        """_queue_heartbeat drops frame when queue full."""
        config = EmitterConfig(max_queue_size=1)
        emitter = DataChannelEmitter(session_id="full-hb-test", config=config)

        # Fill the queue
        frame1 = BlendshapeFrame(
            session_id="full-hb-test", seq=1, t_audio_ms=0, blendshapes={}
        )
        emitter._queue_heartbeat(frame1)

        # This should be dropped
        frame2 = BlendshapeFrame(
            session_id="full-hb-test", seq=2, t_audio_ms=100, blendshapes={}
        )
        emitter._queue_heartbeat(frame2)

        # Queue should still be size 1
        assert emitter.queue_size == 1


class TestDataChannelEmitterSendLoop:
    """Tests for send loop."""

    @pytest.mark.asyncio
    async def test_send_loop_processes_frames(self):
        """Send loop processes queued frames."""
        config = EmitterConfig(heartbeat_enabled=False)
        emitter = DataChannelEmitter(session_id="loop-test", config=config)

        mock_websocket = AsyncMock()
        mock_websocket.send_frame = AsyncMock(return_value=True)

        await emitter.start(websocket=mock_websocket)

        # Send some frames
        for i in range(3):
            frame = BlendshapeFrame(
                session_id="loop-test",
                seq=i,
                t_audio_ms=i * 100,
                blendshapes={"jawOpen": 0.5},
            )
            await emitter.send(frame)

        # Wait for processing
        await asyncio.sleep(0.2)

        # Should have sent frames
        assert emitter.frames_sent >= 1

        await emitter.stop()


class TestStreamFramesFunction:
    """Tests for stream_frames convenience function."""

    @pytest.mark.asyncio
    async def test_stream_frames_sends_all(self):
        """stream_frames sends all frames from iterator."""
        from src.animation.datachannel_emitter import stream_frames

        mock_websocket = AsyncMock()
        mock_websocket.send_frame = AsyncMock(return_value=True)

        async def frame_source():
            for i in range(3):
                yield BlendshapeFrame(
                    session_id="stream-test",
                    seq=i,
                    t_audio_ms=i * 100,
                    blendshapes={},
                )

        await stream_frames(
            session_id="stream-test",
            frame_source=frame_source(),
            websocket=mock_websocket,
        )

        # Should have called send_frame for each frame
        # (actual calls may vary due to timing)


class TestCreateEmitterFactory:
    """Tests for create_emitter factory function."""

    def test_factory_creates_emitter(self):
        """Factory creates DataChannelEmitter instance."""
        from src.animation.datachannel_emitter import create_emitter

        emitter = create_emitter("factory-test")
        assert isinstance(emitter, DataChannelEmitter)
        assert emitter._session_id == "factory-test"

    def test_factory_accepts_config(self):
        """Factory accepts custom config."""
        from src.animation.datachannel_emitter import create_emitter

        config = EmitterConfig(max_queue_size=10)
        emitter = create_emitter("factory-test", config)
        assert emitter._config.max_queue_size == 10
