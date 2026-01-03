"""ElevenLabs TTS Backend - Cloud-based neural text-to-speech.

High-quality streaming TTS using ElevenLabs API.

Features:
- Multiple voice options (professional quality)
- Low-latency streaming
- Natural prosody and emotion
- 29 languages supported

Reference: TMF v3.0 §4 Text-to-Speech
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator

try:
    from elevenlabs.client import AsyncElevenLabs
    from elevenlabs import Voice, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

from src.audio.tts.backends.interface import (
    TTSBackend,
    TTSRequest,
    TTSResult,
    TTSStreamChunk,
    TTSHealthStatus,
)
from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ElevenLabsConfig:
    """Configuration for ElevenLabs TTS."""

    api_key: str
    voice_id: str = "EXAVITQu4vr4xnSDxMaL"  # Default: Sarah (conversational)
    model_id: str = "eleven_turbo_v2"  # Fastest model
    stability: float = 0.5  # Voice consistency
    similarity_boost: float = 0.75  # Voice clarity
    optimize_latency: int = 3  # Max latency optimization
    output_format: str = "pcm_24000"  # 24kHz PCM


class ElevenLabsBackend(TTSBackend):
    """ElevenLabs cloud TTS backend.

    Uses ElevenLabs streaming API for low-latency, high-quality TTS.

    Voice IDs (popular):
    - EXAVITQu4vr4xnSDxMaL: Sarah (conversational, female)
    - pNInz6obpgDQGcFmaJgB: Adam (narrative, male)
    - CYw3kZ02Hs0563khs1Fj: Dave (conversational, male)

    Usage:
        backend = ElevenLabsBackend(api_key="your-key")
        await backend.init()

        async for chunk in backend.stream(TTSRequest(text="Hello")):
            play_audio(chunk.chunk)
    """

    def __init__(self, config: ElevenLabsConfig | None = None) -> None:
        if not ELEVENLABS_AVAILABLE:
            raise ImportError(
                "elevenlabs package not installed. "
                "Install with: pip install elevenlabs"
            )

        if config is None:
            raise ValueError("ElevenLabsConfig required")

        self._config = config
        self._client: AsyncElevenLabs | None = None
        self._is_initialized = False

    @property
    def name(self) -> str:
        """Backend identifier."""
        return "elevenlabs"

    async def init(self) -> None:
        """Initialize ElevenLabs client."""
        if self._is_initialized:
            logger.warning("ElevenLabs backend already initialized")
            return

        try:
            self._client = AsyncElevenLabs(api_key=self._config.api_key)
            self._is_initialized = True
            logger.info(
                "ElevenLabs TTS initialized",
                voice_id=self._config.voice_id,
                model=self._config.model_id,
            )
        except Exception as e:
            logger.error("Failed to initialize ElevenLabs", error=str(e))
            raise

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize complete audio (non-streaming).

        Note: Prefer stream() for lower latency.

        Args:
            request: TTS request

        Returns:
            Complete audio result
        """
        if not self._is_initialized or self._client is None:
            raise RuntimeError("ElevenLabs backend not initialized")

        audio_chunks = []
        async for chunk in self.stream(request):
            audio_chunks.append(chunk.chunk)

        return TTSResult(
            audio=b"".join(audio_chunks),
            sample_rate=24000,
        )

    async def stream(self, request: TTSRequest) -> AsyncIterator[TTSStreamChunk]:
        """Stream synthesized audio (low latency).

        Args:
            request: TTS request

        Yields:
            Audio chunks as they're generated
        """
        if not self._is_initialized or self._client is None:
            raise RuntimeError("ElevenLabs backend not initialized")

        voice_id = request.voice_id or self._config.voice_id

        try:
            logger.debug(
                "Starting ElevenLabs synthesis",
                text_length=len(request.text),
                voice_id=voice_id,
            )

            # Create streaming request
            audio_stream = await self._client.text_to_speech.convert(
                text=request.text,
                voice_id=voice_id,
                model_id=self._config.model_id,
                voice_settings=VoiceSettings(
                    stability=self._config.stability,
                    similarity_boost=self._config.similarity_boost,
                ),
                optimize_streaming_latency=self._config.optimize_latency,
                output_format=self._config.output_format,
                stream=True,
            )

            # Stream audio chunks
            chunk_count = 0
            async for chunk in audio_stream:
                if chunk:
                    chunk_count += 1
                    yield TTSStreamChunk(chunk=chunk, is_final=False)

            # Send final chunk marker
            yield TTSStreamChunk(chunk=b"", is_final=True)

            logger.debug(
                "ElevenLabs synthesis complete",
                chunks=chunk_count,
            )

        except Exception as e:
            logger.error(
                "ElevenLabs synthesis failed",
                error=str(e),
                text_preview=request.text[:50],
            )
            raise

    async def health(self) -> TTSHealthStatus:
        """Check ElevenLabs API health.

        Returns:
            Health status
        """
        if not self._is_initialized or self._client is None:
            return TTSHealthStatus(
                ok=False,
                backend="elevenlabs",
                last_error="Not initialized",
            )

        try:
            # Try to get voices list as health check
            voices = await self._client.voices.get_all()
            return TTSHealthStatus(
                ok=True,
                backend="elevenlabs",
            )
        except Exception as e:
            logger.error("ElevenLabs health check failed", error=str(e))
            return TTSHealthStatus(
                ok=False,
                backend="elevenlabs",
                last_error=str(e),
            )

    async def shutdown(self) -> None:
        """Shutdown ElevenLabs client."""
        if self._client:
            # ElevenLabs client doesn't need explicit cleanup
            self._client = None
            self._is_initialized = False
            logger.info("ElevenLabs TTS shutdown")


def create_elevenlabs_backend(api_key: str, voice_id: str | None = None) -> ElevenLabsBackend:
    """Factory function to create ElevenLabs backend.

    Args:
        api_key: ElevenLabs API key
        voice_id: Optional voice ID (default: Sarah)

    Returns:
        Configured ElevenLabs backend
    """
    config = ElevenLabsConfig(api_key=api_key)
    if voice_id:
        config.voice_id = voice_id

    return ElevenLabsBackend(config)
