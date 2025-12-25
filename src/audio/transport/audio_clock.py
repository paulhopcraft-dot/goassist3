"""Audio Clock - Authoritative monotonic time source.

TMF v3.0 §2.2: Audio is the master clock.
- All timing must derive from a single monotonic clock source
- t_audio_ms is authoritative for all packet timestamps
- Overlap audio does NOT advance the clock
- Never use wall-clock time for audio synchronization

This module provides the single source of truth for audio timing across:
- Audio packets (t_audio_ms field)
- Blendshape frames (time alignment)
- CANCEL events (t_event_ms)
- Latency measurements (TTFA, barge-in)

Platform notes:
- Linux: Uses CLOCK_MONOTONIC via time.monotonic_ns()
- Windows: Uses QueryPerformanceCounter via time.perf_counter_ns()
- Both provide nanosecond resolution, converted to milliseconds
"""

import threading
import time
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ClockReading:
    """A single clock reading with both raw and adjusted values."""

    raw_ns: int  # Raw monotonic nanoseconds
    ms: int  # Milliseconds since session start
    session_id: str | None  # Associated session (if any)


class AudioClock:
    """Authoritative monotonic clock for audio timing.

    Thread-safe singleton that provides consistent timestamps across
    all components of the audio pipeline.

    Usage:
        clock = AudioClock()

        # For session-relative timing
        clock.start_session("session-123")
        t_audio_ms = clock.get_time_ms("session-123")

        # For absolute timing (metrics, logs)
        t_abs_ms = clock.get_absolute_ms()
    """

    # Singleton instance
    _instance: "AudioClock | None" = None
    _lock: threading.Lock = threading.Lock()

    # Nanoseconds per millisecond
    NS_PER_MS: Final[int] = 1_000_000

    def __new__(cls) -> "AudioClock":
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._init_clock()
                    cls._instance = instance
        return cls._instance

    def _init_clock(self) -> None:
        """Initialize clock state."""
        self._session_starts: dict[str, int] = {}  # session_id -> start_ns
        self._session_lock = threading.Lock()

        # Record process start time for absolute measurements
        self._process_start_ns = time.monotonic_ns()

    def _now_ns(self) -> int:
        """Get current monotonic time in nanoseconds.

        Uses time.monotonic_ns() which is:
        - Linux: CLOCK_MONOTONIC
        - Windows: QueryPerformanceCounter
        - macOS: mach_absolute_time

        All provide nanosecond precision and are monotonically increasing.
        """
        return time.monotonic_ns()

    def start_session(self, session_id: str) -> int:
        """Start timing for a new session.

        Args:
            session_id: Unique session identifier

        Returns:
            Session start time in absolute milliseconds (for logging)

        Raises:
            ValueError: If session already exists
        """
        with self._session_lock:
            if session_id in self._session_starts:
                raise ValueError(f"Session {session_id} already started")

            start_ns = self._now_ns()
            self._session_starts[session_id] = start_ns

            # Return absolute ms for logging
            return (start_ns - self._process_start_ns) // self.NS_PER_MS

    def end_session(self, session_id: str) -> int | None:
        """End timing for a session.

        Args:
            session_id: Session identifier

        Returns:
            Session duration in milliseconds, or None if session not found
        """
        with self._session_lock:
            start_ns = self._session_starts.pop(session_id, None)
            if start_ns is None:
                return None

            duration_ns = self._now_ns() - start_ns
            return duration_ns // self.NS_PER_MS

    def get_time_ms(self, session_id: str) -> int:
        """Get session-relative time in milliseconds.

        This is the value to use for t_audio_ms in packets.

        Args:
            session_id: Session identifier

        Returns:
            Milliseconds since session start

        Raises:
            KeyError: If session not found
        """
        with self._session_lock:
            start_ns = self._session_starts.get(session_id)
            if start_ns is None:
                raise KeyError(f"Session {session_id} not found")

            elapsed_ns = self._now_ns() - start_ns
            return elapsed_ns // self.NS_PER_MS

    def get_reading(self, session_id: str) -> ClockReading:
        """Get a full clock reading with raw and converted values.

        Args:
            session_id: Session identifier

        Returns:
            ClockReading with raw_ns, ms, and session_id

        Raises:
            KeyError: If session not found
        """
        with self._session_lock:
            start_ns = self._session_starts.get(session_id)
            if start_ns is None:
                raise KeyError(f"Session {session_id} not found")

            now_ns = self._now_ns()
            elapsed_ns = now_ns - start_ns

            return ClockReading(
                raw_ns=now_ns,
                ms=elapsed_ns // self.NS_PER_MS,
                session_id=session_id,
            )

    def get_absolute_ms(self) -> int:
        """Get absolute time since process start in milliseconds.

        Use this for:
        - Logging timestamps
        - Metrics collection
        - Cross-session comparisons

        NOT for packet timestamps (use get_time_ms for that).
        """
        elapsed_ns = self._now_ns() - self._process_start_ns
        return elapsed_ns // self.NS_PER_MS

    def measure_elapsed_ms(self, start_ns: int) -> float:
        """Measure elapsed time from a raw nanosecond timestamp.

        Useful for latency measurements where sub-millisecond precision matters.

        Args:
            start_ns: Starting time from _now_ns() or ClockReading.raw_ns

        Returns:
            Elapsed time in milliseconds (float for sub-ms precision)
        """
        elapsed_ns = self._now_ns() - start_ns
        return elapsed_ns / self.NS_PER_MS

    def session_exists(self, session_id: str) -> bool:
        """Check if a session is registered with the clock."""
        with self._session_lock:
            return session_id in self._session_starts

    @property
    def active_sessions(self) -> int:
        """Get count of active sessions."""
        with self._session_lock:
            return len(self._session_starts)


# Module-level singleton accessor
_audio_clock: AudioClock | None = None


def get_audio_clock() -> AudioClock:
    """Get the global audio clock instance.

    Preferred way to access the clock for dependency injection.
    """
    global _audio_clock
    if _audio_clock is None:
        _audio_clock = AudioClock()
    return _audio_clock
