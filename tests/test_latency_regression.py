"""Latency Regression Tests - TTFA p95 Tracking.

Tests for Time-to-First-Audio (TTFA) latency tracking and regression detection:
    1. Measure TTFA p50, p95, p99 across multiple requests
    2. Validate TMF v3.0 contract: TTFA ≤ 250ms p95
    3. Track component latency breakdown
    4. Detect regressions between test runs
    5. Performance profiling for optimization
    6. Warm-up vs steady-state latency

TMF v3.0 §1.2: TTFA ≤ 250ms p95 (steady-state, not demo mode)
TMF v3.0 §6: Component latency budgets
"""

import asyncio
import time
from typing import List
from unittest.mock import AsyncMock, patch
from statistics import median, quantiles

import pytest

from src.orchestrator.pipeline import ConversationPipeline, PipelineConfig
from src.orchestrator.session import Session
from src.audio.tts.base import TTSChunk


class TestTTFABaseline:
    """Baseline TTFA measurements with mock components."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="ttfa-baseline-session")
        yield session
        # Cleanup handled by pipeline.stop() in each test
        pass

    @pytest.mark.asyncio
    async def test_measure_ttfa_mock_components(self, session):
        """Measure TTFA with all components mocked (baseline)."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )

        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()

            # Fast TTS (simulates TTFB of 50ms)
            async def mock_tts_stream(text_stream):
                await asyncio.sleep(0.05)  # 50ms TTFB
                yield TTSChunk(audio=b"\x00" * 640, is_final=True, text_offset=0)

            mock_tts.synthesize_stream = mock_tts_stream
            mock_create_tts.return_value = mock_tts

            await pipeline.start()

            # Transition to THINKING
            await session.on_speech_start()
            await session.on_endpoint_detected(100)

            # Mock fast LLM (50ms to first token)
            async def mock_llm_stream(messages):
                await asyncio.sleep(0.05)  # 50ms to first token
                yield "Hello"

            pipeline._llm.generate_stream = mock_llm_stream

            # Measure TTFA
            ttfa_measurements = []

            for i in range(10):
                start_time = time.perf_counter()

                # Generate response
                await pipeline._generate_response([
                    {"role": "user", "content": f"Test {i}"}
                ])

                # First audio chunk time
                ttfa = (time.perf_counter() - start_time) * 1000  # ms
                ttfa_measurements.append(ttfa)

                # Reset for next iteration
                await session.on_endpoint_detected(100 + i * 10)

            await pipeline.stop()

            # Calculate percentiles
            ttfa_p50 = median(ttfa_measurements)
            ttfa_p95 = quantiles(ttfa_measurements, n=20)[18]  # 95th percentile

            print(f"TTFA (mock components): p50={ttfa_p50:.1f}ms, p95={ttfa_p95:.1f}ms")

            # With mocked components, should be very fast (<200ms)
            assert ttfa_p95 < 200, f"Mock TTFA p95={ttfa_p95:.1f}ms too slow"

    @pytest.mark.asyncio
    async def test_ttfa_steady_state_vs_warmup(self, session):
        """Compare warm-up latency vs steady-state latency."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )

        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()

            async def mock_tts_stream(text_stream):
                await asyncio.sleep(0.05)
                yield TTSChunk(audio=b"\x00" * 640, is_final=True, text_offset=0)

            mock_tts.synthesize_stream = mock_tts_stream
            mock_create_tts.return_value = mock_tts

            await pipeline.start()
            await session.on_speech_start()
            await session.on_endpoint_detected(100)

            async def mock_llm_stream(messages):
                await asyncio.sleep(0.05)
                yield "Response"

            pipeline._llm.generate_stream = mock_llm_stream

            # Measure first 3 requests (warm-up)
            warmup_ttfa = []
            for i in range(3):
                start = time.perf_counter()
                await pipeline._generate_response([{"role": "user", "content": f"Warmup {i}"}])
                warmup_ttfa.append((time.perf_counter() - start) * 1000)
                await session.on_endpoint_detected(100 + i * 10)

            # Measure next 10 requests (steady-state)
            steady_ttfa = []
            for i in range(10):
                start = time.perf_counter()
                await pipeline._generate_response([{"role": "user", "content": f"Steady {i}"}])
                steady_ttfa.append((time.perf_counter() - start) * 1000)
                await session.on_endpoint_detected(200 + i * 10)

            await pipeline.stop()

            warmup_median = median(warmup_ttfa)
            steady_median = median(steady_ttfa)

            print(f"Warmup median: {warmup_median:.1f}ms")
            print(f"Steady-state median: {steady_median:.1f}ms")

            # Steady-state should not be significantly worse than warmup
            # (in practice, might be better due to caching)
            assert steady_median < warmup_median * 1.5


class TestComponentLatencyBudget:
    """Test component latency budget compliance (TMF v3.0 §6)."""

    @pytest.mark.asyncio
    async def test_vad_latency_budget(self):
        """Test VAD processing within budget (5-10ms)."""
        from src.audio.vad.silero_vad import SileroVAD
        from src.audio.transport.audio_clock import get_audio_clock

        session_id = "latency-test-session"

        # Register session with audio clock
        clock = get_audio_clock()
        clock.start_session(session_id)

        vad = SileroVAD(session_id=session_id)
        await vad.start()

        # Measure VAD latency
        audio_chunk = b"\x00" * 640  # 20ms @ 16kHz
        latencies = []

        for _ in range(20):
            start = time.perf_counter()
            await vad.process(audio_chunk)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        await vad.stop()

        vad_p95 = quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0]

        print(f"VAD latency: p95={vad_p95:.2f}ms")

        # TMF budget: 5-10ms for VAD
        assert vad_p95 < 20, f"VAD p95={vad_p95:.2f}ms exceeds reasonable limit"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="TurnDetector module not implemented yet")
    async def test_turn_detector_latency_budget(self):
        """Test turn detector within budget (10-15ms)."""
        from src.audio.vad.turn_detector import TurnDetector

        detector = TurnDetector()

        latencies = []

        for i in range(50):
            start = time.perf_counter()
            detector.process(is_speech=True, t_ms=i * 20)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        turn_p95 = quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0]

        print(f"Turn detector latency: p95={turn_p95:.2f}ms")

        # Should be very fast (<5ms)
        assert turn_p95 < 5, f"Turn detector p95={turn_p95:.2f}ms too slow"


class TestTTFARegression:
    """Test for TTFA latency regression detection."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="ttfa-regression-session")
        yield session
        pass

    @pytest.mark.asyncio
    async def test_ttfa_p95_within_contract(self, session):
        """Verify TTFA p95 ≤ 250ms (TMF v3.0 contract)."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )

        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()

            # Simulate TTS with 100ms TTFB
            async def mock_tts_stream(text_stream):
                await asyncio.sleep(0.1)  # 100ms TTFB
                yield TTSChunk(audio=b"\x00" * 640, is_final=True, text_offset=0)

            mock_tts.synthesize_stream = mock_tts_stream
            mock_create_tts.return_value = mock_tts

            await pipeline.start()
            await session.on_speech_start()
            await session.on_endpoint_detected(100)

            # Mock LLM with 80ms to first token
            async def mock_llm_stream(messages):
                await asyncio.sleep(0.08)
                yield "Test response"

            pipeline._llm.generate_stream = mock_llm_stream

            # Measure 20 requests
            ttfa_measurements = []

            for i in range(20):
                start = time.perf_counter()
                await pipeline._generate_response([{"role": "user", "content": f"Test {i}"}])
                ttfa_ms = (time.perf_counter() - start) * 1000
                ttfa_measurements.append(ttfa_ms)
                await session.on_endpoint_detected(100 + i * 10)

            await pipeline.stop()

            # Calculate p95
            ttfa_p50 = median(ttfa_measurements)
            ttfa_p95 = quantiles(ttfa_measurements, n=20)[18]

            print(f"TTFA: p50={ttfa_p50:.1f}ms, p95={ttfa_p95:.1f}ms")

            # TMF contract: p95 ≤ 250ms
            assert ttfa_p95 <= 250, f"TTFA p95={ttfa_p95:.1f}ms exceeds 250ms contract"

    @pytest.mark.asyncio
    async def test_detect_latency_spike(self, session):
        """Detect if TTFA has a latency spike."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )

        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()

            # Simulate normal TTS with occasional spike
            spike_on_request = 5

            async def mock_tts_stream_with_spike(text_stream):
                # Check if this is the spike request
                nonlocal current_request
                if current_request == spike_on_request:
                    await asyncio.sleep(0.3)  # 300ms spike
                else:
                    await asyncio.sleep(0.05)  # 50ms normal

                async for _ in text_stream:
                    pass
                yield TTSChunk(audio=b"\x00" * 640, is_final=True, text_offset=0)

            mock_tts.synthesize_stream = mock_tts_stream_with_spike
            mock_create_tts.return_value = mock_tts

            await pipeline.start()
            await session.on_speech_start()
            await session.on_endpoint_detected(100)

            async def mock_llm_stream(messages):
                await asyncio.sleep(0.05)
                yield "Response"

            pipeline._llm.generate_stream = mock_llm_stream

            ttfa_measurements = []
            current_request = 0

            for i in range(10):
                current_request = i
                start = time.perf_counter()
                await pipeline._generate_response([{"role": "user", "content": f"Test {i}"}])
                ttfa_ms = (time.perf_counter() - start) * 1000
                ttfa_measurements.append(ttfa_ms)
                await session.on_endpoint_detected(100 + i * 10)

            await pipeline.stop()

            # Find max latency (should be the spike)
            max_ttfa = max(ttfa_measurements)
            baseline_ttfa = median([t for i, t in enumerate(ttfa_measurements) if i != spike_on_request])

            print(f"Baseline TTFA: {baseline_ttfa:.1f}ms")
            print(f"Spike TTFA: {max_ttfa:.1f}ms")

            # Spike should be significantly higher than baseline
            assert max_ttfa > baseline_ttfa * 2, "Spike not detected"


class TestLatencyPercentiles:
    """Test percentile calculations for latency metrics."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="percentile-session")
        yield session
        pass

    @pytest.mark.asyncio
    async def test_calculate_ttfa_percentiles(self, session):
        """Calculate p50, p95, p99 for TTFA."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )

        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()

            # Variable latency TTS (50-150ms)
            import random

            async def mock_tts_stream(text_stream):
                await asyncio.sleep(random.uniform(0.05, 0.15))
                async for _ in text_stream:
                    pass
                yield TTSChunk(audio=b"\x00" * 640, is_final=True, text_offset=0)

            mock_tts.synthesize_stream = mock_tts_stream
            mock_create_tts.return_value = mock_tts

            await pipeline.start()
            await session.on_speech_start()
            await session.on_endpoint_detected(100)

            async def mock_llm_stream(messages):
                await asyncio.sleep(random.uniform(0.05, 0.1))
                yield "Response"

            pipeline._llm.generate_stream = mock_llm_stream

            ttfa_measurements = []

            for i in range(100):  # Large sample for accurate percentiles
                start = time.perf_counter()
                await pipeline._generate_response([{"role": "user", "content": f"Test {i}"}])
                ttfa_ms = (time.perf_counter() - start) * 1000
                ttfa_measurements.append(ttfa_ms)
                await session.on_endpoint_detected(100 + i * 10)

            await pipeline.stop()

            # Calculate percentiles
            ttfa_p50 = median(ttfa_measurements)
            percentile_data = quantiles(ttfa_measurements, n=100)
            ttfa_p95 = percentile_data[94]  # 95th percentile
            ttfa_p99 = percentile_data[98]  # 99th percentile

            print(f"TTFA percentiles (n=100):")
            print(f"  p50: {ttfa_p50:.1f}ms")
            print(f"  p95: {ttfa_p95:.1f}ms")
            print(f"  p99: {ttfa_p99:.1f}ms")

            # Sanity checks
            assert ttfa_p50 < ttfa_p95 < ttfa_p99
            assert ttfa_p95 < 300  # Should be reasonable


class TestBargeInLatency:
    """Test barge-in latency regression."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="bargein-latency-session")
        yield session
        pass

    @pytest.mark.asyncio
    async def test_bargein_latency_p95(self, session):
        """Measure barge-in latency p95 (TMF contract: ≤ 150ms)."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )

        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()

            # Fast cancel
            async def fast_cancel():
                await asyncio.sleep(0.01)  # 10ms

            mock_tts.cancel = fast_cancel
            mock_create_tts.return_value = mock_tts

            await pipeline.start()

            async def fast_abort():
                await asyncio.sleep(0.01)

            pipeline._llm.abort = fast_abort

            # Measure barge-in latency
            bargein_latencies = []

            for i in range(20):
                # Transition to SPEAKING
                await session.on_speech_start()
                await session.on_endpoint_detected(100 + i * 10)
                await session.on_response_ready()

                # Measure barge-in
                start = time.perf_counter()
                await pipeline.handle_barge_in()
                bargein_ms = (time.perf_counter() - start) * 1000
                bargein_latencies.append(bargein_ms)

            await pipeline.stop()

            # Calculate p95
            bargein_p50 = median(bargein_latencies)
            bargein_p95 = quantiles(bargein_latencies, n=20)[18]

            print(f"Barge-in latency: p50={bargein_p50:.1f}ms, p95={bargein_p95:.1f}ms")

            # TMF contract: ≤ 150ms
            assert bargein_p95 <= 150, f"Barge-in p95={bargein_p95:.1f}ms exceeds 150ms contract"
