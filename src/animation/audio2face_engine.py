"""Audio2Face Engine - NVIDIA Audio2Face integration.

Default animation engine for audio-driven lip-sync.
Configured for NEUTRAL mode per TMF Addendum A §A3.3.

Key Points:
- No emotion or style inference as product feature
- Focus on accurate lip-sync (speech articulation)
- gRPC streaming for low-latency
- Supports hard cancel for barge-in

Reference: Addendum A §A3, Implementation §4.3
"""

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator

from src.animation.base import (
    BaseAnimationEngine,
    BlendshapeFrame,
    get_neutral_blendshapes,
)
from src.animation.heartbeat import HeartbeatEmitter
from src.animation.yield_controller import YieldController
from src.audio.transport.audio_clock import get_audio_clock
from src.config.constants import TMF
from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Audio2FaceConfig:
    """Configuration for Audio2Face engine."""

    grpc_host: str = "localhost"
    grpc_port: int = 50051
    target_fps: int = 30
    style: str = "NEUTRAL"  # TMF Addendum A §A3.3: Default must be NEUTRAL
    enable_emotion: bool = False  # Disabled per TMF
    batch_audio_ms: int = 20  # Audio batch size for processing
    timeout_s: float = 1.0


class Audio2FaceEngine(BaseAnimationEngine):
    """Audio2Face engine for audio-driven lip-sync.

    Integrates with NVIDIA Audio2Face via gRPC for real-time
    blendshape generation from audio input.

    Configuration (TMF Addendum A §A3.3):
    - Style: NEUTRAL (speech articulation only)
    - No emotion inference
    - Focus on lip-sync accuracy

    Usage:
        engine = Audio2FaceEngine()
        await engine.start("session-123")

        async for frame in engine.generate_frames(audio_stream):
            send_to_client(frame)

        await engine.stop()
    """

    def __init__(self, config: Audio2FaceConfig | None = None) -> None:
        self._config = config or Audio2FaceConfig()
        super().__init__(
            target_fps=self._config.target_fps,
            yield_threshold_ms=TMF.ANIMATION_YIELD_THRESHOLD_MS,
        )

        # gRPC client (initialized in start)
        self._stub = None
        self._channel = None

        # Yield and heartbeat controllers
        self._yield_controller: YieldController | None = None
        self._heartbeat: HeartbeatEmitter | None = None

        # Audio buffer
        self._audio_buffer: bytearray = bytearray()

    async def start(self, session_id: str) -> None:
        """Initialize Audio2Face connection for session.

        Args:
            session_id: Session identifier
        """
        await super().start(session_id)

        # Initialize yield controller
        self._yield_controller = YieldController(session_id)

        # Initialize heartbeat emitter
        self._heartbeat = HeartbeatEmitter(
            session_id,
            on_heartbeat=self._handle_heartbeat,
        )
        self._heartbeat.start()

        # Initialize gRPC connection
        # Note: In production, this would connect to Audio2Face service
        # For now, we use mock implementation
        try:
            await self._connect_grpc()
            logger.info(
                "audio2face_connected",
                session_id=session_id,
                host=self._config.grpc_host,
                port=self._config.grpc_port,
            )
        except Exception as e:
            logger.warning(
                "audio2face_connection_failed",
                session_id=session_id,
                error=str(e),
            )
            # Continue with mock mode

    async def _connect_grpc(self) -> None:
        """Connect to Audio2Face gRPC service."""
        # Placeholder for actual gRPC connection
        # In production:
        # import grpc
        # from audio2face_pb2_grpc import Audio2FaceStub
        # self._channel = grpc.aio.insecure_channel(
        #     f"{self._config.grpc_host}:{self._config.grpc_port}"
        # )
        # self._stub = Audio2FaceStub(self._channel)
        pass

    async def generate_frames(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[BlendshapeFrame]:
        """Generate blendshape frames from audio.

        Args:
            audio_stream: Async iterator of audio chunks

        Yields:
            BlendshapeFrame objects at target FPS
        """
        self._generating = True
        self._cancelled = False

        clock = get_audio_clock()
        frame_interval_s = self.frame_interval_ms / 1000.0
        last_frame_time = clock.get_absolute_ms()

        try:
            async for audio_chunk in audio_stream:
                if self._cancelled:
                    break

                # Buffer audio
                self._audio_buffer.extend(audio_chunk)

                # Check if we have enough audio for a frame
                batch_size = int(self._config.batch_audio_ms * 16 * 2)  # 16kHz mono 16-bit
                if len(self._audio_buffer) < batch_size:
                    continue

                # Get audio batch
                audio_batch = bytes(self._audio_buffer[:batch_size])
                self._audio_buffer = self._audio_buffer[batch_size:]

                # Get current time
                t_ms = clock.get_time_ms(self._session_id or "")

                # Check for yield
                lag_ms = t_ms - last_frame_time - int(self.frame_interval_ms)
                if self._yield_controller and self._yield_controller.should_yield(lag_ms):
                    # Yield: use interpolated pose
                    blendshapes = self._yield_controller.get_yield_pose(t_ms)
                else:
                    # Generate actual blendshapes
                    blendshapes = await self._generate_blendshapes(audio_batch)

                    # Record successful frame
                    if self._yield_controller:
                        self._yield_controller.record_frame(blendshapes, t_ms)

                # Create frame
                frame = BlendshapeFrame(
                    session_id=self._session_id or "",
                    seq=self.next_seq(),
                    t_audio_ms=t_ms,
                    blendshapes=blendshapes,
                    fps=self._target_fps,
                )

                yield frame

                # Update heartbeat
                if self._heartbeat:
                    self._heartbeat.frame_sent(t_ms)

                last_frame_time = t_ms

                # Pace frame output
                await asyncio.sleep(frame_interval_s)

        finally:
            self._generating = False
            self._audio_buffer.clear()

    async def _generate_blendshapes(self, audio: bytes) -> dict[str, float]:
        """Generate blendshapes from audio using Audio2Face.

        Args:
            audio: Audio bytes (16kHz mono 16-bit)

        Returns:
            ARKit-52 blendshape dict
        """
        # In production, this would call Audio2Face gRPC
        # For now, return neutral with simulated lip movement
        blendshapes = get_neutral_blendshapes()

        # Simple lip-sync simulation based on audio energy
        if audio:
            # Calculate RMS energy (simplified)
            samples = [int.from_bytes(audio[i:i+2], 'little', signed=True)
                      for i in range(0, min(len(audio), 320), 2)]
            if samples:
                rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
                normalized = min(1.0, rms / 10000.0)

                # Apply to jaw/mouth
                blendshapes["jawOpen"] = normalized * 0.5
                blendshapes["mouthClose"] = 0.1 - normalized * 0.1

        return blendshapes

    def _handle_heartbeat(self, frame: BlendshapeFrame) -> None:
        """Handle heartbeat frame emission."""
        logger.debug(
            "heartbeat_emitted",
            session_id=self._session_id,
            seq=frame.seq,
        )

    async def cancel(self) -> None:
        """Immediately stop frame generation."""
        await super().cancel()

        # Stop heartbeat
        if self._heartbeat:
            self._heartbeat.stop()

        # Clear buffer
        self._audio_buffer.clear()

    async def stop(self) -> None:
        """Stop engine and cleanup."""
        await self.cancel()

        # Close gRPC channel
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

        if self._yield_controller:
            self._yield_controller.reset()

        await super().stop()

    @property
    def yield_controller(self) -> YieldController | None:
        """Yield controller instance."""
        return self._yield_controller


def create_audio2face_engine(
    config: Audio2FaceConfig | None = None,
) -> Audio2FaceEngine:
    """Factory function to create Audio2Face engine.

    Args:
        config: Optional configuration

    Returns:
        Audio2FaceEngine instance
    """
    return Audio2FaceEngine(config)
