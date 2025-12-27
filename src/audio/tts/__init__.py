"""Text-to-Speech module.

Provides pluggable TTS engines per TMF v3.0 and Addendum A.

Available engines:
- MockTTSEngine: For testing (generates silence)
- KyutaiTTSEngine: Streaming TTS with 220ms latency (recommended)

Usage:
    from src.audio.tts import create_tts_engine

    tts = create_tts_engine("kyutai", server_url="ws://localhost:8080/tts")
    await tts.start("session-123")

    async for audio in tts.synthesize_stream(llm_tokens):
        send_audio(audio)
"""

from src.audio.tts.base import (
    BaseTTSEngine,
    MockTTSEngine,
    TTSChunk,
    TTSEngine,
    text_to_stream,
)

__all__ = [
    # Protocol and base
    "TTSEngine",
    "BaseTTSEngine",
    "TTSChunk",
    # Implementations
    "MockTTSEngine",
    "KyutaiTTSEngine",
    "KyutaiTTSConfig",
    # Utilities
    "text_to_stream",
    "create_tts_engine",
]


# Lazy imports for optional engines
def __getattr__(name: str):
    """Lazy import for optional TTS engines."""
    if name in ("KyutaiTTSEngine", "KyutaiTTSConfig"):
        from src.audio.tts.kyutai_tts import KyutaiTTSConfig, KyutaiTTSEngine

        if name == "KyutaiTTSEngine":
            return KyutaiTTSEngine
        return KyutaiTTSConfig

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def create_tts_engine(
    engine: str = "mock",
    **kwargs,
) -> TTSEngine:
    """Factory function to create TTS engines.

    Args:
        engine: Engine type ("mock", "kyutai")
        **kwargs: Engine-specific configuration

    Returns:
        Configured TTS engine instance

    Raises:
        ValueError: If engine type is unknown
    """
    if engine == "mock":
        return MockTTSEngine(**kwargs)

    elif engine == "kyutai":
        from src.audio.tts.kyutai_tts import KyutaiTTSConfig, KyutaiTTSEngine

        config = KyutaiTTSConfig(
            server_url=kwargs.get("server_url", "ws://localhost:8080/tts"),
            voice_id=kwargs.get("voice_id", "default"),
            sample_rate=kwargs.get("sample_rate", 24000),
        )
        return KyutaiTTSEngine(
            config=config,
            on_word=kwargs.get("on_word"),
        )

    else:
        raise ValueError(
            f"Unknown TTS engine: {engine}. "
            f"Available: mock, kyutai"
        )
