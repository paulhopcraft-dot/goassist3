"""XTTS Backend - Coqui XTTS-v2 TTS integration.

Connects to a running Coqui XTTS-v2 server for high-quality
streaming text-to-speech synthesis.

This is the PRIMARY production TTS backend.

Requirements:
- XTTS-v2 model server running (default: http://localhost:8020)
- Model: /workspace/models/tts/xtts-v2

Reference: https://github.com/coqui-ai/TTS
"""

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

from src.observability.logging import get_logger
from src.audio.tts.backends.interface import (
    TTSBackend,
    TTSHealthStatus,
    TTSRequest,
    TTSResult,
    TTSStreamChunk,
)

logger = get_logger(__name__)


@dataclass
class XTTSConfig:
    """Configuration for XTTS backend."""

    # Server connection
    server_url: str = "http://localhost:8020"

    # Audio settings
    sample_rate: int = 24000

    # Default voice settings
    default_voice: str = "default"
    default_language: str = "en"

    # Streaming settings
    chunk_size_ms: int = 50  # Audio chunk duration

    # Timeouts
    connect_timeout_s: float = 10.0
    request_timeout_s: float = 30.0


class XTTSBackend(TTSBackend):
    """Coqui XTTS-v2 TTS backend.

    Provides high-quality streaming TTS via XTTS-v2.
    This is the primary production backend.

    Features:
    - Multi-language support (17+ languages)
    - Voice cloning from reference audio
    - Streaming synthesis for low latency
    - High quality neural TTS

    Usage:
        config = XTTSConfig(server_url="http://localhost:8020")
        backend = XTTSBackend(config)
        await backend.init()

        async for chunk in backend.stream(TTSRequest(text="Hello")):
            send_audio(chunk.chunk)
    """

    def __init__(self, config: XTTSConfig | None = None) -> None:
        """Initialize XTTS backend.

        Args:
            config: XTTS configuration
        """
        self._config = config or XTTSConfig()
        self._initialized = False
        self._session = None
        self._last_error: str | None = None

    @property
    def name(self) -> str:
        """Backend name identifier."""
        return "xtts-v2"

    async def init(self) -> None:
        """Initialize connection to XTTS server.

        Establishes HTTP session and validates server is running.
        """
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(
                connect=self._config.connect_timeout_s,
                total=self._config.request_timeout_s,
            )
            self._session = aiohttp.ClientSession(timeout=timeout)

            # Validate server is running
            async with self._session.get(
                f"{self._config.server_url}/health"
            ) as response:
                if response.status == 200:
                    self._initialized = True
                    logger.info(
                        "xtts_backend_initialized",
                        server_url=self._config.server_url,
                    )
                else:
                    self._last_error = f"Server returned {response.status}"
                    logger.warning(
                        "xtts_backend_init_failed",
                        server_url=self._config.server_url,
                        status=response.status,
                    )

        except ImportError:
            self._last_error = "aiohttp not installed"
            logger.warning("xtts_backend_missing_aiohttp")

        except Exception as e:
            self._last_error = str(e)
            logger.warning(
                "xtts_backend_init_error",
                server_url=self._config.server_url,
                error=str(e),
            )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize complete audio for text.

        Args:
            request: TTS synthesis request

        Returns:
            Complete audio result
        """
        if not self._initialized or not self._session:
            raise RuntimeError("XTTS backend not initialized")

        voice_id = request.voice_id or self._config.default_voice
        language = request.language or self._config.default_language

        try:
            payload = {
                "text": request.text,
                "speaker": voice_id,
                "language": language,
            }

            if request.prosody:
                payload.update(request.prosody)

            async with self._session.post(
                f"{self._config.server_url}/api/tts",
                json=payload,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    self._last_error = error
                    raise RuntimeError(f"XTTS synthesis failed: {error}")

                audio = await response.read()
                return TTSResult(
                    audio=audio,
                    sample_rate=self._config.sample_rate,
                    latency_ms=0.0,
                )

        except Exception as e:
            self._last_error = str(e)
            raise

    async def stream(
        self, request: TTSRequest
    ) -> AsyncIterator[TTSStreamChunk]:
        """Stream audio chunks for text.

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks as they become available
        """
        if not self._initialized or not self._session:
            raise RuntimeError("XTTS backend not initialized")

        voice_id = request.voice_id or self._config.default_voice
        language = request.language or self._config.default_language

        try:
            payload = {
                "text": request.text,
                "speaker": voice_id,
                "language": language,
                "stream": True,
            }

            if request.prosody:
                payload.update(request.prosody)

            async with self._session.post(
                f"{self._config.server_url}/api/tts-stream",
                json=payload,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    self._last_error = error
                    raise RuntimeError(f"XTTS streaming failed: {error}")

                chunk_count = 0
                async for chunk in response.content.iter_chunked(
                    self._config.sample_rate * 2 * self._config.chunk_size_ms // 1000
                ):
                    chunk_count += 1
                    yield TTSStreamChunk(
                        chunk=chunk,
                        is_final=False,
                        latency_ms=float(chunk_count * self._config.chunk_size_ms),
                    )

                # Final empty chunk to signal completion
                yield TTSStreamChunk(
                    chunk=b"",
                    is_final=True,
                )

        except Exception as e:
            self._last_error = str(e)
            raise

    async def health(self) -> TTSHealthStatus:
        """Check backend health.

        Returns:
            Health status
        """
        if not self._session:
            return TTSHealthStatus(
                ok=False,
                backend=self.name,
                last_error="Not initialized",
            )

        try:
            async with self._session.get(
                f"{self._config.server_url}/health"
            ) as response:
                if response.status == 200:
                    return TTSHealthStatus(
                        ok=True,
                        backend=self.name,
                    )
                else:
                    return TTSHealthStatus(
                        ok=False,
                        backend=self.name,
                        last_error=f"Server returned {response.status}",
                    )

        except Exception as e:
            return TTSHealthStatus(
                ok=False,
                backend=self.name,
                last_error=str(e),
            )

    async def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        self._initialized = False


def create_xtts_backend(
    server_url: str | None = None,
    **kwargs,
) -> XTTSBackend:
    """Factory function to create XTTS backend.

    Args:
        server_url: XTTS server URL
        **kwargs: Additional config options

    Returns:
        Configured XTTSBackend instance
    """
    config = XTTSConfig(
        server_url=server_url or "http://localhost:8020",
        **kwargs,
    )
    return XTTSBackend(config)
