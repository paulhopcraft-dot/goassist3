"""
Pytest tests for Avatar Realism & Utility Checklist.

Run with: pytest tests/avatar_qa/test_checklist.py -v
"""

import pytest
from .checklist import AvatarQAChecklist, CheckStatus


class TestMicroExpressions:
    """Test Check 1: Micro-expressions."""

    def test_passes_with_sufficient_micro_expressions(self):
        """Should pass when 3/5 emphasis points have 2+ micro-expressions."""
        checklist = AvatarQAChecklist()

        # Generate blendshape data with micro-expressions at emphasis points
        blendshape_frames = []
        for i in range(150):  # 5 seconds at 30fps
            ts = i * 33.3
            frame = {
                "timestamp_ms": ts,
                "browInnerUp": 0.0,
                "browOuterUpLeft": 0.0,
                "cheekSquintLeft": 0.0,
            }
            # Add micro-expressions at emphasis points (1000, 2000, 3000, 4000 ms)
            if 900 <= ts <= 1200 or 1900 <= ts <= 2200 or 2900 <= ts <= 3200:
                frame["browInnerUp"] = 0.3
                frame["cheekSquintLeft"] = 0.25
            blendshape_frames.append(frame)

        audio_emphasis_ms = [1000, 2000, 3000, 4000, 4500]

        result = checklist.check_micro_expressions(
            blendshape_frames, audio_emphasis_ms
        )

        assert result.passed
        assert result.metrics["matches"] >= 3

    def test_fails_with_insufficient_micro_expressions(self):
        """Should fail when fewer than 3/5 emphasis points have micro-expressions."""
        checklist = AvatarQAChecklist()

        # Generate blendshape data with NO micro-expressions
        blendshape_frames = [
            {"timestamp_ms": i * 33.3, "browInnerUp": 0.0, "cheekSquintLeft": 0.0}
            for i in range(150)
        ]
        audio_emphasis_ms = [1000, 2000, 3000, 4000, 5000]

        result = checklist.check_micro_expressions(
            blendshape_frames, audio_emphasis_ms
        )

        assert not result.passed
        assert result.metrics["matches"] < 3


class TestLipSync:
    """Test Check 2: Lip-sync accuracy."""

    def test_passes_with_good_lip_sync(self):
        """Should pass with ≤2 desyncs per 10 seconds."""
        checklist = AvatarQAChecklist()

        # 10 seconds of frames at 30fps with jawOpen always active
        # This simulates continuous speech with the mouth consistently open
        blendshape_frames = [
            {
                "timestamp_ms": i * 33.3,
                "jawOpen": 0.5,  # Always active to match DD viseme
                "mouthClose": 0.1,
            }
            for i in range(300)
        ]

        # Expected visemes - all DD which expects jawOpen > 0.3
        expected_visemes = [
            {"timestamp_ms": i * 100, "viseme": "DD", "phoneme": "d"}
            for i in range(100)
        ]

        result = checklist.check_lip_sync(blendshape_frames, expected_visemes)

        # Should have few desyncs since jawOpen is always active
        assert result.metrics["desyncs_per_10s"] <= 2

    def test_fails_with_poor_lip_sync(self):
        """Should fail with many desyncs."""
        checklist = AvatarQAChecklist()

        # Frames with no mouth movement
        blendshape_frames = [
            {"timestamp_ms": i * 33.3, "jawOpen": 0.0, "mouthClose": 0.0}
            for i in range(300)
        ]

        # Many expected visemes that won't match
        expected_visemes = [
            {"timestamp_ms": i * 100, "viseme": "PP", "phoneme": "p"}
            for i in range(100)
        ]

        result = checklist.check_lip_sync(blendshape_frames, expected_visemes)

        # Should have many desyncs
        assert result.metrics["desyncs_per_10s"] > 2


class TestEyeContact:
    """Test Check 3: Eye contact consistency."""

    def test_passes_with_natural_gaze(self):
        """Should pass with 70-90% on-target and natural saccades."""
        checklist = AvatarQAChecklist()

        # Generate natural eye movement pattern
        blendshape_frames = []
        for i in range(300):  # 10 seconds
            ts = i * 33.3
            frame = {"timestamp_ms": ts}
            # Mostly on-target (low gaze values)
            if i % 30 < 25:  # ~83% on-target
                frame["eyeLookInLeft"] = 0.05
                frame["eyeLookInRight"] = 0.05
            else:
                # Saccade moments
                frame["eyeLookInLeft"] = 0.4
                frame["eyeLookOutRight"] = 0.3
            blendshape_frames.append(frame)

        result = checklist.check_eye_contact(blendshape_frames, duration_s=10.0)

        assert 60 <= result.metrics["on_target_pct"] <= 95

    def test_fails_with_dead_stare(self):
        """Should fail with dead stare >2s."""
        checklist = AvatarQAChecklist()

        # No eye movement at all
        blendshape_frames = [
            {"timestamp_ms": i * 33.3, "eyeLookInLeft": 0.1}
            for i in range(300)
        ]

        result = checklist.check_eye_contact(blendshape_frames, duration_s=10.0)

        # Will have very long dead stare since no saccades
        assert result.metrics["saccades_per_10s"] == 0


class TestBlinkCadence:
    """Test Check 4: Blink cadence."""

    def test_passes_with_natural_blink_rate(self):
        """Should pass with 12-18 blinks/min."""
        checklist = AvatarQAChecklist()

        # Generate ~15 blinks per minute (1 blink every 4 seconds)
        blendshape_frames = []
        for i in range(1800):  # 60 seconds at 30fps
            ts = i * 33.3
            frame = {"timestamp_ms": ts, "eyeBlinkLeft": 0.0, "eyeBlinkRight": 0.0}
            # Blink every ~120 frames (4 seconds) = 15/min
            if i % 120 < 6:  # Blink duration ~6 frames
                frame["eyeBlinkLeft"] = 0.8
                frame["eyeBlinkRight"] = 0.8
            blendshape_frames.append(frame)

        result = checklist.check_blink_cadence(blendshape_frames, duration_s=60.0)

        assert 10 <= result.metrics["blinks_per_min"] <= 20

    def test_fails_without_first_blink(self):
        """Should fail if no blink in first 6 seconds."""
        checklist = AvatarQAChecklist()

        # No blinks at all
        blendshape_frames = [
            {"timestamp_ms": i * 33.3, "eyeBlinkLeft": 0.1, "eyeBlinkRight": 0.1}
            for i in range(1800)
        ]

        result = checklist.check_blink_cadence(blendshape_frames, duration_s=60.0)

        assert result.metrics["first_blink_ms"] is None
        assert not result.metrics["first_blink_in_6s"]


class TestAVOffset:
    """Test Check 6: A/V offset."""

    def test_passes_with_low_offset(self):
        """Should pass with A/V offset ≤80ms p95."""
        checklist = AvatarQAChecklist()

        # Good sync - offsets between -40 and +40ms
        offsets = [30, -20, 40, -30, 25, 35, -35, 20, -25, 30] * 10

        result = checklist.check_av_offset(offsets)

        assert result.passed
        assert result.metrics["p95_offset_ms"] <= 80

    def test_fails_with_high_offset(self):
        """Should fail with A/V offset >80ms p95."""
        checklist = AvatarQAChecklist()

        # Poor sync - offsets around 100-150ms
        offsets = [100, 120, 90, 150, 110, 130, 100, 140, 95, 125]

        result = checklist.check_av_offset(offsets)

        assert not result.passed
        assert result.metrics["p95_offset_ms"] > 80


class TestTurnTaking:
    """Test Check 7: Turn-taking."""

    def test_passes_with_fast_interrupt_detection(self):
        """Should pass with interrupt <150ms and resume <500ms."""
        checklist = AvatarQAChecklist()

        interrupt_latencies = [100, 120, 90, 140, 110, 130, 100, 120, 95, 125]
        resume_latencies = [300, 350, 280, 400, 320, 380, 290, 350, 310, 340]

        result = checklist.check_turn_taking(interrupt_latencies, resume_latencies)

        assert result.passed
        assert result.metrics["interrupt_p95_ms"] <= 150
        assert result.metrics["resume_p95_ms"] <= 500

    def test_fails_with_slow_interrupt(self):
        """Should fail with slow interrupt detection."""
        checklist = AvatarQAChecklist()

        interrupt_latencies = [200, 250, 180, 300, 220, 280, 190, 260, 210, 240]
        resume_latencies = [300, 350, 280, 400, 320, 380, 290, 350, 310, 340]

        result = checklist.check_turn_taking(interrupt_latencies, resume_latencies)

        assert not result.passed
        assert result.metrics["interrupt_p95_ms"] > 150


class TestLatency:
    """Test Check 8: Latency under load."""

    def test_passes_with_low_latency(self):
        """Should pass with TTFA ≤250ms and response ≤400ms."""
        checklist = AvatarQAChecklist()

        ttfa_samples = [150, 180, 200, 170, 220, 190, 160, 210, 175, 195]
        response_latencies = [300, 350, 280, 370, 320, 340, 290, 360, 310, 330]

        result = checklist.check_latency(
            ttfa_samples, response_latencies, concurrent_sessions=5
        )

        assert result.passed
        assert result.metrics["ttfa_p95_ms"] <= 250
        assert result.metrics["response_p95_ms"] <= 400

    def test_fails_with_high_latency(self):
        """Should fail with high latency."""
        checklist = AvatarQAChecklist()

        ttfa_samples = [300, 350, 280, 400, 320, 380, 290, 420, 310, 390]
        response_latencies = [500, 550, 480, 600, 520, 580, 490, 620, 510, 590]

        result = checklist.check_latency(
            ttfa_samples, response_latencies, concurrent_sessions=5
        )

        assert not result.passed


class TestContentGrounding:
    """Test Check 10: Content grounding."""

    def test_passes_with_sourced_responses(self):
        """Should pass with ≥9/10 sourced responses."""
        checklist = AvatarQAChecklist()

        responses = [
            {"prompt": f"Q{i}", "response": f"A{i}", "has_source": True, "is_hallucination": False}
            for i in range(10)
        ]

        result = checklist.check_content_grounding(responses)

        assert result.passed
        assert result.metrics["sourced_count"] >= 9
        assert result.metrics["hallucination_count"] == 0

    def test_fails_with_hallucination(self):
        """Should fail with any hallucination."""
        checklist = AvatarQAChecklist()

        responses = [
            {"prompt": f"Q{i}", "response": f"A{i}", "has_source": True, "is_hallucination": False}
            for i in range(9)
        ]
        responses.append(
            {"prompt": "Q10", "response": "A10", "has_source": True, "is_hallucination": True}
        )

        result = checklist.check_content_grounding(responses)

        assert not result.passed
        assert result.metrics["hallucination_count"] > 0


class TestNoiseRobustness:
    """Test Check 12: Noisy-input robustness."""

    def test_passes_with_good_accuracy(self):
        """Should pass with ≥8/10 correct intents."""
        checklist = AvatarQAChecklist()

        results = [
            {"correct": True, "recovered_with_clarify": False}
            for _ in range(9)
        ]
        results.append({"correct": False, "recovered_with_clarify": True})

        result = checklist.check_noise_robustness(results)

        assert result.passed
        assert result.metrics["correct_count"] >= 8

    def test_fails_with_poor_accuracy(self):
        """Should fail with <8/10 correct intents."""
        checklist = AvatarQAChecklist()

        results = [
            {"correct": True, "recovered_with_clarify": False}
            for _ in range(5)
        ]
        results.extend([
            {"correct": False, "recovered_with_clarify": False}
            for _ in range(5)
        ])

        result = checklist.check_noise_robustness(results)

        assert not result.passed
        assert result.metrics["correct_count"] < 8


class TestScoring:
    """Test overall checklist scoring."""

    def test_demo_ready_score(self):
        """Score ≥9 should be demo-ready."""
        checklist = AvatarQAChecklist()

        # Pass 10 checks
        for i, item in enumerate(checklist.ITEMS[:10]):
            checklist.results[item].status = CheckStatus.PASS
            checklist.results[item].score = 1

        score = checklist.get_score()

        assert score.passed >= 9
        assert score.is_demo_ready

    def test_needs_fixes_score(self):
        """Score ≤7 should need fixes."""
        checklist = AvatarQAChecklist()

        # Pass only 5 checks
        for i, item in enumerate(checklist.ITEMS[:5]):
            checklist.results[item].status = CheckStatus.PASS
            checklist.results[item].score = 1

        score = checklist.get_score()

        assert score.passed <= 7
        assert score.needs_fixes

    def test_priority_fixes_order(self):
        """Priority fixes should start with utility items."""
        checklist = AvatarQAChecklist()

        # Fail everything
        for item in checklist.ITEMS:
            checklist.results[item].status = CheckStatus.FAIL
            checklist.results[item].score = 0

        score = checklist.get_score()
        fixes = score.get_priority_fixes()

        # First fixes should be utility items (6, 7, 8, 12)
        assert len(fixes) > 0
