"""Tests for Conversation Pipeline.

Tests cover:
- Pipeline initialization
- Component wiring
- Audio processing flow
- Barge-in handling
- End-to-end turn processing
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.session import Session, SessionConfig
from src.orchestrator.pipeline import (
    ConversationPipeline,
    PipelineConfig,
    create_pipeline,
)
from src.orchestrator.state_machine import SessionState


class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PipelineConfig()

        assert config.enable_vad is True
        assert config.enable_asr is True
        assert config.enable_llm is True
        assert config.enable_tts is True
        assert config.enable_animation is True
        assert config.enable_livelink is True
        assert config.tts_engine == "mock"
        assert config.livelink_port == 11111

    def test_custom_config(self):
        """Test custom configuration."""
        config = PipelineConfig(
            enable_animation=False,
            enable_livelink=False,
            tts_engine="kyutai",
            livelink_host="192.168.1.100",
        )

        assert config.enable_animation is False
        assert config.enable_livelink is False
        assert config.tts_engine == "kyutai"
        assert config.livelink_host == "192.168.1.100"


class TestPipelineCreation:
    """Tests for pipeline initialization."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="test-session")

    @pytest.fixture
    def minimal_config(self):
        """Config with most components disabled for fast tests."""
        return PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

    def test_create_pipeline(self, session, minimal_config):
        """Test pipeline creation."""
        pipeline = ConversationPipeline(session, minimal_config)

        assert pipeline.session == session
        assert pipeline.is_running is False

    @pytest.mark.asyncio
    async def test_start_stop_minimal(self, session, minimal_config):
        """Test pipeline start/stop with minimal config."""
        pipeline = ConversationPipeline(session, minimal_config)

        await pipeline.start()
        assert pipeline.is_running is True

        await pipeline.stop()
        assert pipeline.is_running is False

    @pytest.mark.asyncio
    async def test_double_start_is_safe(self, session, minimal_config):
        """Test calling start twice doesn't cause issues."""
        pipeline = ConversationPipeline(session, minimal_config)

        await pipeline.start()
        await pipeline.start()  # Should be no-op

        assert pipeline.is_running is True

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_double_stop_is_safe(self, session, minimal_config):
        """Test calling stop twice doesn't cause issues."""
        pipeline = ConversationPipeline(session, minimal_config)

        await pipeline.start()
        await pipeline.stop()
        await pipeline.stop()  # Should be no-op

        assert pipeline.is_running is False


class TestPipelineWithMocks:
    """Tests with mocked components."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="mock-session")

    @pytest.fixture
    def mock_config(self):
        """Config for mock testing."""
        return PipelineConfig(
            enable_vad=False,
            enable_asr=True,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

    @pytest.mark.asyncio
    async def test_audio_callback_set(self, session):
        """Test audio output callback is settable."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        audio_received = []

        def on_audio(audio: bytes):
            audio_received.append(audio)

        pipeline.set_audio_output_callback(on_audio)
        await pipeline.start()

        # Callback should be set
        assert pipeline._on_audio_output is not None

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_transcript_callback_set(self, session):
        """Test transcript callback is settable."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        transcripts = []

        def on_transcript(text: str, is_final: bool):
            transcripts.append((text, is_final))

        pipeline.set_transcript_callback(on_transcript)
        await pipeline.start()

        assert pipeline._on_transcript is not None

        await pipeline.stop()


class TestPipelineBargeIn:
    """Tests for barge-in handling."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="bargein-session")

    @pytest.mark.asyncio
    async def test_barge_in_cancels_generation(self, session):
        """Test barge-in cancels ongoing generation."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        await pipeline.start()

        # Simulate that we're in SPEAKING state
        await session.on_speech_start()  # IDLE -> LISTENING
        await session.on_endpoint_detected(100)  # LISTENING -> THINKING
        await session.on_response_ready()  # THINKING -> SPEAKING

        assert session.state == SessionState.SPEAKING

        # Trigger barge-in
        await pipeline.handle_barge_in()

        # Should transition through INTERRUPTED to LISTENING
        assert session.state == SessionState.LISTENING

        await pipeline.stop()


class TestFactoryFunction:
    """Tests for create_pipeline factory."""

    @pytest.mark.asyncio
    async def test_create_pipeline_starts_automatically(self):
        """Test factory function creates and starts pipeline."""
        session = Session(session_id="factory-session")

        pipeline = await create_pipeline(
            session,
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

        assert pipeline.is_running is True

        await pipeline.stop()


class TestPipelineProcessAudio:
    """Tests for audio processing flow."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="audio-session")

    @pytest.mark.asyncio
    async def test_process_audio_when_not_running(self, session):
        """Test process_audio is no-op when not running."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        # Should not raise
        await pipeline.process_audio(b"\x00" * 640, 0)

    @pytest.mark.asyncio
    async def test_process_audio_when_running(self, session):
        """Test process_audio passes through when running."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        await pipeline.start()

        # Should not raise
        await pipeline.process_audio(b"\x00" * 640, 100)

        await pipeline.stop()
