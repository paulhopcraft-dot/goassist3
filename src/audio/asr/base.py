"""ASR Base Interface - Pluggable speech recognition.

Defines the interface for ASR engines per the pluggable engine pattern.
Reference: Implementation-v3.0.md §4.1, Addendum A §A1

ASR must emit:
- Streaming partial hypotheses (not sentence-final only)
- Word/segment timestamps (for barge-in timing)
- Endpoint events (to trigger LISTENING → THINKING transition)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator, Callable, Protocol

from src.observability.logging import get_logger

logger = get_logger(__name__)


class ASREventType(Enum):
    """Types of ASR events."""

    PARTIAL = "partial"  # Streaming partial hypothesis
    FINAL = "final"  # Final transcription
    ENDPOINT = "endpoint"  # Speech endpoint detected


@dataclass
class ASRResult:
    """Result from ASR processing."""

    event_type: ASREventType
    text: str
    start_ms: int | None = None  # Word/segment start time
    end_ms: int | None = None  # Word/segment end time
    confidence: float = 1.0  # Confidence score (0.0-1.0)
    is_final: bool = False
    session_id: str = ""


class ASREngine(Protocol):
    """Protocol for pluggable ASR engines.

    All ASR implementations must conform to this interface.
    Substitution is allowed per Addendum A §A1 if:
    - Latency contracts remain satisfied
    - Streaming partials + timestamps supported
    - Endpoint events emitted

    Usage:
        asr = DeepgramASR(api_key="...")
        await asr.start("session-123")

        asr.on_partial(handle_partial)
        asr.on_final(handle_final)
        asr.on_endpoint(handle_endpoint)

        async for audio in audio_stream:
            await asr.push_audio(audio, t_audio_ms)

        await asr.stop()
    """

    async def start(self, session_id: str) -> None:
        """Initialize ASR for a session.

        Args:
            session_id: Unique session identifier
        """
        ...

    async def push_audio(self, audio: bytes, t_audio_ms: int) -> None:
        """Push audio chunk for processing.

        Args:
            audio: Raw PCM audio bytes (16-bit signed, mono, 16kHz)
            t_audio_ms: Authoritative audio timestamp from audio clock
        """
        ...

    def on_partial(self, callback: Callable[[str, int], None]) -> None:
        """Register callback for partial transcription updates.

        Args:
            callback: Function(text, t_ms) called on partial updates
        """
        ...

    def on_final(self, callback: Callable[[str, int, int], None]) -> None:
        """Register callback for final transcriptions.

        Args:
            callback: Function(text, start_ms, end_ms) called on final result
        """
        ...

    def on_endpoint(self, callback: Callable[[int], None]) -> None:
        """Register callback for endpoint detection.

        Args:
            callback: Function(t_ms) called when speech endpoint detected
        """
        ...

    async def stop(self) -> None:
        """Stop ASR and cleanup resources."""
        ...


class BaseASREngine(ABC):
    """Base class for ASR implementations.

    Provides common functionality and callback management.
    Concrete implementations should override the abstract methods.
    """

    def __init__(self) -> None:
        self._session_id: str | None = None
        self._callbacks_partial: list[Callable[[str, int], None]] = []
        self._callbacks_final: list[Callable[[str, int, int], None]] = []
        self._callbacks_endpoint: list[Callable[[int], None]] = []
        self._running: bool = False

    @abstractmethod
    async def start(self, session_id: str) -> None:
        """Initialize ASR for a session."""
        self._session_id = session_id
        self._running = True

    @abstractmethod
    async def push_audio(self, audio: bytes, t_audio_ms: int) -> None:
        """Push audio chunk for processing."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop ASR and cleanup resources."""
        self._running = False

    def on_partial(self, callback: Callable[[str, int], None]) -> None:
        """Register callback for partial transcription updates."""
        self._callbacks_partial.append(callback)

    def on_final(self, callback: Callable[[str, int, int], None]) -> None:
        """Register callback for final transcriptions."""
        self._callbacks_final.append(callback)

    def on_endpoint(self, callback: Callable[[int], None]) -> None:
        """Register callback for endpoint detection."""
        self._callbacks_endpoint.append(callback)

    async def _emit_partial(self, text: str, t_ms: int) -> None:
        """Emit partial transcription to all registered callbacks."""
        for callback in self._callbacks_partial:
            try:
                callback(text, t_ms)
            except Exception as e:
                logger.warning(
                    "asr_partial_callback_error",
                    callback=getattr(callback, "__name__", str(callback)),
                    error=str(e),
                )

    async def _emit_final(self, text: str, start_ms: int, end_ms: int) -> None:
        """Emit final transcription to all registered callbacks."""
        for callback in self._callbacks_final:
            try:
                callback(text, start_ms, end_ms)
            except Exception as e:
                logger.warning(
                    "asr_final_callback_error",
                    callback=getattr(callback, "__name__", str(callback)),
                    error=str(e),
                )

    async def _emit_endpoint(self, t_ms: int) -> None:
        """Emit endpoint event to all registered callbacks."""
        for callback in self._callbacks_endpoint:
            try:
                callback(t_ms)
            except Exception as e:
                logger.warning(
                    "asr_endpoint_callback_error",
                    callback=getattr(callback, "__name__", str(callback)),
                    error=str(e),
                )

    @property
    def session_id(self) -> str | None:
        """Current session ID."""
        return self._session_id

    @property
    def is_running(self) -> bool:
        """Whether ASR is currently running."""
        return self._running


class MockASREngine(BaseASREngine):
    """Mock ASR engine for testing.

    Simulates ASR behavior without actual speech recognition.
    Useful for unit tests and development.
    """

    async def start(self, session_id: str) -> None:
        """Start mock ASR session."""
        await super().start(session_id)

    async def push_audio(self, audio: bytes, t_audio_ms: int) -> None:
        """Process audio (mock - no actual recognition)."""
        if not self._running:
            return
        # In tests, manually call emit methods to simulate ASR

    async def stop(self) -> None:
        """Stop mock ASR."""
        await super().stop()

    async def simulate_partial(self, text: str, t_ms: int) -> None:
        """Simulate a partial transcription for testing."""
        await self._emit_partial(text, t_ms)

    async def simulate_final(self, text: str, start_ms: int, end_ms: int) -> None:
        """Simulate a final transcription for testing."""
        await self._emit_final(text, start_ms, end_ms)

    async def simulate_endpoint(self, t_ms: int) -> None:
        """Simulate an endpoint event for testing."""
        await self._emit_endpoint(t_ms)
