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


class TestPipelineWithAnimation:
    """Tests for pipeline with animation enabled."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="animation-session")

    @pytest.mark.asyncio
    async def test_pipeline_initializes_audio2face(self, session):
        """Test pipeline initializes Audio2Face engine when animation enabled."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=True,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        await pipeline.start()

        # Animation engine should be initialized
        assert pipeline._animation is not None
        assert pipeline.is_running is True

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_pipeline_with_animation_and_livelink(self, session):
        """Test pipeline with both animation and livelink enabled."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=True,
            enable_livelink=True,
        )
        pipeline = ConversationPipeline(session, config)

        await pipeline.start()

        assert pipeline._animation is not None
        assert pipeline._livelink is not None
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


class TestPipelineASRCallbacks:
    """Tests for ASR callback handling."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="asr-callback-session")

    @pytest.fixture
    def minimal_config(self):
        """Minimal config for testing."""
        return PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

    @pytest.mark.asyncio
    async def test_handle_asr_final_stores_transcript(self, session, minimal_config):
        """Test ASR final callback stores transcript."""
        pipeline = ConversationPipeline(session, minimal_config)
        await pipeline.start()

        pipeline._handle_asr_final("Hello world", 100, 500)

        assert pipeline._current_transcript == "Hello world"

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_handle_asr_final_invokes_callback(self, session, minimal_config):
        """Test ASR final invokes transcript callback."""
        pipeline = ConversationPipeline(session, minimal_config)
        transcripts = []

        def on_transcript(text: str, is_final: bool):
            transcripts.append((text, is_final))

        pipeline.set_transcript_callback(on_transcript)
        await pipeline.start()

        pipeline._handle_asr_final("Test text", 100, 500)

        assert len(transcripts) == 1
        assert transcripts[0] == ("Test text", True)

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_handle_asr_endpoint_prevents_duplicate_turns(
        self, session, minimal_config
    ):
        """Test endpoint handler prevents duplicate turn processing."""
        pipeline = ConversationPipeline(session, minimal_config)
        await pipeline.start()

        # Set processing flag
        pipeline._processing_turn = True

        # This should be skipped
        pipeline._handle_asr_endpoint(1000)

        # Allow async task to run
        await asyncio.sleep(0.01)

        # Still should be True (not reset by skipped handler)
        assert pipeline._processing_turn is True

        await pipeline.stop()


class TestPipelineTurnProcessing:
    """Tests for turn processing flow."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="turn-session")

    @pytest.fixture
    def minimal_config(self):
        """Minimal config for testing."""
        return PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

    @pytest.mark.asyncio
    async def test_process_turn_skips_empty_transcript(self, session, minimal_config):
        """Test empty transcript is skipped."""
        pipeline = ConversationPipeline(session, minimal_config)
        await pipeline.start()

        pipeline._current_transcript = ""
        pipeline._processing_turn = True

        await pipeline._process_turn(1000)

        # Flag should be cleared
        assert pipeline._processing_turn is False

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_process_turn_skips_whitespace_transcript(
        self, session, minimal_config
    ):
        """Test whitespace-only transcript is skipped."""
        pipeline = ConversationPipeline(session, minimal_config)
        await pipeline.start()

        pipeline._current_transcript = "   "
        pipeline._processing_turn = True

        await pipeline._process_turn(1000)

        assert pipeline._processing_turn is False

        await pipeline.stop()


class TestPipelineDefaultConfig:
    """Tests for pipeline with default config."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="default-config-session")

    def test_pipeline_accepts_none_config(self, session):
        """Test pipeline accepts None config."""
        pipeline = ConversationPipeline(session, None)
        assert pipeline._config is not None
        assert pipeline._config.enable_vad is True

    def test_pipeline_uses_default_when_no_config(self, session):
        """Test pipeline uses default config when not provided."""
        pipeline = ConversationPipeline(session)
        assert pipeline._config.enable_vad is True
        assert pipeline._config.enable_asr is True


class TestPipelineProperties:
    """Tests for pipeline properties."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="props-session")

    @pytest.fixture
    def minimal_config(self):
        """Minimal config for testing."""
        return PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

    def test_session_property(self, session, minimal_config):
        """Test session property returns correct session."""
        pipeline = ConversationPipeline(session, minimal_config)
        assert pipeline.session is session

    def test_is_running_initially_false(self, session, minimal_config):
        """Test is_running is initially False."""
        pipeline = ConversationPipeline(session, minimal_config)
        assert pipeline.is_running is False

    @pytest.mark.asyncio
    async def test_is_running_true_after_start(self, session, minimal_config):
        """Test is_running is True after start."""
        pipeline = ConversationPipeline(session, minimal_config)
        await pipeline.start()
        assert pipeline.is_running is True
        await pipeline.stop()


class TestPipelineWithVAD:
    """Tests for pipeline with VAD enabled."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="vad-session")

    @pytest.mark.asyncio
    async def test_pipeline_with_vad_enabled(self, session):
        """Test pipeline initializes VAD when enabled."""
        config = PipelineConfig(
            enable_vad=True,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.SileroVAD") as mock_vad_cls:
            mock_vad = AsyncMock()
            mock_vad.start = AsyncMock()
            mock_vad.stop = AsyncMock()
            mock_vad.process = AsyncMock(return_value=False)
            mock_vad_cls.return_value = mock_vad

            await pipeline.start()
            assert pipeline._vad is not None

            await pipeline.stop()
            mock_vad.stop.assert_awaited()

    @pytest.mark.asyncio
    async def test_process_audio_with_vad(self, session):
        """Test process_audio with VAD enabled."""
        config = PipelineConfig(
            enable_vad=True,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.SileroVAD") as mock_vad_cls:
            mock_vad = AsyncMock()
            mock_vad.start = AsyncMock()
            mock_vad.stop = AsyncMock()
            mock_vad.process = AsyncMock(return_value=True)
            mock_vad_cls.return_value = mock_vad

            await pipeline.start()

            # Process audio should trigger VAD
            await pipeline.process_audio(b"\x00" * 640, 100)

            mock_vad.process.assert_awaited()

            await pipeline.stop()


class TestPipelineWithASR:
    """Tests for pipeline with ASR enabled."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="asr-session")

    @pytest.mark.asyncio
    async def test_pipeline_with_asr_enabled(self, session):
        """Test pipeline initializes ASR when enabled."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=True,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        await pipeline.start()
        assert pipeline._asr is not None

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_process_audio_pushes_to_asr(self, session):
        """Test process_audio pushes to ASR when in LISTENING state."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=True,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        await pipeline.start()

        # Transition to LISTENING state
        await session.on_speech_start()
        assert session.state == SessionState.LISTENING

        # Mock ASR push_audio
        pipeline._asr.push_audio = AsyncMock()

        await pipeline.process_audio(b"\x00" * 640, 100)

        pipeline._asr.push_audio.assert_awaited_with(b"\x00" * 640, 100)

        await pipeline.stop()


class TestPipelineWithLLM:
    """Tests for pipeline with LLM enabled."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="llm-session")

    @pytest.mark.asyncio
    async def test_pipeline_with_llm_enabled(self, session):
        """Test pipeline initializes LLM when enabled."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        await pipeline.start()
        assert pipeline._llm is not None

        await pipeline.stop()


class TestPipelineWithTTS:
    """Tests for pipeline with TTS enabled."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="tts-session")

    @pytest.mark.asyncio
    async def test_pipeline_with_tts_enabled(self, session):
        """Test pipeline initializes TTS when enabled."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()
            mock_create_tts.return_value = mock_tts

            await pipeline.start()
            assert pipeline._tts is not None

            await pipeline.stop()


class TestPipelineStopWithActiveTask:
    """Tests for stopping pipeline with active generation."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="active-task-session")

    @pytest.mark.asyncio
    async def test_stop_cancels_generation_task(self, session):
        """Test stop cancels active generation task."""
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

        # Create a mock task that runs forever
        async def long_running():
            await asyncio.sleep(100)

        pipeline._generation_task = asyncio.create_task(long_running())

        # Stop should cancel the task
        await pipeline.stop()

        assert pipeline._generation_task.cancelled() or pipeline._generation_task.done()


class TestPipelineGenerateResponse:
    """Tests for response generation."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="generate-session")

    @pytest.mark.asyncio
    async def test_generate_response_skips_without_llm_tts(self, session):
        """Test generate response is no-op without LLM/TTS."""
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
        await pipeline._generate_response([{"role": "user", "content": "Hello"}])

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_generate_response_with_mocked_llm_tts(self, session):
        """Test generate response with mocked LLM and TTS."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()
            mock_create_tts.return_value = mock_tts

            await pipeline.start()

            # Transition to SPEAKING state
            await session.on_speech_start()
            await session.on_endpoint_detected(100)

            # Mock LLM stream
            async def mock_llm_stream(messages):
                yield "Hello"
                yield " world"

            pipeline._llm.generate_stream = mock_llm_stream

            # Mock TTS stream with simple dict-like object
            from src.audio.tts.base import TTSChunk

            async def mock_tts_stream(text_stream):
                yield TTSChunk(audio=b"\x00" * 100, is_final=False, text_offset=0)

            pipeline._tts.synthesize_stream = mock_tts_stream

            # Generate response
            await pipeline._generate_response([{"role": "user", "content": "Hi"}])

            await pipeline.stop()


class TestPipelineBargeInWithComponents:
    """Tests for barge-in with components."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="barge-components-session")

    @pytest.mark.asyncio
    async def test_barge_in_aborts_llm(self, session):
        """Test barge-in aborts LLM."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=True,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)
        await pipeline.start()

        # Transition to SPEAKING
        await session.on_speech_start()
        await session.on_endpoint_detected(100)
        await session.on_response_ready()

        # Mock LLM abort
        pipeline._llm.abort = AsyncMock()

        await pipeline.handle_barge_in()

        pipeline._llm.abort.assert_awaited()

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_barge_in_cancels_tts(self, session):
        """Test barge-in cancels TTS."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=True,
            enable_animation=False,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:
            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()
            mock_tts.cancel = AsyncMock()
            mock_create_tts.return_value = mock_tts

            await pipeline.start()

            # Transition to SPEAKING
            await session.on_speech_start()
            await session.on_endpoint_detected(100)
            await session.on_response_ready()

            await pipeline.handle_barge_in()

            pipeline._tts.cancel.assert_awaited()

            await pipeline.stop()

    @pytest.mark.asyncio
    async def test_barge_in_cancels_animation(self, session):
        """Test barge-in cancels animation."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=True,
            enable_livelink=False,
        )
        pipeline = ConversationPipeline(session, config)
        await pipeline.start()

        # Transition to SPEAKING
        await session.on_speech_start()
        await session.on_endpoint_detected(100)
        await session.on_response_ready()

        # Mock animation cancel
        pipeline._animation.cancel = AsyncMock()

        await pipeline.handle_barge_in()

        pipeline._animation.cancel.assert_awaited()

        await pipeline.stop()


class TestPipelineProcessAnimation:
    """Tests for animation processing."""

    @pytest.fixture
    def session(self):
        """Create session for testing."""
        return Session(session_id="anim-process-session")

    @pytest.mark.asyncio
    async def test_process_animation_skips_without_components(self, session):
        """Test process animation is no-op without animation/livelink."""
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
        await pipeline._process_animation(b"\x00" * 640, 100)

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_process_animation_with_mocked_components(self, session):
        """Test process animation with mocked components."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=True,
            enable_livelink=True,
        )
        pipeline = ConversationPipeline(session, config)

        with patch("src.animation.create_audio2face_engine") as mock_create_anim, \
             patch("src.orchestrator.pipeline.create_livelink_sender") as mock_create_ll:
            # Setup mock animation
            mock_anim = AsyncMock()
            mock_anim.start = AsyncMock()
            mock_anim.stop = AsyncMock()
            mock_create_anim.return_value = mock_anim

            # Setup mock livelink
            mock_ll = AsyncMock()
            mock_ll.start = AsyncMock()
            mock_ll.stop = AsyncMock()
            mock_ll.is_running = True
            mock_ll.send_blendshape_frame = AsyncMock()
            mock_create_ll.return_value = mock_ll

            await pipeline.start()

            # Mock animation generate_frames
            from src.animation.base import BlendshapeFrame

            async def mock_generate_frames(audio_stream):
                yield BlendshapeFrame(
                    session_id="anim-process-session",
                    seq=1,
                    t_audio_ms=100,
                    blendshapes={"jawOpen": 0.5},
                )

            pipeline._animation.generate_frames = mock_generate_frames

            await pipeline._process_animation(b"\x00" * 640, 100)

            pipeline._livelink.send_blendshape_frame.assert_awaited()

            await pipeline.stop()
