"""Tests for Blendshape WebSocket.

Tests cover:
- BlendshapeWebSocket connection/disconnection
- Frame sending and queuing
- BlendshapeConnectionManager
- Multiple session handling
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocketState

from src.api.websocket.blendshapes import (
    BlendshapeWebSocket,
    BlendshapeConnectionManager,
    get_blendshape_manager,
)


class TestBlendshapeWebSocket:
    """Tests for BlendshapeWebSocket class."""

    def test_init(self):
        """Test initialization."""
        ws = BlendshapeWebSocket(session_id="test-session")
        assert ws._session_id == "test-session"
        assert ws.is_connected is False

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test WebSocket connection."""
        ws = BlendshapeWebSocket(session_id="test-session")
        mock_websocket = AsyncMock()

        await ws.connect(mock_websocket)

        assert ws.is_connected is True
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test WebSocket disconnection."""
        ws = BlendshapeWebSocket(session_id="test-session")
        mock_websocket = AsyncMock()
        mock_websocket.client_state = WebSocketState.CONNECTED

        await ws.connect(mock_websocket)
        assert ws.is_connected is True

        await ws.disconnect()
        assert ws.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_already_disconnected(self):
        """Disconnect when already disconnected is safe."""
        ws = BlendshapeWebSocket(session_id="test-session")

        # Should not raise
        await ws.disconnect()
        assert ws.is_connected is False

    @pytest.mark.asyncio
    async def test_send_frame_when_connected(self):
        """Send frame when connected."""
        ws = BlendshapeWebSocket(session_id="test-session")
        mock_websocket = AsyncMock()

        await ws.connect(mock_websocket)

        frame = {"blendshapes": {"jawOpen": 0.5}}
        result = await ws.send_frame(frame)

        assert result is True

    @pytest.mark.asyncio
    async def test_send_frame_when_not_connected(self):
        """Send frame fails when not connected."""
        ws = BlendshapeWebSocket(session_id="test-session")

        frame = {"blendshapes": {"jawOpen": 0.5}}
        result = await ws.send_frame(frame)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_frame_queue_full(self):
        """Frames are dropped when queue is full."""
        ws = BlendshapeWebSocket(session_id="test-session")
        mock_websocket = AsyncMock()

        await ws.connect(mock_websocket)

        # Fill the queue (maxsize=30)
        for i in range(30):
            await ws.send_frame({"seq": i})

        # Next frame should be dropped
        result = await ws.send_frame({"seq": 30})
        assert result is False

        # Clean up
        await ws.disconnect()


class TestBlendshapeConnectionManager:
    """Tests for BlendshapeConnectionManager class."""

    def test_init(self):
        """Test initialization."""
        manager = BlendshapeConnectionManager()
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_connect_session(self):
        """Connect a session."""
        manager = BlendshapeConnectionManager()
        mock_websocket = AsyncMock()

        handler = await manager.connect("session-1", mock_websocket)

        assert handler is not None
        assert manager.active_connections == 1
        assert manager.is_connected("session-1") is True

        await manager.disconnect_all()

    @pytest.mark.asyncio
    async def test_disconnect_session(self):
        """Disconnect a session."""
        manager = BlendshapeConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.client_state = WebSocketState.CONNECTED

        await manager.connect("session-1", mock_websocket)
        assert manager.active_connections == 1

        await manager.disconnect("session-1")
        assert manager.active_connections == 0
        assert manager.is_connected("session-1") is False

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_session(self):
        """Disconnect nonexistent session is safe."""
        manager = BlendshapeConnectionManager()

        # Should not raise
        await manager.disconnect("nonexistent")

    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """Handle multiple sessions."""
        manager = BlendshapeConnectionManager()

        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()

        await manager.connect("session-1", mock_ws1)
        await manager.connect("session-2", mock_ws2)
        await manager.connect("session-3", mock_ws3)

        assert manager.active_connections == 3
        assert manager.is_connected("session-1") is True
        assert manager.is_connected("session-2") is True
        assert manager.is_connected("session-3") is True

        await manager.disconnect_all()
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_reconnect_replaces_existing(self):
        """Reconnecting replaces existing connection."""
        manager = BlendshapeConnectionManager()

        mock_ws1 = AsyncMock()
        mock_ws1.client_state = WebSocketState.CONNECTED
        mock_ws2 = AsyncMock()

        await manager.connect("session-1", mock_ws1)
        assert manager.active_connections == 1

        # Reconnect with new websocket
        await manager.connect("session-1", mock_ws2)
        assert manager.active_connections == 1

        await manager.disconnect_all()

    @pytest.mark.asyncio
    async def test_send_frame_to_session(self):
        """Send frame to specific session."""
        manager = BlendshapeConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect("session-1", mock_websocket)

        frame = {"blendshapes": {"jawOpen": 0.5}}
        result = await manager.send_frame("session-1", frame)

        assert result is True

        await manager.disconnect_all()

    @pytest.mark.asyncio
    async def test_send_frame_to_nonexistent_session(self):
        """Send frame to nonexistent session returns False."""
        manager = BlendshapeConnectionManager()

        frame = {"blendshapes": {"jawOpen": 0.5}}
        result = await manager.send_frame("nonexistent", frame)

        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_all(self):
        """Disconnect all sessions."""
        manager = BlendshapeConnectionManager()

        for i in range(5):
            mock_ws = AsyncMock()
            mock_ws.client_state = WebSocketState.CONNECTED
            await manager.connect(f"session-{i}", mock_ws)

        assert manager.active_connections == 5

        await manager.disconnect_all()
        assert manager.active_connections == 0

    def test_is_connected_false_for_unknown(self):
        """is_connected returns False for unknown session."""
        manager = BlendshapeConnectionManager()
        assert manager.is_connected("unknown") is False


class TestGetBlendshapeManager:
    """Tests for get_blendshape_manager singleton."""

    def test_returns_manager(self):
        """Returns a BlendshapeConnectionManager instance."""
        manager = get_blendshape_manager()
        assert isinstance(manager, BlendshapeConnectionManager)

    def test_returns_same_instance(self):
        """Returns same instance on multiple calls."""
        manager1 = get_blendshape_manager()
        manager2 = get_blendshape_manager()
        assert manager1 is manager2
