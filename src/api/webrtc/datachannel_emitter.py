"""Data Channel Emitter - Send blendshapes via WebRTC data channel.

This is a compatibility wrapper around WebRTCGateway.send_blendshapes().
For new code, use WebRTCGateway directly.

Reference: TMF v3.0 §3.7
"""

from __future__ import annotations

import json
from typing import Any

from src.animation.base import BlendshapeFrame
from src.observability.logging import get_logger

logger = get_logger(__name__)


class DataChannelEmitter:
    """Emitter for blendshapes over WebRTC data channel.

    Note: This is a stub for backward compatibility with tests.
    Production code should use WebRTCGateway.send_blendshapes() directly.
    """

    def __init__(self) -> None:
        self._channel: Any | None = None

    def set_data_channel(self, channel: Any) -> None:
        """Set the data channel to send on.

        Args:
            channel: aiortc RTCDataChannel or mock
        """
        self._channel = channel

    async def send_frame(self, frame: BlendshapeFrame) -> None:
        """Send a blendshape frame over the data channel.

        Args:
            frame: BlendshapeFrame to send

        Raises:
            ValueError: If data channel not set or not open
        """
        if not self._channel:
            raise ValueError("Data channel not set")

        if not hasattr(self._channel, "readyState") or self._channel.readyState != "open":
            logger.warning(
                "datachannel_not_open",
                session_id=frame.session_id,
                state=getattr(self._channel, "readyState", "unknown"),
            )
            return

        # Convert frame to JSON
        data = {
            "session_id": frame.session_id,
            "seq": frame.seq,
            "t_audio_ms": frame.t_audio_ms,
            "blendshapes": frame.blendshapes,
        }

        # Send as JSON string
        self._channel.send(json.dumps(data))

        logger.debug(
            "blendshape_sent",
            session_id=frame.session_id,
            seq=frame.seq,
            count=len(frame.blendshapes),
        )
