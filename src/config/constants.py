"""TMF v3.0 Constants - Authoritative thresholds and contracts.

These constants are derived directly from TMF v3.0 and Implementation v3.0.
They define the behavioral contracts that must be met.

Reference: TMF-v3.0.md, Implementation-v3.0.md
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class TMFConstants:
    """Immutable TMF v3.0 contract thresholds.

    All timing values in milliseconds unless otherwise noted.
    """

    # Section 1.2: Latency Contracts
    TTFA_P95_MS: Final[int] = 250  # Time to first audible response (p95)
    TTFA_P50_MS: Final[int] = 150  # Time to first audible response (p50 target)
    BARGE_IN_MS: Final[int] = 150  # Max barge-in response time

    # Section 3.1: Audio Packet Contract
    AUDIO_PACKET_DURATION_MS: Final[int] = 20  # Packet duration
    AUDIO_OVERLAP_MS: Final[int] = 5  # Overlap for cross-fade (does NOT advance clock)
    AUDIO_SAMPLE_RATE: Final[int] = 16000  # Default sample rate for ASR
    AUDIO_CHANNELS: Final[int] = 1  # Mono audio

    # Section 3.2: Context Management
    LLM_MAX_CONTEXT_TOKENS: Final[int] = 8192  # Hard context cap
    CONTEXT_ROLLOVER_THRESHOLD: Final[int] = 7500  # Trigger rollover at 93.75%
    CONTEXT_SUMMARIZATION_TIMEOUT_S: Final[float] = 5.0  # Summarization timeout

    # Section 4.2: Animation Thresholds
    ANIMATION_YIELD_LAG_MS: Final[int] = 120  # Yield animation if lag exceeds
    ANIMATION_YIELD_THRESHOLD_MS: Final[int] = 120  # Alias for ANIMATION_YIELD_LAG_MS
    ANIMATION_SLOW_FREEZE_MS: Final[int] = 150  # Ease to neutral duration
    ANIMATION_FREEZE_DURATION_MS: Final[int] = 150  # Alias for SLOW_FREEZE_MS
    ANIMATION_HEARTBEAT_THRESHOLD_MS: Final[int] = 100  # Missing frame threshold
    ANIMATION_FREEZE_THRESHOLD_MS: Final[int] = 100  # Alias for HEARTBEAT threshold
    ANIMATION_TARGET_FPS: Final[int] = 30  # Minimum animation FPS

    # Section 5.2: Backpressure Thresholds
    VRAM_HEADROOM_GB: Final[int] = 4  # Reserved VRAM headroom
    VRAM_WARNING_THRESHOLD_PERCENT: Final[float] = 0.90  # Warn at 90% usage

    # Section 6: Turn Detection
    TURN_ENDPOINT_BUDGET_MS: Final[int] = 15  # Max time for endpoint detection
    TURN_HARD_TIMEOUT_MS: Final[int] = 500  # Hard timeout before first audio

    # Section 7.3: Soak Test
    SOAK_DURATION_HOURS: Final[int] = 24  # Required soak test duration
    SOAK_DUTY_CYCLE_PERCENT: Final[float] = 0.30  # Active duty cycle

    # Session Defaults
    MAX_CONCURRENT_SESSIONS: Final[int] = 100  # Max concurrent sessions per node
    SESSION_IDLE_TIMEOUT_S: Final[int] = 300  # 5 minutes
    SESSION_MAX_DURATION_S: Final[int] = 3600  # 1 hour max session
    SESSION_WARMUP_TURNS: Final[int] = 3  # Turns before steady-state
    SESSION_WARMUP_SECONDS: Final[int] = 60  # Seconds before steady-state

    # SCOS (Session Control & Optimization Signals)
    SCOS_CONFIDENCE_LOW_THRESHOLD: Final[float] = 0.6  # ASR confidence threshold
    SCOS_FRICTION_REPEAT_WINDOW_S: Final[int] = 30  # Window for repeat detection


# Singleton instance for import convenience
TMF = TMFConstants()
