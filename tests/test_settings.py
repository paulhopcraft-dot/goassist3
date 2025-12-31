"""Tests for Application Settings.

Tests environment-based configuration and validation.
Reference: Ops-Runbook-v3.0.md Section 6.1
"""

import os
import pytest

from src.config.settings import Settings, get_settings
from src.config.constants import TMF


class TestSettingsDefaults:
    """Tests for default settings values."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear settings cache before each test."""
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_api_defaults(self):
        """API defaults are correct."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
        )
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8081
        assert settings.log_level == "INFO"
        assert settings.environment == "development"

    def test_session_defaults(self):
        """Session values are in valid range."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
        )
        # Values may come from env, but should be in valid range
        assert 1 <= settings.max_concurrent_sessions <= 100
        assert 60 <= settings.session_idle_timeout_s <= 3600

    def test_llm_defaults(self):
        """LLM defaults are correct."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
        )
        assert settings.llm_engine == "vllm"
        assert settings.llm_max_context_tokens == TMF.LLM_MAX_CONTEXT_TOKENS
        assert settings.llm_prefix_caching is True
        assert settings.llm_base_url == "http://localhost:8000/v1"

    def test_audio_defaults(self):
        """Audio defaults match TMF."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
        )
        assert settings.audio_packet_ms == TMF.AUDIO_PACKET_DURATION_MS
        assert settings.audio_overlap_ms == TMF.AUDIO_OVERLAP_MS
        assert settings.vad_engine == "silero"

    def test_animation_defaults(self):
        """Animation defaults are correct."""
        settings = Settings(
            _env_file=None,
            animation_enabled=True,
            animation_engine="audio2face",
        )
        assert settings.animation_enabled is True
        assert settings.animation_engine == "audio2face"
        assert settings.animation_drop_if_lag_ms == TMF.ANIMATION_YIELD_LAG_MS
        assert settings.animation_slow_freeze_ms == TMF.ANIMATION_SLOW_FREEZE_MS

    def test_tts_defaults(self):
        """TTS settings are valid."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
        )
        # Engine may come from env, but should be valid
        assert settings.tts_engine in ["mock", "xtts-v2", "kyutai"]
        assert isinstance(settings.tts_fallback_to_mock, bool)
        assert settings.xtts_server_url.startswith("http")


class TestSettingsValidation:
    """Tests for settings validation."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_port_range(self):
        """Port must be in valid range."""
        # Valid port
        settings = Settings(
            _env_file=None,
            api_port=8080,
            animation_enabled=False,
        )
        assert settings.api_port == 8080

        # Invalid port (too low)
        with pytest.raises(ValueError):
            Settings(
                _env_file=None,
                api_port=80,  # Below 1024
                animation_enabled=False,
            )

    def test_max_sessions_range(self):
        """Max sessions must be in range."""
        # Valid
        settings = Settings(
            _env_file=None,
            max_concurrent_sessions=50,
            animation_enabled=False,
        )
        assert settings.max_concurrent_sessions == 50

        # Too high
        with pytest.raises(ValueError):
            Settings(
                _env_file=None,
                max_concurrent_sessions=200,  # Above 100
                animation_enabled=False,
            )

    def test_context_tokens_range(self):
        """Context tokens must be in range."""
        # Valid
        settings = Settings(
            _env_file=None,
            llm_max_context_tokens=4096,
            animation_enabled=False,
        )
        assert settings.llm_max_context_tokens == 4096

        # Too high
        with pytest.raises(ValueError):
            Settings(
                _env_file=None,
                llm_max_context_tokens=16384,  # Above 8192
                animation_enabled=False,
            )

    def test_animation_engine_required(self):
        """Animation engine required if animation enabled."""
        with pytest.raises(ValueError, match="animation_engine is required"):
            Settings(
                _env_file=None,
                animation_enabled=True,
                animation_engine=None,
            )

    def test_animation_engine_not_required_when_disabled(self):
        """Animation engine not required if animation disabled."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
            animation_engine=None,
        )
        assert settings.animation_engine is None

    def test_turn_credentials_required(self):
        """TURN credentials required with TURN server."""
        with pytest.raises(ValueError, match="webrtc_turn_username"):
            Settings(
                _env_file=None,
                animation_enabled=False,
                webrtc_turn_server="turn:example.com",
                webrtc_turn_username=None,
            )

    def test_turn_credentials_not_required_without_server(self):
        """TURN credentials not required without TURN server."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
            webrtc_turn_server=None,
        )
        assert settings.webrtc_turn_username is None

    def test_api_key_required_in_production(self):
        """API key required in production with auth enabled."""
        with pytest.raises(ValueError, match="api_key is required"):
            Settings(
                _env_file=None,
                environment="production",
                auth_enabled=True,
                api_key=None,
                animation_enabled=False,
            )

    def test_api_key_not_required_in_development(self):
        """API key not required in development."""
        settings = Settings(
            _env_file=None,
            environment="development",
            auth_enabled=True,
            api_key=None,
            animation_enabled=False,
        )
        assert settings.api_key is None


class TestSettingsLiteralTypes:
    """Tests for literal type validation."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_valid_log_levels(self):
        """Valid log levels are accepted."""
        for level in ["DEBUG", "INFO", "WARN", "ERROR"]:
            settings = Settings(
                _env_file=None,
                log_level=level,
                animation_enabled=False,
            )
            assert settings.log_level == level

    def test_valid_environments(self):
        """Valid environments are accepted."""
        for env in ["development", "staging"]:
            settings = Settings(
                _env_file=None,
                environment=env,
                animation_enabled=False,
            )
            assert settings.environment == env

    def test_valid_llm_engines(self):
        """Valid LLM engines are accepted."""
        for engine in ["mock", "vllm"]:
            settings = Settings(
                _env_file=None,
                llm_engine=engine,
                animation_enabled=False,
            )
            assert settings.llm_engine == engine

    def test_valid_vad_engines(self):
        """Valid VAD engines are accepted."""
        for engine in ["silero", "webrtc"]:
            settings = Settings(
                _env_file=None,
                vad_engine=engine,
                animation_enabled=False,
            )
            assert settings.vad_engine == engine

    def test_valid_tts_engines(self):
        """Valid TTS engines are accepted."""
        for engine in ["mock", "xtts-v2", "kyutai"]:
            settings = Settings(
                _env_file=None,
                tts_engine=engine,
                animation_enabled=False,
            )
            assert settings.tts_engine == engine


class TestSettingsAliases:
    """Tests for property aliases."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_turn_url_alias(self):
        """turn_url is alias for webrtc_turn_server."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
            webrtc_turn_server="turn:example.com",
            webrtc_turn_username="user",
            webrtc_turn_password="pass",
        )
        assert settings.turn_url == settings.webrtc_turn_server

    def test_turn_username_alias(self):
        """turn_username is alias for webrtc_turn_username."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
            webrtc_turn_server="turn:example.com",
            webrtc_turn_username="testuser",
            webrtc_turn_password="pass",
        )
        assert settings.turn_username == settings.webrtc_turn_username

    def test_turn_credential_alias(self):
        """turn_credential is alias for webrtc_turn_password."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
            webrtc_turn_server="turn:example.com",
            webrtc_turn_username="user",
            webrtc_turn_password="testpass",
        )
        assert settings.turn_credential == settings.webrtc_turn_password


class TestGetSettings:
    """Tests for get_settings factory."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_returns_settings(self):
        """get_settings returns Settings instance."""
        # Set env var to make it work
        os.environ.setdefault("ANIMATION_ENABLED", "false")
        try:
            settings = get_settings()
            assert isinstance(settings, Settings)
        finally:
            pass

    def test_caches_result(self):
        """get_settings caches result."""
        os.environ.setdefault("ANIMATION_ENABLED", "false")
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestKyutaiSettings:
    """Tests for Kyutai TTS settings."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_kyutai_defaults(self):
        """Kyutai defaults are correct."""
        settings = Settings(
            _env_file=None,
            animation_enabled=False,
        )
        assert settings.kyutai_enabled is False
        assert settings.kyutai_tts_url == "ws://localhost:8080/tts"
        assert settings.kyutai_voice_id == "default"
        assert settings.kyutai_sample_rate == 24000

    def test_kyutai_sample_rate_range(self):
        """Kyutai sample rate must be in range."""
        # Valid
        settings = Settings(
            _env_file=None,
            kyutai_sample_rate=48000,
            animation_enabled=False,
        )
        assert settings.kyutai_sample_rate == 48000

        # Too low
        with pytest.raises(ValueError):
            Settings(
                _env_file=None,
                kyutai_sample_rate=8000,  # Below 16000
                animation_enabled=False,
            )
