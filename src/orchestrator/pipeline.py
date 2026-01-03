"""Conversation Pipeline - End-to-end voice conversation orchestration.

Wires all components together for real-time voice + avatar conversation:
    Audio In → VAD → ASR → LLM → TTS → Animation → Live Link
                                   ↓
                               Audio Out

Reference: Implementation-v3.0.md §5 Orchestrator
TMF v3.0: TTFA ≤ 250ms p95, barge-in ≤ 150ms
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator, Callable

from src.audio.transport.audio_clock import get_audio_clock
from src.audio.vad.silero_vad import SileroVAD
from src.audio.asr import ASREngine, create_asr_engine
from src.audio.tts import TTSEngine, create_tts_engine, text_to_stream
from src.animation.base import AnimationEngine, BlendshapeFrame, MockAnimationEngine
from src.animation.livelink import LiveLinkSender, create_livelink_sender
from src.llm.vllm_client import VLLMClient, build_messages
from src.orchestrator.session import Session, SessionState
from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for conversation pipeline."""

    # Component enablement
    enable_vad: bool = True
    enable_asr: bool = True
    enable_llm: bool = True
    enable_tts: bool = True
    enable_animation: bool = True
    enable_livelink: bool = True

    # ASR configuration
    asr_engine: str = "mock"  # "mock", "deepgram"
    deepgram_api_key: str = ""  # Required for "deepgram" engine

    # TTS configuration
    tts_engine: str = "mock"  # "mock", "kyutai"
    tts_server_url: str = "ws://localhost:8080/tts"

    # Live Link configuration
    livelink_host: str = "127.0.0.1"
    livelink_port: int = 11111
    livelink_subject: str = "GoAssist"

    # Audio configuration
    sample_rate: int = 16000
    chunk_size_ms: int = 20


class ConversationPipeline:
    """End-to-end conversation pipeline.

    Orchestrates the full voice + avatar conversation flow:

    1. **Audio Input**: Receives audio from WebRTC
    2. **VAD**: Detects speech activity
    3. **ASR**: Transcribes speech to text
    4. **LLM**: Generates response
    5. **TTS**: Synthesizes speech
    6. **Animation**: Generates facial animation
    7. **Live Link**: Streams to Unreal/MetaHuman

    Usage:
        pipeline = ConversationPipeline(session)
        await pipeline.start()

        # Feed audio from WebRTC
        await pipeline.process_audio(audio_bytes, t_ms)

        # On session end
        await pipeline.stop()
    """

    def __init__(
        self,
        session: Session,
        config: PipelineConfig | None = None,
    ) -> None:
        self._session = session
        self._config = config or PipelineConfig()

        # Components (initialized on start)
        self._vad: SileroVAD | None = None
        self._asr: ASREngine | None = None
        self._llm: VLLMClient | None = None
        self._tts: TTSEngine | None = None
        self._animation: AnimationEngine | None = None
        self._livelink: LiveLinkSender | None = None

        # State
        self._running: bool = False
        self._current_transcript: str = ""
        self._processing_turn: bool = False
        self._turn_lock: asyncio.Lock = asyncio.Lock()

        # Callbacks
        self._on_audio_output: Callable[[bytes], None] | None = None
        self._on_transcript: Callable[[str, bool], None] | None = None

        # Tasks
        self._generation_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Initialize and start all pipeline components."""
        if self._running:
            return

        session_id = self._session.session_id

        # Initialize VAD
        if self._config.enable_vad:
            self._vad = SileroVAD()
            await self._vad.start(session_id)

        # Initialize ASR
        if self._config.enable_asr:
            self._asr = create_asr_engine(
                self._config.asr_engine,
                api_key=self._config.deepgram_api_key,
            )
            await self._asr.start(session_id)
            self._asr.on_final(self._handle_asr_final)
            self._asr.on_endpoint(self._handle_asr_endpoint)

        # Initialize LLM
        if self._config.enable_llm:
            self._llm = VLLMClient()
            await self._llm.start()

        # Initialize TTS
        if self._config.enable_tts:
            self._tts = create_tts_engine(
                self._config.tts_engine,
                server_url=self._config.tts_server_url,
            )
            await self._tts.start(session_id)

        # Initialize Animation
        if self._config.enable_animation:
            from src.animation import create_audio2face_engine
            self._animation = create_audio2face_engine()
            await self._animation.start(session_id)

        # Initialize Live Link
        if self._config.enable_livelink:
            self._livelink = create_livelink_sender(
                host=self._config.livelink_host,
                port=self._config.livelink_port,
                subject_name=self._config.livelink_subject,
            )
            await self._livelink.start()

        # Start session with component references
        await self._session.start(
            vad=self._vad,
            asr=self._asr,
            llm=self._llm,
            tts=self._tts,
            animation=self._animation,
        )

        self._running = True
        logger.info("pipeline_started", session_id=session_id)

    async def stop(self) -> None:
        """Stop all pipeline components."""
        if not self._running:
            return

        self._running = False

        # Cancel any in-progress generation
        if self._generation_task and not self._generation_task.done():
            self._generation_task.cancel()
            try:
                await asyncio.wait_for(self._generation_task, timeout=0.5)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # Stop components in reverse order
        if self._livelink:
            await self._livelink.stop()

        if self._animation:
            await self._animation.stop()

        if self._tts:
            await self._tts.stop()

        if self._llm:
            await self._llm.stop()

        if self._asr:
            await self._asr.stop()

        if self._vad:
            await self._vad.stop()

        # Stop session
        await self._session.stop()

        logger.info("pipeline_stopped", session_id=self._session.session_id)

    async def process_audio(self, audio: bytes, t_ms: int) -> None:
        """Process incoming audio from WebRTC.

        Args:
            audio: Raw PCM audio bytes (16-bit signed, mono, 16kHz)
            t_ms: Audio timestamp in milliseconds
        """
        if not self._running:
            return

        # VAD processing
        if self._vad:
            speech_detected = await self._vad.process(audio, t_ms)

            if speech_detected and self._session.state == SessionState.IDLE:
                await self._session.on_speech_start()

        # Push to ASR
        if self._asr and self._session.state == SessionState.LISTENING:
            await self._asr.push_audio(audio, t_ms)

    def _handle_asr_final(self, text: str, start_ms: int, end_ms: int) -> None:
        """Handle final ASR transcription."""
        self._current_transcript = text
        logger.info("asr_final", text=text, start_ms=start_ms, end_ms=end_ms)

        if self._on_transcript:
            self._on_transcript(text, True)

    def _handle_asr_endpoint(self, t_ms: int) -> None:
        """Handle ASR endpoint detection - user finished speaking.

        Uses atomic flag set to prevent race condition where multiple
        endpoints trigger duplicate turn processing.
        """
        if self._processing_turn:
            logger.debug(
                "asr_endpoint_skipped",
                session_id=self._session.session_id,
                reason="turn_already_processing",
            )
            return

        # Set flag BEFORE creating task to prevent race condition
        # In single-threaded asyncio, this sync callback runs atomically
        self._processing_turn = True
        asyncio.create_task(self._process_turn(t_ms))

    async def _process_turn(self, endpoint_ms: int) -> None:
        """Process a complete turn: ASR → LLM → TTS → Animation.

        This is the core pipeline that generates and outputs a response.
        Note: _processing_turn flag is already set by _handle_asr_endpoint
        to prevent race conditions.
        """
        user_text = self._current_transcript

        if not user_text.strip():
            self._processing_turn = False
            return

        try:
            # Transition to THINKING
            await self._session.on_endpoint_detected(endpoint_ms)

            # Add user message to context
            self._session.add_user_message(user_text)

            # Get context messages for LLM
            messages = await self._session.get_context_messages()

            # Generate LLM response → TTS → Animation
            await self._generate_response(messages)

            # Mark turn complete
            await self._session.on_response_complete()

        except asyncio.CancelledError:
            # Barge-in occurred
            logger.info("turn_cancelled", session_id=self._session.session_id)
        except Exception as e:
            logger.error("turn_error", error=str(e))
        finally:
            self._processing_turn = False
            self._current_transcript = ""

    async def _generate_response(self, messages: list[dict]) -> None:
        """Generate response: LLM → TTS → Animation → Output.

        This is where TTFA is measured (endpoint → first audio byte).
        """
        if not self._llm or not self._tts:
            return

        # Transition to SPEAKING
        await self._session.on_response_ready()

        clock = get_audio_clock()
        first_audio_sent = False
        full_response = []

        try:
            # Stream LLM tokens
            token_stream = self._llm.generate_stream(messages)

            # Convert token stream to text stream for TTS
            async def llm_text_stream() -> AsyncIterator[str]:
                async for token in token_stream:
                    full_response.append(token)
                    yield token

            # TTS synthesizes audio from token stream
            async for audio_chunk in self._tts.synthesize_stream(llm_text_stream()):
                # Track first audio byte for TTFA
                if not first_audio_sent:
                    t_ms = clock.get_time_ms(self._session.session_id)
                    await self._session.on_first_audio_byte(t_ms)
                    first_audio_sent = True

                # Output audio
                if self._on_audio_output:
                    self._on_audio_output(audio_chunk.audio)

                # Generate and send animation
                if self._animation and self._livelink:
                    await self._process_animation(audio_chunk.audio, audio_chunk.timestamp_ms)

            # Add assistant response to context
            response_text = "".join(full_response)
            self._session.add_assistant_message(response_text)

        except asyncio.CancelledError:
            raise

    async def _process_animation(self, audio: bytes, t_ms: int) -> None:
        """Generate animation frames from audio and send to Live Link."""
        if not self._animation or not self._livelink:
            return

        # Create single-chunk audio stream
        async def audio_stream() -> AsyncIterator[bytes]:
            yield audio

        # Generate and send frames
        async for frame in self._animation.generate_frames(audio_stream()):
            if self._livelink.is_running:
                await self._livelink.send_blendshape_frame(frame)

    async def handle_barge_in(self) -> None:
        """Handle user interruption (barge-in).

        Must complete within 150ms per TMF v3.0.
        """
        logger.info("barge_in", session_id=self._session.session_id)

        # Clear processing flag to prevent duplicate turn processing
        self._processing_turn = False

        # Cancel generation task
        if self._generation_task and not self._generation_task.done():
            self._generation_task.cancel()

        # Cancel all components in parallel for speed
        cancel_tasks = []
        if self._llm:
            cancel_tasks.append(self._llm.abort())
        if self._tts:
            cancel_tasks.append(self._tts.cancel())
        if self._animation:
            cancel_tasks.append(self._animation.cancel())

        if cancel_tasks:
            await asyncio.gather(*cancel_tasks, return_exceptions=True)

        # Session handles state transition
        await self._session.on_barge_in()

    def set_audio_output_callback(self, callback: Callable[[bytes], None]) -> None:
        """Set callback for audio output."""
        self._on_audio_output = callback

    def set_transcript_callback(
        self, callback: Callable[[str, bool], None]
    ) -> None:
        """Set callback for transcripts (text, is_final)."""
        self._on_transcript = callback

    @property
    def is_running(self) -> bool:
        """Whether pipeline is active."""
        return self._running

    @property
    def session(self) -> Session:
        """Associated session."""
        return self._session


async def create_pipeline(
    session: Session,
    **config_kwargs,
) -> ConversationPipeline:
    """Factory function to create and start a conversation pipeline.

    Args:
        session: Session to associate with pipeline
        **config_kwargs: Pipeline configuration options

    Returns:
        Started ConversationPipeline instance
    """
    config = PipelineConfig(**config_kwargs) if config_kwargs else None
    pipeline = ConversationPipeline(session, config)
    await pipeline.start()
    return pipeline
