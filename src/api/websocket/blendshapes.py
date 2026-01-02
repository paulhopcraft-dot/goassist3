"""WebSocket Blendshapes - Fallback transport for animation data.

Provides WebSocket endpoint for blendshape streaming when WebRTC
data channel is not available. Note: WebRTC data channel is preferred
per TMF §3.7 to avoid TCP head-of-line blocking.

Reference: Implementation-v3.0.md §4.4
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from src.observability.logging import get_logger

logger = get_logger(__name__)


class BlendshapeWebSocket:
    """WebSocket handler for blendshape streaming.

    Fallback for when WebRTC data channel is not available.
    Use WebRTC data channel when possible to avoid head-of-line blocking.

    Usage:
        ws_handler = BlendshapeWebSocket(session_id)
        await ws_handler.connect(websocket)

        # Send blendshapes
        await ws_handler.send_frame(blendshape_dict)

        # Disconnect
        await ws_handler.disconnect()
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._websocket: WebSocket | None = None
        self._connected = False
        self._send_queue: asyncio.Queue = asyncio.Queue(maxsize=30)
        self._send_task: asyncio.Task | None = None

    @property
    def is_connected(self) -> bool:
        """Whether WebSocket is connected."""
        return self._connected

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and store WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
        """
        await websocket.accept()
        self._websocket = websocket
        self._connected = True

        # Start send task
        self._send_task = asyncio.create_task(self._send_loop())

        logger.info(
            "blendshape_ws_connected",
            session_id=self._session_id,
        )

    async def disconnect(self) -> None:
        """Disconnect WebSocket."""
        self._connected = False

        if self._send_task:
            self._send_task.cancel()
            try:
                await self._send_task
            except asyncio.CancelledError:
                pass

        if self._websocket and self._websocket.client_state == WebSocketState.CONNECTED:
            try:
                await self._websocket.close()
            except Exception:
                pass

        logger.info(
            "blendshape_ws_disconnected",
            session_id=self._session_id,
        )

    async def send_frame(self, frame: dict) -> bool:
        """Queue a blendshape frame for sending.

        Args:
            frame: Blendshape frame dict per TMF schema

        Returns:
            True if queued successfully
        """
        if not self._connected:
            return False

        try:
            # Non-blocking put - drop frames if queue full
            self._send_queue.put_nowait(frame)
            return True
        except asyncio.QueueFull:
            # Drop frame rather than block (animation can tolerate drops)
            logger.debug(
                "blendshape_frame_dropped",
                session_id=self._session_id,
            )
            return False

    async def _send_loop(self) -> None:
        """Background loop to send queued frames."""
        while self._connected:
            try:
                frame = await asyncio.wait_for(
                    self._send_queue.get(),
                    timeout=0.1,
                )

                if self._websocket and self._connected:
                    await self._websocket.send_json(frame)

            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                self._connected = False
                break
            except Exception as e:
                logger.warning(
                    "blendshape_send_error",
                    session_id=self._session_id,
                    error=str(e),
                )
                continue


class BlendshapeConnectionManager:
    """Manages multiple blendshape WebSocket connections.

    Usage:
        manager = BlendshapeConnectionManager()

        # New connection
        handler = await manager.connect(session_id, websocket)

        # Send to session
        await manager.send_frame(session_id, frame)

        # Disconnect
        await manager.disconnect(session_id)
    """

    def __init__(self) -> None:
        self._connections: dict[str, BlendshapeWebSocket] = {}

    async def connect(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> BlendshapeWebSocket:
        """Create and connect handler for session.

        Args:
            session_id: Session identifier
            websocket: FastAPI WebSocket

        Returns:
            Connected BlendshapeWebSocket handler
        """
        # Disconnect existing if any
        await self.disconnect(session_id)

        handler = BlendshapeWebSocket(session_id)
        await handler.connect(websocket)
        self._connections[session_id] = handler

        return handler

    async def disconnect(self, session_id: str) -> None:
        """Disconnect session's WebSocket.

        Args:
            session_id: Session identifier
        """
        handler = self._connections.pop(session_id, None)
        if handler:
            await handler.disconnect()

    async def disconnect_all(self) -> None:
        """Disconnect all WebSockets."""
        for session_id in list(self._connections.keys()):
            await self.disconnect(session_id)

    async def send_frame(
        self,
        session_id: str,
        frame: dict,
    ) -> bool:
        """Send blendshape frame to session.

        Args:
            session_id: Session identifier
            frame: Blendshape frame dict

        Returns:
            True if sent successfully
        """
        handler = self._connections.get(session_id)
        if handler:
            return await handler.send_frame(frame)
        return False

    def is_connected(self, session_id: str) -> bool:
        """Check if session has active WebSocket.

        Args:
            session_id: Session identifier

        Returns:
            True if connected
        """
        handler = self._connections.get(session_id)
        return handler is not None and handler.is_connected

    @property
    def active_connections(self) -> int:
        """Number of active connections."""
        return len(self._connections)


# Global manager instance
_manager: BlendshapeConnectionManager | None = None


def get_blendshape_manager() -> BlendshapeConnectionManager:
    """Get global blendshape connection manager."""
    global _manager
    if _manager is None:
        _manager = BlendshapeConnectionManager()
    return _manager
