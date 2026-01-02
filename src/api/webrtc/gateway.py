"""WebRTC Gateway - aiortc-based real-time audio/data transport.

Provides:
- WebRTC peer connections with STUN/TURN support
- Audio track for voice input/output
- Data channel for blendshapes (UDP, no head-of-line blocking)
- Jitter buffer integration

Reference: TMF v3.0 §3.7, Implementation §4.4
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from aiortc import (
    MediaStreamTrack,
    RTCConfiguration,
    RTCDataChannel,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.media import MediaBlackhole, MediaRecorder, MediaRelay

from src.config.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WebRTCConfig:
    """Configuration for WebRTC connections."""

    stun_servers: list[str] = field(default_factory=lambda: [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302",
    ])
    turn_servers: list[dict] = field(default_factory=list)
    enable_data_channel: bool = True
    data_channel_ordered: bool = False  # UDP-like for animation
    data_channel_max_retransmits: int = 0  # Don't retransmit
    audio_sample_rate: int = 16000
    audio_channels: int = 1


@dataclass
class PeerConnectionState:
    """State of a peer connection."""

    session_id: str
    pc: RTCPeerConnection
    audio_track: MediaStreamTrack | None = None
    data_channel: RTCDataChannel | None = None
    is_connected: bool = False
    is_audio_active: bool = False


class AudioTrackSink:
    """Sink for incoming audio from WebRTC.

    Receives audio frames and forwards to VAD/ASR pipeline.
    """

    def __init__(
        self,
        session_id: str,
        on_audio: Callable[[bytes, int], None],
    ) -> None:
        self._session_id = session_id
        self._on_audio = on_audio
        self._running = False

    async def start(self, track: MediaStreamTrack) -> None:
        """Start receiving audio from track.

        Args:
            track: WebRTC audio track
        """
        self._running = True

        while self._running:
            try:
                frame = await track.recv()

                # Extract audio bytes and timestamp
                # aiortc frames are av.AudioFrame objects
                audio_bytes = frame.to_ndarray().tobytes()
                timestamp_ms = int(frame.pts * 1000 / frame.sample_rate)

                self._on_audio(audio_bytes, timestamp_ms)

            except Exception as e:
                if self._running:
                    logger.error(
                        "audio_receive_error",
                        session_id=self._session_id,
                        error=str(e),
                    )
                break

    def stop(self) -> None:
        """Stop receiving audio."""
        self._running = False


class WebRTCGateway:
    """WebRTC gateway for real-time audio and data transport.

    Manages peer connections with:
    - Audio tracks for voice I/O
    - Data channels for blendshapes (TMF §3.7)
    - STUN/TURN for NAT traversal

    Usage:
        gateway = WebRTCGateway()

        # Handle SDP offer from client
        answer = await gateway.handle_offer(session_id, offer_sdp)

        # Set up audio callback
        gateway.on_audio(session_id, handle_audio)

        # Send audio to client
        await gateway.send_audio(session_id, audio_bytes, timestamp_ms)

        # Send blendshapes via data channel
        await gateway.send_blendshapes(session_id, blendshape_dict)
    """

    def __init__(self, config: WebRTCConfig | None = None) -> None:
        if config is None:
            settings = get_settings()
            config = WebRTCConfig(
                turn_servers=[{
                    "urls": settings.turn_url,
                    "username": settings.turn_username,
                    "credential": settings.turn_credential,
                }] if settings.turn_url else [],
            )

        self._config = config
        self._connections: dict[str, PeerConnectionState] = {}
        self._audio_callbacks: dict[str, Callable[[bytes, int], None]] = {}
        self._relay = MediaRelay()

    def _create_rtc_config(self) -> RTCConfiguration:
        """Create RTCConfiguration with STUN/TURN servers."""
        ice_servers = []

        # Add STUN servers
        for stun in self._config.stun_servers:
            ice_servers.append(RTCIceServer(urls=stun))

        # Add TURN servers
        for turn in self._config.turn_servers:
            ice_servers.append(RTCIceServer(
                urls=turn.get("urls", ""),
                username=turn.get("username"),
                credential=turn.get("credential"),
            ))

        return RTCConfiguration(iceServers=ice_servers)

    async def handle_offer(
        self,
        session_id: str,
        offer_sdp: str,
    ) -> str:
        """Handle SDP offer from client and return answer.

        Args:
            session_id: Session identifier
            offer_sdp: SDP offer from client

        Returns:
            SDP answer string
        """
        # Create peer connection
        pc = RTCPeerConnection(self._create_rtc_config())

        state = PeerConnectionState(session_id=session_id, pc=pc)
        self._connections[session_id] = state

        # Set up event handlers
        @pc.on("connectionstatechange")
        async def on_connection_state_change():
            logger.info(
                "connection_state_change",
                session_id=session_id,
                state=pc.connectionState,
            )
            state.is_connected = pc.connectionState == "connected"

        @pc.on("track")
        async def on_track(track: MediaStreamTrack):
            if track.kind == "audio":
                state.audio_track = track
                state.is_audio_active = True

                logger.info(
                    "audio_track_received",
                    session_id=session_id,
                )

                # Start audio sink if callback registered
                if session_id in self._audio_callbacks:
                    sink = AudioTrackSink(
                        session_id,
                        self._audio_callbacks[session_id],
                    )
                    asyncio.create_task(sink.start(track))

        # Create data channel for blendshapes (TMF §3.7)
        if self._config.enable_data_channel:
            data_channel = pc.createDataChannel(
                "blendshapes",
                ordered=self._config.data_channel_ordered,
                maxRetransmits=self._config.data_channel_max_retransmits,
            )
            state.data_channel = data_channel

            @data_channel.on("open")
            def on_data_channel_open():
                logger.info(
                    "data_channel_open",
                    session_id=session_id,
                )

            @data_channel.on("close")
            def on_data_channel_close():
                logger.info(
                    "data_channel_close",
                    session_id=session_id,
                )

        # Set remote description (offer)
        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await pc.setRemoteDescription(offer)

        # Create and set local description (answer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return pc.localDescription.sdp

    async def handle_ice_candidate(
        self,
        session_id: str,
        candidate: dict,
    ) -> None:
        """Add ICE candidate from client.

        Args:
            session_id: Session identifier
            candidate: ICE candidate dict
        """
        state = self._connections.get(session_id)
        if not state:
            return

        await state.pc.addIceCandidate(candidate)

    def on_audio(
        self,
        session_id: str,
        callback: Callable[[bytes, int], None],
    ) -> None:
        """Register callback for incoming audio.

        Args:
            session_id: Session identifier
            callback: Function to call with (audio_bytes, timestamp_ms)
        """
        self._audio_callbacks[session_id] = callback

    async def send_blendshapes(
        self,
        session_id: str,
        blendshapes: dict,
    ) -> bool:
        """Send blendshape frame via data channel.

        Uses WebRTC data channel (UDP-like) to avoid
        head-of-line blocking that affects WebSocket.

        Args:
            session_id: Session identifier
            blendshapes: Blendshape frame dict per TMF schema

        Returns:
            True if sent successfully
        """
        state = self._connections.get(session_id)
        if not state or not state.data_channel:
            return False

        if state.data_channel.readyState != "open":
            return False

        try:
            # Serialize and send
            data = json.dumps(blendshapes)
            state.data_channel.send(data)
            return True
        except Exception as e:
            logger.warning(
                "blendshape_send_error",
                session_id=session_id,
                error=str(e),
            )
            return False

    async def close_connection(self, session_id: str) -> None:
        """Close a peer connection.

        Args:
            session_id: Session identifier
        """
        state = self._connections.pop(session_id, None)
        if state:
            await state.pc.close()

        self._audio_callbacks.pop(session_id, None)

        logger.info(
            "connection_closed",
            session_id=session_id,
        )

    async def close_all(self) -> None:
        """Close all peer connections."""
        for session_id in list(self._connections.keys()):
            await self.close_connection(session_id)

    def get_connection_state(self, session_id: str) -> str | None:
        """Get connection state for a session.

        Args:
            session_id: Session identifier

        Returns:
            Connection state string, or None if not found
        """
        state = self._connections.get(session_id)
        if state:
            return state.pc.connectionState
        return None

    def is_connected(self, session_id: str) -> bool:
        """Check if session is connected.

        Args:
            session_id: Session identifier

        Returns:
            True if connected
        """
        state = self._connections.get(session_id)
        return state is not None and state.is_connected

    @property
    def active_connections(self) -> int:
        """Number of active connections."""
        return len(self._connections)


# Factory function
def create_webrtc_gateway(config: WebRTCConfig | None = None) -> WebRTCGateway:
    """Create WebRTC gateway instance.

    Args:
        config: Optional configuration

    Returns:
        WebRTCGateway instance
    """
    return WebRTCGateway(config)
