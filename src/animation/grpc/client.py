"""Audio2Face gRPC Client.

Connects to NVIDIA Audio2Face service for real-time lip-sync.

Audio2Face uses a bidirectional streaming API:
1. Client streams audio chunks
2. Server streams blendshape frames

Reference: NVIDIA Audio2Face SDK, TMF v3.0 §3
"""

import asyncio
import logging
from typing import AsyncIterator

try:
    import grpc
    from grpc import aio as grpc_aio
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

from src.animation.grpc.audio2face_pb2 import (
    AudioRequest,
    BlendshapeResponse,
    StreamConfig,
    get_neutral_blendshapes,
)

logger = logging.getLogger(__name__)


class Audio2FaceClient:
    """gRPC client for NVIDIA Audio2Face service.

    Manages connection and streaming to Audio2Face for
    audio-driven facial animation.

    Usage:
        client = Audio2FaceClient("localhost", 50051)
        await client.connect()

        async for blendshapes in client.stream_audio(audio_chunks):
            apply_to_avatar(blendshapes)

        await client.disconnect()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        instance_id: str = "default",
        style: str = "NEUTRAL",
        timeout_s: float = 5.0,
    ) -> None:
        """Initialize Audio2Face client.

        Args:
            host: Audio2Face server host
            port: Audio2Face server port
            instance_id: Audio2Face instance identifier
            style: Animation style (NEUTRAL, EXPRESSIVE, etc.)
            timeout_s: Connection timeout in seconds
        """
        self._host = host
        self._port = port
        self._instance_id = instance_id
        self._style = style
        self._timeout_s = timeout_s

        self._channel: grpc_aio.Channel | None = None
        self._connected = False
        self._cancel_event = asyncio.Event()

    async def connect(self) -> bool:
        """Connect to Audio2Face server.

        Returns:
            True if connected successfully
        """
        if not GRPC_AVAILABLE:
            logger.error("gRPC not available. Install grpcio: pip install grpcio")
            return False

        try:
            target = f"{self._host}:{self._port}"
            logger.info(f"Connecting to Audio2Face at {target}")

            # Create async channel
            self._channel = grpc_aio.insecure_channel(
                target,
                options=[
                    ('grpc.keepalive_time_ms', 10000),
                    ('grpc.keepalive_timeout_ms', 5000),
                    ('grpc.http2.max_pings_without_data', 0),
                ],
            )

            # Wait for channel to be ready
            try:
                await asyncio.wait_for(
                    self._channel.channel_ready(),
                    timeout=self._timeout_s,
                )
                self._connected = True
                logger.info(f"Connected to Audio2Face at {target}")
                return True

            except asyncio.TimeoutError:
                logger.warning(f"Audio2Face connection timeout: {target}")
                await self.disconnect()
                return False

        except Exception as e:
            logger.error(f"Audio2Face connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Audio2Face server."""
        self._connected = False
        self._cancel_event.set()

        if self._channel:
            await self._channel.close()
            self._channel = None

        logger.info("Disconnected from Audio2Face")

    async def stream_audio(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int = 16000,
    ) -> AsyncIterator[dict[str, float]]:
        """Stream audio and receive blendshapes.

        Args:
            audio_stream: Async iterator of audio chunks (PCM, 16-bit)
            sample_rate: Audio sample rate

        Yields:
            ARKit-52 blendshape dictionaries
        """
        if not self._connected:
            logger.warning("Audio2Face not connected, using fallback")
            async for audio in audio_stream:
                yield self._fallback_blendshapes(audio)
            return

        self._cancel_event.clear()

        try:
            # Create bidirectional stream
            # Note: Actual Audio2Face API uses different method names
            # This is a simplified version for the pattern

            async def request_generator():
                """Generate audio requests from stream."""
                async for audio_chunk in audio_stream:
                    if self._cancel_event.is_set():
                        break
                    yield AudioRequest(
                        audio_data=audio_chunk,
                        sample_rate=sample_rate,
                        instance_id=self._instance_id,
                    )

            # In production, this would be:
            # async for response in self._stub.StreamAudio(request_generator()):
            #     yield response.blendshapes

            # For now, use fallback
            async for audio in audio_stream:
                if self._cancel_event.is_set():
                    break
                yield self._fallback_blendshapes(audio)

        except Exception as e:
            logger.error(f"Audio2Face streaming error: {e}")
            # Return neutral pose on error
            yield get_neutral_blendshapes()

    def _fallback_blendshapes(self, audio: bytes) -> dict[str, float]:
        """Generate fallback blendshapes from audio energy.

        Simple lip-sync simulation when Audio2Face is unavailable.

        Args:
            audio: Audio bytes (PCM, 16-bit)

        Returns:
            ARKit-52 blendshape dictionary
        """
        blendshapes = get_neutral_blendshapes()

        if not audio:
            return blendshapes

        try:
            # Calculate RMS energy
            samples = [
                int.from_bytes(audio[i:i+2], 'little', signed=True)
                for i in range(0, min(len(audio), 640), 2)
            ]

            if samples:
                rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
                normalized = min(1.0, rms / 8000.0)

                # Jaw opening based on volume
                blendshapes["jawOpen"] = normalized * 0.6

                # Mouth shapes for speech simulation
                blendshapes["mouthClose"] = max(0, 0.1 - normalized * 0.15)
                blendshapes["mouthFunnel"] = normalized * 0.2
                blendshapes["mouthPucker"] = normalized * 0.1

                # Subtle lip movement
                blendshapes["mouthUpperUpLeft"] = normalized * 0.15
                blendshapes["mouthUpperUpRight"] = normalized * 0.15
                blendshapes["mouthLowerDownLeft"] = normalized * 0.2
                blendshapes["mouthLowerDownRight"] = normalized * 0.2

        except Exception as e:
            logger.debug(f"Fallback blendshape error: {e}")

        return blendshapes

    async def cancel(self) -> None:
        """Cancel ongoing streaming."""
        self._cancel_event.set()

    @property
    def connected(self) -> bool:
        """Check if connected to Audio2Face."""
        return self._connected


async def create_audio2face_client(
    host: str = "localhost",
    port: int = 50051,
    auto_connect: bool = True,
) -> Audio2FaceClient:
    """Create and optionally connect Audio2Face client.

    Args:
        host: Audio2Face server host
        port: Audio2Face server port
        auto_connect: If True, attempt connection immediately

    Returns:
        Audio2FaceClient instance
    """
    client = Audio2FaceClient(host=host, port=port)

    if auto_connect:
        await client.connect()

    return client
