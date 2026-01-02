"""Backpressure Policy - Graceful degradation under load.

TMF v3.0 §5.2, Implementation §5.3: Explicit degradation order.

Backpressure Order (MUST be followed in sequence):
1. Drop avatar frames first (visual degrade)
2. Shorten responses (verbosity policy) - driven by SCOS
3. Refuse non-essential tool calls
4. Queue or reject new sessions (last resort)
5. Audio continuity ALWAYS wins - NEVER degrade audio

Reference: Implementation-v3.0.md §5.3
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable

from src.config.constants import TMF
from src.observability.logging import BackpressureLogger, get_logger
from src.observability.metrics import record_backpressure

logger = get_logger(__name__)


class BackpressureLevel(IntEnum):
    """Backpressure levels in order of severity."""

    NORMAL = 0  # No backpressure
    ANIMATION_YIELD = 1  # Drop/relax animation frames
    VERBOSITY_REDUCE = 2  # Shorten LLM responses
    TOOL_REFUSE = 3  # Refuse non-essential tool calls
    SESSION_QUEUE = 4  # Queue new sessions
    SESSION_REJECT = 5  # Reject new sessions (last resort)


@dataclass
class BackpressureState:
    """Current backpressure state."""

    level: BackpressureLevel = BackpressureLevel.NORMAL
    animation_yield_active: bool = False
    verbosity_factor: float = 1.0  # 1.0 = normal, 0.5 = half verbosity
    max_tokens_override: int | None = None
    tools_disabled: bool = False
    queue_depth: int = 0
    rejecting_sessions: bool = False

    @property
    def is_degraded(self) -> bool:
        """Whether any degradation is active."""
        return self.level > BackpressureLevel.NORMAL


@dataclass
class SystemMetrics:
    """System resource metrics for backpressure decisions."""

    vram_usage_pct: float = 0.0  # 0-100
    cpu_usage_pct: float = 0.0
    active_sessions: int = 0
    queue_depth: int = 0
    avg_ttfa_ms: float = 0.0
    animation_lag_ms: float = 0.0
    error_rate_pct: float = 0.0


# Thresholds for triggering backpressure levels
THRESHOLDS = {
    BackpressureLevel.ANIMATION_YIELD: {
        "animation_lag_ms": 120,  # TMF §4.3: >120ms → yield
        "vram_usage_pct": 85,
    },
    BackpressureLevel.VERBOSITY_REDUCE: {
        "avg_ttfa_ms": 200,  # 80% of 250ms contract
        "vram_usage_pct": 90,
        "active_sessions": TMF.MAX_CONCURRENT_SESSIONS - 2,
    },
    BackpressureLevel.TOOL_REFUSE: {
        "avg_ttfa_ms": 225,  # 90% of 250ms contract
        "vram_usage_pct": 93,
    },
    BackpressureLevel.SESSION_QUEUE: {
        "avg_ttfa_ms": 240,  # 96% of 250ms contract
        "vram_usage_pct": 95,
        "active_sessions": TMF.MAX_CONCURRENT_SESSIONS - 1,
    },
    BackpressureLevel.SESSION_REJECT: {
        "avg_ttfa_ms": 250,  # At contract limit
        "vram_usage_pct": 98,
        "active_sessions": TMF.MAX_CONCURRENT_SESSIONS,
        "error_rate_pct": 5,
    },
}


class BackpressureController:
    """Controls backpressure policy based on system metrics.

    Monitors system state and applies degradation in the
    correct order to maintain audio continuity.

    Usage:
        controller = BackpressureController()
        controller.on_level_change(handle_backpressure)

        # Update metrics periodically
        controller.update_metrics(SystemMetrics(...))

        # Check current state
        if controller.state.animation_yield_active:
            # Skip animation frames
            ...

        # Get LLM token limit
        max_tokens = controller.get_max_tokens()
    """

    def __init__(
        self,
        session_id: str | None = None,
        check_interval_s: float = 1.0,
    ) -> None:
        self._session_id = session_id
        self._check_interval_s = check_interval_s
        self._state = BackpressureState()
        self._metrics = SystemMetrics()
        self._logger = BackpressureLogger(session_id)

        # Callbacks
        self._on_level_change: list[Callable[[BackpressureLevel], None]] = []

        # Background task
        self._monitor_task: asyncio.Task | None = None
        self._running = False

    @property
    def state(self) -> BackpressureState:
        """Current backpressure state."""
        return self._state

    @property
    def level(self) -> BackpressureLevel:
        """Current backpressure level."""
        return self._state.level

    def on_level_change(
        self, callback: Callable[[BackpressureLevel], None]
    ) -> None:
        """Register callback for level changes.

        Args:
            callback: Function to call when level changes
        """
        self._on_level_change.append(callback)

    def update_metrics(self, metrics: SystemMetrics) -> BackpressureLevel:
        """Update system metrics and recalculate backpressure.

        Args:
            metrics: Current system metrics

        Returns:
            New backpressure level
        """
        self._metrics = metrics
        return self._evaluate_level()

    def _evaluate_level(self) -> BackpressureLevel:
        """Evaluate current backpressure level based on metrics."""
        new_level = BackpressureLevel.NORMAL

        # Check each level's thresholds (in order)
        for level in BackpressureLevel:
            if level == BackpressureLevel.NORMAL:
                continue

            thresholds = THRESHOLDS.get(level, {})
            if self._exceeds_thresholds(thresholds):
                new_level = level

        # Apply level change if needed
        if new_level != self._state.level:
            self._apply_level(new_level)

        return new_level

    def _exceeds_thresholds(self, thresholds: dict) -> bool:
        """Check if any threshold is exceeded.

        Args:
            thresholds: Dict of metric name → threshold value

        Returns:
            True if any threshold exceeded
        """
        for metric, threshold in thresholds.items():
            value = getattr(self._metrics, metric, 0)
            if value >= threshold:
                return True
        return False

    def _apply_level(self, new_level: BackpressureLevel) -> None:
        """Apply a new backpressure level.

        Args:
            new_level: New level to apply
        """
        old_level = self._state.level
        self._state.level = new_level

        # Apply level-specific state
        self._state.animation_yield_active = (
            new_level >= BackpressureLevel.ANIMATION_YIELD
        )

        if new_level >= BackpressureLevel.VERBOSITY_REDUCE:
            # Reduce verbosity progressively
            if new_level == BackpressureLevel.VERBOSITY_REDUCE:
                self._state.verbosity_factor = 0.7
                self._state.max_tokens_override = 384
            elif new_level >= BackpressureLevel.TOOL_REFUSE:
                self._state.verbosity_factor = 0.5
                self._state.max_tokens_override = 256
        else:
            self._state.verbosity_factor = 1.0
            self._state.max_tokens_override = None

        self._state.tools_disabled = new_level >= BackpressureLevel.TOOL_REFUSE
        self._state.rejecting_sessions = (
            new_level >= BackpressureLevel.SESSION_REJECT
        )

        # Log and record metrics
        if new_level > old_level:
            self._logger.level_activated(
                level=new_level.name,
                trigger=self._get_trigger_reason(),
            )
            record_backpressure(new_level.name.lower())

        # Notify callbacks
        for callback in self._on_level_change:
            try:
                callback(new_level)
            except Exception as e:
                logger.warning(
                    "backpressure_callback_error",
                    session_id=self._session_id,
                    callback=getattr(callback, "__name__", str(callback)),
                    level=new_level.name,
                    error=str(e),
                )

    def _get_trigger_reason(self) -> str:
        """Get the primary reason for current backpressure."""
        reasons = []

        if self._metrics.animation_lag_ms > 120:
            reasons.append(f"animation_lag={self._metrics.animation_lag_ms}ms")
        if self._metrics.vram_usage_pct > 85:
            reasons.append(f"vram={self._metrics.vram_usage_pct}%")
        if self._metrics.avg_ttfa_ms > 200:
            reasons.append(f"ttfa={self._metrics.avg_ttfa_ms}ms")
        if self._metrics.active_sessions >= TMF.MAX_CONCURRENT_SESSIONS - 1:
            reasons.append(f"sessions={self._metrics.active_sessions}")

        return ", ".join(reasons) if reasons else "threshold_exceeded"

    def get_max_tokens(self) -> int:
        """Get max tokens for LLM based on backpressure.

        Returns:
            Max tokens to use for generation
        """
        if self._state.max_tokens_override:
            return self._state.max_tokens_override
        return 512  # Default

    def should_allow_tool_call(self, tool_name: str) -> bool:
        """Check if a tool call should be allowed.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool call is allowed
        """
        if not self._state.tools_disabled:
            return True

        # Always allow essential tools
        essential_tools = {"cancel", "end_session", "emergency_stop"}
        return tool_name in essential_tools

    def should_allow_new_session(self) -> bool:
        """Check if a new session should be allowed.

        Returns:
            True if new session is allowed
        """
        return not self._state.rejecting_sessions

    def get_queue_position(self) -> int | None:
        """Get queue position if sessions are being queued.

        Returns:
            Queue position, or None if not queuing
        """
        if self._state.level >= BackpressureLevel.SESSION_QUEUE:
            self._state.queue_depth += 1
            self._logger.session_queued(self._state.queue_depth)
            return self._state.queue_depth
        return None

    async def start_monitoring(self) -> None:
        """Start background metrics monitoring."""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self) -> None:
        """Background loop to check metrics."""
        while self._running:
            try:
                # Evaluate level with current metrics
                self._evaluate_level()
                await asyncio.sleep(self._check_interval_s)
            except asyncio.CancelledError:
                break
            except Exception:
                # Don't let monitoring errors crash the system
                await asyncio.sleep(self._check_interval_s)

    def reset(self) -> None:
        """Reset backpressure to normal."""
        self._state = BackpressureState()
        self._metrics = SystemMetrics()


def create_backpressure_controller(
    session_id: str | None = None,
) -> BackpressureController:
    """Factory function to create backpressure controller.

    Args:
        session_id: Optional session ID for logging

    Returns:
        BackpressureController instance
    """
    return BackpressureController(session_id=session_id)
