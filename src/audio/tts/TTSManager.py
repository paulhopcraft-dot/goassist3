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

logger = get_logger(__name__)


@dataclass
class TTSManagerConfig:
    """Configuration for TTS Manager.

    Controls which backend is used and how.
    """

    # Primary backend selection
    primary: str = "xtts-v2"  # "xtts-v2", "kyutai", "mock"

    # Optional backends (disabled by default)
    kyutai_enabled: bool = False
    kyutai_server_url: str = "ws://localhost:8080/tts"

    # XTTS configuration
    xtts_server_url: str = "http://localhost:8020"

    # Fallback behavior
    fallback_to_mock: bool = True  # If primary fails, use mock


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

        else:
            raise ValueError(
                f"Unknown TTS backend: {backend_name}. "
                f"Available: xtts-v2, kyutai, mock"
            )

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize audio from text (one-shot).

        Args:
            request: TTS synthesis request

        Returns:
            Complete audio result
        """
        if not self._initialized or not self._backend:
            await self.init()

        return await self._backend.synthesize(request)

    async def stream(
        self, request: TTSRequest
    ) -> AsyncIterator[TTSStreamChunk]:
        """Stream audio chunks from text.

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks as they become available
        """
        if not self._initialized or not self._backend:
            await self.init()

        async for chunk in self._backend.stream(request):
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
        primary: Primary backend ("xtts-v2", "kyutai", "mock")
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
    """
    config = TTSManagerConfig(
        primary=primary,
        kyutai_enabled=kyutai_enabled,
        **{k: v for k, v in kwargs.items() if hasattr(TTSManagerConfig, k)},
    )
    return TTSManager(config)
