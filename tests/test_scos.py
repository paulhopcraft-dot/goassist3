"""Tests for SCOS - Session Control & Optimization Signals.

Tests objective conversation metrics WITHOUT emotional inference.
Reference: Implementation-v3.0.md §6
"""

import pytest

from src.orchestrator.scos import (
    TurnMetrics,
    SCOSSignals,
    SCOSCalculator,
    FRICTION_PHRASES,
    create_scos_calculator,
)
from src.audio.transport.audio_clock import get_audio_clock


class TestTurnMetrics:
    """Tests for TurnMetrics dataclass."""

    def test_default_metrics(self):
        """Default metrics have sensible values."""
        metrics = TurnMetrics(turn_id=1)
        assert metrics.turn_id == 1
        assert metrics.user_speech_duration_ms == 0
        assert metrics.assistant_speech_duration_ms == 0
        assert metrics.asr_confidence == 1.0
        assert metrics.was_interrupted is False
        assert metrics.silence_before_ms == 0
        assert metrics.word_count == 0

    def test_custom_metrics(self):
        """Custom metrics are applied."""
        metrics = TurnMetrics(
            turn_id=5,
            user_speech_duration_ms=2500,
            assistant_speech_duration_ms=3000,
            asr_confidence=0.85,
            was_interrupted=True,
            silence_before_ms=500,
            word_count=15,
        )
        assert metrics.turn_id == 5
        assert metrics.user_speech_duration_ms == 2500
        assert metrics.assistant_speech_duration_ms == 3000
        assert metrics.asr_confidence == 0.85
        assert metrics.was_interrupted is True
        assert metrics.silence_before_ms == 500
        assert metrics.word_count == 15


class TestSCOSSignals:
    """Tests for SCOSSignals dataclass."""

    def test_default_signals(self):
        """Default signals have sensible values."""
        signals = SCOSSignals()
        assert signals.avg_user_speech_ms == 0.0
        assert signals.user_speech_variance == 0.0
        assert signals.avg_silence_gap_ms == 0.0
        assert signals.interruption_rate == 0.0
        assert signals.consecutive_interruptions == 0
        assert signals.avg_asr_confidence == 1.0
        assert signals.low_confidence_turn_rate == 0.0
        assert signals.clarification_requests == 0
        assert signals.repeat_requests == 0
        assert signals.consecutive_short_turns == 0
        assert signals.turns_per_minute == 0.0
        assert signals.avg_response_latency_ms == 0.0
        assert signals.session_duration_ms == 0
        assert signals.should_reduce_verbosity is False
        assert signals.should_seek_confirmation is False
        assert signals.should_slow_down is False
        assert signals.suggested_backchannel_interval_ms == 3000

    def test_recommendation_flags(self):
        """Recommendation flags can be set."""
        signals = SCOSSignals(
            should_reduce_verbosity=True,
            should_seek_confirmation=True,
            should_slow_down=True,
        )
        assert signals.should_reduce_verbosity is True
        assert signals.should_seek_confirmation is True
        assert signals.should_slow_down is True


class TestFrictionPhrases:
    """Tests for friction phrase detection."""

    def test_friction_phrases_exist(self):
        """Friction phrases are defined."""
        assert len(FRICTION_PHRASES) > 0

    def test_common_friction_phrases(self):
        """Common friction phrases are included."""
        assert "what?" in FRICTION_PHRASES
        assert "huh?" in FRICTION_PHRASES
        assert "repeat" in FRICTION_PHRASES
        assert "say again" in FRICTION_PHRASES
        assert "didn't hear" in FRICTION_PHRASES

    def test_pardon_included(self):
        """Pardon variants are included."""
        assert "pardon" in FRICTION_PHRASES
        assert "pardon?" in FRICTION_PHRASES


class TestSCOSCalculator:
    """Tests for SCOSCalculator."""

    @pytest.fixture
    def scos(self):
        """Create SCOS calculator with registered session."""
        clock = get_audio_clock()
        session_id = "test-scos"
        clock.start_session(session_id)
        calculator = SCOSCalculator(session_id)
        calculator.start()
        yield calculator
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    def test_init_empty(self, scos):
        """New calculator has no turns."""
        assert scos.turn_count == 0

    def test_record_turn(self, scos):
        """Recording turn increments count."""
        turn = TurnMetrics(
            turn_id=1,
            user_speech_duration_ms=2000,
            asr_confidence=0.9,
        )
        scos.record_turn(turn)
        assert scos.turn_count == 1

    def test_record_multiple_turns(self, scos):
        """Recording multiple turns works."""
        for i in range(5):
            turn = TurnMetrics(
                turn_id=i,
                user_speech_duration_ms=1000 * (i + 1),
                asr_confidence=0.8,
            )
            scos.record_turn(turn)
        assert scos.turn_count == 5

    def test_get_signals_no_turns(self, scos):
        """Get signals returns defaults with no turns."""
        signals = scos.get_signals()
        assert signals.avg_user_speech_ms == 0.0
        assert signals.turns_per_minute == 0.0

    def test_get_signals_with_turns(self, scos):
        """Get signals calculates averages correctly."""
        scos.record_turn(TurnMetrics(turn_id=1, user_speech_duration_ms=1000))
        scos.record_turn(TurnMetrics(turn_id=2, user_speech_duration_ms=2000))
        scos.record_turn(TurnMetrics(turn_id=3, user_speech_duration_ms=3000))

        signals = scos.get_signals()
        assert signals.avg_user_speech_ms == 2000.0  # (1000+2000+3000)/3

    def test_interruption_tracking(self, scos):
        """Interruption rate is calculated correctly."""
        # 2 out of 4 turns are interruptions
        scos.record_turn(TurnMetrics(turn_id=1, was_interrupted=True))
        scos.record_turn(TurnMetrics(turn_id=2, was_interrupted=False))
        scos.record_turn(TurnMetrics(turn_id=3, was_interrupted=True))
        scos.record_turn(TurnMetrics(turn_id=4, was_interrupted=False))

        signals = scos.get_signals()
        assert signals.interruption_rate == 0.5  # 2/4

    def test_consecutive_interruptions(self, scos):
        """Consecutive interruptions are tracked."""
        scos.record_turn(TurnMetrics(turn_id=1, was_interrupted=True))
        scos.record_turn(TurnMetrics(turn_id=2, was_interrupted=True))
        scos.record_turn(TurnMetrics(turn_id=3, was_interrupted=True))

        signals = scos.get_signals()
        assert signals.consecutive_interruptions == 3

    def test_consecutive_interruptions_reset(self, scos):
        """Consecutive interruptions reset on non-interrupt."""
        scos.record_turn(TurnMetrics(turn_id=1, was_interrupted=True))
        scos.record_turn(TurnMetrics(turn_id=2, was_interrupted=True))
        scos.record_turn(TurnMetrics(turn_id=3, was_interrupted=False))  # Reset

        signals = scos.get_signals()
        assert signals.consecutive_interruptions == 0

    def test_low_confidence_tracking(self, scos):
        """Low confidence turns are tracked."""
        scos.record_turn(TurnMetrics(turn_id=1, asr_confidence=0.9))
        scos.record_turn(TurnMetrics(turn_id=2, asr_confidence=0.5))  # Low
        scos.record_turn(TurnMetrics(turn_id=3, asr_confidence=0.6))  # Low
        scos.record_turn(TurnMetrics(turn_id=4, asr_confidence=0.8))

        signals = scos.get_signals()
        assert signals.low_confidence_turn_rate == 0.5  # 2/4

    def test_short_turns_tracking(self, scos):
        """Short turns are tracked."""
        scos.record_turn(TurnMetrics(turn_id=1, word_count=2))  # Short
        scos.record_turn(TurnMetrics(turn_id=2, word_count=1))  # Short
        scos.record_turn(TurnMetrics(turn_id=3, word_count=2))  # Short

        signals = scos.get_signals()
        assert signals.consecutive_short_turns == 3

    def test_short_turns_reset(self, scos):
        """Short turns reset on longer turn."""
        scos.record_turn(TurnMetrics(turn_id=1, word_count=1))  # Short
        scos.record_turn(TurnMetrics(turn_id=2, word_count=2))  # Short
        scos.record_turn(TurnMetrics(turn_id=3, word_count=10))  # Long - reset

        signals = scos.get_signals()
        assert signals.consecutive_short_turns == 0

    def test_reset_clears_all(self, scos):
        """Reset clears all tracking."""
        scos.record_turn(TurnMetrics(turn_id=1, user_speech_duration_ms=1000))
        scos.record_turn(TurnMetrics(turn_id=2, was_interrupted=True))
        scos.reset()

        assert scos.turn_count == 0
        signals = scos.get_signals()
        assert signals.avg_user_speech_ms == 0.0


class TestSCOSRecommendations:
    """Tests for SCOS behavioral recommendations."""

    @pytest.fixture
    def scos(self):
        """Create SCOS calculator."""
        clock = get_audio_clock()
        session_id = "test-recommendations"
        clock.start_session(session_id)
        calculator = SCOSCalculator(session_id)
        calculator.start()
        yield calculator
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    def test_reduce_verbosity_high_interruption_rate(self, scos):
        """Should reduce verbosity when interruption rate > 0.3."""
        # 4/10 = 0.4 interruption rate
        for i in range(10):
            scos.record_turn(TurnMetrics(
                turn_id=i,
                was_interrupted=(i < 4),
            ))

        signals = scos.get_signals()
        assert signals.should_reduce_verbosity is True

    def test_reduce_verbosity_consecutive_interrupts(self, scos):
        """Should reduce verbosity with 2+ consecutive interrupts."""
        scos.record_turn(TurnMetrics(turn_id=1, was_interrupted=True))
        scos.record_turn(TurnMetrics(turn_id=2, was_interrupted=True))

        signals = scos.get_signals()
        assert signals.should_reduce_verbosity is True

    def test_reduce_verbosity_short_turns(self, scos):
        """Should reduce verbosity with 3+ consecutive short turns."""
        for i in range(4):
            scos.record_turn(TurnMetrics(turn_id=i, word_count=2))

        signals = scos.get_signals()
        assert signals.should_reduce_verbosity is True

    def test_no_reduce_verbosity_normal(self, scos):
        """Should not reduce verbosity in normal conversation."""
        for i in range(5):
            scos.record_turn(TurnMetrics(
                turn_id=i,
                word_count=10,
                was_interrupted=False,
            ))

        signals = scos.get_signals()
        assert signals.should_reduce_verbosity is False

    def test_seek_confirmation_low_confidence(self, scos):
        """Should seek confirmation when avg confidence < 0.7."""
        for i in range(5):
            scos.record_turn(TurnMetrics(turn_id=i, asr_confidence=0.5))

        signals = scos.get_signals()
        assert signals.should_seek_confirmation is True

    def test_seek_confirmation_clarifications(self, scos):
        """Should seek confirmation with multiple clarifications."""
        scos.record_turn(TurnMetrics(turn_id=1, asr_confidence=0.9))
        scos.record_user_text("what?")
        scos.record_user_text("huh?")

        signals = scos.get_signals()
        assert signals.should_seek_confirmation is True

    def test_slow_down_repeat_requests(self, scos):
        """Should slow down with repeat requests."""
        scos.record_turn(TurnMetrics(turn_id=1))
        scos.record_user_text("can you repeat that")
        scos.record_user_text("say again please")

        signals = scos.get_signals()
        assert signals.should_slow_down is True


class TestSCOSTextAnalysis:
    """Tests for user text analysis."""

    @pytest.fixture
    def scos(self):
        """Create SCOS calculator with initial turn."""
        clock = get_audio_clock()
        session_id = "test-text"
        clock.start_session(session_id)
        calculator = SCOSCalculator(session_id)
        calculator.start()
        # Record initial turn so get_signals() doesn't return defaults
        calculator.record_turn(TurnMetrics(turn_id=0))
        yield calculator
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    def test_detect_clarification_what(self, scos):
        """Detects 'what' as clarification."""
        scos.record_user_text("what?")
        signals = scos.get_signals()
        assert signals.clarification_requests == 1

    def test_detect_clarification_huh(self, scos):
        """Detects 'huh' as clarification."""
        scos.record_user_text("huh")
        signals = scos.get_signals()
        assert signals.clarification_requests == 1

    def test_detect_repeat_request(self, scos):
        """Detects repeat requests separately."""
        scos.record_user_text("can you repeat that")
        signals = scos.get_signals()
        assert signals.repeat_requests == 1
        assert signals.clarification_requests == 0

    def test_detect_say_again(self, scos):
        """Detects 'say again' as repeat request."""
        scos.record_user_text("say again please")
        signals = scos.get_signals()
        assert signals.repeat_requests == 1

    def test_case_insensitive(self, scos):
        """Detection is case insensitive."""
        scos.record_user_text("WHAT?")
        signals = scos.get_signals()
        assert signals.clarification_requests == 1

    def test_normal_text_not_friction(self, scos):
        """Normal text is not detected as friction."""
        scos.record_user_text("I would like to schedule an appointment")
        signals = scos.get_signals()
        assert signals.clarification_requests == 0
        assert signals.repeat_requests == 0


class TestSCOSBackchannelInterval:
    """Tests for backchannel interval calculation."""

    @pytest.fixture
    def scos(self):
        """Create SCOS calculator."""
        clock = get_audio_clock()
        session_id = "test-backchannel"
        clock.start_session(session_id)
        calculator = SCOSCalculator(session_id)
        calculator.start()
        yield calculator
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    def test_long_speech_short_interval(self, scos):
        """Long user speech gets shorter backchannel interval."""
        # Average speech > 5000ms
        for i in range(3):
            scos.record_turn(TurnMetrics(turn_id=i, user_speech_duration_ms=6000))

        signals = scos.get_signals()
        assert signals.suggested_backchannel_interval_ms == 2000

    def test_medium_speech_medium_interval(self, scos):
        """Medium user speech gets medium backchannel interval."""
        # Average speech 3000-5000ms
        for i in range(3):
            scos.record_turn(TurnMetrics(turn_id=i, user_speech_duration_ms=4000))

        signals = scos.get_signals()
        assert signals.suggested_backchannel_interval_ms == 2500

    def test_short_speech_long_interval(self, scos):
        """Short user speech gets longer backchannel interval."""
        # Average speech < 3000ms
        for i in range(3):
            scos.record_turn(TurnMetrics(turn_id=i, user_speech_duration_ms=1500))

        signals = scos.get_signals()
        assert signals.suggested_backchannel_interval_ms == 3000


class TestSCOSCallback:
    """Tests for SCOS signal update callback."""

    @pytest.fixture
    def scos(self):
        """Create SCOS calculator."""
        clock = get_audio_clock()
        session_id = "test-callback"
        clock.start_session(session_id)
        calculator = SCOSCalculator(session_id)
        calculator.start()
        yield calculator
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    def test_callback_called_on_get_signals(self, scos):
        """Callback is called when getting signals."""
        received_signals = []

        def callback(signals):
            received_signals.append(signals)

        scos.on_signals_update(callback)
        scos.record_turn(TurnMetrics(turn_id=1))
        scos.get_signals()

        assert len(received_signals) == 1
        assert isinstance(received_signals[0], SCOSSignals)


class TestCreateSCOSFactory:
    """Tests for create_scos_calculator factory function."""

    @pytest.fixture(autouse=True)
    def setup_session(self):
        clock = get_audio_clock()
        clock.start_session("factory-scos")
        yield
        try:
            clock.end_session("factory-scos")
        except KeyError:
            pass

    def test_creates_calculator(self):
        """Factory creates and starts calculator."""
        calculator = create_scos_calculator("factory-scos")
        assert isinstance(calculator, SCOSCalculator)

    def test_factory_starts_calculator(self):
        """Factory starts the calculator."""
        calculator = create_scos_calculator("factory-scos")
        # start() sets _start_time_ms
        assert calculator._start_time_ms > 0
