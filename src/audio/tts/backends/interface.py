"""TTSBackend Interface - Canonical TTS backend abstraction.

All TTS backends must implement this interface.
Higher-level code is blind to which backend is used.

Reference: Pluggable TTS Architecture spec
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Any


@dataclass
class TTSRequest:
    """Request for TTS synthesis."""

    text: str
    voice_id: str | None = None
    language: str | None = None
    prosody: dict[str, Any] | None = None  # speed, pitch, volume, etc.


@dataclass
class TTSResult:
    """Result from TTS synthesis."""

    audio: bytes  # Raw PCM audio (16-bit signed, mono)
    sample_rate: int = 24000
    latency_ms: float = 0.0


@dataclass
class TTSStreamChunk:
    """A streaming chunk of synthesized audio."""

    chunk: bytes  # Raw PCM audio
    is_final: bool = False
    latency_ms: float | None = None


@dataclass
class TTSHealthStatus:
    """Health status of a TTS backend."""

    ok: bool
    backend: str
    last_error: str | None = None


class TTSBackend(ABC):
    """Canonical interface for TTS backends.

    All TTS implementations must conform to this interface.
    This abstraction allows config-only switching between backends.

    Usage:
        backend = XTTSBackend(config)
        await backend.init()

        # One-shot synthesis
        result = await backend.synthesize(TTSRequest(text="Hello"))

        # Streaming synthesis
        async for chunk in backend.stream(TTSRequest(text="Hello")):
            send_audio(chunk.chunk)

        # Health check
        status = await backend.health()
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name identifier.

        Returns:
            String identifier (e.g., "xtts-v2", "kyutai", "mock")
        """
        ...

    @abstractmethod
    async def init(self) -> None:
        """Initialize the backend.

        Called once before any synthesis.
        Should establish connections, load models, etc.
        """
        ...

    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize audio from text (one-shot).

        Args:
            request: TTS synthesis request

        Returns:
            Complete audio result

        Note:
            Prefer stream() for low-latency applications.
        """
        ...

    @abstractmethod
    async def stream(
        self, request: TTSRequest
    ) -> AsyncIterator[TTSStreamChunk]:
        """Synthesize audio from text (streaming).

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks as they become available

        Note:
            This is the preferred method for real-time applications.
            Audio should start emitting before full synthesis completes.
        """
        ...

    @abstractmethod
    async def health(self) -> TTSHealthStatus:
        """Check backend health.

        Returns:
            Health status with ok flag and any error info
        """
        ...

    async def shutdown(self) -> None:
        """Shutdown the backend and cleanup resources.

        Default implementation does nothing.
        Override if cleanup is needed.
        """
        pass
