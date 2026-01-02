"""Automatic Speech Recognition module.

Provides pluggable ASR engines per TMF v3.0 and Addendum A.

Available engines:
- MockASREngine: For testing (no actual recognition)
- DeepgramStreamingASR: Cloud-based streaming ASR (recommended for production)

Usage:
    from src.audio.asr import create_asr_engine

    asr = create_asr_engine("deepgram")
    await asr.start("session-123")

    asr.on_partial(handle_partial)
    asr.on_final(handle_final)
    asr.on_endpoint(handle_endpoint)

    async for audio in audio_stream:
        await asr.push_audio(audio, t_ms)
"""

from __future__ import annotations

from src.audio.asr.base import (
    ASREngine,
    ASREventType,
    ASRResult,
    BaseASREngine,
    MockASREngine,
)

__all__ = [
    # Protocol and base
    "ASREngine",
    "BaseASREngine",
    "ASREventType",
    "ASRResult",
    # Implementations
    "MockASREngine",
    "DeepgramStreamingASR",
    "DeepgramConfig",
    # Factory
    "create_asr_engine",
]


# Lazy imports for optional engines
def __getattr__(name: str):
    """Lazy import for optional ASR engines."""
    if name in ("DeepgramStreamingASR", "DeepgramConfig"):
        from src.audio.asr.deepgram_streaming import DeepgramConfig, DeepgramStreamingASR

        if name == "DeepgramStreamingASR":
            return DeepgramStreamingASR
        return DeepgramConfig

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def create_asr_engine(
    engine: str = "mock",
    **kwargs,
) -> ASREngine:
    """Factory function to create ASR engines.

    Args:
        engine: Engine type ("mock", "deepgram")
        **kwargs: Engine-specific configuration

    Returns:
        Configured ASR engine instance

    Raises:
        ValueError: If engine type is unknown

    Examples:
        # Development/testing with mock
        asr = create_asr_engine("mock")

        # Production with Deepgram
        asr = create_asr_engine("deepgram", api_key="...")
    """
    if engine == "mock":
        return MockASREngine()

    elif engine == "deepgram":
        from src.audio.asr.deepgram_streaming import DeepgramConfig, DeepgramStreamingASR

        config = DeepgramConfig(
            api_key=kwargs.get("api_key", ""),
            model=kwargs.get("model", "nova-2"),
            language=kwargs.get("language", "en"),
            punctuate=kwargs.get("punctuate", True),
            interim_results=kwargs.get("interim_results", True),
            endpointing=kwargs.get("endpointing", 300),
            vad_events=kwargs.get("vad_events", True),
            smart_format=kwargs.get("smart_format", True),
        )
        return DeepgramStreamingASR(config)

    else:
        raise ValueError(
            f"Unknown ASR engine: {engine}. "
            f"Available: mock, deepgram"
        )
