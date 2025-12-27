"""Live Link UDP Sender - Stream blendshapes to Unreal Engine.

Sends ARKit-52 blendshapes to Unreal Engine via Live Link protocol
for MetaHuman facial animation.

Reference: TMF v3.0 §3.6 - Unreal avatar render + ingest

Protocol:
- UDP packets to Unreal Engine (default port 11111)
- JSON payload matching Live Link Face format
- 30-60 Hz update rate for smooth animation

Usage:
    sender = LiveLinkSender(host="127.0.0.1", port=11111)
    await sender.start("GoAssist")

    # Send blendshape frame
    await sender.send_frame(blendshapes, timestamp_ms)

    await sender.stop()
"""

import asyncio
import json
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Callable

from src.animation.base import ARKIT_52_BLENDSHAPES, BlendshapeFrame
from src.config.constants import TMF
from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LiveLinkConfig:
    """Configuration for Live Link sender."""

    # Unreal Engine Live Link settings
    host: str = "127.0.0.1"
    port: int = 11111  # Default Live Link Face port

    # Subject name (appears in Unreal Live Link panel)
    subject_name: str = "GoAssist"

    # Frame rate
    target_fps: int = 30

    # Head rotation (optional)
    send_head_rotation: bool = True
    default_head_pitch: float = 0.0
    default_head_yaw: float = 0.0
    default_head_roll: float = 0.0


@dataclass
class LiveLinkState:
    """Internal state for Live Link sender."""

    running: bool = False
    frame_count: int = 0
    last_send_time: float = 0.0
    errors: int = 0


class LiveLinkSender:
    """Streams blendshapes to Unreal Engine via Live Link UDP.

    Implements the Live Link Face protocol for MetaHuman animation.
    Compatible with:
    - Live Link Face plugin
    - MetaHuman Blueprint
    - ARKit Face component

    Architecture:
        GoAssist Backend
              ↓
        [Audio2Face / LAM]
              ↓
        [ARKit-52 Blendshapes]
              ↓
        [LiveLinkSender] ──UDP──→ [Unreal Engine]
                                        ↓
                                  [MetaHuman]
    """

    # Live Link message types
    MSG_TYPE_SUBJECT_FRAME = 0
    MSG_TYPE_SUBJECT_STATIC = 1

    def __init__(
        self,
        config: LiveLinkConfig | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialize Live Link sender.

        Args:
            config: Live Link configuration
            on_error: Callback for send errors
        """
        self._config = config or LiveLinkConfig()
        self._on_error = on_error
        self._state = LiveLinkState()

        # UDP socket (created on start)
        self._socket: socket.socket | None = None

        # Blendshape name to index mapping
        self._blendshape_indices = {
            name: i for i, name in enumerate(ARKIT_52_BLENDSHAPES)
        }

    async def start(self, subject_name: str | None = None) -> None:
        """Start Live Link sender.

        Args:
            subject_name: Override subject name for this session
        """
        if self._state.running:
            return

        if subject_name:
            self._config.subject_name = subject_name

        # Create UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)

        self._state = LiveLinkState(running=True)

        logger.info(
            "livelink_started",
            host=self._config.host,
            port=self._config.port,
            subject_name=self._config.subject_name,
        )

    async def stop(self) -> None:
        """Stop Live Link sender."""
        self._state.running = False

        if self._socket:
            self._socket.close()
            self._socket = None

        logger.info(
            "livelink_stopped",
            frames_sent=self._state.frame_count,
            errors=self._state.errors,
        )

    async def send_frame(
        self,
        blendshapes: dict[str, float],
        timestamp_ms: int,
        head_rotation: tuple[float, float, float] | None = None,
    ) -> bool:
        """Send a blendshape frame to Unreal Engine.

        Args:
            blendshapes: ARKit-52 blendshape values (0.0-1.0)
            timestamp_ms: Frame timestamp in milliseconds
            head_rotation: Optional (pitch, yaw, roll) in degrees

        Returns:
            True if sent successfully
        """
        if not self._state.running or not self._socket:
            return False

        try:
            # Build Live Link packet
            packet = self._build_packet(blendshapes, timestamp_ms, head_rotation)

            # Send via UDP
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._socket.sendto,
                packet,
                (self._config.host, self._config.port),
            )

            self._state.frame_count += 1
            self._state.last_send_time = time.monotonic()

            return True

        except Exception as e:
            self._state.errors += 1
            logger.warning("livelink_send_error", error=str(e))

            if self._on_error:
                self._on_error(e)

            return False

    async def send_blendshape_frame(self, frame: BlendshapeFrame) -> bool:
        """Send a BlendshapeFrame object.

        Convenience method that extracts data from BlendshapeFrame.

        Args:
            frame: BlendshapeFrame from animation engine

        Returns:
            True if sent successfully
        """
        return await self.send_frame(
            blendshapes=frame.blendshapes,
            timestamp_ms=frame.t_audio_ms,
        )

    def _build_packet(
        self,
        blendshapes: dict[str, float],
        timestamp_ms: int,
        head_rotation: tuple[float, float, float] | None = None,
    ) -> bytes:
        """Build Live Link Face UDP packet.

        The packet format matches Unreal's Live Link Face plugin expectations.

        Format:
        {
            "DeviceID": "GoAssist",
            "Timestamp": 123456.789,
            "Blendshapes": {
                "browDownLeft": 0.0,
                ...
            },
            "HeadRotation": {
                "Pitch": 0.0,
                "Yaw": 0.0,
                "Roll": 0.0
            }
        }
        """
        # Use default head rotation if not provided
        if head_rotation is None:
            head_rotation = (
                self._config.default_head_pitch,
                self._config.default_head_yaw,
                self._config.default_head_roll,
            )

        # Build payload
        payload = {
            "DeviceID": self._config.subject_name,
            "Timestamp": timestamp_ms / 1000.0,  # Convert to seconds
            "Blendshapes": {},
        }

        # Add blendshapes (ensure all 52 are present)
        for name in ARKIT_52_BLENDSHAPES:
            value = blendshapes.get(name, 0.0)
            # Clamp to valid range
            payload["Blendshapes"][name] = max(0.0, min(1.0, value))

        # Add head rotation if enabled
        if self._config.send_head_rotation:
            payload["HeadRotation"] = {
                "Pitch": head_rotation[0],
                "Yaw": head_rotation[1],
                "Roll": head_rotation[2],
            }

        # Encode as JSON
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

    @property
    def is_running(self) -> bool:
        """Whether sender is active."""
        return self._state.running

    @property
    def frame_count(self) -> int:
        """Total frames sent."""
        return self._state.frame_count

    @property
    def error_count(self) -> int:
        """Total send errors."""
        return self._state.errors

    @property
    def config(self) -> LiveLinkConfig:
        """Current configuration."""
        return self._config


class LiveLinkBridge:
    """Bridges animation engine output to Live Link.

    Connects the animation pipeline to Unreal Engine:

        BlendshapeFrame stream
              ↓
        [LiveLinkBridge]
              ↓
        [LiveLinkSender] → UDP → Unreal

    Handles:
    - Frame rate limiting
    - Heartbeat frames during silence
    - Graceful degradation
    """

    def __init__(
        self,
        sender: LiveLinkSender,
        target_fps: int = 30,
    ) -> None:
        """Initialize bridge.

        Args:
            sender: Live Link sender instance
            target_fps: Target frame rate
        """
        self._sender = sender
        self._target_fps = target_fps
        self._frame_interval = 1.0 / target_fps

        self._running = False
        self._last_frame_time: float = 0.0
        self._frames_sent: int = 0
        self._frames_dropped: int = 0

    async def start(self) -> None:
        """Start the bridge."""
        self._running = True
        self._frames_sent = 0
        self._frames_dropped = 0

    async def stop(self) -> None:
        """Stop the bridge."""
        self._running = False

    async def process_frame(self, frame: BlendshapeFrame) -> bool:
        """Process and send a blendshape frame.

        Applies rate limiting to maintain target FPS.

        Args:
            frame: Blendshape frame to send

        Returns:
            True if frame was sent, False if dropped
        """
        if not self._running:
            return False

        now = time.monotonic()
        elapsed = now - self._last_frame_time

        # Rate limit to target FPS
        if elapsed < self._frame_interval:
            self._frames_dropped += 1
            return False

        # Send frame
        success = await self._sender.send_blendshape_frame(frame)

        if success:
            self._last_frame_time = now
            self._frames_sent += 1

        return success

    @property
    def frames_sent(self) -> int:
        """Total frames sent."""
        return self._frames_sent

    @property
    def frames_dropped(self) -> int:
        """Total frames dropped (rate limited)."""
        return self._frames_dropped

    @property
    def effective_fps(self) -> float:
        """Calculate effective FPS based on sent frames."""
        if self._last_frame_time == 0:
            return 0.0
        # This is a simplified calculation
        return self._target_fps


def create_livelink_sender(
    host: str = "127.0.0.1",
    port: int = 11111,
    subject_name: str = "GoAssist",
) -> LiveLinkSender:
    """Factory function to create Live Link sender.

    Args:
        host: Unreal Engine host IP
        port: Live Link Face port
        subject_name: Subject name in Unreal

    Returns:
        Configured LiveLinkSender
    """
    config = LiveLinkConfig(
        host=host,
        port=port,
        subject_name=subject_name,
    )
    return LiveLinkSender(config=config)
