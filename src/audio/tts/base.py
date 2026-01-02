"""TTS Base Interface - Pluggable text-to-speech.

Defines the interface for TTS engines per the pluggable engine pattern.
Reference: Implementation-v3.0.md §4.2, Addendum A §A4

TTS must support:
- Streaming audio emission (start speaking early)
- Hard cancel within barge-in contract (150ms)
- Commercially viable licensing
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Protocol


@dataclass
class TTSChunk:
    """A chunk of synthesized audio."""

    audio: bytes  # Raw PCM audio (16-bit signed, mono)
    is_final: bool = False  # True for last chunk
    text_offset: int = 0  # Character offset in source text
    duration_ms: int = 0  # Duration of this chunk


class TTSEngine(Protocol):
    """Protocol for pluggable TTS engines.

    All TTS implementations must conform to this interface.
    Substitution is allowed per Addendum A §A4 if:
    - Streaming audio emission supported
    - Hard cancel within 150ms
    - Commercially viable licensing

    Usage:
        tts = StreamingTTS(...)
        await tts.start("session-123")

        async for audio in tts.synthesize_stream(text_stream):
            send_audio(audio)

        # On barge-in
        await tts.cancel()

        await tts.stop()
    """

    async def start(self, session_id: str) -> None:
        """Initialize TTS for a session.

        Args:
            session_id: Unique session identifier
        """
        ...

    async def synthesize_stream(
        self, text_stream: AsyncIterator[str]
    ) -> AsyncIterator[bytes]:
        """Synthesize audio from streaming text input.

        Args:
            text_stream: Async iterator of text chunks from LLM

        Yields:
            Audio bytes as they become available

        Note:
            Must start emitting audio before full text is received
            (streaming synthesis for low TTFA).
        """
        ...

    async def cancel(self) -> None:
        """Immediately stop synthesis and drain buffers.

        Must complete within barge-in contract (150ms).
        Called when user interrupts agent.
        """
        ...

    async def stop(self) -> None:
        """Stop TTS and cleanup resources."""
        ...


class BaseTTSEngine(ABC):
    """Base class for TTS implementations.

    Provides common functionality and state management.
    Concrete implementations should override abstract methods.
    """

    def __init__(self) -> None:
        self._session_id: str | None = None
        self._running: bool = False
        self._synthesizing: bool = False
        self._cancelled: bool = False

    @abstractmethod
    async def start(self, session_id: str) -> None:
        """Initialize TTS for a session."""
        self._session_id = session_id
        self._running = True
        self._cancelled = False

    @abstractmethod
    async def synthesize_stream(
        self, text_stream: AsyncIterator[str]
    ) -> AsyncIterator[bytes]:
        """Synthesize audio from streaming text input."""
        ...

    async def cancel(self) -> None:
        """Immediately stop synthesis.

        Default implementation sets cancel flag.
        Subclasses should override to add buffer draining.
        """
        self._cancelled = True
        self._synthesizing = False

    async def stop(self) -> None:
        """Stop TTS and cleanup resources."""
        await self.cancel()
        self._running = False

    @property
    def session_id(self) -> str | None:
        """Current session ID."""
        return self._session_id

    @property
    def is_running(self) -> bool:
        """Whether TTS is ready to synthesize."""
        return self._running

    @property
    def is_synthesizing(self) -> bool:
        """Whether synthesis is currently in progress."""
        return self._synthesizing

    @property
    def is_cancelled(self) -> bool:
        """Whether synthesis was cancelled."""
        return self._cancelled


class MockTTSEngine(BaseTTSEngine):
    """Mock TTS engine for testing.

    Generates silence or simple audio patterns.
    Useful for unit tests and development.
    """

    def __init__(self, chunk_duration_ms: int = 20) -> None:
        super().__init__()
        self._chunk_duration_ms = chunk_duration_ms
        self._sample_rate = 16000

    async def start(self, session_id: str) -> None:
        """Start mock TTS session."""
        await super().start(session_id)

    async def synthesize_stream(
        self, text_stream: AsyncIterator[str]
    ) -> AsyncIterator[bytes]:
        """Generate mock audio for text."""
        self._synthesizing = True
        self._cancelled = False

        try:
            collected_text = ""
            async for text_chunk in text_stream:
                if self._cancelled:
                    break

                collected_text += text_chunk

                # Generate silence for each character (mock audio)
                samples_per_char = self._sample_rate // 10  # 100ms per char
                for _ in range(len(text_chunk)):
                    if self._cancelled:
                        break

                    # Generate one chunk of silence
                    samples = (self._sample_rate * self._chunk_duration_ms) // 1000
                    silence = b"\x00\x00" * samples  # 16-bit silence
                    yield silence

        finally:
            self._synthesizing = False

    async def cancel(self) -> None:
        """Cancel mock synthesis."""
        await super().cancel()


async def text_to_stream(text: str) -> AsyncIterator[str]:
    """Convert a string to an async iterator of characters.

    Utility for testing TTS with non-streaming text input.
    """
    for char in text:
        yield char
