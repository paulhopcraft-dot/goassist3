"""SCOS - Session Control & Optimization Signals.

Non-emotional session signals for conversation optimization.
Reference: Implementation-v3.0.md §6

SCOS calculates:
- User speaking duration / cadence
- Interruption frequency
- Uncertainty indicators (ASR confidence dips)
- Conversation friction (repeats, "what?", low confidence)
- Engagement proxies (turn frequency, long silences)

SCOS outputs drive:
- Backchannel timing
- Verbosity adjustments
- Clarification strategy
- When to ask confirmation questions

IMPORTANT: SCOS MUST NOT:
- Label emotions ("angry", "sad")
- Attempt persuasion
- Track psychological state
"""

from dataclasses import dataclass, field
from typing import Callable

from src.audio.transport.audio_clock import get_audio_clock


@dataclass
class TurnMetrics:
    """Metrics for a single conversation turn."""

    turn_id: int
    user_speech_duration_ms: int = 0
    assistant_speech_duration_ms: int = 0
    asr_confidence: float = 1.0
    was_interrupted: bool = False
    silence_before_ms: int = 0
    word_count: int = 0


@dataclass
class SCOSSignals:
    """Session Control & Optimization Signals.

    These signals inform conversation strategy WITHOUT
    attempting emotional inference.
    """

    # Speaking patterns (objective measurements)
    avg_user_speech_ms: float = 0.0
    user_speech_variance: float = 0.0
    avg_silence_gap_ms: float = 0.0

    # Interruption patterns
    interruption_rate: float = 0.0  # Interruptions per turn
    consecutive_interruptions: int = 0

    # Uncertainty indicators
    avg_asr_confidence: float = 1.0
    low_confidence_turn_rate: float = 0.0  # % turns with confidence < 0.7

    # Friction indicators
    clarification_requests: int = 0  # User asked "what?" or similar
    repeat_requests: int = 0  # User asked to repeat
    consecutive_short_turns: int = 0  # User turns < 3 words

    # Engagement proxies
    turns_per_minute: float = 0.0
    avg_response_latency_ms: float = 0.0
    session_duration_ms: int = 0

    # Derived recommendations (not emotions!)
    should_reduce_verbosity: bool = False
    should_seek_confirmation: bool = False
    should_slow_down: bool = False
    suggested_backchannel_interval_ms: int = 3000


# Friction phrases that indicate communication issues
FRICTION_PHRASES = {
    "what",
    "what?",
    "huh",
    "huh?",
    "sorry",
    "sorry?",
    "pardon",
    "pardon?",
    "repeat",
    "say again",
    "didn't catch",
    "didn't hear",
    "come again",
    "one more time",
}


class SCOSCalculator:
    """Calculates Session Control & Optimization Signals.

    Tracks objective conversation metrics and derives
    behavioral recommendations WITHOUT emotional inference.

    Usage:
        scos = SCOSCalculator(session_id="session-123")

        # Record turn metrics
        scos.record_turn(TurnMetrics(...))

        # Get current signals
        signals = scos.get_signals()

        if signals.should_reduce_verbosity:
            # Shorten responses
            ...
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._turns: list[TurnMetrics] = []
        self._start_time_ms: int = 0
        self._last_turn_time_ms: int = 0

        # Running totals for efficiency
        self._total_user_speech_ms: int = 0
        self._total_silence_ms: int = 0
        self._total_confidence: float = 0.0
        self._low_confidence_turns: int = 0
        self._interruption_count: int = 0
        self._clarification_count: int = 0
        self._repeat_count: int = 0
        self._consecutive_short: int = 0
        self._consecutive_interrupts: int = 0

        # Callbacks
        self._on_signals_update: Callable[[SCOSSignals], None] | None = None

    def start(self) -> None:
        """Start SCOS tracking for session."""
        clock = get_audio_clock()
        self._start_time_ms = clock.get_absolute_ms()
        self._last_turn_time_ms = self._start_time_ms

    def record_turn(self, turn: TurnMetrics) -> None:
        """Record metrics for a completed turn.

        Args:
            turn: Turn metrics
        """
        self._turns.append(turn)

        # Update running totals
        self._total_user_speech_ms += turn.user_speech_duration_ms
        self._total_silence_ms += turn.silence_before_ms
        self._total_confidence += turn.asr_confidence

        if turn.asr_confidence < 0.7:
            self._low_confidence_turns += 1

        if turn.was_interrupted:
            self._interruption_count += 1
            self._consecutive_interrupts += 1
        else:
            self._consecutive_interrupts = 0

        # Track short turns
        if turn.word_count < 3:
            self._consecutive_short += 1
        else:
            self._consecutive_short = 0

        # Update timestamp
        clock = get_audio_clock()
        self._last_turn_time_ms = clock.get_absolute_ms()

    def record_user_text(self, text: str) -> None:
        """Analyze user text for friction indicators.

        Args:
            text: Transcribed user speech
        """
        text_lower = text.lower().strip()

        # Check for clarification requests
        if text_lower in FRICTION_PHRASES or any(
            phrase in text_lower for phrase in FRICTION_PHRASES
        ):
            if "repeat" in text_lower or "again" in text_lower:
                self._repeat_count += 1
            else:
                self._clarification_count += 1

    def get_signals(self) -> SCOSSignals:
        """Calculate current SCOS signals.

        Returns:
            Current SCOSSignals
        """
        n_turns = len(self._turns)
        if n_turns == 0:
            return SCOSSignals()

        clock = get_audio_clock()
        session_duration_ms = clock.get_absolute_ms() - self._start_time_ms

        # Calculate averages
        avg_user_speech = self._total_user_speech_ms / n_turns
        avg_silence = self._total_silence_ms / n_turns
        avg_confidence = self._total_confidence / n_turns

        # Calculate variance
        if n_turns > 1:
            variance = sum(
                (t.user_speech_duration_ms - avg_user_speech) ** 2
                for t in self._turns
            ) / (n_turns - 1)
        else:
            variance = 0.0

        # Calculate rates
        interruption_rate = self._interruption_count / n_turns
        low_confidence_rate = self._low_confidence_turns / n_turns

        # Calculate turns per minute
        if session_duration_ms > 0:
            turns_per_minute = (n_turns * 60_000) / session_duration_ms
        else:
            turns_per_minute = 0.0

        # Calculate average response latency (TTFA proxy)
        # This is simplified - real implementation would track actual TTFA
        avg_response_latency = 200.0  # Placeholder

        # Derive recommendations (based on objective metrics, NOT emotions)
        should_reduce_verbosity = (
            interruption_rate > 0.3  # User interrupts often
            or self._consecutive_interrupts >= 2  # Two in a row
            or self._consecutive_short >= 3  # Very short responses
        )

        should_seek_confirmation = (
            avg_confidence < 0.7  # Low ASR confidence
            or self._clarification_count >= 2  # Multiple clarifications
            or low_confidence_rate > 0.3  # Many low-confidence turns
        )

        should_slow_down = (
            self._repeat_count >= 2  # Multiple repeat requests
            or (avg_silence < 500 and turns_per_minute > 20)  # Rapid-fire
        )

        # Backchannel interval based on speaking patterns
        # Longer user speech → more frequent backchannels
        if avg_user_speech > 5000:
            backchannel_interval = 2000
        elif avg_user_speech > 3000:
            backchannel_interval = 2500
        else:
            backchannel_interval = 3000

        signals = SCOSSignals(
            avg_user_speech_ms=avg_user_speech,
            user_speech_variance=variance,
            avg_silence_gap_ms=avg_silence,
            interruption_rate=interruption_rate,
            consecutive_interruptions=self._consecutive_interrupts,
            avg_asr_confidence=avg_confidence,
            low_confidence_turn_rate=low_confidence_rate,
            clarification_requests=self._clarification_count,
            repeat_requests=self._repeat_count,
            consecutive_short_turns=self._consecutive_short,
            turns_per_minute=turns_per_minute,
            avg_response_latency_ms=avg_response_latency,
            session_duration_ms=session_duration_ms,
            should_reduce_verbosity=should_reduce_verbosity,
            should_seek_confirmation=should_seek_confirmation,
            should_slow_down=should_slow_down,
            suggested_backchannel_interval_ms=backchannel_interval,
        )

        # Notify callback if registered
        if self._on_signals_update:
            self._on_signals_update(signals)

        return signals

    def on_signals_update(
        self, callback: Callable[[SCOSSignals], None]
    ) -> None:
        """Register callback for signal updates.

        Args:
            callback: Function to call with updated signals
        """
        self._on_signals_update = callback

    def reset(self) -> None:
        """Reset all SCOS tracking."""
        self._turns.clear()
        self._total_user_speech_ms = 0
        self._total_silence_ms = 0
        self._total_confidence = 0.0
        self._low_confidence_turns = 0
        self._interruption_count = 0
        self._clarification_count = 0
        self._repeat_count = 0
        self._consecutive_short = 0
        self._consecutive_interrupts = 0

    @property
    def turn_count(self) -> int:
        """Number of turns recorded."""
        return len(self._turns)


def create_scos_calculator(session_id: str) -> SCOSCalculator:
    """Factory function to create SCOS calculator.

    Args:
        session_id: Session identifier

    Returns:
        Initialized SCOSCalculator
    """
    calculator = SCOSCalculator(session_id)
    calculator.start()
    return calculator
