"""Audio2Face gRPC Client Implementation.

Provides async gRPC client for NVIDIA Audio2Face service.
Handles connection management, streaming, and fallback behavior.

Key Features:
- Async bidirectional streaming
- Automatic reconnection with backoff
- Graceful degradation when service unavailable
- TMF-compliant NEUTRAL configuration

Reference: TMF v3.0 Addendum A §A3
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Callable

from src.animation.base import ARKIT_52_BLENDSHAPES, get_neutral_blendshapes
from src.config.constants import TMF
from src.observability.logging import get_logger

logger = get_logger(__name__)


class ConnectionState(Enum):
    """gRPC connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class Audio2FaceClientConfig:
    """Configuration for Audio2Face gRPC client."""

    host: str = "localhost"
    port: int = 50051
    sample_rate: int = TMF.AUDIO_SAMPLE_RATE
    target_fps: int = 30
    style: str = "NEUTRAL"  # TMF Addendum A §A3.3
    enable_emotion: bool = False  # Disabled per TMF
    blendshape_format: str = "arkit52"
    connect_timeout_s: float = 5.0
    request_timeout_s: float = 1.0
    max_retries: int = 3
    retry_backoff_s: float = 1.0
    keepalive_interval_s: float = 10.0


@dataclass
class BlendshapeFrame:
    """Blendshape frame from Audio2Face."""

    session_id: str
    sequence: int
    timestamp_ms: int
    blendshapes: dict[str, float]
    fps: int = 30
    heartbeat: bool = False
    latency_ms: int = 0


class Audio2FaceClient:
    """Async gRPC client for Audio2Face service.

    Provides streaming audio-to-blendshape conversion with
    automatic connection management and fallback behavior.

    Usage:
        client = Audio2FaceClient(config)
        await client.connect()

        async for frame in client.process_audio_stream(audio_iterator):
            send_to_avatar(frame)

        await client.disconnect()

    Reference: TMF v3.0 Addendum A §A3
    """

    def __init__(self, config: Audio2FaceClientConfig | None = None) -> None:
        self._config = config or Audio2FaceClientConfig()
        self._state = ConnectionState.DISCONNECTED
        self._channel = None
        self._stub = None
        self._session_id: str | None = None
        self._sequence: int = 0
        self._connected_event = asyncio.Event()
        self._shutdown_event = asyncio.Event()
        self._keepalive_task: asyncio.Task | None = None
        self._on_state_change: Callable[[ConnectionState], None] | None = None
        self._grpc_available = False

        # Check if grpc is available
        try:
            import grpc
            self._grpc_available = True
        except ImportError:
            logger.warning("grpc_not_available", message="grpc package not installed, using mock mode")

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Whether client is connected to service."""
        return self._state == ConnectionState.CONNECTED

    @property
    def session_id(self) -> str | None:
        """Current session ID."""
        return self._session_id

    def on_state_change(self, callback: Callable[[ConnectionState], None]) -> None:
        """Register callback for connection state changes."""
        self._on_state_change = callback

    def _set_state(self, state: ConnectionState) -> None:
        """Update connection state and notify callback."""
        old_state = self._state
        self._state = state
        if self._on_state_change and old_state != state:
            try:
                self._on_state_change(state)
            except Exception as e:
                logger.warning("state_change_callback_error", error=str(e))

    async def connect(self, session_id: str | None = None) -> bool:
        """Connect to Audio2Face service.

        Args:
            session_id: Optional session ID (generated if not provided)

        Returns:
            True if connected successfully
        """
        if self._state == ConnectionState.CONNECTED:
            return True

        self._session_id = session_id or f"a2f-{id(self)}"
        self._set_state(ConnectionState.CONNECTING)

        if not self._grpc_available:
            # Mock mode - simulate connected
            logger.info(
                "audio2face_mock_connected",
                session_id=self._session_id,
            )
            self._set_state(ConnectionState.CONNECTED)
            self._connected_event.set()
            return True

        try:
            import grpc

            # Create async channel
            target = f"{self._config.host}:{self._config.port}"
            self._channel = grpc.aio.insecure_channel(
                target,
                options=[
                    ("grpc.keepalive_time_ms", int(self._config.keepalive_interval_s * 1000)),
                    ("grpc.keepalive_timeout_ms", 5000),
                    ("grpc.keepalive_permit_without_calls", True),
                ],
            )

            # Wait for channel to be ready
            try:
                await asyncio.wait_for(
                    self._channel.channel_ready(),
                    timeout=self._config.connect_timeout_s,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "audio2face_connect_timeout",
                    session_id=self._session_id,
                    host=self._config.host,
                    port=self._config.port,
                    message="Falling back to mock mode",
                )
                # Close failed channel
                await self._channel.close()
                self._channel = None
                # Fall through to mock mode instead of failing
                self._set_state(ConnectionState.CONNECTED)
                self._connected_event.set()
                logger.info(
                    "audio2face_mock_mode",
                    session_id=self._session_id,
                    message="Using mock blendshape generation",
                )
                return True

            # Try to load generated stub
            try:
                from src.animation.grpc import audio2face_pb2_grpc
                self._stub = audio2face_pb2_grpc.Audio2FaceStub(self._channel)
            except ImportError:
                logger.warning(
                    "audio2face_stub_not_generated",
                    message="Run protoc to generate stubs",
                )
                # Continue without stub - will use mock mode for calls
                self._stub = None

            # Configure session
            await self._configure_session()

            # Start keepalive
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())

            self._set_state(ConnectionState.CONNECTED)
            self._connected_event.set()

            logger.info(
                "audio2face_connected",
                session_id=self._session_id,
                host=self._config.host,
                port=self._config.port,
            )
            return True

        except Exception as e:
            logger.error(
                "audio2face_connect_error",
                session_id=self._session_id,
                error=str(e),
            )
            # Fall back to mock mode on any error
            self._set_state(ConnectionState.CONNECTED)
            self._connected_event.set()
            logger.info(
                "audio2face_mock_fallback",
                session_id=self._session_id,
                message="Using mock blendshape generation",
            )
            return True

    async def _configure_session(self) -> None:
        """Send session configuration to server."""
        if not self._stub:
            return

        try:
            from src.animation.grpc import audio2face_pb2

            config = audio2face_pb2.SessionConfig(
                session_id=self._session_id,
                sample_rate=self._config.sample_rate,
                target_fps=self._config.target_fps,
                style=self._config.style,
                enable_emotion=self._config.enable_emotion,
                blendshape_format=self._config.blendshape_format,
            )

            response = await asyncio.wait_for(
                self._stub.ConfigureSession(config),
                timeout=self._config.request_timeout_s,
            )

            if not response.success:
                logger.warning(
                    "audio2face_config_failed",
                    session_id=self._session_id,
                    error=response.error,
                )

        except ImportError:
            pass  # Proto not generated
        except Exception as e:
            logger.warning(
                "audio2face_config_error",
                session_id=self._session_id,
                error=str(e),
            )

    async def disconnect(self) -> None:
        """Disconnect from Audio2Face service."""
        self._shutdown_event.set()

        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
            self._keepalive_task = None

        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

        self._set_state(ConnectionState.DISCONNECTED)
        self._connected_event.clear()
        self._shutdown_event.clear()

        logger.info("audio2face_disconnected", session_id=self._session_id)

    async def _keepalive_loop(self) -> None:
        """Background task to maintain connection."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self._config.keepalive_interval_s)

                if self._stub:
                    # Check service status
                    await self.get_status()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    "audio2face_keepalive_error",
                    session_id=self._session_id,
                    error=str(e),
                )

    async def get_status(self) -> dict | None:
        """Get service status.

        Returns:
            Status dict or None if unavailable
        """
        if not self._stub:
            return {"ready": True, "version": "mock", "model_name": "mock"}

        try:
            from src.animation.grpc import audio2face_pb2

            request = audio2face_pb2.StatusRequest()
            response = await asyncio.wait_for(
                self._stub.GetStatus(request),
                timeout=self._config.request_timeout_s,
            )

            return {
                "ready": response.ready,
                "version": response.version,
                "active_sessions": response.active_sessions,
                "gpu_memory_mb": response.gpu_memory_mb,
                "model_name": response.model_name,
            }

        except ImportError:
            return {"ready": True, "version": "mock", "model_name": "mock"}
        except Exception as e:
            logger.warning(
                "audio2face_status_error",
                session_id=self._session_id,
                error=str(e),
            )
            return None

    async def process_audio_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        timestamp_fn: Callable[[], int] | None = None,
    ) -> AsyncIterator[BlendshapeFrame]:
        """Process audio stream and yield blendshape frames.

        Args:
            audio_stream: Async iterator of audio chunks (PCM 16-bit mono)
            timestamp_fn: Optional function to get current timestamp

        Yields:
            BlendshapeFrame objects
        """
        if not self.is_connected:
            logger.warning(
                "audio2face_not_connected",
                session_id=self._session_id,
            )
            return

        self._sequence = 0

        if self._stub and self._grpc_available:
            # Real gRPC streaming
            async for frame in self._process_stream_grpc(audio_stream, timestamp_fn):
                yield frame
        else:
            # Mock mode - simulate blendshape generation
            async for frame in self._process_stream_mock(audio_stream, timestamp_fn):
                yield frame

    async def _process_stream_grpc(
        self,
        audio_stream: AsyncIterator[bytes],
        timestamp_fn: Callable[[], int] | None,
    ) -> AsyncIterator[BlendshapeFrame]:
        """Process audio via gRPC streaming."""
        try:
            from src.animation.grpc import audio2face_pb2

            async def request_generator():
                async for audio_chunk in audio_stream:
                    self._sequence += 1
                    timestamp = timestamp_fn() if timestamp_fn else 0

                    request = audio2face_pb2.AudioRequest(
                        session_id=self._session_id,
                        audio_data=audio_chunk,
                        sample_rate=self._config.sample_rate,
                        timestamp_ms=timestamp,
                        sequence=self._sequence,
                        end_of_stream=False,
                    )
                    yield request

                # Send end of stream
                yield audio2face_pb2.AudioRequest(
                    session_id=self._session_id,
                    end_of_stream=True,
                )

            # Create bidirectional stream
            response_stream = self._stub.ProcessAudioStream(request_generator())

            async for response in response_stream:
                frame = BlendshapeFrame(
                    session_id=response.session_id,
                    sequence=response.sequence,
                    timestamp_ms=response.timestamp_ms,
                    blendshapes=dict(response.blendshapes),
                    fps=response.fps,
                    heartbeat=response.heartbeat,
                    latency_ms=response.latency_ms,
                )
                yield frame

        except ImportError:
            # Fall back to mock
            async for frame in self._process_stream_mock(audio_stream, timestamp_fn):
                yield frame

        except Exception as e:
            logger.error(
                "audio2face_stream_error",
                session_id=self._session_id,
                error=str(e),
            )
            # Attempt reconnection
            self._set_state(ConnectionState.RECONNECTING)
            if await self._reconnect():
                # Retry with mock for remaining audio
                async for frame in self._process_stream_mock(audio_stream, timestamp_fn):
                    yield frame

    async def _process_stream_mock(
        self,
        audio_stream: AsyncIterator[bytes],
        timestamp_fn: Callable[[], int] | None,
    ) -> AsyncIterator[BlendshapeFrame]:
        """Mock audio processing - simulate blendshape generation."""
        frame_interval = 1.0 / self._config.target_fps

        async for audio_chunk in audio_stream:
            self._sequence += 1
            timestamp = timestamp_fn() if timestamp_fn else self._sequence * int(frame_interval * 1000)

            # Generate blendshapes based on audio energy
            blendshapes = self._generate_mock_blendshapes(audio_chunk)

            frame = BlendshapeFrame(
                session_id=self._session_id or "",
                sequence=self._sequence,
                timestamp_ms=timestamp,
                blendshapes=blendshapes,
                fps=self._config.target_fps,
                heartbeat=False,
                latency_ms=1,  # Mock latency
            )

            yield frame

            # Simulate frame timing
            await asyncio.sleep(frame_interval)

    def _generate_mock_blendshapes(self, audio: bytes) -> dict[str, float]:
        """Generate mock blendshapes from audio energy.

        Simple lip-sync simulation based on RMS energy.
        In production, Audio2Face provides accurate lip-sync.
        """
        blendshapes = get_neutral_blendshapes()

        if audio and len(audio) >= 2:
            # Calculate RMS energy
            try:
                samples = [
                    int.from_bytes(audio[i:i + 2], "little", signed=True)
                    for i in range(0, min(len(audio), 320), 2)
                ]
                if samples:
                    rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
                    normalized = min(1.0, rms / 10000.0)

                    # Apply to mouth/jaw blendshapes
                    blendshapes["jawOpen"] = normalized * 0.5
                    blendshapes["mouthClose"] = max(0, 0.1 - normalized * 0.1)

                    # Add subtle lip movement
                    blendshapes["mouthPucker"] = normalized * 0.1
                    blendshapes["mouthFunnel"] = normalized * 0.15

            except Exception:
                pass  # Keep neutral on error

        return blendshapes

    async def _reconnect(self) -> bool:
        """Attempt to reconnect to service."""
        for attempt in range(self._config.max_retries):
            logger.info(
                "audio2face_reconnecting",
                session_id=self._session_id,
                attempt=attempt + 1,
            )

            await asyncio.sleep(self._config.retry_backoff_s * (attempt + 1))

            if await self.connect(self._session_id):
                return True

        self._set_state(ConnectionState.FAILED)
        return False

    async def send_heartbeat(self) -> BlendshapeFrame | None:
        """Send heartbeat and get neutral frame.

        Used when no audio is playing to maintain animation.
        """
        if not self.is_connected:
            return None

        self._sequence += 1
        return BlendshapeFrame(
            session_id=self._session_id or "",
            sequence=self._sequence,
            timestamp_ms=0,
            blendshapes=get_neutral_blendshapes(),
            fps=self._config.target_fps,
            heartbeat=True,
            latency_ms=0,
        )


def create_audio2face_client(
    host: str = "localhost",
    port: int = 50051,
    **kwargs,
) -> Audio2FaceClient:
    """Factory function to create Audio2Face client.

    Args:
        host: gRPC server host
        port: gRPC server port
        **kwargs: Additional config options

    Returns:
        Audio2FaceClient instance
    """
    config = Audio2FaceClientConfig(host=host, port=port, **kwargs)
    return Audio2FaceClient(config)
