"""TTS Factory - Automatic engine selection.

Selects the best available TTS engine based on system capabilities:
1. Kyutai TTS (if GPU available) - Ultra-low latency, best quality
2. Edge TTS (fallback) - Free, works everywhere

Reference: TMF v3.0 §4.2, Addendum A §A4
"""

import logging
from typing import Literal

from src.audio.tts.base import BaseTTSEngine, MockTTSEngine

logger = logging.getLogger(__name__)

TTSEngineType = Literal["kyutai", "edge", "mock", "auto"]


def create_tts_engine(
    engine: TTSEngineType = "auto",
    voice: str | None = None,
    **kwargs,
) -> BaseTTSEngine:
    """Create a TTS engine instance.

    Automatically selects the best available engine if 'auto' is specified.

    Args:
        engine: Engine type ('kyutai', 'edge', 'mock', 'auto')
        voice: Voice identifier (engine-specific)
        **kwargs: Additional engine-specific options

    Returns:
        Configured TTS engine instance

    Selection priority (for 'auto'):
        1. Kyutai TTS - if moshi package and CUDA available
        2. Edge TTS - if edge-tts package available
        3. Mock TTS - fallback for testing
    """
    if engine == "auto":
        return _auto_select_engine(voice, **kwargs)

    if engine == "kyutai":
        return _create_kyutai(voice, **kwargs)

    if engine == "edge":
        return _create_edge(voice, **kwargs)

    if engine == "mock":
        return MockTTSEngine(**kwargs)

    raise ValueError(f"Unknown TTS engine: {engine}")


def _auto_select_engine(voice: str | None, **kwargs) -> BaseTTSEngine:
    """Automatically select the best available TTS engine."""

    # Try Kyutai first (best quality, requires GPU)
    try:
        import torch
        if torch.cuda.is_available():
            try:
                import moshi
                logger.info("Using Kyutai TTS (GPU available)")
                return _create_kyutai(voice, **kwargs)
            except ImportError:
                logger.info("Kyutai TTS not installed, trying Edge TTS")
        else:
            logger.info("CUDA not available, trying Edge TTS")
    except ImportError:
        logger.info("PyTorch not available, trying Edge TTS")

    # Try Edge TTS (free, works on CPU)
    try:
        import edge_tts
        logger.info("Using Edge TTS (CPU fallback)")
        return _create_edge(voice, **kwargs)
    except ImportError:
        logger.info("Edge TTS not installed, using Mock TTS")

    # Fallback to mock
    logger.warning("No real TTS available, using Mock TTS (silence only)")
    return MockTTSEngine(**kwargs)


def _create_kyutai(voice: str | None, **kwargs) -> BaseTTSEngine:
    """Create Kyutai TTS engine."""
    from src.audio.tts.kyutai_tts import KyutaiTTSEngine

    return KyutaiTTSEngine(
        voice=voice or "am_adam",
        **kwargs,
    )


def _create_edge(voice: str | None, **kwargs) -> BaseTTSEngine:
    """Create Edge TTS engine."""
    from src.audio.tts.edge_tts import EdgeTTSEngine

    return EdgeTTSEngine(
        voice=voice or "aria",
        **kwargs,
    )


def get_available_engines() -> list[str]:
    """Get list of available TTS engines on this system.

    Returns:
        List of engine names that can be used
    """
    available = ["mock"]

    try:
        import edge_tts
        available.append("edge")
    except ImportError:
        pass

    try:
        import torch
        import moshi
        if torch.cuda.is_available():
            available.append("kyutai")
    except ImportError:
        pass

    return available


def get_recommended_engine() -> str:
    """Get the recommended TTS engine for this system.

    Returns:
        Engine name ('kyutai', 'edge', or 'mock')
    """
    available = get_available_engines()

    if "kyutai" in available:
        return "kyutai"
    if "edge" in available:
        return "edge"
    return "mock"
