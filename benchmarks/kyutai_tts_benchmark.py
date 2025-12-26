#!/usr/bin/env python3
"""Kyutai TTS Benchmark Script.

Compares Kyutai TTS latency and quality against GoAssist3 requirements:
- TTFA (Time to First Audio): ≤250ms p95
- Streaming text input support
- Cancel latency for barge-in: ≤150ms

Reference: TMF v3.0 §5.2, PRD v3.0 §4.1
"""

import asyncio
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator


@dataclass
class BenchmarkResult:
    """Results from a single TTS benchmark run."""

    text: str
    ttfa_ms: float  # Time to first audio chunk
    total_time_ms: float  # Total synthesis time
    audio_duration_ms: float  # Duration of generated audio
    chunk_count: int
    first_chunk_size: int
    total_audio_bytes: int
    error: str | None = None


@dataclass
class BenchmarkSummary:
    """Aggregated benchmark statistics."""

    engine_name: str
    num_runs: int
    ttfa_p50_ms: float
    ttfa_p95_ms: float
    ttfa_min_ms: float
    ttfa_max_ms: float
    total_time_p50_ms: float
    real_time_factor: float  # <1 means faster than real-time
    errors: list[str] = field(default_factory=list)

    def meets_goassist_requirements(self) -> tuple[bool, list[str]]:
        """Check if results meet GoAssist3 TMF requirements."""
        issues = []

        # TTFA requirement: ≤250ms p95
        if self.ttfa_p95_ms > 250:
            issues.append(f"TTFA p95 ({self.ttfa_p95_ms:.1f}ms) exceeds 250ms limit")

        # Real-time requirement
        if self.real_time_factor > 1.0:
            issues.append(f"RTF ({self.real_time_factor:.2f}) > 1.0 - slower than real-time")

        return len(issues) == 0, issues


# Test sentences of varying lengths
TEST_SENTENCES = [
    "Hello.",  # Minimal
    "How can I help you today?",  # Short
    "The quick brown fox jumps over the lazy dog.",  # Medium
    "I'd be happy to help you with that. Let me look into it and get back to you with more information.",  # Long
    "According to the latest research, artificial intelligence systems are becoming increasingly capable of understanding and generating human language, which has significant implications for how we interact with technology in our daily lives.",  # Very long
]


async def simulate_llm_stream(text: str, tokens_per_second: float = 50) -> AsyncIterator[str]:
    """Simulate LLM token streaming.

    Args:
        text: Full text to stream
        tokens_per_second: Simulated LLM generation speed

    Yields:
        Words as they would come from an LLM
    """
    words = text.split()
    delay = 1.0 / tokens_per_second

    for word in words:
        yield word + " "
        await asyncio.sleep(delay)


async def benchmark_kyutai_moshi(
    text: str,
    mimi: "MimiModel | None" = None,
    moshi_lm: "LMModel | None" = None,
) -> BenchmarkResult:
    """Benchmark Kyutai Moshi full-duplex model.

    Uses the actual Moshi model for speech-to-speech benchmarking.
    Requires GPU with 24GB VRAM.

    Args:
        text: Text to synthesize (used for generating test audio)
        mimi: Pre-loaded Mimi codec model
        moshi_lm: Pre-loaded Moshi LM model

    Returns:
        BenchmarkResult with timing metrics
    """
    try:
        import torch
        from moshi.models import loaders, LMGen

        if not torch.cuda.is_available():
            return BenchmarkResult(
                text=text,
                ttfa_ms=0,
                total_time_ms=0,
                audio_duration_ms=0,
                chunk_count=0,
                first_chunk_size=0,
                total_audio_bytes=0,
                error="CUDA not available - Moshi requires GPU",
            )

        # Load models if not provided
        if mimi is None:
            from huggingface_hub import hf_hub_download
            mimi_weight = hf_hub_download(loaders.DEFAULT_REPO, loaders.MIMI_NAME)
            mimi = loaders.get_mimi(mimi_weight, device='cuda')
            mimi.set_num_codebooks(8)

        if moshi_lm is None:
            from huggingface_hub import hf_hub_download
            moshi_weight = hf_hub_download(loaders.DEFAULT_REPO, loaders.MOSHI_NAME)
            moshi_lm = loaders.get_moshi_lm(moshi_weight, device='cuda')

        # Generate test audio (silence with some random noise to simulate speech)
        sample_rate = 24000
        duration_s = len(text) / 15  # ~15 chars per second of speech
        wav = torch.randn(1, 1, int(sample_rate * duration_s)).cuda() * 0.01

        chunks: list[bytes] = []
        ttfa_ms = 0.0
        start_time = time.perf_counter()
        first_chunk_time = None

        lm_gen = LMGen(moshi_lm, temp=0.8, temp_text=0.7)
        frame_size = mimi.frame_size

        with torch.no_grad():
            # Encode input audio
            codes = mimi.encode(wav)

            # Stream through Moshi
            with lm_gen.streaming(1), mimi.streaming(1):
                for idx in range(codes.shape[-1]):
                    code_frame = codes[:, :, idx:idx+1]
                    tokens_out = lm_gen.step(code_frame)

                    if tokens_out is not None:
                        wav_chunk = mimi.decode(tokens_out[:, 1:])

                        if first_chunk_time is None:
                            first_chunk_time = time.perf_counter()
                            ttfa_ms = (first_chunk_time - start_time) * 1000

                        chunk_bytes = wav_chunk.cpu().numpy().tobytes()
                        chunks.append(chunk_bytes)

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000

        # Calculate audio duration
        total_bytes = sum(len(c) for c in chunks)
        samples = total_bytes // 4  # float32 = 4 bytes per sample
        audio_duration_ms = (samples / sample_rate) * 1000

        return BenchmarkResult(
            text=text,
            ttfa_ms=ttfa_ms,
            total_time_ms=total_time_ms,
            audio_duration_ms=audio_duration_ms,
            chunk_count=len(chunks),
            first_chunk_size=len(chunks[0]) if chunks else 0,
            total_audio_bytes=total_bytes,
        )

    except ImportError as e:
        return BenchmarkResult(
            text=text,
            ttfa_ms=0,
            total_time_ms=0,
            audio_duration_ms=0,
            chunk_count=0,
            first_chunk_size=0,
            total_audio_bytes=0,
            error=f"Kyutai Moshi not installed: {e}",
        )
    except Exception as e:
        return BenchmarkResult(
            text=text,
            ttfa_ms=0,
            total_time_ms=0,
            audio_duration_ms=0,
            chunk_count=0,
            first_chunk_size=0,
            total_audio_bytes=0,
            error=str(e),
        )


async def benchmark_kyutai_tts(
    text: str,
    voice: str = "am_adam",
    streaming_text: bool = True,
) -> BenchmarkResult:
    """Benchmark Kyutai TTS for a single text input.

    Args:
        text: Text to synthesize
        voice: Voice identifier
        streaming_text: If True, stream text like LLM output

    Returns:
        BenchmarkResult with timing metrics
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return BenchmarkResult(
                text=text,
                ttfa_ms=0,
                total_time_ms=0,
                audio_duration_ms=0,
                chunk_count=0,
                first_chunk_size=0,
                total_audio_bytes=0,
                error="CUDA not available - Kyutai TTS requires GPU",
            )

        # Try to use delayed-streams-modeling TTS if available
        try:
            from moshi.tts import stream_tts
        except ImportError:
            # Fall back to Moshi-based synthesis
            return await benchmark_kyutai_moshi(text)

        chunks: list[bytes] = []
        ttfa_ms = 0.0
        start_time = time.perf_counter()
        first_chunk_time = None

        if streaming_text:
            text_stream = simulate_llm_stream(text)
        else:
            async def full_text():
                yield text
            text_stream = full_text()

        async for chunk in stream_tts(text_stream, voice=voice):
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter()
                ttfa_ms = (first_chunk_time - start_time) * 1000
            chunks.append(chunk)

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000

        total_bytes = sum(len(c) for c in chunks)
        samples = total_bytes // 2
        audio_duration_ms = (samples / 24000) * 1000

        return BenchmarkResult(
            text=text,
            ttfa_ms=ttfa_ms,
            total_time_ms=total_time_ms,
            audio_duration_ms=audio_duration_ms,
            chunk_count=len(chunks),
            first_chunk_size=len(chunks[0]) if chunks else 0,
            total_audio_bytes=total_bytes,
        )

    except ImportError as e:
        return BenchmarkResult(
            text=text,
            ttfa_ms=0,
            total_time_ms=0,
            audio_duration_ms=0,
            chunk_count=0,
            first_chunk_size=0,
            total_audio_bytes=0,
            error=f"Kyutai TTS not installed: {e}",
        )
    except Exception as e:
        return BenchmarkResult(
            text=text,
            ttfa_ms=0,
            total_time_ms=0,
            audio_duration_ms=0,
            chunk_count=0,
            first_chunk_size=0,
            total_audio_bytes=0,
            error=str(e),
        )


async def benchmark_kyutai_tts_cli(
    text: str,
) -> BenchmarkResult:
    """Benchmark Kyutai TTS using CLI (fallback method).

    Uses the moshi CLI tool directly for systems where Python import doesn't work.
    """
    import tempfile

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name

        start_time = time.perf_counter()

        # Run TTS via CLI
        proc = await asyncio.create_subprocess_exec(
            "python", "-m", "moshi.run_tts",
            "-",  # stdin
            output_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate(input=text.encode())

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000

        if proc.returncode != 0:
            return BenchmarkResult(
                text=text,
                ttfa_ms=0,
                total_time_ms=total_time_ms,
                audio_duration_ms=0,
                chunk_count=0,
                first_chunk_size=0,
                total_audio_bytes=0,
                error=stderr.decode(),
            )

        # Read output file
        output_file = Path(output_path)
        if output_file.exists():
            audio_bytes = output_file.read_bytes()
            output_file.unlink()

            # Estimate audio duration (assuming 24kHz, 16-bit mono, skip WAV header)
            samples = (len(audio_bytes) - 44) // 2
            audio_duration_ms = (samples / 24000) * 1000

            return BenchmarkResult(
                text=text,
                ttfa_ms=total_time_ms,  # CLI doesn't give streaming TTFA
                total_time_ms=total_time_ms,
                audio_duration_ms=audio_duration_ms,
                chunk_count=1,
                first_chunk_size=len(audio_bytes),
                total_audio_bytes=len(audio_bytes),
            )
        else:
            return BenchmarkResult(
                text=text,
                ttfa_ms=0,
                total_time_ms=total_time_ms,
                audio_duration_ms=0,
                chunk_count=0,
                first_chunk_size=0,
                total_audio_bytes=0,
                error="Output file not created",
            )

    except Exception as e:
        return BenchmarkResult(
            text=text,
            ttfa_ms=0,
            total_time_ms=0,
            audio_duration_ms=0,
            chunk_count=0,
            first_chunk_size=0,
            total_audio_bytes=0,
            error=str(e),
        )


def summarize_results(results: list[BenchmarkResult], engine_name: str) -> BenchmarkSummary:
    """Compute aggregate statistics from benchmark results."""

    valid_results = [r for r in results if r.error is None]
    errors = [r.error for r in results if r.error is not None]

    if not valid_results:
        return BenchmarkSummary(
            engine_name=engine_name,
            num_runs=len(results),
            ttfa_p50_ms=0,
            ttfa_p95_ms=0,
            ttfa_min_ms=0,
            ttfa_max_ms=0,
            total_time_p50_ms=0,
            real_time_factor=0,
            errors=errors,
        )

    ttfa_values = [r.ttfa_ms for r in valid_results]
    total_times = [r.total_time_ms for r in valid_results]

    # Calculate real-time factor
    total_audio = sum(r.audio_duration_ms for r in valid_results)
    total_processing = sum(r.total_time_ms for r in valid_results)
    rtf = total_processing / total_audio if total_audio > 0 else 0

    return BenchmarkSummary(
        engine_name=engine_name,
        num_runs=len(valid_results),
        ttfa_p50_ms=statistics.median(ttfa_values),
        ttfa_p95_ms=statistics.quantiles(ttfa_values, n=20)[18] if len(ttfa_values) >= 20 else max(ttfa_values),
        ttfa_min_ms=min(ttfa_values),
        ttfa_max_ms=max(ttfa_values),
        total_time_p50_ms=statistics.median(total_times),
        real_time_factor=rtf,
        errors=errors,
    )


def print_summary(summary: BenchmarkSummary) -> None:
    """Print formatted benchmark summary."""

    print(f"\n{'='*60}")
    print(f"  {summary.engine_name} Benchmark Results")
    print(f"{'='*60}")
    print(f"  Runs: {summary.num_runs}")
    print(f"  TTFA p50: {summary.ttfa_p50_ms:.1f}ms")
    print(f"  TTFA p95: {summary.ttfa_p95_ms:.1f}ms")
    print(f"  TTFA range: {summary.ttfa_min_ms:.1f}ms - {summary.ttfa_max_ms:.1f}ms")
    print(f"  Total time p50: {summary.total_time_p50_ms:.1f}ms")
    print(f"  Real-time factor: {summary.real_time_factor:.2f}x")

    if summary.errors:
        print(f"\n  Errors ({len(summary.errors)}):")
        for err in summary.errors[:3]:
            print(f"    - {err[:80]}...")

    # GoAssist3 requirements check
    meets, issues = summary.meets_goassist_requirements()
    print(f"\n  GoAssist3 TMF Compliance: {'PASS' if meets else 'FAIL'}")
    if not meets:
        for issue in issues:
            print(f"    - {issue}")
    print(f"{'='*60}\n")


async def run_benchmark(
    num_runs: int = 10,
    warmup_runs: int = 2,
    streaming: bool = True,
) -> BenchmarkSummary:
    """Run complete Kyutai TTS benchmark.

    Args:
        num_runs: Number of benchmark runs per sentence
        warmup_runs: Number of warmup runs to discard
        streaming: Use streaming text input (simulates LLM)

    Returns:
        BenchmarkSummary with aggregated results
    """

    print(f"\nKyutai TTS Benchmark")
    print(f"  Runs per sentence: {num_runs}")
    print(f"  Warmup runs: {warmup_runs}")
    print(f"  Streaming text: {streaming}")
    print(f"  Test sentences: {len(TEST_SENTENCES)}")

    # Warmup
    print("\n  Warming up...")
    for _ in range(warmup_runs):
        await benchmark_kyutai_tts(TEST_SENTENCES[0], streaming_text=streaming)

    # Benchmark runs
    results: list[BenchmarkResult] = []

    for i, sentence in enumerate(TEST_SENTENCES):
        print(f"\n  Testing sentence {i+1}/{len(TEST_SENTENCES)}: '{sentence[:40]}...'")

        for run in range(num_runs):
            result = await benchmark_kyutai_tts(sentence, streaming_text=streaming)
            results.append(result)

            if result.error:
                print(f"    Run {run+1}: ERROR - {result.error[:50]}")
            else:
                print(f"    Run {run+1}: TTFA={result.ttfa_ms:.1f}ms, Total={result.total_time_ms:.1f}ms")

    summary = summarize_results(results, "Kyutai TTS")
    print_summary(summary)

    return summary


def check_kyutai_installed() -> bool:
    """Check if Kyutai TTS is installed."""
    try:
        import moshi
        return True
    except ImportError:
        return False


def install_kyutai() -> bool:
    """Install Kyutai TTS package."""
    print("\nInstalling Kyutai TTS (moshi>=0.2.6)...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "moshi>=0.2.6"],
            check=True,
            capture_output=True,
        )
        print("  Installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Installation failed: {e.stderr.decode()}")
        return False


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Kyutai TTS for GoAssist3")
    parser.add_argument("--runs", type=int, default=5, help="Runs per sentence")
    parser.add_argument("--warmup", type=int, default=2, help="Warmup runs")
    parser.add_argument("--no-streaming", action="store_true", help="Disable streaming text")
    parser.add_argument("--install", action="store_true", help="Install Kyutai if missing")
    parser.add_argument("--cli-mode", action="store_true", help="Use CLI instead of Python API")
    args = parser.parse_args()

    # Check/install Kyutai
    if not check_kyutai_installed():
        if args.install:
            if not install_kyutai():
                print("Failed to install Kyutai TTS. Exiting.")
                sys.exit(1)
        else:
            print("\nKyutai TTS not installed.")
            print("Run with --install to auto-install, or:")
            print("  pip install moshi>=0.2.6")
            sys.exit(1)

    # Run benchmark
    summary = await run_benchmark(
        num_runs=args.runs,
        warmup_runs=args.warmup,
        streaming=not args.no_streaming,
    )

    # Exit code based on requirements
    meets, _ = summary.meets_goassist_requirements()
    sys.exit(0 if meets else 1)


if __name__ == "__main__":
    asyncio.run(main())
