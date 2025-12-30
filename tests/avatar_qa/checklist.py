"""
Avatar Realism & Utility Checklist Implementation

12-point pass/fail scoring system for avatar quality assessment.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class CheckStatus(Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    """Result of a single checklist item evaluation."""

    name: str
    status: CheckStatus
    score: int  # 1 for pass, 0 for fail
    details: str = ""
    metrics: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASS


@dataclass
class ChecklistScore:
    """Overall checklist scoring."""

    total: int
    passed: int
    failed: int
    skipped: int
    results: list[CheckResult]

    @property
    def score(self) -> str:
        return f"{self.passed}/{self.total}"

    @property
    def is_demo_ready(self) -> bool:
        return self.passed >= 9

    @property
    def needs_fixes(self) -> bool:
        return self.passed <= 7

    def get_priority_fixes(self) -> list[str]:
        """Return priority items to fix based on score."""
        if not self.needs_fixes:
            return []

        # Utility first: 6, 7, 8, 12
        # Realism second: 2, 3, 5
        priority_order = [6, 7, 8, 12, 2, 3, 5, 1, 4, 9, 10, 11]
        failed_items = [r.name for r in self.results if not r.passed]

        return [
            name
            for idx in priority_order
            for name in failed_items
            if name.startswith(f"{idx}.")
        ]


class AvatarQAChecklist:
    """
    12-Point Avatar Realism & Utility Checklist.

    Usage:
        checklist = AvatarQAChecklist()
        checklist.check_micro_expressions(blendshape_data, audio_emphasis)
        checklist.check_lip_sync(blendshape_data, audio_data)
        ...
        score = checklist.get_score()
        print(f"Score: {score.score}, Demo-ready: {score.is_demo_ready}")
    """

    ITEMS = [
        "1. Micro-expressions",
        "2. Lip-sync accuracy",
        "3. Eye contact consistency",
        "4. Blink cadence",
        "5. Head pose dynamics",
        "6. Voice-to-lip sync (A/V offset)",
        "7. Turn-taking (barge-in)",
        "8. Latency under load",
        "9. Prosody & emphasis",
        "10. Content grounding",
        "11. Fallback behaviors",
        "12. Noisy-input robustness",
    ]

    def __init__(self):
        self.results: dict[str, CheckResult] = {}
        self._initialize_pending()

    def _initialize_pending(self):
        """Initialize all items as pending."""
        for item in self.ITEMS:
            self.results[item] = CheckResult(
                name=item, status=CheckStatus.PENDING, score=0
            )

    def _record_result(
        self,
        item: str,
        passed: bool,
        details: str = "",
        metrics: Optional[dict] = None,
    ) -> CheckResult:
        """Record a check result."""
        result = CheckResult(
            name=item,
            status=CheckStatus.PASS if passed else CheckStatus.FAIL,
            score=1 if passed else 0,
            details=details,
            metrics=metrics or {},
        )
        self.results[item] = result
        return result

    # =========================================================================
    # CHECK 1: Micro-expressions
    # =========================================================================
    def check_micro_expressions(
        self,
        blendshape_frames: list[dict],
        audio_emphasis_ms: list[float],
        fps: float = 30.0,
    ) -> CheckResult:
        """
        Check 1: Micro-expressions.

        Pass if: At least 2 distinct micro-moves fire within 300ms of stressed
        syllables (e.g., brow raise + squint) on 3/5 test lines.

        Args:
            blendshape_frames: List of blendshape dicts with timestamps
            audio_emphasis_ms: List of timestamps (ms) where emphasis occurs
            fps: Frames per second
        """
        item = "1. Micro-expressions"
        micro_blendshapes = [
            "browInnerUp",
            "browOuterUpLeft",
            "browOuterUpRight",
            "cheekSquintLeft",
            "cheekSquintRight",
        ]

        # Track micro-expression activations within 300ms of emphasis
        window_ms = 300
        matches = 0
        total_emphasis = len(audio_emphasis_ms)

        for emphasis_ts in audio_emphasis_ms:
            activations = set()
            for frame in blendshape_frames:
                frame_ts = frame.get("timestamp_ms", 0)
                if abs(frame_ts - emphasis_ts) <= window_ms:
                    for bs in micro_blendshapes:
                        if frame.get(bs, 0) > 0.15:  # Activation threshold
                            activations.add(bs)
            if len(activations) >= 2:
                matches += 1

        # Pass if 3/5 emphasis points have 2+ micro-expressions
        required_matches = max(3, int(total_emphasis * 0.6))
        passed = matches >= required_matches

        return self._record_result(
            item,
            passed,
            f"{matches}/{total_emphasis} emphasis points had 2+ micro-expressions",
            {"matches": matches, "total": total_emphasis, "required": required_matches},
        )

    # =========================================================================
    # CHECK 2: Lip-sync accuracy
    # =========================================================================
    def check_lip_sync(
        self,
        blendshape_frames: list[dict],
        expected_visemes: list[dict],
        fps: float = 30.0,
    ) -> CheckResult:
        """
        Check 2: Lip-sync accuracy.

        Pass if: ≤2 visible desyncs per 10-second read at 24-30 fps.

        Args:
            blendshape_frames: List of blendshape dicts with timestamps
            expected_visemes: List of {timestamp_ms, viseme, phoneme} dicts
            fps: Frames per second
        """
        item = "2. Lip-sync accuracy"

        # Viseme to blendshape mapping
        viseme_map = {
            "PP": ["mouthClose"],  # p, b, m
            "FF": ["mouthFunnel"],  # f, v
            "TH": ["tongueOut"],  # th
            "DD": ["jawOpen"],  # d, t, n
            "kk": ["jawOpen"],  # k, g
            "CH": ["mouthPucker"],  # ch, j, sh
            "SS": ["mouthSmileLeft", "mouthSmileRight"],  # s, z
            "nn": ["jawOpen"],  # n
            "RR": ["mouthPucker"],  # r
            "aa": ["jawOpen"],  # a
            "E": ["mouthSmileLeft", "mouthSmileRight"],  # e
            "ih": ["jawOpen"],  # i
            "oh": ["mouthFunnel", "jawOpen"],  # o
            "ou": ["mouthPucker", "mouthFunnel"],  # u
        }

        desyncs = 0
        window_ms = 50  # Tolerance window

        for expected in expected_visemes:
            ts = expected["timestamp_ms"]
            viseme = expected.get("viseme", "")
            expected_shapes = viseme_map.get(viseme, [])

            if not expected_shapes:
                continue

            # Find closest frame
            closest_frame = min(
                blendshape_frames,
                key=lambda f: abs(f.get("timestamp_ms", 0) - ts),
                default=None,
            )

            if closest_frame is None:
                desyncs += 1
                continue

            # Check if expected blendshape is active
            frame_ts = closest_frame.get("timestamp_ms", 0)
            if abs(frame_ts - ts) > window_ms:
                desyncs += 1
                continue

            # Check blendshape activation
            activated = any(
                closest_frame.get(shape, 0) > 0.3 for shape in expected_shapes
            )
            if not activated:
                desyncs += 1

        # Calculate duration and normalize
        if blendshape_frames:
            duration_ms = (
                blendshape_frames[-1].get("timestamp_ms", 0)
                - blendshape_frames[0].get("timestamp_ms", 0)
            )
            duration_s = duration_ms / 1000
            desyncs_per_10s = (desyncs / duration_s) * 10 if duration_s > 0 else desyncs
        else:
            desyncs_per_10s = desyncs

        passed = desyncs_per_10s <= 2

        return self._record_result(
            item,
            passed,
            f"{desyncs_per_10s:.1f} desyncs per 10s (threshold: ≤2)",
            {"desyncs_per_10s": desyncs_per_10s, "total_desyncs": desyncs},
        )

    # =========================================================================
    # CHECK 3: Eye contact consistency
    # =========================================================================
    def check_eye_contact(
        self,
        blendshape_frames: list[dict],
        duration_s: float = 10.0,
    ) -> CheckResult:
        """
        Check 3: Eye contact consistency.

        Pass if: 70-90% on-target gaze with 2-5 saccades per 10s;
        no "dead stare" >2s.
        """
        item = "3. Eye contact consistency"

        eye_shapes = [
            "eyeLookDownLeft",
            "eyeLookDownRight",
            "eyeLookInLeft",
            "eyeLookInRight",
            "eyeLookOutLeft",
            "eyeLookOutRight",
            "eyeLookUpLeft",
            "eyeLookUpRight",
        ]

        # Calculate gaze metrics
        on_target_frames = 0
        total_frames = len(blendshape_frames)
        saccade_count = 0
        dead_stare_ms = 0
        last_movement_ts = 0
        prev_gaze = None

        for frame in blendshape_frames:
            ts = frame.get("timestamp_ms", 0)

            # Calculate gaze vector magnitude
            gaze_magnitude = sum(abs(frame.get(s, 0)) for s in eye_shapes)

            # On-target if gaze is mostly centered (low deviation)
            if gaze_magnitude < 0.3:
                on_target_frames += 1

            # Detect saccade (rapid gaze change)
            current_gaze = tuple(frame.get(s, 0) for s in eye_shapes)
            if prev_gaze is not None:
                gaze_delta = sum(
                    abs(c - p) for c, p in zip(current_gaze, prev_gaze)
                )
                if gaze_delta > 0.2:
                    saccade_count += 1
                    last_movement_ts = ts
            prev_gaze = current_gaze

            # Track dead stare
            if ts - last_movement_ts > dead_stare_ms:
                dead_stare_ms = ts - last_movement_ts

        # Calculate percentages
        on_target_pct = (on_target_frames / total_frames * 100) if total_frames else 0
        saccades_per_10s = (saccade_count / duration_s) * 10 if duration_s > 0 else 0
        max_dead_stare_s = dead_stare_ms / 1000

        passed = (
            70 <= on_target_pct <= 90
            and 2 <= saccades_per_10s <= 5
            and max_dead_stare_s <= 2.0
        )

        return self._record_result(
            item,
            passed,
            f"Gaze: {on_target_pct:.0f}% on-target, {saccades_per_10s:.1f} saccades/10s, max stare: {max_dead_stare_s:.1f}s",
            {
                "on_target_pct": on_target_pct,
                "saccades_per_10s": saccades_per_10s,
                "max_dead_stare_s": max_dead_stare_s,
            },
        )

    # =========================================================================
    # CHECK 4: Blink cadence
    # =========================================================================
    def check_blink_cadence(
        self,
        blendshape_frames: list[dict],
        duration_s: float = 60.0,
    ) -> CheckResult:
        """
        Check 4: Blink cadence.

        Pass if: Average 12-18 blinks/min with ≥1 blink in first 6s of turn.
        """
        item = "4. Blink cadence"

        blink_threshold = 0.5
        blink_count = 0
        first_blink_ts = None
        in_blink = False

        for frame in blendshape_frames:
            ts = frame.get("timestamp_ms", 0)
            blink_val = max(
                frame.get("eyeBlinkLeft", 0), frame.get("eyeBlinkRight", 0)
            )

            if blink_val > blink_threshold and not in_blink:
                in_blink = True
                blink_count += 1
                if first_blink_ts is None:
                    first_blink_ts = ts
            elif blink_val <= blink_threshold:
                in_blink = False

        # Calculate metrics
        blinks_per_min = (blink_count / duration_s) * 60 if duration_s > 0 else 0
        first_blink_in_6s = first_blink_ts is not None and first_blink_ts <= 6000

        passed = 12 <= blinks_per_min <= 18 and first_blink_in_6s

        return self._record_result(
            item,
            passed,
            f"{blinks_per_min:.1f} blinks/min, first blink at {first_blink_ts}ms",
            {
                "blinks_per_min": blinks_per_min,
                "first_blink_ms": first_blink_ts,
                "first_blink_in_6s": first_blink_in_6s,
            },
        )

    # =========================================================================
    # CHECK 5: Head pose dynamics
    # =========================================================================
    def check_head_pose(
        self,
        head_rotation_frames: list[dict],
        sentence_boundaries_ms: list[float],
    ) -> CheckResult:
        """
        Check 5: Head pose dynamics.

        Pass if: 1-3 small pose changes per sentence without jitter or drift.
        """
        item = "5. Head pose dynamics"

        pose_change_threshold = 2.0  # degrees
        jitter_threshold = 0.5  # High-freq oscillation threshold
        drift_threshold = 10.0  # Max cumulative drift

        sentence_pose_changes = []
        has_jitter = False
        has_drift = False

        # Calculate pose changes per sentence
        for i, boundary in enumerate(sentence_boundaries_ms[:-1]):
            next_boundary = sentence_boundaries_ms[i + 1]
            pose_changes = 0
            prev_pose = None
            poses_in_sentence = []

            for frame in head_rotation_frames:
                ts = frame.get("timestamp_ms", 0)
                if boundary <= ts < next_boundary:
                    current_pose = (
                        frame.get("pitch", 0),
                        frame.get("yaw", 0),
                        frame.get("roll", 0),
                    )
                    poses_in_sentence.append(current_pose)

                    if prev_pose is not None:
                        delta = sum(
                            abs(c - p) for c, p in zip(current_pose, prev_pose)
                        )
                        if delta > pose_change_threshold:
                            pose_changes += 1
                    prev_pose = current_pose

            sentence_pose_changes.append(pose_changes)

            # Check for jitter (many small oscillations)
            if len(poses_in_sentence) > 10:
                deltas = []
                for j in range(1, len(poses_in_sentence)):
                    d = sum(
                        abs(poses_in_sentence[j][k] - poses_in_sentence[j - 1][k])
                        for k in range(3)
                    )
                    deltas.append(d)
                if len([d for d in deltas if d > jitter_threshold]) > len(deltas) * 0.3:
                    has_jitter = True

        # Check for drift
        if head_rotation_frames:
            start_pose = (
                head_rotation_frames[0].get("pitch", 0),
                head_rotation_frames[0].get("yaw", 0),
                head_rotation_frames[0].get("roll", 0),
            )
            end_pose = (
                head_rotation_frames[-1].get("pitch", 0),
                head_rotation_frames[-1].get("yaw", 0),
                head_rotation_frames[-1].get("roll", 0),
            )
            total_drift = sum(abs(e - s) for e, s in zip(end_pose, start_pose))
            has_drift = total_drift > drift_threshold

        # Check if pose changes are in 1-3 range for most sentences
        valid_sentences = sum(1 for pc in sentence_pose_changes if 1 <= pc <= 3)
        pct_valid = (
            valid_sentences / len(sentence_pose_changes) * 100
            if sentence_pose_changes
            else 0
        )

        passed = pct_valid >= 80 and not has_jitter and not has_drift

        return self._record_result(
            item,
            passed,
            f"{pct_valid:.0f}% sentences with 1-3 pose changes, jitter={has_jitter}, drift={has_drift}",
            {
                "pct_valid_sentences": pct_valid,
                "has_jitter": has_jitter,
                "has_drift": has_drift,
                "pose_changes_per_sentence": sentence_pose_changes,
            },
        )

    # =========================================================================
    # CHECK 6: Voice-to-lip sync (A/V offset)
    # =========================================================================
    def check_av_offset(
        self,
        av_offsets_ms: list[float],
    ) -> CheckResult:
        """
        Check 6: Voice-to-lip sync (A/V offset).

        Pass if: Absolute A/V offset ≤80ms p95 under load.
        """
        item = "6. Voice-to-lip sync (A/V offset)"

        if not av_offsets_ms:
            return self._record_result(
                item, False, "No A/V offset data available", {}
            )

        sorted_offsets = sorted(abs(o) for o in av_offsets_ms)
        p95_idx = int(len(sorted_offsets) * 0.95)
        p95_offset = sorted_offsets[p95_idx] if p95_idx < len(sorted_offsets) else sorted_offsets[-1]

        passed = p95_offset <= 80

        return self._record_result(
            item,
            passed,
            f"A/V offset p95: {p95_offset:.1f}ms (threshold: ≤80ms)",
            {
                "p95_offset_ms": p95_offset,
                "mean_offset_ms": sum(abs(o) for o in av_offsets_ms) / len(av_offsets_ms),
            },
        )

    # =========================================================================
    # CHECK 7: Turn-taking (barge-in)
    # =========================================================================
    def check_turn_taking(
        self,
        interrupt_latencies_ms: list[float],
        resume_latencies_ms: list[float],
    ) -> CheckResult:
        """
        Check 7: Turn-taking (barge-in).

        Pass if:
        - Detects user speech and halts TTS within 150ms p95
        - Resumes within 500ms after hand-off
        """
        item = "7. Turn-taking (barge-in)"

        if not interrupt_latencies_ms or not resume_latencies_ms:
            return self._record_result(
                item, False, "No turn-taking data available", {}
            )

        # Calculate p95 for interrupt detection
        sorted_interrupts = sorted(interrupt_latencies_ms)
        p95_idx = int(len(sorted_interrupts) * 0.95)
        interrupt_p95 = sorted_interrupts[min(p95_idx, len(sorted_interrupts) - 1)]

        # Calculate p95 for resume
        sorted_resumes = sorted(resume_latencies_ms)
        p95_idx = int(len(sorted_resumes) * 0.95)
        resume_p95 = sorted_resumes[min(p95_idx, len(sorted_resumes) - 1)]

        passed = interrupt_p95 <= 150 and resume_p95 <= 500

        return self._record_result(
            item,
            passed,
            f"Interrupt p95: {interrupt_p95:.0f}ms (≤150), Resume p95: {resume_p95:.0f}ms (≤500)",
            {
                "interrupt_p95_ms": interrupt_p95,
                "resume_p95_ms": resume_p95,
            },
        )

    # =========================================================================
    # CHECK 8: Latency under load
    # =========================================================================
    def check_latency(
        self,
        ttfa_samples_ms: list[float],
        response_latencies_ms: list[float],
        concurrent_sessions: int = 1,
    ) -> CheckResult:
        """
        Check 8: Latency under load.

        Pass if:
        - TTFA (time-to-first-audio) ≤250ms p95
        - Steady-state response ≤400ms p95 with 5 concurrent sessions
        """
        item = "8. Latency under load"

        if not ttfa_samples_ms or not response_latencies_ms:
            return self._record_result(
                item, False, "No latency data available", {}
            )

        # Calculate TTFA p95
        sorted_ttfa = sorted(ttfa_samples_ms)
        p95_idx = int(len(sorted_ttfa) * 0.95)
        ttfa_p95 = sorted_ttfa[min(p95_idx, len(sorted_ttfa) - 1)]

        # Calculate response latency p95
        sorted_response = sorted(response_latencies_ms)
        p95_idx = int(len(sorted_response) * 0.95)
        response_p95 = sorted_response[min(p95_idx, len(sorted_response) - 1)]

        passed = ttfa_p95 <= 250 and response_p95 <= 400

        return self._record_result(
            item,
            passed,
            f"TTFA p95: {ttfa_p95:.0f}ms (≤250), Response p95: {response_p95:.0f}ms (≤400) @ {concurrent_sessions} sessions",
            {
                "ttfa_p95_ms": ttfa_p95,
                "response_p95_ms": response_p95,
                "concurrent_sessions": concurrent_sessions,
            },
        )

    # =========================================================================
    # CHECK 9: Prosody & emphasis
    # =========================================================================
    def check_prosody(
        self,
        emphasis_audio_metrics: list[dict],
    ) -> CheckResult:
        """
        Check 9: Prosody & emphasis.

        Pass if: Words flagged as emphasis receive ≥10% amplitude or pitch delta
        and ≤15% speed change; audibly clear in ABX test.

        Args:
            emphasis_audio_metrics: List of {word, amplitude_delta_pct, pitch_delta_pct, speed_delta_pct}
        """
        item = "9. Prosody & emphasis"

        if not emphasis_audio_metrics:
            return self._record_result(
                item, False, "No prosody data available", {}
            )

        valid_emphasis = 0
        for metric in emphasis_audio_metrics:
            amp_delta = abs(metric.get("amplitude_delta_pct", 0))
            pitch_delta = abs(metric.get("pitch_delta_pct", 0))
            speed_delta = abs(metric.get("speed_delta_pct", 0))

            # Must have ≥10% amplitude OR pitch change, AND ≤15% speed change
            if (amp_delta >= 10 or pitch_delta >= 10) and speed_delta <= 15:
                valid_emphasis += 1

        pct_valid = valid_emphasis / len(emphasis_audio_metrics) * 100

        passed = pct_valid >= 80  # 80% of emphasis words should meet criteria

        return self._record_result(
            item,
            passed,
            f"{pct_valid:.0f}% of emphasis words met prosody criteria",
            {
                "pct_valid": pct_valid,
                "valid_count": valid_emphasis,
                "total_count": len(emphasis_audio_metrics),
            },
        )

    # =========================================================================
    # CHECK 10: Content grounding
    # =========================================================================
    def check_content_grounding(
        self,
        responses: list[dict],
    ) -> CheckResult:
        """
        Check 10: Content grounding.

        Pass if: For 10 factual prompts, ≥9 include source tag or retrieval
        snippet; 0 critical hallucinations.

        Args:
            responses: List of {prompt, response, has_source, is_hallucination}
        """
        item = "10. Content grounding"

        if not responses:
            return self._record_result(
                item, False, "No grounding data available", {}
            )

        sourced_count = sum(1 for r in responses if r.get("has_source", False))
        hallucination_count = sum(
            1 for r in responses if r.get("is_hallucination", False)
        )

        passed = sourced_count >= 9 and hallucination_count == 0

        return self._record_result(
            item,
            passed,
            f"{sourced_count}/{len(responses)} sourced, {hallucination_count} hallucinations",
            {
                "sourced_count": sourced_count,
                "hallucination_count": hallucination_count,
                "total_prompts": len(responses),
            },
        )

    # =========================================================================
    # CHECK 11: Fallback behaviors
    # =========================================================================
    def check_fallback_behaviors(
        self,
        asr_drop_response_ms: Optional[float],
        silence_response_ms: Optional[float],
        retrieval_miss_handled: bool,
    ) -> CheckResult:
        """
        Check 11: Fallback behaviors.

        Pass if:
        - On ASR drop or 2s silence: displays "listening" cue and asks clarify within 1s
        - On retrieval miss: returns "I don't have that yet" + next step
        """
        item = "11. Fallback behaviors"

        asr_ok = asr_drop_response_ms is not None and asr_drop_response_ms <= 1000
        silence_ok = silence_response_ms is not None and silence_response_ms <= 1000

        passed = asr_ok and silence_ok and retrieval_miss_handled

        details = []
        if not asr_ok:
            details.append(f"ASR drop response: {asr_drop_response_ms}ms (≤1000)")
        if not silence_ok:
            details.append(f"Silence response: {silence_response_ms}ms (≤1000)")
        if not retrieval_miss_handled:
            details.append("Retrieval miss not handled gracefully")

        return self._record_result(
            item,
            passed,
            "; ".join(details) if details else "All fallbacks working",
            {
                "asr_drop_response_ms": asr_drop_response_ms,
                "silence_response_ms": silence_response_ms,
                "retrieval_miss_handled": retrieval_miss_handled,
            },
        )

    # =========================================================================
    # CHECK 12: Noisy-input robustness
    # =========================================================================
    def check_noise_robustness(
        self,
        noisy_intent_results: list[dict],
    ) -> CheckResult:
        """
        Check 12: Noisy-input robustness.

        Pass if:
        - With -5 dB SNR babble, intent is correct ≥8/10
        - Misfires recover with 1 clarify question

        Args:
            noisy_intent_results: List of {correct, recovered_with_clarify}
        """
        item = "12. Noisy-input robustness"

        if not noisy_intent_results:
            return self._record_result(
                item, False, "No noise robustness data available", {}
            )

        correct_count = sum(1 for r in noisy_intent_results if r.get("correct", False))
        # Misfires that recovered
        misfires = [r for r in noisy_intent_results if not r.get("correct", False)]
        recovered = sum(1 for r in misfires if r.get("recovered_with_clarify", False))

        correct_pct = correct_count / len(noisy_intent_results) * 100
        recovery_ok = len(misfires) == 0 or recovered == len(misfires)

        passed = correct_count >= 8 and recovery_ok

        return self._record_result(
            item,
            passed,
            f"{correct_count}/10 correct intents, {recovered}/{len(misfires)} misfires recovered",
            {
                "correct_count": correct_count,
                "total_tests": len(noisy_intent_results),
                "misfires_recovered": recovered,
            },
        )

    # =========================================================================
    # Scoring
    # =========================================================================
    def get_score(self) -> ChecklistScore:
        """Calculate and return the overall checklist score."""
        results = list(self.results.values())
        passed = sum(1 for r in results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
        skipped = sum(1 for r in results if r.status == CheckStatus.SKIPPED)

        return ChecklistScore(
            total=len(self.ITEMS),
            passed=passed,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    def print_report(self) -> str:
        """Generate a human-readable report."""
        score = self.get_score()
        lines = [
            "=" * 60,
            "AVATAR REALISM & UTILITY CHECKLIST REPORT",
            "=" * 60,
            "",
            f"Score: {score.score}",
            f"Status: {'DEMO-READY' if score.is_demo_ready else 'NEEDS FIXES' if score.needs_fixes else 'ACCEPTABLE'}",
            "",
            "-" * 60,
            "RESULTS:",
            "-" * 60,
        ]

        for result in score.results:
            status_icon = (
                "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "○"
            )
            lines.append(f"  {status_icon} {result.name}")
            if result.details:
                lines.append(f"      {result.details}")

        if score.needs_fixes:
            lines.extend(
                [
                    "",
                    "-" * 60,
                    "PRIORITY FIXES:",
                    "-" * 60,
                ]
            )
            for fix in score.get_priority_fixes():
                lines.append(f"  → {fix}")

        lines.append("=" * 60)
        return "\n".join(lines)
