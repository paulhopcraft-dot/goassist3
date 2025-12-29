"""Text-to-Speech module.

Provides pluggable TTS engines with automatic selection based on
system capabilities.

Available engines:
- KyutaiTTSEngine: Ultra-low latency (220ms TTFA), requires GPU
- EdgeTTSEngine: Free fallback, works on CPU
- MockTTSEngine: Testing only (generates silence)

Usage:
    from src.audio.tts import create_tts_engine

    # Auto-select best available
    tts = create_tts_engine("auto")

    # Or specify engine
    tts = create_tts_engine("kyutai", voice="am_adam")
    tts = create_tts_engine("edge", voice="aria")

Reference: TMF v3.0 §4.2
"""

from src.audio.tts.base import (
    BaseTTSEngine,
    MockTTSEngine,
    TTSChunk,
    TTSEngine,
    text_to_stream,
)
from src.audio.tts.factory import (
    create_tts_engine,
    get_available_engines,
    get_recommended_engine,
)

__all__ = [
    # Base classes
    "BaseTTSEngine",
    "MockTTSEngine",
    "TTSChunk",
    "TTSEngine",
    # Factory
    "create_tts_engine",
    "get_available_engines",
    "get_recommended_engine",
    # Utilities
    "text_to_stream",
]
