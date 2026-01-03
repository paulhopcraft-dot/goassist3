"""TTS Manager - Config-based TTS backend selection.

Provides a single entry point for TTS operations.
Backend selection is done via configuration ONLY.

Higher-level code should use TTSManager and be blind to
which backend is actually being used.

Usage:
    manager = TTSManager(config)
    await manager.init()

    # Streaming synthesis
    async for chunk in manager.stream(TTSRequest(text="Hello")):
        send_audio(chunk.chunk)

    # One-shot synthesis
    result = await manager.synthesize(TTSRequest(text="Hello"))

    # Health check
    status = await manager.health()

    await manager.shutdown()
"""

from __future__ import annotations

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
from src.audio.tts.backends.mock_backend import MockBackend
from src.audio.tts.sanitize import (
    SanitizationConfig,
    sanitize_text,
    sanitize_prosody,
    sanitize_voice_id,
    sanitize_language,
    TextSanitizationError,
)

logger = get_logger(__name__)


@dataclass
class TTSManagerConfig:
    """Configuration for TTS Manager.

    Controls which backend is used and how.
    """

    # Primary backend selection
    primary: str = "xtts-v2"  # "xtts-v2", "kyutai", "elevenlabs", "mock"

    # Optional backends (disabled by default)
    kyutai_enabled: bool = False
    kyutai_server_url: str = "ws://localhost:8080/tts"

    # XTTS configuration
    xtts_server_url: str = "http://localhost:8020"

    # ElevenLabs configuration (cloud API)
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str = "EXAVITQu4vr4xnSDxMaL"  # Sarah (default)
    elevenlabs_model: str = "eleven_turbo_v2"  # Fastest model

    # Fallback behavior
    fallback_to_mock: bool = True  # If primary fails, use mock

    # Input sanitization
    sanitize_input: bool = True  # Enable text sanitization
    max_text_length: int = 4096  # Maximum text length
    strip_ssml_tags: bool = True  # Remove SSML-like tags


class TTSManager:
    """TTS Manager - Unified TTS interface with config-based backend selection.

    This is the entry point for all TTS operations.
    The manager:
    - Selects the appropriate backend based on config
    - Initializes the backend on first use
    - Provides fallback to mock if primary fails
    - Exposes the canonical TTSBackend interface

    Important:
    - Kyutai is NOT instantiated unless kyutai_enabled=True
    - XTTS-v2 is the default primary backend
    - All switching is done via config, not runtime
    """

    def __init__(self, config: TTSManagerConfig | None = None) -> None:
        """Initialize TTS manager.

        Args:
            config: Manager configuration
        """
        self._config = config or TTSManagerConfig()
        self._backend: TTSBackend | None = None
        self._initialized = False

        # Create sanitization config from manager config
        self._sanitize_config = SanitizationConfig(
            max_length=self._config.max_text_length,
            strip_ssml_tags=self._config.strip_ssml_tags,
        )

    @property
    def backend_name(self) -> str:
        """Currently selected backend name."""
        if self._backend:
            return self._backend.name
        return self._config.primary

    async def init(self) -> None:
        """Initialize the configured TTS backend.

        Creates and initializes the backend based on config.
        If the primary backend fails and fallback_to_mock is True,
        falls back to MockBackend.
        """
        if self._initialized:
            return

        # Select backend based on config
        backend = await self._create_backend(self._config.primary)

        # Try to initialize
        try:
            await backend.init()
            health = await backend.health()

            if health.ok:
                self._backend = backend
                self._initialized = True
                logger.info(
                    "tts_manager_initialized",
                    backend=backend.name,
                )
                return
            else:
                logger.warning(
                    "tts_backend_unhealthy",
                    backend=backend.name,
                    error=health.last_error,
                )

        except Exception as e:
            logger.warning(
                "tts_backend_init_failed",
                backend=backend.name,
                error=str(e),
            )

        # Fallback to mock if enabled
        if self._config.fallback_to_mock:
            logger.info(
                "tts_fallback_to_mock",
                original_backend=self._config.primary,
            )
            self._backend = MockBackend()
            await self._backend.init()
            self._initialized = True
        else:
            raise RuntimeError(
                f"TTS backend '{self._config.primary}' failed to initialize"
            )

    async def _create_backend(self, backend_name: str) -> TTSBackend:
        """Create a backend instance by name.

        Args:
            backend_name: Backend identifier

        Returns:
            Configured backend instance

        Raises:
            ValueError: If backend is unknown or disabled
        """
        if backend_name == "mock":
            return MockBackend()

        elif backend_name == "xtts-v2":
            from src.audio.tts.backends.xtts_backend import XTTSBackend, XTTSConfig

            config = XTTSConfig(
                server_url=self._config.xtts_server_url,
            )
            return XTTSBackend(config)

        elif backend_name == "kyutai":
            # Only create Kyutai if explicitly enabled
            if not self._config.kyutai_enabled:
                raise ValueError(
                    "Kyutai backend is disabled. "
                    "Set kyutai_enabled=True to use it."
                )

            from src.audio.tts.backends.kyutai_backend import (
                KyutaiBackend,
                KyutaiConfig,
            )

            config = KyutaiConfig(
                server_url=self._config.kyutai_server_url,
            )
            return KyutaiBackend(config)

        elif backend_name == "elevenlabs":
            # ElevenLabs cloud API backend
            if not self._config.elevenlabs_api_key:
                raise ValueError(
                    "ElevenLabs API key required. "
                    "Set ELEVENLABS_API_KEY in environment or config."
                )

            from src.audio.tts.backends.elevenlabs_backend import (
                ElevenLabsBackend,
                ElevenLabsConfig,
            )

            config = ElevenLabsConfig(
                api_key=self._config.elevenlabs_api_key,
                voice_id=self._config.elevenlabs_voice_id,
                model_id=self._config.elevenlabs_model,
            )
            return ElevenLabsBackend(config)

        else:
            raise ValueError(
                f"Unknown TTS backend: {backend_name}. "
                f"Available: xtts-v2, kyutai, elevenlabs, mock"
            )

    def _sanitize_request(self, request: TTSRequest) -> TTSRequest:
        """Sanitize a TTS request if sanitization is enabled.

        Args:
            request: Original TTS request

        Returns:
            Sanitized TTS request (or original if sanitization disabled)

        Raises:
            TextSanitizationError: If text cannot be sanitized
        """
        if not self._config.sanitize_input:
            return request

        # Sanitize text (required field)
        sanitized_text = sanitize_text(request.text, self._sanitize_config)

        # Sanitize optional fields
        sanitized_voice_id = sanitize_voice_id(request.voice_id)
        sanitized_language = sanitize_language(request.language)
        sanitized_prosody = sanitize_prosody(request.prosody, self._sanitize_config)

        # Create new request with sanitized values
        return TTSRequest(
            text=sanitized_text,
            voice_id=sanitized_voice_id if sanitized_voice_id else request.voice_id,
            language=sanitized_language if sanitized_language else request.language,
            prosody=sanitized_prosody if sanitized_prosody else request.prosody,
        )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize audio from text (one-shot).

        Args:
            request: TTS synthesis request

        Returns:
            Complete audio result

        Raises:
            TextSanitizationError: If text cannot be sanitized
        """
        if not self._initialized or not self._backend:
            await self.init()

        sanitized_request = self._sanitize_request(request)
        return await self._backend.synthesize(sanitized_request)

    async def stream(
        self, request: TTSRequest
    ) -> AsyncIterator[TTSStreamChunk]:
        """Stream audio chunks from text.

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks as they become available

        Raises:
            TextSanitizationError: If text cannot be sanitized
        """
        if not self._initialized or not self._backend:
            await self.init()

        sanitized_request = self._sanitize_request(request)
        async for chunk in self._backend.stream(sanitized_request):
            yield chunk

    async def health(self) -> TTSHealthStatus:
        """Check backend health.

        Returns:
            Health status of current backend
        """
        if not self._backend:
            return TTSHealthStatus(
                ok=False,
                backend="none",
                last_error="Not initialized",
            )

        return await self._backend.health()

    async def shutdown(self) -> None:
        """Shutdown the manager and cleanup resources."""
        if self._backend:
            await self._backend.shutdown()
            self._backend = None
        self._initialized = False

        logger.info("tts_manager_shutdown")


def create_tts_manager(
    primary: str = "xtts-v2",
    kyutai_enabled: bool = False,
    **kwargs,
) -> TTSManager:
    """Factory function to create TTS manager.

    Args:
        primary: Primary backend ("xtts-v2", "kyutai", "elevenlabs", "mock")
        kyutai_enabled: Whether Kyutai is available
        **kwargs: Additional config options

    Returns:
        Configured TTSManager instance

    Examples:
        # Production with XTTS (default)
        manager = create_tts_manager()

        # Development with mock
        manager = create_tts_manager(primary="mock")

        # Enable Kyutai as primary
        manager = create_tts_manager(
            primary="kyutai",
            kyutai_enabled=True,
            kyutai_server_url="ws://localhost:8080/tts",
        )

        # Cloud API with ElevenLabs
        manager = create_tts_manager(
            primary="elevenlabs",
            elevenlabs_api_key="your-key",
            elevenlabs_voice_id="EXAVITQu4vr4xnSDxMaL",
        )
    """
    config = TTSManagerConfig(
        primary=primary,
        kyutai_enabled=kyutai_enabled,
        **{k: v for k, v in kwargs.items() if hasattr(TTSManagerConfig, k)},
    )
    return TTSManager(config)
