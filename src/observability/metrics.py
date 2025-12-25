"""Prometheus Metrics - TMF v3.0 observability.

Exports:
- TTFA p50/p95 latencies
- Barge-in latency p95
- Animation yield counts
- Session counts
- Context rollover events

Reference: Implementation-v3.0.md §7, Ops-Runbook-v3.0.md §3
"""

from prometheus_client import Counter, Gauge, Histogram, Info

# -----------------------------------------------------------------------------
# Latency Histograms (TMF contracts)
# -----------------------------------------------------------------------------

# TTFA: Time to first audio byte (VAD endpoint → client audio)
# Contract: p95 ≤ 250ms
TTFA_HISTOGRAM = Histogram(
    "goassist_ttfa_seconds",
    "Time to first audio byte (VAD endpoint to client audio)",
    buckets=[0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0],
)

# Barge-in latency: User speech detected → audio stops at client
# Contract: p95 ≤ 150ms
BARGE_IN_HISTOGRAM = Histogram(
    "goassist_barge_in_seconds",
    "Barge-in latency (user speech to audio stop)",
    buckets=[0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.2, 0.25, 0.3],
)

# Component latencies for debugging
ASR_LATENCY = Histogram(
    "goassist_asr_latency_seconds",
    "ASR processing latency",
    buckets=[0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5],
)

LLM_TTFT = Histogram(
    "goassist_llm_ttft_seconds",
    "LLM time to first token",
    buckets=[0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0],
)

TTS_LATENCY = Histogram(
    "goassist_tts_latency_seconds",
    "TTS synthesis latency",
    buckets=[0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3],
)

# -----------------------------------------------------------------------------
# Counters
# -----------------------------------------------------------------------------

# Session lifecycle
SESSION_STARTED = Counter(
    "goassist_sessions_started_total",
    "Total sessions started",
)

SESSION_ENDED = Counter(
    "goassist_sessions_ended_total",
    "Total sessions ended",
    ["reason"],  # normal, timeout, error
)

# Conversation turns
TURNS_COMPLETED = Counter(
    "goassist_turns_completed_total",
    "Total conversation turns completed",
)

TURNS_TIMEOUT = Counter(
    "goassist_turns_timeout_total",
    "Turns that hit hard timeout (500ms)",
)

# Barge-in events
BARGE_IN_EVENTS = Counter(
    "goassist_barge_in_events_total",
    "Total barge-in events",
)

# Context rollover
CONTEXT_ROLLOVER = Counter(
    "goassist_context_rollover_total",
    "Context rollover events",
    ["status"],  # success, timeout, error
)

# Animation yield events (TMF §4.3)
ANIMATION_YIELD = Counter(
    "goassist_animation_yield_total",
    "Animation frames yielded due to lag",
)

# Backpressure events
BACKPRESSURE_EVENTS = Counter(
    "goassist_backpressure_events_total",
    "Backpressure policy activations",
    ["level"],  # animation_yield, verbosity_reduce, session_reject
)

# Errors
ERRORS = Counter(
    "goassist_errors_total",
    "Total errors by component",
    ["component", "type"],  # vad, asr, llm, tts, animation
)

# -----------------------------------------------------------------------------
# Gauges
# -----------------------------------------------------------------------------

# Active sessions
ACTIVE_SESSIONS = Gauge(
    "goassist_active_sessions",
    "Currently active sessions",
)

# Session states
SESSIONS_BY_STATE = Gauge(
    "goassist_sessions_by_state",
    "Sessions in each state",
    ["state"],  # idle, listening, thinking, speaking, interrupted
)

# Queue depth
SESSION_QUEUE_DEPTH = Gauge(
    "goassist_session_queue_depth",
    "Sessions waiting in queue",
)

# Resource utilization
VRAM_USAGE_BYTES = Gauge(
    "goassist_vram_usage_bytes",
    "GPU VRAM usage in bytes",
)

CONTEXT_TOKENS = Gauge(
    "goassist_context_tokens",
    "Current context window token count",
    ["session_id"],
)

# -----------------------------------------------------------------------------
# Info
# -----------------------------------------------------------------------------

BUILD_INFO = Info(
    "goassist_build",
    "Build information",
)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------


def record_ttfa(latency_ms: float) -> None:
    """Record TTFA latency in milliseconds."""
    TTFA_HISTOGRAM.observe(latency_ms / 1000.0)


def record_barge_in(latency_ms: float) -> None:
    """Record barge-in latency in milliseconds."""
    BARGE_IN_HISTOGRAM.observe(latency_ms / 1000.0)
    BARGE_IN_EVENTS.inc()


def record_turn_complete() -> None:
    """Record successful turn completion."""
    TURNS_COMPLETED.inc()


def record_turn_timeout() -> None:
    """Record turn timeout (>500ms)."""
    TURNS_TIMEOUT.inc()


def record_session_start() -> None:
    """Record session start."""
    SESSION_STARTED.inc()
    ACTIVE_SESSIONS.inc()


def record_session_end(reason: str = "normal") -> None:
    """Record session end."""
    SESSION_ENDED.labels(reason=reason).inc()
    ACTIVE_SESSIONS.dec()


def record_context_rollover(status: str = "success") -> None:
    """Record context rollover event."""
    CONTEXT_ROLLOVER.labels(status=status).inc()


def record_animation_yield() -> None:
    """Record animation frame yield due to lag."""
    ANIMATION_YIELD.inc()


def record_backpressure(level: str) -> None:
    """Record backpressure activation."""
    BACKPRESSURE_EVENTS.labels(level=level).inc()


def record_error(component: str, error_type: str) -> None:
    """Record error by component."""
    ERRORS.labels(component=component, type=error_type).inc()


def update_session_state(state: str, count: int) -> None:
    """Update sessions in state gauge."""
    SESSIONS_BY_STATE.labels(state=state).set(count)


def update_vram_usage(bytes_used: int) -> None:
    """Update VRAM usage gauge."""
    VRAM_USAGE_BYTES.set(bytes_used)


def update_context_tokens(session_id: str, tokens: int) -> None:
    """Update context token count for session."""
    CONTEXT_TOKENS.labels(session_id=session_id).set(tokens)


def set_build_info(version: str, commit: str, build_time: str) -> None:
    """Set build information."""
    BUILD_INFO.info({
        "version": version,
        "commit": commit,
        "build_time": build_time,
    })
