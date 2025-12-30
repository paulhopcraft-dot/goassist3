"""
Metrics collection and analysis for Avatar QA.

Provides utilities for collecting and analyzing blendshape data,
latency measurements, and audio characteristics.
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Optional
import statistics


@dataclass
class BlendshapeFrame:
    """Single frame of blendshape data."""

    timestamp_ms: float
    blendshapes: dict[str, float]
    head_rotation: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp_ms": self.timestamp_ms,
            **self.blendshapes,
            **{f"head_{k}": v for k, v in self.head_rotation.items()},
        }


class BlendshapeAnalyzer:
    """
    Collects and analyzes blendshape data streams.

    Usage:
        analyzer = BlendshapeAnalyzer()

        # During animation
        for frame in animation_stream:
            analyzer.add_frame(frame)

        # Get analysis
        blink_rate = analyzer.get_blink_rate()
        gaze_metrics = analyzer.get_gaze_metrics()
    """

    # ARKit 52 blendshape names
    BLINK_SHAPES = ["eyeBlinkLeft", "eyeBlinkRight"]
    GAZE_SHAPES = [
        "eyeLookDownLeft",
        "eyeLookDownRight",
        "eyeLookInLeft",
        "eyeLookInRight",
        "eyeLookOutLeft",
        "eyeLookOutRight",
        "eyeLookUpLeft",
        "eyeLookUpRight",
    ]
    BROW_SHAPES = [
        "browDownLeft",
        "browDownRight",
        "browInnerUp",
        "browOuterUpLeft",
        "browOuterUpRight",
    ]
    MOUTH_SHAPES = [
        "jawOpen",
        "mouthClose",
        "mouthPucker",
        "mouthFunnel",
        "mouthSmileLeft",
        "mouthSmileRight",
    ]

    def __init__(self):
        self.frames: list[BlendshapeFrame] = []
        self._start_time: Optional[float] = None

    def add_frame(
        self,
        blendshapes: dict[str, float],
        head_rotation: Optional[dict[str, float]] = None,
        timestamp_ms: Optional[float] = None,
    ):
        """Add a blendshape frame to the analysis buffer."""
        if self._start_time is None:
            self._start_time = time.time()

        if timestamp_ms is None:
            timestamp_ms = (time.time() - self._start_time) * 1000

        frame = BlendshapeFrame(
            timestamp_ms=timestamp_ms,
            blendshapes=blendshapes,
            head_rotation=head_rotation or {},
        )
        self.frames.append(frame)

    def get_duration_s(self) -> float:
        """Get total duration of recorded data in seconds."""
        if len(self.frames) < 2:
            return 0.0
        return (self.frames[-1].timestamp_ms - self.frames[0].timestamp_ms) / 1000

    def get_blink_rate(self, threshold: float = 0.5) -> float:
        """Calculate blinks per minute."""
        blink_count = 0
        in_blink = False

        for frame in self.frames:
            blink_val = max(
                frame.blendshapes.get(s, 0) for s in self.BLINK_SHAPES
            )
            if blink_val > threshold and not in_blink:
                in_blink = True
                blink_count += 1
            elif blink_val <= threshold:
                in_blink = False

        duration_min = self.get_duration_s() / 60
        return blink_count / duration_min if duration_min > 0 else 0

    def get_first_blink_ms(self, threshold: float = 0.5) -> Optional[float]:
        """Get timestamp of first blink in milliseconds."""
        for frame in self.frames:
            blink_val = max(
                frame.blendshapes.get(s, 0) for s in self.BLINK_SHAPES
            )
            if blink_val > threshold:
                return frame.timestamp_ms
        return None

    def get_gaze_metrics(self) -> dict:
        """Analyze eye gaze patterns."""
        if not self.frames:
            return {"on_target_pct": 0, "saccade_count": 0, "max_dead_stare_ms": 0}

        on_target = 0
        saccade_count = 0
        max_dead_stare_ms = 0
        last_movement_ts = self.frames[0].timestamp_ms
        prev_gaze = None

        for frame in self.frames:
            # Calculate gaze deviation
            gaze = tuple(frame.blendshapes.get(s, 0) for s in self.GAZE_SHAPES)
            gaze_magnitude = sum(abs(g) for g in gaze)

            if gaze_magnitude < 0.3:
                on_target += 1

            # Detect saccades
            if prev_gaze is not None:
                delta = sum(abs(g - p) for g, p in zip(gaze, prev_gaze))
                if delta > 0.2:
                    saccade_count += 1
                    dead_stare = frame.timestamp_ms - last_movement_ts
                    max_dead_stare_ms = max(max_dead_stare_ms, dead_stare)
                    last_movement_ts = frame.timestamp_ms

            prev_gaze = gaze

        # Final dead stare check
        if self.frames:
            final_stare = self.frames[-1].timestamp_ms - last_movement_ts
            max_dead_stare_ms = max(max_dead_stare_ms, final_stare)

        return {
            "on_target_pct": on_target / len(self.frames) * 100 if self.frames else 0,
            "saccade_count": saccade_count,
            "saccades_per_10s": saccade_count / self.get_duration_s() * 10
            if self.get_duration_s() > 0
            else 0,
            "max_dead_stare_ms": max_dead_stare_ms,
        }

    def get_micro_expression_events(
        self, threshold: float = 0.15
    ) -> list[dict]:
        """Detect micro-expression activation events."""
        events = []
        prev_active = set()

        for frame in self.frames:
            current_active = set()
            for shape in self.BROW_SHAPES:
                if frame.blendshapes.get(shape, 0) > threshold:
                    current_active.add(shape)

            # New activations
            new_active = current_active - prev_active
            if new_active:
                events.append(
                    {
                        "timestamp_ms": frame.timestamp_ms,
                        "shapes": list(new_active),
                        "count": len(new_active),
                    }
                )
            prev_active = current_active

        return events

    def get_head_pose_frames(self) -> list[dict]:
        """Extract head rotation data."""
        return [
            {
                "timestamp_ms": f.timestamp_ms,
                "pitch": f.head_rotation.get("pitch", 0),
                "yaw": f.head_rotation.get("yaw", 0),
                "roll": f.head_rotation.get("roll", 0),
            }
            for f in self.frames
            if f.head_rotation
        ]

    def to_checklist_format(self) -> list[dict]:
        """Convert frames to checklist-compatible format."""
        return [f.to_dict() for f in self.frames]


class LatencyMeasurer:
    """
    Measures various latency metrics for avatar responsiveness.

    Usage:
        measurer = LatencyMeasurer()

        # Measure TTFA
        measurer.start_ttfa()
        # ... wait for first audio ...
        measurer.end_ttfa()

        # Measure interrupt handling
        measurer.start_interrupt()
        # ... avatar stops ...
        measurer.end_interrupt()
    """

    def __init__(self):
        self.ttfa_samples: list[float] = []
        self.response_latencies: list[float] = []
        self.interrupt_latencies: list[float] = []
        self.resume_latencies: list[float] = []
        self.av_offsets: list[float] = []

        self._ttfa_start: Optional[float] = None
        self._response_start: Optional[float] = None
        self._interrupt_start: Optional[float] = None
        self._resume_start: Optional[float] = None

    def start_ttfa(self):
        """Start measuring time-to-first-audio."""
        self._ttfa_start = time.time()

    def end_ttfa(self):
        """End TTFA measurement."""
        if self._ttfa_start is not None:
            self.ttfa_samples.append((time.time() - self._ttfa_start) * 1000)
            self._ttfa_start = None

    def start_response(self):
        """Start measuring response latency."""
        self._response_start = time.time()

    def end_response(self):
        """End response latency measurement."""
        if self._response_start is not None:
            self.response_latencies.append(
                (time.time() - self._response_start) * 1000
            )
            self._response_start = None

    def start_interrupt(self):
        """Start measuring interrupt detection latency."""
        self._interrupt_start = time.time()

    def end_interrupt(self):
        """End interrupt measurement."""
        if self._interrupt_start is not None:
            self.interrupt_latencies.append(
                (time.time() - self._interrupt_start) * 1000
            )
            self._interrupt_start = None

    def start_resume(self):
        """Start measuring resume latency after interrupt."""
        self._resume_start = time.time()

    def end_resume(self):
        """End resume measurement."""
        if self._resume_start is not None:
            self.resume_latencies.append((time.time() - self._resume_start) * 1000)
            self._resume_start = None

    def record_av_offset(self, audio_ts_ms: float, video_ts_ms: float):
        """Record an A/V synchronization offset."""
        self.av_offsets.append(audio_ts_ms - video_ts_ms)

    def get_percentile(self, samples: list[float], percentile: float) -> float:
        """Calculate percentile from samples."""
        if not samples:
            return 0.0
        sorted_samples = sorted(samples)
        idx = int(len(sorted_samples) * percentile / 100)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]

    def get_ttfa_p95(self) -> float:
        return self.get_percentile(self.ttfa_samples, 95)

    def get_response_p95(self) -> float:
        return self.get_percentile(self.response_latencies, 95)

    def get_interrupt_p95(self) -> float:
        return self.get_percentile(self.interrupt_latencies, 95)

    def get_resume_p95(self) -> float:
        return self.get_percentile(self.resume_latencies, 95)

    def get_av_offset_p95(self) -> float:
        return self.get_percentile([abs(o) for o in self.av_offsets], 95)

    def get_summary(self) -> dict:
        """Get summary of all latency metrics."""
        return {
            "ttfa_p95_ms": self.get_ttfa_p95(),
            "ttfa_samples": len(self.ttfa_samples),
            "response_p95_ms": self.get_response_p95(),
            "response_samples": len(self.response_latencies),
            "interrupt_p95_ms": self.get_interrupt_p95(),
            "interrupt_samples": len(self.interrupt_latencies),
            "resume_p95_ms": self.get_resume_p95(),
            "resume_samples": len(self.resume_latencies),
            "av_offset_p95_ms": self.get_av_offset_p95(),
            "av_offset_samples": len(self.av_offsets),
        }


class AudioAnalyzer:
    """
    Analyzes audio characteristics for prosody and emphasis detection.

    Usage:
        analyzer = AudioAnalyzer()
        metrics = analyzer.analyze_emphasis(audio_data, sample_rate, word_boundaries)
    """

    def __init__(self):
        self.emphasis_metrics: list[dict] = []

    def analyze_emphasis(
        self,
        audio_samples: list[float],
        sample_rate: int,
        word_boundaries: list[dict],
    ) -> list[dict]:
        """
        Analyze emphasis characteristics for each word.

        Args:
            audio_samples: Raw audio samples (normalized -1 to 1)
            sample_rate: Sample rate in Hz
            word_boundaries: List of {word, start_ms, end_ms, is_emphasis}

        Returns:
            List of emphasis metrics per word
        """
        results = []

        # Calculate baseline metrics
        if not audio_samples:
            return results

        baseline_amplitude = statistics.mean(abs(s) for s in audio_samples)

        for word_info in word_boundaries:
            start_idx = int(word_info["start_ms"] / 1000 * sample_rate)
            end_idx = int(word_info["end_ms"] / 1000 * sample_rate)

            if start_idx >= len(audio_samples) or end_idx > len(audio_samples):
                continue

            word_samples = audio_samples[start_idx:end_idx]
            if not word_samples:
                continue

            # Calculate word metrics
            word_amplitude = statistics.mean(abs(s) for s in word_samples)
            word_duration_ms = word_info["end_ms"] - word_info["start_ms"]

            # Estimate pitch (simplified - real impl would use librosa or similar)
            zero_crossings = sum(
                1
                for i in range(1, len(word_samples))
                if word_samples[i - 1] * word_samples[i] < 0
            )
            estimated_pitch = zero_crossings * sample_rate / len(word_samples) / 2

            # Calculate deltas from baseline
            amp_delta_pct = (
                (word_amplitude - baseline_amplitude) / baseline_amplitude * 100
                if baseline_amplitude > 0
                else 0
            )

            # Duration-based speed estimation
            avg_word_duration = 300  # Typical word duration in ms
            speed_delta_pct = (
                (avg_word_duration - word_duration_ms) / avg_word_duration * 100
            )

            result = {
                "word": word_info["word"],
                "is_emphasis": word_info.get("is_emphasis", False),
                "amplitude_delta_pct": amp_delta_pct,
                "pitch_delta_pct": 0,  # Would need proper pitch analysis
                "speed_delta_pct": speed_delta_pct,
                "duration_ms": word_duration_ms,
            }
            results.append(result)

        self.emphasis_metrics = results
        return results

    def detect_emphasis_timestamps(
        self,
        audio_samples: list[float],
        sample_rate: int,
        window_ms: float = 50,
        threshold: float = 1.5,
    ) -> list[float]:
        """
        Detect timestamps where emphasis occurs based on amplitude spikes.

        Returns list of timestamps (ms) where emphasis is detected.
        """
        if not audio_samples:
            return []

        window_size = int(window_ms / 1000 * sample_rate)
        emphasis_timestamps = []

        # Calculate RMS for each window
        rms_values = []
        for i in range(0, len(audio_samples) - window_size, window_size):
            window = audio_samples[i : i + window_size]
            rms = (sum(s * s for s in window) / len(window)) ** 0.5
            rms_values.append((i, rms))

        if not rms_values:
            return []

        # Find emphasis points (RMS > threshold * mean)
        mean_rms = statistics.mean(r[1] for r in rms_values)
        for idx, rms in rms_values:
            if rms > threshold * mean_rms:
                timestamp_ms = idx / sample_rate * 1000
                emphasis_timestamps.append(timestamp_ms)

        return emphasis_timestamps

    def get_viseme_sequence(
        self,
        phonemes: list[dict],
    ) -> list[dict]:
        """
        Convert phoneme sequence to expected visemes.

        Args:
            phonemes: List of {phoneme, start_ms, end_ms}

        Returns:
            List of {viseme, timestamp_ms, phoneme}
        """
        phoneme_to_viseme = {
            "p": "PP",
            "b": "PP",
            "m": "PP",
            "f": "FF",
            "v": "FF",
            "th": "TH",
            "dh": "TH",
            "t": "DD",
            "d": "DD",
            "n": "DD",
            "k": "kk",
            "g": "kk",
            "ch": "CH",
            "jh": "CH",
            "sh": "CH",
            "zh": "CH",
            "s": "SS",
            "z": "SS",
            "r": "RR",
            "l": "DD",
            "w": "ou",
            "y": "ih",
            "aa": "aa",
            "ae": "aa",
            "ah": "aa",
            "ao": "oh",
            "aw": "oh",
            "ay": "aa",
            "eh": "E",
            "er": "RR",
            "ey": "E",
            "ih": "ih",
            "iy": "E",
            "ow": "oh",
            "oy": "oh",
            "uh": "ou",
            "uw": "ou",
        }

        visemes = []
        for p in phonemes:
            phoneme = p["phoneme"].lower()
            viseme = phoneme_to_viseme.get(phoneme, "")
            if viseme:
                visemes.append(
                    {
                        "viseme": viseme,
                        "timestamp_ms": p["start_ms"],
                        "phoneme": p["phoneme"],
                    }
                )

        return visemes


@dataclass
class GroundingResult:
    """Result of a content grounding check."""

    prompt: str
    response: str
    has_source: bool
    is_hallucination: bool
    source_text: Optional[str] = None


class GroundingChecker:
    """
    Checks response content for proper source grounding.

    Usage:
        checker = GroundingChecker()
        result = checker.check_response(prompt, response, expected_sources)
    """

    SOURCE_INDICATORS = [
        "according to",
        "based on",
        "from the",
        "source:",
        "[source]",
        "reference:",
        "per the",
        "as stated in",
        "documentation shows",
        "the record indicates",
    ]

    def __init__(self, known_facts: Optional[dict] = None):
        self.known_facts = known_facts or {}
        self.results: list[GroundingResult] = []

    def check_response(
        self,
        prompt: str,
        response: str,
        expected_answer: Optional[str] = None,
    ) -> GroundingResult:
        """Check if a response is properly grounded."""
        # Check for source indicators
        response_lower = response.lower()
        has_source = any(ind in response_lower for ind in self.SOURCE_INDICATORS)

        # Check for hallucination (if expected answer provided)
        is_hallucination = False
        if expected_answer is not None:
            # Simple check - response should contain key parts of expected answer
            expected_words = set(expected_answer.lower().split())
            response_words = set(response_lower.split())
            overlap = len(expected_words & response_words) / len(expected_words)
            is_hallucination = overlap < 0.3  # Less than 30% overlap

        result = GroundingResult(
            prompt=prompt,
            response=response,
            has_source=has_source,
            is_hallucination=is_hallucination,
        )
        self.results.append(result)
        return result

    def to_checklist_format(self) -> list[dict]:
        """Convert results to checklist-compatible format."""
        return [
            {
                "prompt": r.prompt,
                "response": r.response,
                "has_source": r.has_source,
                "is_hallucination": r.is_hallucination,
            }
            for r in self.results
        ]
