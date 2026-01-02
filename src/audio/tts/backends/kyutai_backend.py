"""Kyutai TTS Backend - Streaming TTS with ultra-low latency.

Wraps the existing KyutaiTTSEngine behind the TTSBackend interface.
This is an OPTIONAL backend, disabled by default.

Features:
- Streaming text input (TTS starts before LLM finishes)
- 220ms TTFB latency
- Word-level timestamps for lip-sync
- Voice cloning from 10s audio sample

Requirements:
- Kyutai TTS server running (default: ws://localhost:8080/tts)

Reference: https://github.com/kyutai-labs/delayed-streams-modeling
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
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
class KyutaiConfig:
    """Configuration for Kyutai backend."""

    # Server connection
    server_url: str = "ws://localhost:8080/tts"

    # Audio settings
    sample_rate: int = 24000

    # Voice settings
    default_voice: str = "default"
    voice_sample_path: str | None = None  # For voice cloning

    # Streaming settings
    chunk_size_ms: int = 20

    # Timeouts
    connect_timeout_s: float = 5.0


class KyutaiBackend(TTSBackend):
    """Kyutai TTS backend.

    Provides ultra-low latency streaming TTS via Kyutai.
    This is an OPTIONAL backend - disabled by default.

    Wraps the existing KyutaiTTSEngine to provide the
    canonical TTSBackend interface for config-based switching.

    Usage:
        config = KyutaiConfig(server_url="ws://localhost:8080/tts")
        backend = KyutaiBackend(config)
        await backend.init()

        async for chunk in backend.stream(TTSRequest(text="Hello")):
            send_audio(chunk.chunk)
    """

    def __init__(self, config: KyutaiConfig | None = None) -> None:
        """Initialize Kyutai backend.

        Args:
            config: Kyutai configuration
        """
        self._config = config or KyutaiConfig()
        self._engine = None
        self._initialized = False
        self._last_error: str | None = None
        self._session_id: str = "kyutai-backend"

    @property
    def name(self) -> str:
        """Backend name identifier."""
        return "kyutai"

    async def init(self) -> None:
        """Initialize Kyutai TTS engine.

        Creates the underlying KyutaiTTSEngine and starts connection.
        """
        try:
            from src.audio.tts.kyutai_tts import KyutaiTTSConfig, KyutaiTTSEngine

            engine_config = KyutaiTTSConfig(
                server_url=self._config.server_url,
                sample_rate=self._config.sample_rate,
                voice_id=self._config.default_voice,
                voice_sample_path=self._config.voice_sample_path,
                chunk_size_ms=self._config.chunk_size_ms,
                connect_timeout_s=self._config.connect_timeout_s,
            )

            self._engine = KyutaiTTSEngine(config=engine_config)
            await self._engine.start(self._session_id)
            self._initialized = True

            logger.info(
                "kyutai_backend_initialized",
                server_url=self._config.server_url,
            )

        except ImportError as e:
            self._last_error = f"Missing dependency: {e}"
            logger.warning(
                "kyutai_backend_missing_dependency",
                error=str(e),
            )

        except Exception as e:
            self._last_error = str(e)
            logger.warning(
                "kyutai_backend_init_error",
                server_url=self._config.server_url,
                error=str(e),
            )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize complete audio for text.

        Collects all streaming chunks and returns as single result.

        Args:
            request: TTS synthesis request

        Returns:
            Complete audio result
        """
        audio_chunks = []
        start_time = asyncio.get_event_loop().time()

        async for chunk in self.stream(request):
            audio_chunks.append(chunk.chunk)

        elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000

        return TTSResult(
            audio=b"".join(audio_chunks),
            sample_rate=self._config.sample_rate,
            latency_ms=elapsed_ms,
        )

    async def stream(
        self, request: TTSRequest
    ) -> AsyncIterator[TTSStreamChunk]:
        """Stream audio chunks for text.

        Leverages Kyutai's streaming text input capability.

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks as they become available
        """
        if not self._initialized or not self._engine:
            raise RuntimeError("Kyutai backend not initialized")

        # Create text stream from request text
        async def text_stream() -> AsyncIterator[str]:
            # Emit text in small chunks to simulate streaming
            for char in request.text:
                yield char

        try:
            chunk_count = 0
            async for audio_bytes in self._engine.synthesize_stream(text_stream()):
                chunk_count += 1
                yield TTSStreamChunk(
                    chunk=audio_bytes,
                    is_final=False,
                    latency_ms=float(chunk_count * self._config.chunk_size_ms),
                )

            # Final chunk
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
        if not self._initialized:
            return TTSHealthStatus(
                ok=False,
                backend=self.name,
                last_error=self._last_error or "Not initialized",
            )

        # Try to verify connection is still alive
        if self._engine and hasattr(self._engine, '_state'):
            if self._engine._state.ws and self._engine._state.running:
                return TTSHealthStatus(
                    ok=True,
                    backend=self.name,
                )

        return TTSHealthStatus(
            ok=False,
            backend=self.name,
            last_error=self._last_error or "Connection lost",
        )

    async def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
        if self._engine:
            await self._engine.stop()
            self._engine = None
        self._initialized = False


def create_kyutai_backend(
    server_url: str | None = None,
    **kwargs,
) -> KyutaiBackend:
    """Factory function to create Kyutai backend.

    Args:
        server_url: Kyutai server WebSocket URL
        **kwargs: Additional config options

    Returns:
        Configured KyutaiBackend instance
    """
    config = KyutaiConfig(
        server_url=server_url or "ws://localhost:8080/tts",
        **kwargs,
    )
    return KyutaiBackend(config)
