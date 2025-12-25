"""Animation Yield Controller - Backpressure management for animation.

TMF v3.0 §1.2, §4.3: If animation lag > 120ms, yield frames.
Audio continuity ALWAYS wins - animation can be degraded.

Yield Behavior:
1. Lag > 120ms: Start yielding (skip frames)
2. Hold last valid blendshape pose
3. If yield persists > 100ms: Begin slow-freeze
4. Slow-freeze: Ease to neutral over exactly 150ms

Reference: Implementation-v3.0.md §4.3
"""

import asyncio
from dataclasses import dataclass
from typing import Callable

from src.audio.transport.audio_clock import get_audio_clock
from src.config.constants import TMF
from src.observability.logging import AnimationLogger
from src.observability.metrics import record_animation_yield


@dataclass
class YieldState:
    """Current yield state."""

    is_yielding: bool = False
    yield_start_ms: int = 0
    frames_skipped: int = 0
    in_slow_freeze: bool = False
    freeze_progress: float = 0.0  # 0.0 to 1.0
    last_valid_frame: dict | None = None


class YieldController:
    """Controls animation yield under backpressure.

    Monitors lag and triggers yield behavior per TMF §4.3:
    - Lag > 120ms: Start skipping frames
    - Hold last pose
    - After 100ms: Begin slow-freeze to neutral

    Usage:
        controller = YieldController(session_id="session-123")

        # Each frame generation
        if controller.should_yield(current_lag_ms):
            # Skip frame, get interpolated pose
            pose = controller.get_yield_pose(t_ms)
        else:
            pose = generate_actual_pose()
            controller.record_frame(pose, t_ms)
    """

    def __init__(
        self,
        session_id: str,
        yield_threshold_ms: int = TMF.ANIMATION_YIELD_THRESHOLD_MS,
        freeze_trigger_ms: int = TMF.ANIMATION_FREEZE_THRESHOLD_MS,
        freeze_duration_ms: int = TMF.ANIMATION_FREEZE_DURATION_MS,
    ) -> None:
        self._session_id = session_id
        self._yield_threshold_ms = yield_threshold_ms
        self._freeze_trigger_ms = freeze_trigger_ms
        self._freeze_duration_ms = freeze_duration_ms

        self._state = YieldState()
        self._logger = AnimationLogger(session_id)
        self._neutral_pose: dict | None = None

        # Callbacks
        self._on_yield_start: Callable[[], None] | None = None
        self._on_slow_freeze: Callable[[], None] | None = None

    def should_yield(self, lag_ms: int) -> bool:
        """Check if should yield based on lag.

        Args:
            lag_ms: Current animation lag in milliseconds

        Returns:
            True if frames should be skipped
        """
        if lag_ms > self._yield_threshold_ms:
            if not self._state.is_yielding:
                self._start_yield()
            return True

        if self._state.is_yielding:
            self._end_yield()
        return False

    def _start_yield(self) -> None:
        """Start yielding frames."""
        clock = get_audio_clock()
        self._state.is_yielding = True
        self._state.yield_start_ms = clock.get_absolute_ms()
        self._state.frames_skipped = 0

        self._logger.yield_triggered(self._yield_threshold_ms)
        record_animation_yield()

        if self._on_yield_start:
            self._on_yield_start()

    def _end_yield(self) -> None:
        """End yield period."""
        self._state.is_yielding = False
        self._state.in_slow_freeze = False
        self._state.freeze_progress = 0.0

    def record_frame(self, blendshapes: dict, t_ms: int) -> None:
        """Record a successfully generated frame.

        Args:
            blendshapes: The blendshape values
            t_ms: Timestamp of the frame
        """
        self._state.last_valid_frame = {
            "blendshapes": blendshapes.copy(),
            "t_ms": t_ms,
        }

    def get_yield_pose(self, t_ms: int) -> dict:
        """Get pose to use during yield.

        Implements hold → slow-freeze behavior:
        1. Initially: Hold last valid pose
        2. After 100ms: Ease to neutral over 150ms

        Args:
            t_ms: Current timestamp

        Returns:
            Blendshape dict to use
        """
        self._state.frames_skipped += 1

        clock = get_audio_clock()
        yield_duration = clock.get_absolute_ms() - self._state.yield_start_ms

        # Check if should start slow-freeze
        if yield_duration >= self._freeze_trigger_ms and not self._state.in_slow_freeze:
            self._state.in_slow_freeze = True
            self._logger.slow_freeze_started(t_ms)

            if self._on_slow_freeze:
                self._on_slow_freeze()

        if self._state.in_slow_freeze:
            # Calculate freeze progress (0.0 to 1.0)
            freeze_elapsed = yield_duration - self._freeze_trigger_ms
            self._state.freeze_progress = min(
                1.0,
                freeze_elapsed / self._freeze_duration_ms,
            )

            # Interpolate from last pose to neutral
            return self._interpolate_to_neutral(self._state.freeze_progress)

        # Not yet freezing: hold last pose
        if self._state.last_valid_frame:
            return self._state.last_valid_frame["blendshapes"]

        # No last frame: return neutral
        return self._get_neutral()

    def _interpolate_to_neutral(self, progress: float) -> dict:
        """Interpolate from last pose to neutral.

        Uses ease-out curve for smooth transition.

        Args:
            progress: 0.0 (start) to 1.0 (fully neutral)

        Returns:
            Interpolated blendshape dict
        """
        # Ease-out curve: 1 - (1 - t)^2
        eased = 1.0 - (1.0 - progress) ** 2

        neutral = self._get_neutral()

        if not self._state.last_valid_frame:
            return neutral

        last_pose = self._state.last_valid_frame["blendshapes"]
        result = {}

        for key in neutral:
            start_val = last_pose.get(key, 0.0)
            end_val = neutral[key]
            result[key] = start_val + (end_val - start_val) * eased

        return result

    def _get_neutral(self) -> dict:
        """Get neutral pose."""
        if self._neutral_pose is None:
            from src.animation.base import get_neutral_blendshapes
            self._neutral_pose = get_neutral_blendshapes()
        return self._neutral_pose.copy()

    def set_neutral_pose(self, pose: dict) -> None:
        """Set custom neutral pose.

        Args:
            pose: Blendshape dict to use as neutral
        """
        self._neutral_pose = pose.copy()

    def on_yield_start(self, callback: Callable[[], None]) -> None:
        """Register callback for yield start."""
        self._on_yield_start = callback

    def on_slow_freeze(self, callback: Callable[[], None]) -> None:
        """Register callback for slow-freeze start."""
        self._on_slow_freeze = callback

    def reset(self) -> None:
        """Reset yield state."""
        self._state = YieldState()

    @property
    def state(self) -> YieldState:
        """Current yield state."""
        return self._state

    @property
    def is_yielding(self) -> bool:
        """Whether currently yielding."""
        return self._state.is_yielding

    @property
    def is_freezing(self) -> bool:
        """Whether in slow-freeze."""
        return self._state.in_slow_freeze

    @property
    def frames_skipped(self) -> int:
        """Total frames skipped."""
        return self._state.frames_skipped


def create_yield_controller(session_id: str) -> YieldController:
    """Factory function to create yield controller.

    Args:
        session_id: Session identifier

    Returns:
        Configured YieldController
    """
    return YieldController(session_id)
