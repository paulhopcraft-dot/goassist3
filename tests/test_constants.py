"""Tests for TMF v3.0 Constants.

Verifies all TMF contract values are correctly defined.
Reference: TMF-v3.0.md, Implementation-v3.0.md
"""

import pytest

from src.config.constants import TMF, TMFConstants


class TestTMFConstants:
    """Tests for TMFConstants class."""

    def test_is_frozen(self):
        """Constants are frozen (immutable)."""
        with pytest.raises(Exception):  # FrozenInstanceError
            TMF.TTFA_P95_MS = 999

    def test_singleton_instance(self):
        """TMF is a singleton instance."""
        assert isinstance(TMF, TMFConstants)


class TestLatencyContracts:
    """Tests for TMF §1.2 Latency Contracts."""

    def test_ttfa_p95(self):
        """TTFA p95 is 250ms per TMF §1.2."""
        assert TMF.TTFA_P95_MS == 250

    def test_ttfa_p50(self):
        """TTFA p50 target is 150ms."""
        assert TMF.TTFA_P50_MS == 150

    def test_barge_in(self):
        """Barge-in must complete in 150ms per TMF §4.2."""
        assert TMF.BARGE_IN_MS == 150

    def test_ttfa_p50_faster_than_p95(self):
        """P50 should be faster than P95."""
        assert TMF.TTFA_P50_MS < TMF.TTFA_P95_MS


class TestAudioPacketContract:
    """Tests for TMF §3.1 Audio Packet Contract."""

    def test_packet_duration(self):
        """Audio packets are 20ms per TMF §3.1."""
        assert TMF.AUDIO_PACKET_DURATION_MS == 20

    def test_overlap(self):
        """Overlap is 5ms for cross-fade."""
        assert TMF.AUDIO_OVERLAP_MS == 5

    def test_sample_rate(self):
        """Default sample rate is 16kHz for ASR."""
        assert TMF.AUDIO_SAMPLE_RATE == 16000

    def test_channels(self):
        """Audio is mono."""
        assert TMF.AUDIO_CHANNELS == 1


class TestContextManagement:
    """Tests for TMF §3.2 Context Management."""

    def test_max_context_tokens(self):
        """Hard context cap is 8192 tokens."""
        assert TMF.LLM_MAX_CONTEXT_TOKENS == 8192

    def test_rollover_threshold(self):
        """Rollover at 93.75% (7500/8192)."""
        assert TMF.CONTEXT_ROLLOVER_THRESHOLD == 7500
        # Verify it's actually ~93.75%
        ratio = TMF.CONTEXT_ROLLOVER_THRESHOLD / TMF.LLM_MAX_CONTEXT_TOKENS
        assert 0.90 < ratio < 0.95

    def test_summarization_timeout(self):
        """Summarization timeout is 5 seconds."""
        assert TMF.CONTEXT_SUMMARIZATION_TIMEOUT_S == 5.0


class TestAnimationThresholds:
    """Tests for TMF §4.2 Animation Thresholds."""

    def test_yield_lag(self):
        """Yield animation if lag exceeds 120ms per TMF §4.3."""
        assert TMF.ANIMATION_YIELD_LAG_MS == 120
        assert TMF.ANIMATION_YIELD_THRESHOLD_MS == 120  # Alias

    def test_slow_freeze(self):
        """Slow freeze duration is 150ms."""
        assert TMF.ANIMATION_SLOW_FREEZE_MS == 150
        assert TMF.ANIMATION_FREEZE_DURATION_MS == 150  # Alias

    def test_heartbeat_threshold(self):
        """Heartbeat threshold is 100ms."""
        assert TMF.ANIMATION_HEARTBEAT_THRESHOLD_MS == 100
        assert TMF.ANIMATION_FREEZE_THRESHOLD_MS == 100  # Alias

    def test_target_fps(self):
        """Target animation FPS is 30."""
        assert TMF.ANIMATION_TARGET_FPS == 30


class TestBackpressureThresholds:
    """Tests for TMF §5.2 Backpressure Thresholds."""

    def test_vram_headroom(self):
        """Reserved VRAM headroom is 4GB."""
        assert TMF.VRAM_HEADROOM_GB == 4

    def test_vram_warning(self):
        """Warn at 90% VRAM usage."""
        assert TMF.VRAM_WARNING_THRESHOLD_PERCENT == 0.90


class TestTurnDetection:
    """Tests for TMF §6 Turn Detection."""

    def test_endpoint_budget(self):
        """Endpoint detection budget is 15ms."""
        assert TMF.TURN_ENDPOINT_BUDGET_MS == 15

    def test_hard_timeout(self):
        """Hard timeout is 500ms per TMF §6.1."""
        assert TMF.TURN_HARD_TIMEOUT_MS == 500


class TestSoakTest:
    """Tests for TMF §7.3 Soak Test."""

    def test_duration(self):
        """Soak test duration is 24 hours."""
        assert TMF.SOAK_DURATION_HOURS == 24

    def test_duty_cycle(self):
        """Duty cycle is 30%."""
        assert TMF.SOAK_DUTY_CYCLE_PERCENT == 0.30


class TestSessionDefaults:
    """Tests for session default values."""

    def test_max_concurrent_sessions(self):
        """Max concurrent sessions per node."""
        assert TMF.MAX_CONCURRENT_SESSIONS == 100

    def test_idle_timeout(self):
        """Idle timeout is 5 minutes."""
        assert TMF.SESSION_IDLE_TIMEOUT_S == 300

    def test_max_duration(self):
        """Max session duration is 1 hour."""
        assert TMF.SESSION_MAX_DURATION_S == 3600

    def test_warmup_turns(self):
        """Warmup is 3 turns."""
        assert TMF.SESSION_WARMUP_TURNS == 3

    def test_warmup_seconds(self):
        """Warmup is 60 seconds."""
        assert TMF.SESSION_WARMUP_SECONDS == 60


class TestSCOS:
    """Tests for SCOS (Session Control & Optimization Signals)."""

    def test_confidence_threshold(self):
        """Low confidence threshold is 0.6."""
        assert TMF.SCOS_CONFIDENCE_LOW_THRESHOLD == 0.6

    def test_friction_window(self):
        """Repeat detection window is 30 seconds."""
        assert TMF.SCOS_FRICTION_REPEAT_WINDOW_S == 30


class TestContractRelationships:
    """Tests for relationships between contracts."""

    def test_barge_in_within_ttfa(self):
        """Barge-in must complete within TTFA budget."""
        assert TMF.BARGE_IN_MS <= TMF.TTFA_P95_MS

    def test_animation_yield_before_barge_in(self):
        """Animation yields before barge-in timeout."""
        assert TMF.ANIMATION_YIELD_LAG_MS < TMF.BARGE_IN_MS

    def test_animation_freeze_before_yield(self):
        """Heartbeat threshold before yield threshold."""
        assert TMF.ANIMATION_HEARTBEAT_THRESHOLD_MS < TMF.ANIMATION_YIELD_LAG_MS

    def test_endpoint_budget_small(self):
        """Endpoint budget is small fraction of TTFA."""
        assert TMF.TURN_ENDPOINT_BUDGET_MS < TMF.TTFA_P95_MS * 0.1

    def test_rollover_before_max(self):
        """Rollover triggers before hitting max context."""
        assert TMF.CONTEXT_ROLLOVER_THRESHOLD < TMF.LLM_MAX_CONTEXT_TOKENS

    def test_warmup_turns_reasonable(self):
        """Warmup turns is a small number."""
        assert 1 <= TMF.SESSION_WARMUP_TURNS <= 10
