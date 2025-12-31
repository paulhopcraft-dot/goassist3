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
