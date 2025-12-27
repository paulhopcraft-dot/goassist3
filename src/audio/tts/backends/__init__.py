"""TTS Backends - Pluggable TTS engine implementations.

This module provides the backend abstraction for TTS engines.
All backends implement the TTSBackend interface.

Available backends:
- XTTSBackend: Coqui XTTS-v2 (primary production backend)
- KyutaiBackend: Kyutai delayed-streams-modeling (optional)
- MockBackend: For testing (generates silence)
"""

from src.audio.tts.backends.interface import (
    TTSBackend,
    TTSRequest,
    TTSResult,
    TTSHealthStatus,
)
from src.audio.tts.backends.mock_backend import MockBackend

__all__ = [
    # Interface
    "TTSBackend",
    "TTSRequest",
    "TTSResult",
    "TTSHealthStatus",
    # Backends
    "MockBackend",
    "XTTSBackend",
    "KyutaiBackend",
]


# Lazy imports for optional backends
def __getattr__(name: str):
    """Lazy import for optional backends."""
    if name == "XTTSBackend":
        from src.audio.tts.backends.xtts_backend import XTTSBackend
        return XTTSBackend

    if name == "KyutaiBackend":
        from src.audio.tts.backends.kyutai_backend import KyutaiBackend
        return KyutaiBackend

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
