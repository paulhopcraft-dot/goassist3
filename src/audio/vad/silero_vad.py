"""Silero VAD Wrapper - Voice Activity Detection.

Provides voice activity detection using Silero VAD model.
Used to determine when the user starts/stops speaking.

Key responsibilities:
- Detect speech onset (user starts speaking)
- Detect speech endpoint (user stops speaking)
- Provide speech probability scores
- Support barge-in detection (user interrupts agent)

Reference: TMF v3.0 §6 Turn Detection
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

import numpy as np

from src.audio.transport.audio_clock import get_audio_clock
from src.config.constants import TMF
from src.observability.logging import get_logger

logger = get_logger(__name__)


class VADState(Enum):
    """Voice activity detection state."""

    SILENCE = "silence"
    SPEECH = "speech"
    ENDPOINT = "endpoint"  # Speech just ended


@dataclass
class VADEvent:
    """Event emitted by VAD on state changes."""

    state: VADState
    t_ms: int  # Timestamp from audio clock
    probability: float  # Speech probability (0.0-1.0)
    session_id: str


@dataclass
class SileroVAD:
    """Silero VAD wrapper for voice activity detection.

    Uses Silero VAD v5 for efficient CPU-based voice detection.

    Usage:
        vad = SileroVAD(session_id="session-123")
        await vad.start()

        # Register callbacks
        vad.on_speech_start(handle_speech_start)
        vad.on_speech_end(handle_speech_end)

        # Process audio chunks
        await vad.process(audio_bytes)

        # Cleanup
        await vad.stop()
    """

    session_id: str
    sample_rate: int = TMF.AUDIO_SAMPLE_RATE
    threshold: float = 0.5  # Speech probability threshold
    min_speech_duration_ms: int = 250  # Minimum speech duration to trigger
    min_silence_duration_ms: int = 300  # Silence before endpoint
    speech_pad_ms: int = 30  # Padding around speech

    # Internal state
    _model: object = field(default=None, init=False)
    _state: VADState = field(default=VADState.SILENCE, init=False)
    _speech_start_ms: int | None = field(default=None, init=False)
    _last_speech_ms: int | None = field(default=None, init=False)
    _callbacks_speech_start: list = field(default_factory=list, init=False)
    _callbacks_speech_end: list = field(default_factory=list, init=False)
    _running: bool = field(default=False, init=False)

    async def start(self) -> None:
        """Initialize VAD model."""
        if self._running:
            return

        # Load Silero VAD model
        # Note: In production, this would load the actual model
        # For now, we stub it to allow testing without the model
        try:
            import torch

            self._model, _ = torch.hub.load(
                "snakers4/silero-vad",
                "silero_vad",
                force_reload=False,
                onnx=True,  # Use ONNX for faster inference
            )
        except ImportError:
            # Stub for testing without torch
            self._model = None

        self._state = VADState.SILENCE
        self._speech_start_ms = None
        self._last_speech_ms = None
        self._running = True

    async def stop(self) -> None:
        """Stop VAD and cleanup."""
        self._running = False
        self._model = None

    def on_speech_start(self, callback: Callable[[VADEvent], None]) -> None:
        """Register callback for speech start events."""
        self._callbacks_speech_start.append(callback)

    def on_speech_end(self, callback: Callable[[VADEvent], None]) -> None:
        """Register callback for speech end events."""
        self._callbacks_speech_end.append(callback)

    def _get_timestamp(self) -> int:
        """Get current timestamp from audio clock."""
        clock = get_audio_clock()
        return clock.get_time_ms(self.session_id)

    async def process(self, audio_bytes: bytes) -> VADEvent | None:
        """Process audio chunk and detect voice activity.

        Args:
            audio_bytes: Raw PCM audio (16-bit signed, mono)

        Returns:
            VADEvent if state changed, None otherwise
        """
        if not self._running:
            return None

        t_ms = self._get_timestamp()

        # Convert bytes to numpy array
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Get speech probability
        probability = await self._get_speech_probability(audio)

        # Determine if this is speech
        is_speech = probability >= self.threshold

        event = None

        if self._state == VADState.SILENCE:
            if is_speech:
                # Potential speech start
                if self._speech_start_ms is None:
                    self._speech_start_ms = t_ms

                # Check if speech duration exceeds minimum
                speech_duration = t_ms - self._speech_start_ms
                if speech_duration >= self.min_speech_duration_ms:
                    self._state = VADState.SPEECH
                    self._last_speech_ms = t_ms
                    event = VADEvent(
                        state=VADState.SPEECH,
                        t_ms=self._speech_start_ms,  # Report when speech actually started
                        probability=probability,
                        session_id=self.session_id,
                    )
                    await self._emit_speech_start(event)
            else:
                # Reset potential speech start
                self._speech_start_ms = None

        elif self._state == VADState.SPEECH:
            if is_speech:
                # Continue speech
                self._last_speech_ms = t_ms
            else:
                # Potential endpoint
                if self._last_speech_ms is not None:
                    silence_duration = t_ms - self._last_speech_ms
                    if silence_duration >= self.min_silence_duration_ms:
                        self._state = VADState.ENDPOINT
                        event = VADEvent(
                            state=VADState.ENDPOINT,
                            t_ms=self._last_speech_ms,  # Report when speech actually ended
                            probability=probability,
                            session_id=self.session_id,
                        )
                        await self._emit_speech_end(event)

                        # Reset to silence
                        self._state = VADState.SILENCE
                        self._speech_start_ms = None
                        self._last_speech_ms = None

        return event

    async def _get_speech_probability(self, audio: np.ndarray) -> float:
        """Get speech probability from VAD model.

        Args:
            audio: Normalized float32 audio array

        Returns:
            Speech probability (0.0-1.0)
        """
        if self._model is None:
            # Stub: return low probability when model not loaded
            return 0.0

        try:
            import torch

            # Silero VAD expects specific chunk sizes
            # Resample/chunk as needed
            audio_tensor = torch.from_numpy(audio)

            # Run inference
            speech_prob = self._model(audio_tensor, self.sample_rate).item()
            return float(speech_prob)

        except Exception as e:
            logger.warning(
                "vad_inference_error",
                session_id=self.session_id,
                error=str(e),
            )
            return 0.0

    async def _emit_speech_start(self, event: VADEvent) -> None:
        """Emit speech start event to all callbacks."""
        for callback in self._callbacks_speech_start:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(
                    "vad_speech_start_callback_error",
                    session_id=self.session_id,
                    callback=getattr(callback, "__name__", str(callback)),
                    error=str(e),
                )

    async def _emit_speech_end(self, event: VADEvent) -> None:
        """Emit speech end event to all callbacks."""
        for callback in self._callbacks_speech_end:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(
                    "vad_speech_end_callback_error",
                    session_id=self.session_id,
                    callback=getattr(callback, "__name__", str(callback)),
                    error=str(e),
                )

    @property
    def state(self) -> VADState:
        """Current VAD state."""
        return self._state

    @property
    def is_speaking(self) -> bool:
        """Whether speech is currently detected."""
        return self._state == VADState.SPEECH


def create_vad(session_id: str, **kwargs) -> SileroVAD:
    """Factory function to create VAD instance.

    Args:
        session_id: Session identifier
        **kwargs: Additional configuration options

    Returns:
        Configured SileroVAD instance
    """
    return SileroVAD(session_id=session_id, **kwargs)
