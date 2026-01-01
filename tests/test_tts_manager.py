"""Tests for TTS Manager.

Tests cover:
- TTSManagerConfig defaults and customization
- TTSManager initialization
- Backend selection logic
- Fallback to mock behavior
- synthesize/stream/health methods
- Factory function
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.audio.tts.TTSManager import (
    TTSManager,
    TTSManagerConfig,
    create_tts_manager,
)
from src.audio.tts.backends.interface import (
    TTSRequest,
    TTSResult,
    TTSStreamChunk,
    TTSHealthStatus,
)
from src.audio.tts.backends.mock_backend import MockBackend
from src.audio.tts.sanitize import TextSanitizationError


class TestTTSManagerConfig:
    """Tests for TTSManagerConfig dataclass."""

    def test_default_values(self):
        """Default configuration values."""
        config = TTSManagerConfig()
        assert config.primary == "xtts-v2"
        assert config.kyutai_enabled is False
        assert config.kyutai_server_url == "ws://localhost:8080/tts"
        assert config.xtts_server_url == "http://localhost:8020"
        assert config.fallback_to_mock is True

    def test_custom_primary(self):
        """Custom primary backend."""
        config = TTSManagerConfig(primary="mock")
        assert config.primary == "mock"

    def test_kyutai_enabled(self):
        """Kyutai can be enabled."""
        config = TTSManagerConfig(
            primary="kyutai",
            kyutai_enabled=True,
            kyutai_server_url="ws://custom:9000/tts",
        )
        assert config.kyutai_enabled is True
        assert config.kyutai_server_url == "ws://custom:9000/tts"

    def test_disable_fallback(self):
        """Fallback can be disabled."""
        config = TTSManagerConfig(fallback_to_mock=False)
        assert config.fallback_to_mock is False


class TestTTSManagerInit:
    """Tests for TTSManager initialization."""

    def test_init_with_default_config(self):
        """Initialize with default config."""
        manager = TTSManager()
        assert manager._config.primary == "xtts-v2"
        assert manager._initialized is False
        assert manager._backend is None

    def test_init_with_custom_config(self):
        """Initialize with custom config."""
        config = TTSManagerConfig(primary="mock")
        manager = TTSManager(config)
        assert manager._config.primary == "mock"

    def test_backend_name_before_init(self):
        """Backend name returns config primary before init."""
        config = TTSManagerConfig(primary="mock")
        manager = TTSManager(config)
        assert manager.backend_name == "mock"


class TestTTSManagerMockBackend:
    """Tests for TTSManager with mock backend."""

    @pytest.fixture
    def manager(self):
        """Create manager with mock backend."""
        config = TTSManagerConfig(primary="mock")
        return TTSManager(config)

    @pytest.mark.asyncio
    async def test_init_mock_backend(self, manager):
        """Initialize with mock backend."""
        await manager.init()
        assert manager._initialized is True
        assert manager._backend is not None
        assert manager.backend_name == "mock"

    @pytest.mark.asyncio
    async def test_double_init_is_safe(self, manager):
        """Double init is a no-op."""
        await manager.init()
        await manager.init()
        assert manager._initialized is True

    @pytest.mark.asyncio
    async def test_synthesize(self, manager):
        """Synthesize returns audio."""
        await manager.init()
        request = TTSRequest(text="Hello world")
        result = await manager.synthesize(request)

        assert isinstance(result, TTSResult)
        assert len(result.audio) > 0

    @pytest.mark.asyncio
    async def test_synthesize_auto_inits(self, manager):
        """Synthesize auto-initializes if needed."""
        request = TTSRequest(text="Hello")
        result = await manager.synthesize(request)

        assert manager._initialized is True
        assert isinstance(result, TTSResult)

    @pytest.mark.asyncio
    async def test_stream(self, manager):
        """Stream yields chunks."""
        await manager.init()
        request = TTSRequest(text="Hello world")
        chunks = []

        async for chunk in manager.stream(request):
            chunks.append(chunk)

        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, TTSStreamChunk)

    @pytest.mark.asyncio
    async def test_stream_auto_inits(self, manager):
        """Stream auto-initializes if needed."""
        request = TTSRequest(text="Hello")
        chunks = []

        async for chunk in manager.stream(request):
            chunks.append(chunk)

        assert manager._initialized is True
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_health(self, manager):
        """Health returns status."""
        await manager.init()
        status = await manager.health()

        assert isinstance(status, TTSHealthStatus)
        assert status.ok is True
        assert status.backend == "mock"

    @pytest.mark.asyncio
    async def test_health_before_init(self, manager):
        """Health returns not-ok before init."""
        status = await manager.health()

        assert status.ok is False
        assert status.backend == "none"
        assert status.last_error == "Not initialized"

    @pytest.mark.asyncio
    async def test_shutdown(self, manager):
        """Shutdown clears state."""
        await manager.init()
        assert manager._initialized is True

        await manager.shutdown()
        assert manager._initialized is False
        assert manager._backend is None


class TestTTSManagerFallback:
    """Tests for fallback behavior."""

    @pytest.mark.asyncio
    async def test_fallback_to_mock_on_init_failure(self):
        """Falls back to mock when primary fails."""
        # Use xtts which will fail (no server)
        config = TTSManagerConfig(
            primary="xtts-v2",
            fallback_to_mock=True,
        )
        manager = TTSManager(config)

        await manager.init()

        # Should have fallen back to mock
        assert manager._initialized is True
        assert manager.backend_name == "mock"

    @pytest.mark.asyncio
    async def test_no_fallback_raises(self):
        """Raises when fallback disabled and primary fails."""
        config = TTSManagerConfig(
            primary="xtts-v2",
            fallback_to_mock=False,
        )
        manager = TTSManager(config)

        with pytest.raises(RuntimeError, match="failed to initialize"):
            await manager.init()


class TestTTSManagerBackendSelection:
    """Tests for backend selection."""

    @pytest.mark.asyncio
    async def test_create_mock_backend(self):
        """Create mock backend."""
        config = TTSManagerConfig(primary="mock")
        manager = TTSManager(config)

        backend = await manager._create_backend("mock")
        assert isinstance(backend, MockBackend)

    @pytest.mark.asyncio
    async def test_unknown_backend_raises(self):
        """Unknown backend raises ValueError."""
        manager = TTSManager()

        with pytest.raises(ValueError, match="Unknown TTS backend"):
            await manager._create_backend("unknown")

    @pytest.mark.asyncio
    async def test_kyutai_disabled_raises(self):
        """Kyutai raises if not enabled."""
        config = TTSManagerConfig(kyutai_enabled=False)
        manager = TTSManager(config)

        with pytest.raises(ValueError, match="Kyutai backend is disabled"):
            await manager._create_backend("kyutai")


class TestCreateTTSManagerFactory:
    """Tests for create_tts_manager factory function."""

    def test_default_factory(self):
        """Factory with defaults."""
        manager = create_tts_manager()
        assert manager._config.primary == "xtts-v2"
        assert manager._config.kyutai_enabled is False

    def test_factory_mock(self):
        """Factory with mock primary."""
        manager = create_tts_manager(primary="mock")
        assert manager._config.primary == "mock"

    def test_factory_kyutai(self):
        """Factory with kyutai enabled."""
        manager = create_tts_manager(
            primary="kyutai",
            kyutai_enabled=True,
            kyutai_server_url="ws://custom:8080/tts",
        )
        assert manager._config.primary == "kyutai"
        assert manager._config.kyutai_enabled is True
        assert manager._config.kyutai_server_url == "ws://custom:8080/tts"

    def test_factory_custom_xtts_url(self):
        """Factory with custom XTTS URL."""
        manager = create_tts_manager(
            xtts_server_url="http://custom:8020",
        )
        assert manager._config.xtts_server_url == "http://custom:8020"

    @pytest.mark.asyncio
    async def test_factory_creates_working_manager(self):
        """Factory creates a working manager."""
        manager = create_tts_manager(primary="mock")
        await manager.init()

        request = TTSRequest(text="Test")
        result = await manager.synthesize(request)

        assert len(result.audio) > 0
        await manager.shutdown()


class TestTTSManagerSanitization:
    """Tests for TTSManager input sanitization."""

    @pytest.fixture
    def manager(self):
        """Create manager with mock backend and sanitization enabled."""
        config = TTSManagerConfig(
            primary="mock",
            sanitize_input=True,
            max_text_length=100,
            strip_ssml_tags=True,
        )
        return TTSManager(config)

    @pytest.fixture
    def manager_no_sanitize(self):
        """Create manager with sanitization disabled."""
        config = TTSManagerConfig(
            primary="mock",
            sanitize_input=False,
        )
        return TTSManager(config)

    def test_config_includes_sanitization_fields(self):
        """Config includes sanitization fields."""
        config = TTSManagerConfig()
        assert hasattr(config, "sanitize_input")
        assert hasattr(config, "max_text_length")
        assert hasattr(config, "strip_ssml_tags")
        assert config.sanitize_input is True  # Default enabled
        assert config.max_text_length == 4096
        assert config.strip_ssml_tags is True

    def test_sanitize_config_created(self):
        """Sanitization config is created from manager config."""
        config = TTSManagerConfig(
            max_text_length=500,
            strip_ssml_tags=False,
        )
        manager = TTSManager(config)
        assert manager._sanitize_config.max_length == 500
        assert manager._sanitize_config.strip_ssml_tags is False

    def test_sanitize_request_strips_ssml(self, manager):
        """Sanitize request removes SSML tags."""
        request = TTSRequest(text="Hello <break/> world")
        sanitized = manager._sanitize_request(request)
        assert "<break/>" not in sanitized.text
        assert "Hello" in sanitized.text
        assert "world" in sanitized.text

    def test_sanitize_request_truncates_long_text(self, manager):
        """Sanitize request truncates text to max length."""
        long_text = "A" * 200
        request = TTSRequest(text=long_text)
        sanitized = manager._sanitize_request(request)
        assert len(sanitized.text) == 100

    def test_sanitize_request_strips_control_chars(self, manager):
        """Sanitize request removes control characters."""
        request = TTSRequest(text="Hello\x00\x01world")
        sanitized = manager._sanitize_request(request)
        assert "\x00" not in sanitized.text
        assert "\x01" not in sanitized.text
        assert "Hello" in sanitized.text

    def test_sanitize_request_preserves_voice_id(self, manager):
        """Sanitize request preserves valid voice ID."""
        request = TTSRequest(text="Hello", voice_id="speaker_1")
        sanitized = manager._sanitize_request(request)
        assert sanitized.voice_id == "speaker_1"

    def test_sanitize_request_cleans_voice_id(self, manager):
        """Sanitize request cleans invalid voice ID characters."""
        request = TTSRequest(text="Hello", voice_id="speaker@#$1")
        sanitized = manager._sanitize_request(request)
        # Should be cleaned to alphanumeric only
        assert sanitized.voice_id == "speaker1"

    def test_sanitize_request_preserves_language(self, manager):
        """Sanitize request preserves valid language code."""
        request = TTSRequest(text="Hello", language="en-US")
        sanitized = manager._sanitize_request(request)
        assert sanitized.language == "en-US"

    def test_sanitize_request_preserves_prosody(self, manager):
        """Sanitize request preserves valid prosody."""
        request = TTSRequest(text="Hello", prosody={"speed": 1.5})
        sanitized = manager._sanitize_request(request)
        assert sanitized.prosody["speed"] == 1.5

    def test_sanitize_request_clamps_prosody(self, manager):
        """Sanitize request clamps prosody values."""
        request = TTSRequest(text="Hello", prosody={"speed": 10.0})
        sanitized = manager._sanitize_request(request)
        assert sanitized.prosody["speed"] == 2.0  # Clamped to max

    def test_sanitize_disabled_bypasses(self, manager_no_sanitize):
        """Disabled sanitization passes request through."""
        request = TTSRequest(text="Hello <break/> world")
        sanitized = manager_no_sanitize._sanitize_request(request)
        # Should be same object when disabled
        assert sanitized is request

    @pytest.mark.asyncio
    async def test_synthesize_sanitizes_input(self, manager):
        """Synthesize sanitizes input before backend call."""
        await manager.init()
        request = TTSRequest(text="Hello <break/> world")
        result = await manager.synthesize(request)

        # Should succeed with sanitized text
        assert isinstance(result, TTSResult)
        assert len(result.audio) > 0

    @pytest.mark.asyncio
    async def test_stream_sanitizes_input(self, manager):
        """Stream sanitizes input before backend call."""
        await manager.init()
        request = TTSRequest(text="Hello <break/> world")
        chunks = []

        async for chunk in manager.stream(request):
            chunks.append(chunk)

        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_synthesize_rejects_invalid_text(self, manager):
        """Synthesize rejects non-string text."""
        await manager.init()
        request = TTSRequest(text=123)  # type: ignore

        with pytest.raises(TextSanitizationError):
            await manager.synthesize(request)
