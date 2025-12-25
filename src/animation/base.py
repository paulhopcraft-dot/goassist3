"""Animation Base Interface - Pluggable audio-driven animation.

Defines interface for animation engines that generate ARKit-52
blendshape frames from audio input.

Reference: TMF v3.0 §3.1, Implementation §4.3, Addendum A §A3

Animation engines must support:
- Audio-driven blendshape generation at 30-60 Hz
- Hard cancel for barge-in (part of 150ms budget)
- Yield under backpressure (>120ms lag → yield)
- Heartbeat frames when audio pauses
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Protocol

from src.config.constants import TMF


# ARKit-52 blendshape names (standard set)
ARKIT_52_BLENDSHAPES = [
    # Brows
    "browDownLeft", "browDownRight", "browInnerUp",
    "browOuterUpLeft", "browOuterUpRight",
    # Eyes
    "eyeBlinkLeft", "eyeBlinkRight",
    "eyeLookDownLeft", "eyeLookDownRight",
    "eyeLookInLeft", "eyeLookInRight",
    "eyeLookOutLeft", "eyeLookOutRight",
    "eyeLookUpLeft", "eyeLookUpRight",
    "eyeSquintLeft", "eyeSquintRight",
    "eyeWideLeft", "eyeWideRight",
    # Jaw
    "jawForward", "jawLeft", "jawOpen", "jawRight",
    # Mouth
    "mouthClose", "mouthDimpleLeft", "mouthDimpleRight",
    "mouthFrownLeft", "mouthFrownRight",
    "mouthFunnel", "mouthLeft", "mouthLowerDownLeft",
    "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight",
    "mouthPucker", "mouthRight", "mouthRollLower", "mouthRollUpper",
    "mouthShrugLower", "mouthShrugUpper",
    "mouthSmileLeft", "mouthSmileRight",
    "mouthStretchLeft", "mouthStretchRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    # Nose
    "noseSneerLeft", "noseSneerRight",
    # Cheeks
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
    # Tongue
    "tongueOut",
]


def get_neutral_blendshapes() -> dict[str, float]:
    """Get neutral blendshape configuration.

    TMF Addendum A §A3.3: Default must be NEUTRAL (speech articulation only).
    Neutral = all blendshapes at 0.0 except baseline resting pose.

    Returns:
        Dict of blendshape name -> weight (all 0.0 for neutral)
    """
    return {name: 0.0 for name in ARKIT_52_BLENDSHAPES}


@dataclass
class BlendshapeFrame:
    """A single frame of ARKit-52 blendshapes.

    Schema per TMF v3.0 §3.1:
    {
        "session_id": "uuid",
        "seq": 4321,
        "t_audio_ms": 987654321,
        "fps": 30,
        "heartbeat": false,
        "blendshapes": {...}
    }
    """

    session_id: str
    seq: int
    t_audio_ms: int
    blendshapes: dict[str, float]
    fps: int = 30
    heartbeat: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "seq": self.seq,
            "t_audio_ms": self.t_audio_ms,
            "fps": self.fps,
            "heartbeat": self.heartbeat,
            "blendshapes": self.blendshapes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BlendshapeFrame":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            seq=data["seq"],
            t_audio_ms=data["t_audio_ms"],
            fps=data.get("fps", 30),
            heartbeat=data.get("heartbeat", False),
            blendshapes=data["blendshapes"],
        )

    @classmethod
    def heartbeat_frame(
        cls,
        session_id: str,
        seq: int,
        t_audio_ms: int,
    ) -> "BlendshapeFrame":
        """Create a heartbeat frame.

        Used when no audio is playing to maintain animation connection.
        """
        return cls(
            session_id=session_id,
            seq=seq,
            t_audio_ms=t_audio_ms,
            blendshapes=get_neutral_blendshapes(),
            heartbeat=True,
        )


class AnimationEngine(Protocol):
    """Protocol for pluggable animation engines.

    All animation implementations must conform to this interface.
    Per Addendum A §A3, substitution is allowed if:
    - Lip-sync accuracy maintained
    - FPS target (30-60Hz) met
    - Latency contribution fits budget
    - Commercially viable licensing

    Usage:
        engine = Audio2FaceEngine(...)
        await engine.start("session-123")

        async for frame in engine.generate_frames(audio_stream):
            send_to_client(frame)

        # On barge-in
        await engine.cancel()

        await engine.stop()
    """

    async def start(self, session_id: str) -> None:
        """Initialize animation engine for a session.

        Args:
            session_id: Unique session identifier
        """
        ...

    async def generate_frames(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[BlendshapeFrame]:
        """Generate blendshape frames from audio stream.

        Args:
            audio_stream: Async iterator of audio chunks

        Yields:
            BlendshapeFrame objects at target FPS

        Note:
            Must maintain 30-60 Hz output rate.
            If audio pauses, emit heartbeat frames.
        """
        ...

    async def cancel(self) -> None:
        """Immediately stop frame generation.

        Part of 150ms barge-in budget.
        Called when user interrupts.
        """
        ...

    async def stop(self) -> None:
        """Stop engine and cleanup resources."""
        ...

    def should_yield(self) -> bool:
        """Check if engine should yield due to backpressure.

        TMF §4.3: If animation lag > 120ms, yield.
        Returns True if frames should be skipped.
        """
        ...


class BaseAnimationEngine(ABC):
    """Base class for animation engine implementations.

    Provides common functionality and state management.
    Concrete implementations should override abstract methods.
    """

    def __init__(
        self,
        target_fps: int = 30,
        yield_threshold_ms: int = TMF.ANIMATION_YIELD_THRESHOLD_MS,
    ) -> None:
        self._session_id: str | None = None
        self._target_fps = target_fps
        self._yield_threshold_ms = yield_threshold_ms
        self._running: bool = False
        self._generating: bool = False
        self._cancelled: bool = False
        self._seq: int = 0
        self._last_frame_ms: int = 0
        self._current_lag_ms: int = 0

    @abstractmethod
    async def start(self, session_id: str) -> None:
        """Initialize engine for session."""
        self._session_id = session_id
        self._running = True
        self._cancelled = False
        self._seq = 0

    @abstractmethod
    async def generate_frames(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[BlendshapeFrame]:
        """Generate blendshape frames from audio."""
        ...

    async def cancel(self) -> None:
        """Immediately stop generation.

        Default implementation sets cancel flag.
        Subclasses should override to add cleanup.
        """
        self._cancelled = True
        self._generating = False

    async def stop(self) -> None:
        """Stop engine and cleanup."""
        await self.cancel()
        self._running = False

    def should_yield(self) -> bool:
        """Check if should yield due to backpressure.

        TMF §4.3: Lag > 120ms → yield.
        """
        return self._current_lag_ms > self._yield_threshold_ms

    def update_lag(self, lag_ms: int) -> None:
        """Update current lag measurement."""
        self._current_lag_ms = lag_ms

    def next_seq(self) -> int:
        """Get next sequence number."""
        self._seq += 1
        return self._seq

    @property
    def session_id(self) -> str | None:
        """Current session ID."""
        return self._session_id

    @property
    def is_running(self) -> bool:
        """Whether engine is ready."""
        return self._running

    @property
    def is_generating(self) -> bool:
        """Whether frame generation is in progress."""
        return self._generating

    @property
    def is_cancelled(self) -> bool:
        """Whether generation was cancelled."""
        return self._cancelled

    @property
    def target_fps(self) -> int:
        """Target frames per second."""
        return self._target_fps

    @property
    def frame_interval_ms(self) -> float:
        """Milliseconds between frames."""
        return 1000.0 / self._target_fps


class MockAnimationEngine(BaseAnimationEngine):
    """Mock animation engine for testing.

    Generates neutral blendshapes at target FPS.
    Useful for unit tests and development.
    """

    async def start(self, session_id: str) -> None:
        """Start mock engine."""
        await super().start(session_id)

    async def generate_frames(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[BlendshapeFrame]:
        """Generate mock frames (neutral pose)."""
        import asyncio

        self._generating = True
        self._cancelled = False
        frame_interval = self.frame_interval_ms / 1000.0

        try:
            t_audio_ms = 0
            async for audio_chunk in audio_stream:
                if self._cancelled:
                    break

                # Check for yield
                if self.should_yield():
                    continue

                # Generate frame
                frame = BlendshapeFrame(
                    session_id=self._session_id or "",
                    seq=self.next_seq(),
                    t_audio_ms=t_audio_ms,
                    blendshapes=get_neutral_blendshapes(),
                    fps=self._target_fps,
                )

                yield frame

                # Simulate frame timing
                t_audio_ms += int(frame_interval * 1000)
                await asyncio.sleep(frame_interval)

        finally:
            self._generating = False


async def audio_to_frames(
    audio_bytes: bytes,
    chunk_size: int = 640,  # 20ms at 16kHz mono
) -> AsyncIterator[bytes]:
    """Convert audio bytes to async stream of chunks.

    Utility for testing animation engines with non-streaming audio.
    """
    for i in range(0, len(audio_bytes), chunk_size):
        yield audio_bytes[i:i + chunk_size]
