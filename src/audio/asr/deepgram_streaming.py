"""Deepgram Streaming ASR - Cloud-based speech recognition.

Uses Deepgram's real-time streaming API for:
- Low-latency transcription
- Streaming partial hypotheses
- Word-level timestamps
- Endpoint detection

This is the default ASR engine for production use.
Reference: TMF v3.0 §6 Turn Detection
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from src.audio.asr.base import BaseASREngine
from src.config.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DeepgramConfig:
    """Configuration for Deepgram ASR."""

    api_key: str
    model: str = "nova-2"  # Latest model
    language: str = "en"
    punctuate: bool = True
    interim_results: bool = True  # Enable streaming partials
    endpointing: int = 300  # Endpoint after 300ms silence
    vad_events: bool = True  # Enable VAD events
    smart_format: bool = True
    filler_words: bool = False


class DeepgramStreamingASR(BaseASREngine):
    """Deepgram streaming ASR implementation.

    Features:
    - Real-time streaming transcription
    - Partial hypotheses for responsive UI
    - Word timestamps for precise timing
    - Built-in endpoint detection

    Usage:
        config = DeepgramConfig(api_key="...")
        asr = DeepgramStreamingASR(config)
        await asr.start("session-123")

        asr.on_partial(handle_partial)
        asr.on_final(handle_final)
        asr.on_endpoint(handle_endpoint)

        async for audio in audio_stream:
            await asr.push_audio(audio, t_audio_ms)

        await asr.stop()
    """

    def __init__(self, config: DeepgramConfig | None = None) -> None:
        super().__init__()

        if config is None:
            settings = get_settings()
            api_key = settings.deepgram_api_key or ""
            config = DeepgramConfig(api_key=api_key)

        self._config = config
        self._websocket: Any = None
        self._receive_task: asyncio.Task | None = None
        self._last_partial: str = ""

    async def start(self, session_id: str) -> None:
        """Initialize Deepgram streaming connection."""
        await super().start(session_id)

        if not self._config.api_key:
            # Skip connection if no API key (for testing)
            return

        try:
            from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

            # Create Deepgram client
            client = DeepgramClient(self._config.api_key)

            # Configure live transcription
            options = LiveOptions(
                model=self._config.model,
                language=self._config.language,
                punctuate=self._config.punctuate,
                interim_results=self._config.interim_results,
                endpointing=self._config.endpointing,
                vad_events=self._config.vad_events,
                smart_format=self._config.smart_format,
                filler_words=self._config.filler_words,
                encoding="linear16",
                sample_rate=16000,
                channels=1,
            )

            # Create live connection
            self._websocket = client.listen.live.v("1")

            # Register event handlers
            self._websocket.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
            self._websocket.on(LiveTranscriptionEvents.SpeechStarted, self._on_speech_started)
            self._websocket.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)

            # Start connection
            await self._websocket.start(options)

        except ImportError:
            # Deepgram SDK not installed - continue in mock mode
            self._websocket = None
        except Exception as e:
            self._websocket = None
            raise RuntimeError(f"Failed to connect to Deepgram: {e}")

    async def push_audio(self, audio: bytes, t_audio_ms: int) -> None:
        """Send audio to Deepgram for processing."""
        if not self._running:
            return

        if self._websocket is None:
            return

        try:
            # Send audio chunk
            await self._websocket.send(audio)
        except Exception as e:
            logger.warning(
                "deepgram_send_error",
                session_id=self._session_id,
                error=str(e),
            )

    async def stop(self) -> None:
        """Close Deepgram connection and cleanup."""
        if self._websocket:
            try:
                await self._websocket.finish()
            except Exception as e:
                logger.warning(
                    "deepgram_close_error",
                    session_id=self._session_id,
                    error=str(e),
                )
            self._websocket = None

        await super().stop()

    def _on_transcript(self, *args, **kwargs) -> None:
        """Handle transcript events from Deepgram."""
        try:
            result = kwargs.get("result")
            if not result:
                return

            channel = result.channel
            alternatives = channel.alternatives
            if not alternatives:
                return

            transcript = alternatives[0].transcript
            if not transcript:
                return

            is_final = result.is_final
            words = alternatives[0].words

            if is_final:
                # Final transcription
                start_ms = 0
                end_ms = 0
                if words:
                    start_ms = int(words[0].start * 1000)
                    end_ms = int(words[-1].end * 1000)

                asyncio.create_task(self._emit_final(transcript, start_ms, end_ms))
                self._last_partial = ""
            else:
                # Partial transcription
                if transcript != self._last_partial:
                    t_ms = 0
                    if words:
                        t_ms = int(words[-1].end * 1000)

                    asyncio.create_task(self._emit_partial(transcript, t_ms))
                    self._last_partial = transcript

        except Exception as e:
            logger.warning(
                "deepgram_transcript_error",
                session_id=self._session_id,
                error=str(e),
            )

    def _on_speech_started(self, *args, **kwargs) -> None:
        """Handle speech start events from Deepgram."""
        # Deepgram detected speech start
        # This is handled by our VAD, so we don't need to emit here
        pass

    def _on_utterance_end(self, *args, **kwargs) -> None:
        """Handle utterance end (endpoint) events from Deepgram."""
        try:
            result = kwargs.get("result")
            if not result:
                return

            # Emit endpoint event
            t_ms = int(result.last_word_end * 1000) if hasattr(result, "last_word_end") else 0
            asyncio.create_task(self._emit_endpoint(t_ms))

        except Exception as e:
            logger.warning(
                "deepgram_utterance_end_error",
                session_id=self._session_id,
                error=str(e),
            )


def create_deepgram_asr(api_key: str | None = None, **kwargs) -> DeepgramStreamingASR:
    """Factory function to create Deepgram ASR instance.

    Args:
        api_key: Deepgram API key (uses settings if not provided)
        **kwargs: Additional configuration options

    Returns:
        Configured DeepgramStreamingASR instance
    """
    if api_key is None:
        settings = get_settings()
        api_key = settings.deepgram_api_key or ""

    config = DeepgramConfig(api_key=api_key, **kwargs)
    return DeepgramStreamingASR(config)
