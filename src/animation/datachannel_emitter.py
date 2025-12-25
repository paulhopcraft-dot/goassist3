"""WebRTC Data Channel Emitter - UDP-based blendshape streaming.

TMF v3.0 §3.7: Use WebRTC Data Channel for blendshapes to avoid
TCP head-of-line blocking that causes jittery animation.

Key Points:
- UDP-like transport (unreliable, unordered) for low latency
- Same path as audio for synchronized delivery
- Graceful fallback to WebSocket if data channel unavailable

Reference: Implementation-v3.0.md §4.4
"""

import asyncio
import json
from dataclasses import dataclass
from typing import AsyncIterator, Callable

from src.animation.base import BlendshapeFrame
from src.animation.heartbeat import HeartbeatEmitter, create_heartbeat_emitter
from src.api.webrtc.gateway import WebRTCGateway
from src.api.websocket.blendshapes import BlendshapeWebSocket
from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EmitterConfig:
    """Configuration for data channel emitter."""

    use_data_channel: bool = True  # Prefer WebRTC data channel
    fallback_to_websocket: bool = True  # Fallback to WS if DC unavailable
    heartbeat_enabled: bool = True
    compress_frames: bool = False  # Optional frame compression
    max_queue_size: int = 30  # Max frames in send queue


class DataChannelEmitter:
    """Emits blendshape frames via WebRTC Data Channel.

    Provides low-latency UDP-like transport for animation frames.
    Falls back to WebSocket if data channel is unavailable.

    Usage:
        emitter = DataChannelEmitter(session_id="session-123")
        await emitter.start(webrtc_gateway)

        # Stream frames
        async for frame in animation_engine.generate_frames(audio):
            await emitter.send(frame)

        await emitter.stop()
    """

    def __init__(
        self,
        session_id: str,
        config: EmitterConfig | None = None,
    ) -> None:
        self._session_id = session_id
        self._config = config or EmitterConfig()

        self._webrtc: WebRTCGateway | None = None
        self._websocket: BlendshapeWebSocket | None = None
        self._heartbeat: HeartbeatEmitter | None = None

        self._running = False
        self._using_data_channel = False
        self._send_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self._config.max_queue_size
        )
        self._send_task: asyncio.Task | None = None

        # Metrics
        self._frames_sent = 0
        self._frames_dropped = 0

    async def start(
        self,
        webrtc: WebRTCGateway | None = None,
        websocket: BlendshapeWebSocket | None = None,
    ) -> None:
        """Start the emitter.

        Args:
            webrtc: WebRTC gateway for data channel
            websocket: WebSocket handler for fallback
        """
        self._webrtc = webrtc
        self._websocket = websocket

        # Determine transport
        if self._config.use_data_channel and webrtc:
            self._using_data_channel = True
            logger.info(
                "using_data_channel",
                session_id=self._session_id,
            )
        elif self._config.fallback_to_websocket and websocket:
            self._using_data_channel = False
            logger.info(
                "using_websocket_fallback",
                session_id=self._session_id,
            )
        else:
            raise RuntimeError("No transport available for blendshapes")

        # Start send loop
        self._running = True
        self._send_task = asyncio.create_task(self._send_loop())

        # Start heartbeat
        if self._config.heartbeat_enabled:
            self._heartbeat = create_heartbeat_emitter(
                self._session_id,
                on_heartbeat=self._queue_heartbeat,
            )
            self._heartbeat.start()

    async def stop(self) -> None:
        """Stop the emitter."""
        self._running = False

        # Stop heartbeat
        if self._heartbeat:
            self._heartbeat.stop()

        # Stop send task
        if self._send_task:
            self._send_task.cancel()
            try:
                await self._send_task
            except asyncio.CancelledError:
                pass

        logger.info(
            "emitter_stopped",
            session_id=self._session_id,
            frames_sent=self._frames_sent,
            frames_dropped=self._frames_dropped,
        )

    async def send(self, frame: BlendshapeFrame) -> bool:
        """Queue a frame for sending.

        Args:
            frame: Blendshape frame to send

        Returns:
            True if queued, False if dropped
        """
        try:
            self._send_queue.put_nowait(frame)
            return True
        except asyncio.QueueFull:
            self._frames_dropped += 1
            return False

    def _queue_heartbeat(self, frame: BlendshapeFrame) -> None:
        """Queue heartbeat frame (sync callback)."""
        try:
            self._send_queue.put_nowait(frame)
        except asyncio.QueueFull:
            pass  # Drop heartbeat if queue full

    async def _send_loop(self) -> None:
        """Background loop to send queued frames."""
        while self._running:
            try:
                frame = await asyncio.wait_for(
                    self._send_queue.get(),
                    timeout=0.1,
                )

                success = await self._send_frame(frame)
                if success:
                    self._frames_sent += 1

                    # Update heartbeat timer
                    if self._heartbeat and not frame.heartbeat:
                        self._heartbeat.frame_sent(frame.t_audio_ms)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    "send_error",
                    session_id=self._session_id,
                    error=str(e),
                )

    async def _send_frame(self, frame: BlendshapeFrame) -> bool:
        """Send frame via appropriate transport.

        Args:
            frame: Frame to send

        Returns:
            True if sent successfully
        """
        frame_dict = frame.to_dict()

        if self._using_data_channel and self._webrtc:
            return await self._webrtc.send_blendshapes(
                self._session_id,
                frame_dict,
            )
        elif self._websocket:
            return await self._websocket.send_frame(frame_dict)

        return False

    @property
    def is_running(self) -> bool:
        """Whether emitter is running."""
        return self._running

    @property
    def using_data_channel(self) -> bool:
        """Whether using WebRTC data channel."""
        return self._using_data_channel

    @property
    def frames_sent(self) -> int:
        """Total frames sent."""
        return self._frames_sent

    @property
    def frames_dropped(self) -> int:
        """Total frames dropped."""
        return self._frames_dropped

    @property
    def queue_size(self) -> int:
        """Current send queue size."""
        return self._send_queue.qsize()


async def stream_frames(
    session_id: str,
    frame_source: AsyncIterator[BlendshapeFrame],
    webrtc: WebRTCGateway | None = None,
    websocket: BlendshapeWebSocket | None = None,
) -> None:
    """Convenience function to stream frames.

    Args:
        session_id: Session identifier
        frame_source: Async iterator of frames
        webrtc: Optional WebRTC gateway
        websocket: Optional WebSocket handler
    """
    emitter = DataChannelEmitter(session_id)
    await emitter.start(webrtc, websocket)

    try:
        async for frame in frame_source:
            await emitter.send(frame)
    finally:
        await emitter.stop()


def create_emitter(
    session_id: str,
    config: EmitterConfig | None = None,
) -> DataChannelEmitter:
    """Factory function to create data channel emitter.

    Args:
        session_id: Session identifier
        config: Optional configuration

    Returns:
        DataChannelEmitter instance
    """
    return DataChannelEmitter(session_id, config)
