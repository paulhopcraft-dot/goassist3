"""Animation Heartbeat - Maintain connection during silence.

TMF v3.0 §4.3: If animation frames are missing > 100ms, trigger slow-freeze.
Heartbeat frames prevent jarring pose changes and maintain client connection.

Behavior:
1. During audio output: Normal blendshape frames at 30-60 Hz
2. During silence/pause: Emit heartbeat frames to maintain connection
3. If no frames > 100ms: Client triggers slow-freeze locally

Reference: Implementation-v3.0.md §4.3
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable

from src.animation.base import BlendshapeFrame, get_neutral_blendshapes
from src.audio.transport.audio_clock import get_audio_clock
from src.config.constants import TMF
from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HeartbeatConfig:
    """Configuration for heartbeat emission."""

    interval_ms: int = 100  # Emit heartbeat every 100ms during silence
    timeout_ms: int = TMF.ANIMATION_FREEZE_THRESHOLD_MS  # 100ms before freeze
    neutral_pose: dict | None = None


class HeartbeatEmitter:
    """Emits heartbeat frames during audio silence.

    Maintains animation connection when no audio is playing.
    Prevents client from triggering slow-freeze unnecessarily.

    Usage:
        emitter = HeartbeatEmitter(session_id="session-123")
        emitter.start()

        # During audio: normal frames suppress heartbeat
        emitter.frame_sent(t_ms)

        # During silence: heartbeat auto-emits
        # Get frames via callback or async iterator

        emitter.stop()
    """

    def __init__(
        self,
        session_id: str,
        config: HeartbeatConfig | None = None,
        on_heartbeat: Callable[[BlendshapeFrame], None] | None = None,
    ) -> None:
        self._session_id = session_id
        self._config = config or HeartbeatConfig()
        self._on_heartbeat = on_heartbeat

        self._running = False
        self._task: asyncio.Task | None = None
        self._last_frame_ms: int = 0
        self._seq: int = 0
        self._neutral = self._config.neutral_pose or get_neutral_blendshapes()

    def start(self) -> None:
        """Start heartbeat emitter."""
        if self._running:
            return

        self._running = True
        clock = get_audio_clock()
        self._last_frame_ms = clock.get_absolute_ms()
        self._task = asyncio.create_task(self._heartbeat_loop())

    def stop(self) -> None:
        """Stop heartbeat emitter."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def frame_sent(self, t_ms: int) -> None:
        """Record that a normal frame was sent.

        Resets heartbeat timer.

        Args:
            t_ms: Timestamp of the frame
        """
        self._last_frame_ms = t_ms

    async def _heartbeat_loop(self) -> None:
        """Background loop to emit heartbeat frames."""
        interval_s = self._config.interval_ms / 1000.0

        while self._running:
            try:
                await asyncio.sleep(interval_s)

                if not self._running:
                    break

                # Check if heartbeat needed
                clock = get_audio_clock()
                now_ms = clock.get_absolute_ms()
                elapsed = now_ms - self._last_frame_ms

                if elapsed >= self._config.interval_ms:
                    # Emit heartbeat
                    self._seq += 1
                    frame = BlendshapeFrame.heartbeat_frame(
                        session_id=self._session_id,
                        seq=self._seq,
                        t_audio_ms=now_ms,
                    )

                    if self._on_heartbeat:
                        self._on_heartbeat(frame)

                    self._last_frame_ms = now_ms

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    "heartbeat_loop_error",
                    session_id=self._session_id,
                    error=str(e),
                )
                continue

    def set_neutral_pose(self, pose: dict) -> None:
        """Set custom neutral pose for heartbeats.

        Args:
            pose: Blendshape dict
        """
        self._neutral = pose.copy()

    @property
    def is_running(self) -> bool:
        """Whether emitter is running."""
        return self._running

    @property
    def last_frame_ms(self) -> int:
        """Timestamp of last frame sent."""
        return self._last_frame_ms


class HeartbeatMonitor:
    """Monitors incoming frames and detects missing frames.

    Used by client or for testing to detect when frames stop.
    Triggers slow-freeze behavior per TMF §4.3.

    Usage:
        monitor = HeartbeatMonitor(session_id="session-123")
        monitor.on_missing(handle_missing_frames)

        # For each received frame
        monitor.frame_received(frame)
    """

    def __init__(
        self,
        session_id: str,
        threshold_ms: int = TMF.ANIMATION_FREEZE_THRESHOLD_MS,
    ) -> None:
        self._session_id = session_id
        self._threshold_ms = threshold_ms

        self._last_frame_ms: int = 0
        self._last_seq: int = 0
        self._missing_detected = False
        self._on_missing: Callable[[int], None] | None = None

        self._running = False
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        """Start monitoring for missing frames."""
        if self._running:
            return

        self._running = True
        clock = get_audio_clock()
        self._last_frame_ms = clock.get_absolute_ms()
        self._task = asyncio.create_task(self._monitor_loop())

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def frame_received(self, frame: BlendshapeFrame) -> None:
        """Record received frame.

        Args:
            frame: Received blendshape frame
        """
        self._last_frame_ms = frame.t_audio_ms
        self._last_seq = frame.seq
        self._missing_detected = False

    def on_missing(self, callback: Callable[[int], None]) -> None:
        """Register callback for missing frames.

        Args:
            callback: Function called with elapsed_ms when frames missing
        """
        self._on_missing = callback

    async def _monitor_loop(self) -> None:
        """Background loop to check for missing frames."""
        check_interval_s = self._threshold_ms / 2000.0  # Check at half threshold

        while self._running:
            try:
                await asyncio.sleep(check_interval_s)

                if not self._running:
                    break

                clock = get_audio_clock()
                now_ms = clock.get_absolute_ms()
                elapsed = now_ms - self._last_frame_ms

                if elapsed >= self._threshold_ms and not self._missing_detected:
                    self._missing_detected = True
                    if self._on_missing:
                        self._on_missing(elapsed)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    "heartbeat_monitor_error",
                    session_id=self._session_id,
                    error=str(e),
                )
                continue

    @property
    def is_missing_frames(self) -> bool:
        """Whether frames are currently missing."""
        return self._missing_detected

    @property
    def elapsed_since_last_ms(self) -> int:
        """Milliseconds since last frame."""
        clock = get_audio_clock()
        return clock.get_absolute_ms() - self._last_frame_ms


def create_heartbeat_emitter(
    session_id: str,
    on_heartbeat: Callable[[BlendshapeFrame], None] | None = None,
) -> HeartbeatEmitter:
    """Factory function to create heartbeat emitter.

    Args:
        session_id: Session identifier
        on_heartbeat: Callback for heartbeat frames

    Returns:
        Configured HeartbeatEmitter
    """
    return HeartbeatEmitter(session_id, on_heartbeat=on_heartbeat)
