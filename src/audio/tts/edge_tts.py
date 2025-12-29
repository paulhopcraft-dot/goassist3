"""Edge TTS Engine - Free streaming TTS fallback.

Uses Microsoft Edge's TTS service for synthesis.
Features:
- No API key required
- Streaming output
- Multiple voices and languages
- Works on CPU (no GPU needed)

This is a fallback for when Kyutai TTS is unavailable.

Reference: TMF v3.0 §4.2
"""

import asyncio
import io
import logging
from typing import AsyncIterator

from src.audio.tts.base import BaseTTSEngine

logger = logging.getLogger(__name__)

# Default voice - natural sounding US English
DEFAULT_VOICE = "en-US-AriaNeural"

# Voice options for different personas
VOICE_OPTIONS = {
    "aria": "en-US-AriaNeural",  # Female, conversational
    "guy": "en-US-GuyNeural",  # Male, conversational
    "jenny": "en-US-JennyNeural",  # Female, professional
    "davis": "en-US-DavisNeural",  # Male, professional
}


class EdgeTTSEngine(BaseTTSEngine):
    """Edge TTS implementation using Microsoft's free TTS service.

    This is a fallback engine for systems without GPU support.
    Lower quality than Kyutai but works everywhere.

    Usage:
        tts = EdgeTTSEngine(voice="aria")
        await tts.start("session-123")

        async for audio in tts.synthesize_stream(text_stream):
            send_audio(audio)

        await tts.stop()
    """

    def __init__(
        self,
        voice: str = "aria",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        sample_rate: int = 24000,
    ) -> None:
        """Initialize Edge TTS engine.

        Args:
            voice: Voice name or key from VOICE_OPTIONS
            rate: Speech rate adjustment (e.g., "+10%", "-20%")
            pitch: Pitch adjustment (e.g., "+5Hz", "-10Hz")
            sample_rate: Target sample rate (will resample if needed)
        """
        super().__init__()
        self._voice = VOICE_OPTIONS.get(voice, voice)
        self._rate = rate
        self._pitch = pitch
        self._sample_rate = sample_rate
        self._cancel_event: asyncio.Event | None = None

    async def start(self, session_id: str) -> None:
        """Initialize Edge TTS for a session."""
        await super().start(session_id)
        self._cancel_event = asyncio.Event()

        # Verify edge-tts is available
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError(
                "Edge TTS requires edge-tts package: pip install edge-tts"
            )

    async def synthesize_stream(
        self, text_stream: AsyncIterator[str]
    ) -> AsyncIterator[bytes]:
        """Synthesize audio from streaming text input.

        Buffers text until sentence boundaries for natural synthesis.

        Args:
            text_stream: Async iterator of text chunks

        Yields:
            Audio bytes as they become available (16-bit PCM)
        """
        if not self._running:
            raise RuntimeError("TTS not started. Call start() first.")

        self._synthesizing = True
        self._cancelled = False
        self._cancel_event.clear()

        try:
            import edge_tts

            text_buffer = []

            async for chunk in text_stream:
                if self._cancelled:
                    break
                text_buffer.append(chunk)

                # Synthesize at sentence boundaries
                full_text = "".join(text_buffer)
                if self._should_synthesize(full_text):
                    async for audio in self._synthesize_text(full_text):
                        if self._cancelled:
                            break
                        yield audio
                    text_buffer.clear()

            # Synthesize remaining text
            if text_buffer and not self._cancelled:
                remaining = "".join(text_buffer)
                if remaining.strip():
                    async for audio in self._synthesize_text(remaining):
                        if self._cancelled:
                            break
                        yield audio

        finally:
            self._synthesizing = False

    def _should_synthesize(self, text: str) -> bool:
        """Check if we should synthesize the buffered text."""
        return any(text.rstrip().endswith(p) for p in ".!?")

    async def _synthesize_text(self, text: str) -> AsyncIterator[bytes]:
        """Synthesize audio for a text segment.

        Args:
            text: Text to synthesize

        Yields:
            Audio bytes (16-bit PCM)
        """
        try:
            import edge_tts

            communicate = edge_tts.Communicate(
                text=text.strip(),
                voice=self._voice,
                rate=self._rate,
                pitch=self._pitch,
            )

            # Stream audio chunks
            async for chunk in communicate.stream():
                if self._cancelled:
                    break

                if chunk["type"] == "audio":
                    # Edge TTS returns MP3, convert to PCM
                    audio_bytes = await self._mp3_to_pcm(chunk["data"])
                    if audio_bytes:
                        yield audio_bytes

                # Yield control for cancellation
                await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Edge TTS synthesis error: {e}")
            raise

    async def _mp3_to_pcm(self, mp3_data: bytes) -> bytes:
        """Convert MP3 audio to 16-bit PCM.

        Args:
            mp3_data: MP3 audio bytes

        Returns:
            16-bit PCM audio bytes at target sample rate
        """
        try:
            import numpy as np

            # Try pydub for conversion
            try:
                from pydub import AudioSegment

                audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
                audio = audio.set_frame_rate(self._sample_rate)
                audio = audio.set_channels(1)
                audio = audio.set_sample_width(2)  # 16-bit
                return audio.raw_data

            except ImportError:
                # Fallback: try soundfile
                try:
                    import soundfile as sf

                    audio, sr = sf.read(io.BytesIO(mp3_data))
                    if sr != self._sample_rate:
                        # Simple resampling
                        import scipy.signal
                        audio = scipy.signal.resample(
                            audio,
                            int(len(audio) * self._sample_rate / sr)
                        )
                    audio = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
                    return audio.tobytes()

                except ImportError:
                    logger.warning("No audio conversion library available")
                    return b""

        except Exception as e:
            logger.error(f"MP3 to PCM conversion error: {e}")
            return b""

    async def cancel(self) -> None:
        """Immediately stop synthesis."""
        self._cancelled = True
        self._synthesizing = False
        if self._cancel_event:
            self._cancel_event.set()
        await super().cancel()

    async def stop(self) -> None:
        """Stop TTS and cleanup resources."""
        await self.cancel()
        self._running = False


def create_edge_tts(
    voice: str = "aria",
    rate: str = "+0%",
) -> EdgeTTSEngine:
    """Factory function to create Edge TTS instance.

    Args:
        voice: Voice name (aria, guy, jenny, davis) or full voice ID
        rate: Speech rate adjustment

    Returns:
        Configured EdgeTTSEngine instance
    """
    return EdgeTTSEngine(voice=voice, rate=rate)
