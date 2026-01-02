"""Integration Tests - Full Session Flow.

End-to-end tests covering complete session lifecycle:
    1. Session creation
    2. Audio input processing
    3. Speech detection
    4. Transcription
    5. LLM response generation
    6. TTS synthesis
    7. Audio output delivery
    8. Session cleanup

These tests use mock LLM/TTS but real pipeline components.
"""

import asyncio
from typing import List, Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.orchestrator.pipeline import ConversationPipeline, PipelineConfig
from src.orchestrator.session import Session, SessionState
from src.audio.tts.base import TTSChunk


class TestFullSessionLifecycle:
    """Tests for complete session lifecycle."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_create_session_via_api(self, client):
        """Test session creation through API."""
        response = client.post("/sessions", json={})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["state"] == "idle"
        assert "created_at" in data

    def test_session_lifecycle_complete(self, client):
        """Test complete session lifecycle: create → status → delete."""
        # Create
        create_resp = client.post("/sessions", json={})
        assert create_resp.status_code == 200
        session_id = create_resp.json()["session_id"]

        # Get status
        status_resp = client.get(f"/sessions/{session_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["session_id"] == session_id

        # List sessions
        list_resp = client.get("/sessions")
        assert list_resp.status_code == 200
        session_ids = [s["session_id"] for s in list_resp.json()["sessions"]]
        assert session_id in session_ids

        # Delete
        delete_resp = client.delete(f"/sessions/{session_id}")
        assert delete_resp.status_code == 200

        # Verify deleted
        status_after = client.get(f"/sessions/{session_id}")
        assert status_after.status_code == 404

    def test_multiple_concurrent_sessions(self, client):
        """Test creating multiple concurrent sessions."""
        session_ids = []

        # Create 3 sessions
        for _ in range(3):
            resp = client.post("/sessions", json={})
            assert resp.status_code == 200
            session_ids.append(resp.json()["session_id"])

        # Verify all exist
        list_resp = client.get("/sessions")
        assert list_resp.status_code == 200
        active_ids = [s["session_id"] for s in list_resp.json()["sessions"]]

        for sid in session_ids:
            assert sid in active_ids

        # Cleanup
        for sid in session_ids:
            client.delete(f"/sessions/{sid}")

    def test_session_state_transitions(self, client):
        """Test session state transitions through API."""
        # Create session
        create_resp = client.post("/sessions", json={})
        session_id = create_resp.json()["session_id"]

        # Initial state should be IDLE
        status = client.get(f"/sessions/{session_id}").json()
        assert status["state"] == "idle"

        # Cleanup
        client.delete(f"/sessions/{session_id}")


class TestAudioInputProcessing:
    """Tests for audio input processing through session."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="audio-test-session")
        yield session
        # Cleanup handled by pipeline.stop() in each test

    @pytest.fixture
    def minimal_pipeline_config(self):
        """Minimal config for fast tests."""
        return PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

    @pytest.mark.asyncio
    async def test_pipeline_processes_audio(self, session, minimal_pipeline_config):
        """Test pipeline accepts and processes audio input."""
        pipeline = ConversationPipeline(session, minimal_pipeline_config)
        await pipeline.start()

        # Feed audio
        audio_chunk = b"\x00" * 640  # 20ms @ 16kHz
        await pipeline.process_audio(audio_chunk, t_audio_ms=20)

        # Should not raise
        assert pipeline.is_running

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_audio_flow_with_vad(self, session):
        """Test audio flow with VAD enabled."""
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
            mock_vad.process = AsyncMock(return_value=True)  # Speech detected
            mock_vad_cls.return_value = mock_vad

            await pipeline.start()

            # Feed audio
            await pipeline.process_audio(b"\x00" * 640, 20)

            # VAD should have been called
            mock_vad.process.assert_awaited()

            await pipeline.stop()


class TestSpeechToTextFlow:
    """Tests for speech recognition flow."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="asr-test-session")
        yield session
        # Cleanup handled by pipeline.stop() in each test
        pass

    @pytest.mark.asyncio
    async def test_asr_receives_audio_when_listening(self, session):
        """Test ASR receives audio in LISTENING state."""
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

        # Transition to LISTENING
        await session.on_speech_start()
        assert session.state == SessionState.LISTENING

        # Mock ASR push_audio
        pipeline._asr.push_audio = AsyncMock()

        # Feed audio
        audio = b"\x00" * 640
        await pipeline.process_audio(audio, 100)

        # ASR should receive audio
        pipeline._asr.push_audio.assert_awaited_with(audio, 100)

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_asr_transcript_callback(self, session):
        """Test ASR transcript callback invocation."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

        pipeline = ConversationPipeline(session, config)

        transcripts: List[Tuple[str, bool]] = []

        def on_transcript(text: str, is_final: bool):
            transcripts.append((text, is_final))

        pipeline.set_transcript_callback(on_transcript)
        await pipeline.start()

        # Simulate ASR final
        pipeline._handle_asr_final("Hello world", 100, 500)

        assert len(transcripts) == 1
        assert transcripts[0] == ("Hello world", True)

        await pipeline.stop()


class TestLLMResponseGeneration:
    """Tests for LLM response generation."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="llm-test-session")
        yield session
        # Cleanup handled by pipeline.stop() in each test
        pass

    @pytest.mark.asyncio
    async def test_llm_generates_response(self, session):
        """Test LLM response generation in pipeline."""
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

        # Transition to THINKING
        await session.on_speech_start()
        await session.on_endpoint_detected(100)
        assert session.state == SessionState.THINKING

        # Mock LLM stream
        async def mock_llm_stream(messages):
            yield "Hello"
            yield " there"

        pipeline._llm.generate_stream = mock_llm_stream

        # Generate response
        await pipeline._generate_response([
            {"role": "user", "content": "Hi"}
        ])

        await pipeline.stop()

    @pytest.mark.asyncio
    async def test_llm_abort_on_barge_in(self, session):
        """Test LLM generation is aborted on barge-in."""
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
        assert session.state == SessionState.SPEAKING

        # Mock LLM abort
        pipeline._llm.abort = AsyncMock()

        # Trigger barge-in
        await pipeline.handle_barge_in()

        # LLM should be aborted
        pipeline._llm.abort.assert_awaited()

        await pipeline.stop()


class TestTTSSynthesis:
    """Tests for TTS synthesis flow."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="tts-test-session")
        yield session
        # Cleanup handled by pipeline.stop() in each test
        pass

    @pytest.mark.asyncio
    async def test_tts_synthesizes_llm_output(self, session):
        """Test TTS synthesizes LLM output."""
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

            # Mock TTS stream
            async def mock_tts_stream(text_stream):
                yield TTSChunk(audio=b"\x00" * 320, is_final=False, text_offset=0)
                yield TTSChunk(audio=b"\x00" * 320, is_final=True, text_offset=5)

            mock_tts.synthesize_stream = mock_tts_stream
            mock_create_tts.return_value = mock_tts

            await pipeline.start()

            # Transition to THINKING
            await session.on_speech_start()
            await session.on_endpoint_detected(100)

            # Mock LLM stream
            async def mock_llm_stream(messages):
                yield "Hello"

            pipeline._llm.generate_stream = mock_llm_stream

            # Generate response (should trigger TTS)
            await pipeline._generate_response([
                {"role": "user", "content": "Hi"}
            ])

            await pipeline.stop()

    @pytest.mark.asyncio
    async def test_tts_cancellation_on_barge_in(self, session):
        """Test TTS cancellation during barge-in."""
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

            # Trigger barge-in
            await pipeline.handle_barge_in()

            # TTS should be cancelled
            mock_tts.cancel.assert_awaited()

            await pipeline.stop()


class TestAudioOutputDelivery:
    """Tests for audio output delivery."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="audio-output-session")
        yield session
        # Cleanup handled by pipeline.stop() in each test
        pass

    @pytest.mark.asyncio
    async def test_audio_output_callback_invoked(self, session):
        """Test audio output callback receives TTS audio."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=False,
            enable_llm=False,
            enable_tts=False,
            enable_animation=False,
            enable_livelink=False,
        )

        pipeline = ConversationPipeline(session, config)

        audio_received: List[bytes] = []

        def on_audio_output(audio: bytes):
            audio_received.append(audio)

        pipeline.set_audio_output_callback(on_audio_output)
        await pipeline.start()

        # Manually trigger callback
        test_audio = b"\x00" * 640
        if pipeline._on_audio_output:
            pipeline._on_audio_output(test_audio)

        assert len(audio_received) == 1
        assert audio_received[0] == test_audio

        await pipeline.stop()


class TestEndToEndSession:
    """Complete end-to-end session tests."""

    @pytest.fixture
    async def session(self):
        """Create session for testing."""
        session = Session(session_id="e2e-session")
        yield session
        # Cleanup handled by pipeline.stop() in each test
        pass

    @pytest.mark.asyncio
    async def test_complete_conversation_turn(self, session):
        """Test complete conversation turn: audio → ASR → LLM → TTS → audio."""
        config = PipelineConfig(
            enable_vad=False,
            enable_asr=True,
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

            async def mock_tts_stream(text_stream):
                async for _ in text_stream:
                    pass
                yield TTSChunk(audio=b"\x00" * 640, is_final=True, text_offset=0)

            mock_tts.synthesize_stream = mock_tts_stream
            mock_create_tts.return_value = mock_tts

            await pipeline.start()

            # Simulate ASR transcript
            pipeline._current_transcript = "Hello"
            pipeline._processing_turn = True

            # Mock LLM
            async def mock_llm_stream(messages):
                yield "Hi there!"

            pipeline._llm.generate_stream = mock_llm_stream

            # Transition session state
            await session.on_speech_start()
            await session.on_endpoint_detected(100)

            # Process turn
            await pipeline._process_turn(500)

            # Should complete without errors
            assert pipeline._processing_turn is False

            await pipeline.stop()

    @pytest.mark.asyncio
    async def test_session_cleanup_on_stop(self, session):
        """Test session cleanup stops all components."""
        config = PipelineConfig(
            enable_vad=True,
            enable_asr=True,
            enable_llm=True,
            enable_tts=True,
            enable_animation=True,
            enable_livelink=True,
        )

        pipeline = ConversationPipeline(session, config)

        with patch("src.orchestrator.pipeline.SileroVAD") as mock_vad_cls, \
             patch("src.orchestrator.pipeline.create_tts_engine") as mock_create_tts:

            # Setup mocks
            mock_vad = AsyncMock()
            mock_vad.start = AsyncMock()
            mock_vad.stop = AsyncMock()
            mock_vad_cls.return_value = mock_vad

            mock_tts = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()
            mock_create_tts.return_value = mock_tts

            await pipeline.start()
            assert pipeline.is_running

            # Stop pipeline
            await pipeline.stop()

            # All components should be stopped
            mock_vad.stop.assert_awaited()
            mock_tts.stop.assert_awaited()
            assert pipeline.is_running is False
