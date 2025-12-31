"""Tests for Audio2Face Engine.

Tests cover:
- Audio2FaceConfig defaults
- Audio2FaceEngine initialization
- Engine lifecycle (start/stop)
- TMF compliance (NEUTRAL style)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.animation.audio2face_engine import (
    Audio2FaceConfig,
    Audio2FaceEngine,
)
from src.config.constants import TMF


class TestAudio2FaceConfig:
    """Tests for Audio2FaceConfig dataclass."""

    def test_default_values(self):
        """Default config has sensible values."""
        config = Audio2FaceConfig()
        assert config.grpc_host == "localhost"
        assert config.grpc_port == 50051
        assert config.target_fps == 30
        assert config.style == "NEUTRAL"
        assert config.enable_emotion is False
        assert config.batch_audio_ms == 20
        assert config.timeout_s == 1.0

    def test_custom_values(self):
        """Custom config values are applied."""
        config = Audio2FaceConfig(
            grpc_host="192.168.1.100",
            grpc_port=50052,
            target_fps=60,
            timeout_s=5.0,
        )
        assert config.grpc_host == "192.168.1.100"
        assert config.grpc_port == 50052
        assert config.target_fps == 60
        assert config.timeout_s == 5.0

    def test_neutral_style_is_default(self):
        """NEUTRAL style is default per TMF Addendum A."""
        config = Audio2FaceConfig()
        assert config.style == "NEUTRAL"

    def test_emotion_disabled_by_default(self):
        """Emotion inference is disabled by default per TMF."""
        config = Audio2FaceConfig()
        assert config.enable_emotion is False


class TestAudio2FaceEngine:
    """Tests for Audio2FaceEngine class."""

    def test_init_default_config(self):
        """Engine initializes with default config."""
        engine = Audio2FaceEngine()
        assert engine._config.style == "NEUTRAL"
        assert engine._config.target_fps == 30

    def test_init_custom_config(self):
        """Engine uses custom config."""
        config = Audio2FaceConfig(target_fps=60)
        engine = Audio2FaceEngine(config=config)
        assert engine._config.target_fps == 60

    def test_init_sets_yield_threshold(self):
        """Engine sets yield threshold from TMF constants."""
        engine = Audio2FaceEngine()
        assert engine._yield_threshold_ms == TMF.ANIMATION_YIELD_THRESHOLD_MS


class TestAudio2FaceEngineLifecycle:
    """Tests for engine start/stop lifecycle."""

    @pytest.fixture
    def engine(self):
        """Create engine for testing."""
        return Audio2FaceEngine()

    @pytest.mark.asyncio
    async def test_stop_without_start(self, engine):
        """Stop without start is safe."""
        # Should not raise
        await engine.stop()


class TestAudio2FaceEngineTMFCompliance:
    """Tests for TMF compliance."""

    def test_default_style_is_neutral(self):
        """Default style must be NEUTRAL per TMF Addendum A §A3.3."""
        engine = Audio2FaceEngine()
        assert engine._config.style == "NEUTRAL"

    def test_emotion_disabled(self):
        """Emotion inference must be disabled per TMF."""
        engine = Audio2FaceEngine()
        assert engine._config.enable_emotion is False

    def test_yield_threshold_matches_tmf(self):
        """Yield threshold matches TMF constant."""
        engine = Audio2FaceEngine()
        assert engine._yield_threshold_ms == 120  # TMF specifies 120ms
