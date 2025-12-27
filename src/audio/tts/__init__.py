"""Text-to-Speech module.

Provides pluggable TTS engines per TMF v3.0 and Addendum A.

ARCHITECTURE:
- TTSBackend: Canonical interface for all TTS backends
- TTSManager: Config-based backend selection (recommended)
- Legacy TTSEngine: Original interface (maintained for compatibility)

Available backends:
- xtts-v2: Coqui XTTS-v2 (PRIMARY production backend)
- kyutai: Streaming TTS (OPTIONAL, disabled by default)
- mock: For testing (generates silence)

Usage (recommended - new backend architecture):
    from src.audio.tts import create_tts_manager

    manager = create_tts_manager(primary="xtts-v2")
    await manager.init()

    async for chunk in manager.stream(TTSRequest(text="Hello")):
        send_audio(chunk.chunk)

Usage (legacy - for existing code compatibility):
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
from src.audio.tts.TTSManager import (
    TTSManager,
    TTSManagerConfig,
    create_tts_manager,
)

__all__ = [
    # New backend architecture (recommended)
    "TTSBackend",
    "TTSManager",
    "TTSManagerConfig",
    "TTSRequest",
    "TTSResult",
    "TTSStreamChunk",
    "TTSHealthStatus",
    "create_tts_manager",
    # Legacy interface (compatibility)
    "TTSEngine",
    "BaseTTSEngine",
    "TTSChunk",
    "MockTTSEngine",
    "KyutaiTTSEngine",
    "KyutaiTTSConfig",
    "text_to_stream",
    "create_tts_engine",
]


# Lazy imports for optional components
def __getattr__(name: str):
    """Lazy import for optional TTS components."""
    # Backend interface
    if name in ("TTSBackend", "TTSRequest", "TTSResult", "TTSStreamChunk", "TTSHealthStatus"):
        from src.audio.tts.backends.interface import (
            TTSBackend,
            TTSRequest,
            TTSResult,
            TTSStreamChunk,
            TTSHealthStatus,
        )
        return {
            "TTSBackend": TTSBackend,
            "TTSRequest": TTSRequest,
            "TTSResult": TTSResult,
            "TTSStreamChunk": TTSStreamChunk,
            "TTSHealthStatus": TTSHealthStatus,
        }[name]

    # Legacy Kyutai engine (for compatibility)
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
    """Factory function to create TTS engines (legacy interface).

    DEPRECATED: Prefer create_tts_manager() for new code.

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
