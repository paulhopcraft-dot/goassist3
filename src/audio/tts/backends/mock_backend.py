"""Mock TTS Backend - For testing and development.

Generates silence with configurable timing.
Does not require any external services.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from src.audio.tts.backends.interface import (
    TTSBackend,
    TTSHealthStatus,
    TTSRequest,
    TTSResult,
    TTSStreamChunk,
)


class MockBackend(TTSBackend):
    """Mock TTS backend for testing.

    Generates silence with realistic timing.
    Useful for development and testing without TTS server.
    """

    def __init__(
        self,
        sample_rate: int = 24000,
        chunk_duration_ms: int = 20,
        chars_per_second: float = 15.0,
    ) -> None:
        """Initialize mock backend.

        Args:
            sample_rate: Audio sample rate
            chunk_duration_ms: Duration of each audio chunk
            chars_per_second: Simulated speech rate
        """
        self._sample_rate = sample_rate
        self._chunk_duration_ms = chunk_duration_ms
        self._chars_per_second = chars_per_second
        self._initialized = False

    @property
    def name(self) -> str:
        """Backend name identifier."""
        return "mock"

    async def init(self) -> None:
        """Initialize mock backend (no-op)."""
        self._initialized = True

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate complete audio for text.

        Args:
            request: TTS synthesis request

        Returns:
            Complete audio result (silence)
        """
        # Calculate audio duration based on text length
        duration_s = len(request.text) / self._chars_per_second
        samples = int(duration_s * self._sample_rate)
        audio = b"\x00\x00" * samples  # 16-bit silence

        return TTSResult(
            audio=audio,
            sample_rate=self._sample_rate,
            latency_ms=0.0,
        )

    async def stream(
        self, request: TTSRequest
    ) -> AsyncIterator[TTSStreamChunk]:
        """Stream audio chunks for text.

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks (silence)
        """
        # Calculate total chunks needed
        duration_s = len(request.text) / self._chars_per_second
        total_chunks = max(1, int(duration_s * 1000 / self._chunk_duration_ms))

        samples_per_chunk = int(
            self._sample_rate * self._chunk_duration_ms / 1000
        )
        chunk_audio = b"\x00\x00" * samples_per_chunk

        for i in range(total_chunks):
            is_final = (i == total_chunks - 1)
            yield TTSStreamChunk(
                chunk=chunk_audio,
                is_final=is_final,
                latency_ms=float(i * self._chunk_duration_ms),
            )

            # Simulate real-time streaming
            await asyncio.sleep(self._chunk_duration_ms / 1000)

    async def health(self) -> TTSHealthStatus:
        """Check backend health.

        Returns:
            Always healthy for mock backend
        """
        return TTSHealthStatus(
            ok=self._initialized,
            backend=self.name,
            last_error=None if self._initialized else "Not initialized",
        )
