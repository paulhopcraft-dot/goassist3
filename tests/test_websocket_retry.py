"""Tests for WebSocket Retry utilities."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.utils.websocket_retry import (
    RetryConfig,
    RetryExhausted,
    with_retry,
    ReconnectingWebSocket,
)


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_defaults(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay_s == 0.5
        assert config.max_delay_s == 10.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            initial_delay_s=1.0,
            max_delay_s=30.0,
            backoff_factor=3.0,
            jitter=False,
        )
        assert config.max_retries == 5
        assert config.initial_delay_s == 1.0
        assert config.max_delay_s == 30.0
        assert config.backoff_factor == 3.0
        assert config.jitter is False


class TestWithRetry:
    """Tests for with_retry function."""

    @pytest.mark.asyncio
    async def test_success_first_attempt(self):
        """Test successful connection on first attempt."""
        mock_connect = AsyncMock(return_value="connection")

        result = await with_retry(mock_connect)

        assert result == "connection"
        assert mock_connect.call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retries(self):
        """Test successful connection after retries."""
        mock_connect = AsyncMock(
            side_effect=[
                ConnectionError("First fail"),
                ConnectionError("Second fail"),
                "connection",
            ]
        )
        config = RetryConfig(max_retries=3, initial_delay_s=0.01, jitter=False)

        result = await with_retry(mock_connect, config=config)

        assert result == "connection"
        assert mock_connect.call_count == 3

    @pytest.mark.asyncio
    async def test_exhausted_retries(self):
        """Test RetryExhausted raised when all retries fail."""
        mock_connect = AsyncMock(side_effect=ConnectionError("Always fails"))
        config = RetryConfig(max_retries=3, initial_delay_s=0.01, jitter=False)

        with pytest.raises(RetryExhausted) as exc_info:
            await with_retry(mock_connect, config=config)

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_error, ConnectionError)

    @pytest.mark.asyncio
    async def test_cancelled_error_not_retried(self):
        """Test CancelledError is not retried."""
        mock_connect = AsyncMock(side_effect=asyncio.CancelledError())
        config = RetryConfig(max_retries=3, initial_delay_s=0.01)

        with pytest.raises(asyncio.CancelledError):
            await with_retry(mock_connect, config=config)

        assert mock_connect.call_count == 1

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff increases delay."""
        delays = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            delays.append(delay)

        mock_connect = AsyncMock(
            side_effect=[
                ConnectionError("Fail 1"),
                ConnectionError("Fail 2"),
                ConnectionError("Fail 3"),
            ]
        )
        config = RetryConfig(
            max_retries=3,
            initial_delay_s=1.0,
            backoff_factor=2.0,
            jitter=False,
        )

        # Patch sleep to capture delays
        asyncio.sleep = mock_sleep
        try:
            with pytest.raises(RetryExhausted):
                await with_retry(mock_connect, config=config)
        finally:
            asyncio.sleep = original_sleep

        # Should have delays of 1.0, 2.0 (exponential backoff)
        assert len(delays) == 2
        assert delays[0] == 1.0
        assert delays[1] == 2.0


class TestReconnectingWebSocket:
    """Tests for ReconnectingWebSocket class."""

    @pytest.mark.asyncio
    async def test_start_success(self):
        """Test successful start."""
        mock_ws = MagicMock()
        mock_connect = AsyncMock(return_value=mock_ws)

        rws = ReconnectingWebSocket(mock_connect, session_id="test-123")
        await rws.start()

        assert rws.is_connected
        assert rws.connection is mock_ws

    @pytest.mark.asyncio
    async def test_stop_closes_connection(self):
        """Test stop closes connection."""
        mock_ws = AsyncMock()
        mock_connect = AsyncMock(return_value=mock_ws)

        rws = ReconnectingWebSocket(mock_connect, session_id="test-123")
        await rws.start()
        await rws.stop()

        assert not rws.is_connected
        mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_connect_callback(self):
        """Test on_connect callback is called."""
        mock_ws = MagicMock()
        mock_connect = AsyncMock(return_value=mock_ws)
        on_connect = AsyncMock()

        rws = ReconnectingWebSocket(
            mock_connect,
            session_id="test-123",
            on_connect=on_connect,
        )
        await rws.start()

        on_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_disconnect_callback(self):
        """Test on_disconnect callback is called."""
        mock_ws = AsyncMock()
        mock_connect = AsyncMock(return_value=mock_ws)
        on_disconnect = AsyncMock()

        rws = ReconnectingWebSocket(
            mock_connect,
            session_id="test-123",
            on_disconnect=on_disconnect,
        )
        await rws.start()
        await rws.stop()

        on_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_reconnect_success(self):
        """Test successful reconnect."""
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        call_count = 0

        async def mock_connect():
            nonlocal call_count
            call_count += 1
            return mock_ws1 if call_count == 1 else mock_ws2

        rws = ReconnectingWebSocket(
            mock_connect,
            session_id="test-123",
            retry_config=RetryConfig(max_retries=1, initial_delay_s=0.01),
        )
        await rws.start()
        assert rws.connection is mock_ws1

        success = await rws.reconnect()

        assert success
        assert rws.connection is mock_ws2

    @pytest.mark.asyncio
    async def test_reconnect_when_not_running(self):
        """Test reconnect returns False when not running."""
        mock_connect = AsyncMock(return_value=MagicMock())

        rws = ReconnectingWebSocket(mock_connect, session_id="test-123")
        # Don't start - _running is False

        success = await rws.reconnect()

        assert not success


class TestRetryExhausted:
    """Tests for RetryExhausted exception."""

    def test_exception_message(self):
        """Test exception message format."""
        error = ConnectionError("Connection refused")
        exc = RetryExhausted(attempts=5, last_error=error)

        assert exc.attempts == 5
        assert exc.last_error is error
        assert "5 attempts" in str(exc)

    def test_exception_without_last_error(self):
        """Test exception without last error."""
        exc = RetryExhausted(attempts=3)

        assert exc.attempts == 3
        assert exc.last_error is None


class TestWithRetryJitter:
    """Tests for jitter behavior in with_retry."""

    @pytest.mark.asyncio
    async def test_jitter_varies_delay(self):
        """Jitter varies the actual delay."""
        from unittest.mock import patch

        delays = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            delays.append(delay)

        mock_connect = AsyncMock(
            side_effect=[ConnectionError("fail"), "conn"]
        )
        config = RetryConfig(
            max_retries=2,
            initial_delay_s=1.0,
            jitter=True,
        )

        asyncio.sleep = mock_sleep
        try:
            with patch("random.random", return_value=0.25):
                await with_retry(mock_connect, config=config)
        finally:
            asyncio.sleep = original_sleep

        # Delay should be 1.0 * (0.5 + 0.25) = 0.75
        assert len(delays) == 1
        assert delays[0] == 0.75

    @pytest.mark.asyncio
    async def test_max_delay_caps_backoff(self):
        """Max delay caps exponential backoff."""
        delays = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            delays.append(delay)

        mock_connect = AsyncMock(
            side_effect=[ConnectionError(), ConnectionError(), ConnectionError()]
        )
        config = RetryConfig(
            max_retries=3,
            initial_delay_s=5.0,
            max_delay_s=8.0,
            backoff_factor=2.0,
            jitter=False,
        )

        asyncio.sleep = mock_sleep
        try:
            with pytest.raises(RetryExhausted):
                await with_retry(mock_connect, config=config)
        finally:
            asyncio.sleep = original_sleep

        # First delay: 5.0, second delay: 8.0 (capped at max_delay_s)
        assert delays[0] == 5.0
        assert delays[1] == 8.0


class TestWithRetryLogging:
    """Tests for logging in with_retry."""

    @pytest.mark.asyncio
    async def test_operation_name_and_session_id(self):
        """Operation name and session ID used for logging."""
        mock_connect = AsyncMock(return_value="conn")

        result = await with_retry(
            mock_connect,
            operation_name="test_op",
            session_id="sess-456",
        )

        assert result == "conn"

    @pytest.mark.asyncio
    async def test_default_config_used(self):
        """Default config used when none provided."""
        mock_connect = AsyncMock(return_value="conn")

        result = await with_retry(mock_connect)

        assert result == "conn"


class TestReconnectingWebSocketInit:
    """Tests for ReconnectingWebSocket initialization."""

    def test_init_default_config(self):
        """Initialize with default config."""
        connect_fn = AsyncMock()
        rws = ReconnectingWebSocket(connect_fn)

        assert rws._retry_config.max_retries == 3
        assert rws._session_id is None
        assert rws._on_connect is None
        assert rws._on_disconnect is None

    def test_init_custom_config(self):
        """Initialize with custom config."""
        connect_fn = AsyncMock()
        config = RetryConfig(max_retries=10)

        rws = ReconnectingWebSocket(
            connect_fn,
            session_id="test-session",
            retry_config=config,
        )

        assert rws._retry_config.max_retries == 10
        assert rws._session_id == "test-session"


class TestReconnectingWebSocketProperties:
    """Tests for ReconnectingWebSocket properties."""

    def test_connection_property(self):
        """connection property returns current connection."""
        connect_fn = AsyncMock()
        rws = ReconnectingWebSocket(connect_fn)

        assert rws.connection is None

        mock_ws = MagicMock()
        rws._connection = mock_ws

        assert rws.connection is mock_ws

    def test_is_connected_false_initially(self):
        """is_connected is False before start."""
        connect_fn = AsyncMock()
        rws = ReconnectingWebSocket(connect_fn)

        assert rws.is_connected is False

    def test_is_connected_false_without_running(self):
        """is_connected is False when not running."""
        connect_fn = AsyncMock()
        rws = ReconnectingWebSocket(connect_fn)
        rws._connection = MagicMock()
        rws._running = False

        assert rws.is_connected is False

    def test_is_connected_true_when_running(self):
        """is_connected is True when running with connection."""
        connect_fn = AsyncMock()
        rws = ReconnectingWebSocket(connect_fn)
        rws._connection = MagicMock()
        rws._running = True

        assert rws.is_connected is True


class TestReconnectingWebSocketCallbacks:
    """Tests for ReconnectingWebSocket callback handling."""

    @pytest.mark.asyncio
    async def test_sync_on_connect_callback(self):
        """Sync on_connect callback is called."""
        mock_ws = MagicMock()
        connect_fn = AsyncMock(return_value=mock_ws)
        on_connect = MagicMock()

        rws = ReconnectingWebSocket(connect_fn, on_connect=on_connect)
        await rws.start()

        on_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_on_disconnect_callback(self):
        """Sync on_disconnect callback is called."""
        mock_ws = AsyncMock()
        connect_fn = AsyncMock(return_value=mock_ws)
        on_disconnect = MagicMock()

        rws = ReconnectingWebSocket(connect_fn, on_disconnect=on_disconnect)
        await rws.start()
        await rws.stop()

        on_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_connect_error_handled(self):
        """on_connect errors are handled gracefully."""
        mock_ws = MagicMock()
        connect_fn = AsyncMock(return_value=mock_ws)
        on_connect = MagicMock(side_effect=ValueError("callback error"))

        rws = ReconnectingWebSocket(connect_fn, on_connect=on_connect)
        # Should not raise
        await rws.start()

        assert rws._connection is mock_ws

    @pytest.mark.asyncio
    async def test_on_disconnect_error_handled(self):
        """on_disconnect errors are handled gracefully."""
        mock_ws = AsyncMock()
        connect_fn = AsyncMock(return_value=mock_ws)
        on_disconnect = MagicMock(side_effect=ValueError("callback error"))

        rws = ReconnectingWebSocket(connect_fn, on_disconnect=on_disconnect)
        await rws.start()
        # Should not raise
        await rws.stop()

        assert rws._connection is None


class TestReconnectingWebSocketLifecycle:
    """Tests for ReconnectingWebSocket lifecycle."""

    @pytest.mark.asyncio
    async def test_stop_clears_state(self):
        """stop() clears all state."""
        mock_ws = AsyncMock()
        connect_fn = AsyncMock(return_value=mock_ws)
        rws = ReconnectingWebSocket(connect_fn)

        await rws.start()
        await rws.stop()

        assert rws._running is False
        assert rws._connection is None

    @pytest.mark.asyncio
    async def test_stop_handles_close_error(self):
        """stop() handles close errors gracefully."""
        mock_ws = AsyncMock()
        mock_ws.close.side_effect = Exception("close error")
        connect_fn = AsyncMock(return_value=mock_ws)
        rws = ReconnectingWebSocket(connect_fn)

        await rws.start()
        # Should not raise
        await rws.stop()

        assert rws._connection is None

    @pytest.mark.asyncio
    async def test_stop_cancels_monitor_task(self):
        """stop() cancels monitor task."""
        mock_ws = AsyncMock()
        connect_fn = AsyncMock(return_value=mock_ws)
        rws = ReconnectingWebSocket(connect_fn)

        await rws.start()

        # Create a mock monitor task
        async def mock_monitor():
            await asyncio.sleep(100)

        rws._monitor_task = asyncio.create_task(mock_monitor())

        await rws.stop()

        assert rws._monitor_task.cancelled() or rws._monitor_task.done()


class TestReconnectingWebSocketReconnect:
    """Tests for ReconnectingWebSocket reconnect."""

    @pytest.mark.asyncio
    async def test_reconnect_calls_on_connect(self):
        """reconnect() calls on_connect callback."""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        connect_fn = AsyncMock(side_effect=[mock_ws1, mock_ws2])
        on_connect = MagicMock()

        rws = ReconnectingWebSocket(connect_fn, on_connect=on_connect)
        await rws.start()
        on_connect.reset_mock()

        await rws.reconnect()

        on_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_reconnect_handles_on_connect_error(self):
        """reconnect() handles on_connect errors gracefully."""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        connect_fn = AsyncMock(side_effect=[mock_ws1, mock_ws2])
        on_connect = MagicMock(side_effect=[None, ValueError("error")])

        rws = ReconnectingWebSocket(connect_fn, on_connect=on_connect)
        await rws.start()

        # Should not raise
        result = await rws.reconnect()

        assert result is True
        assert rws._connection is mock_ws2

    @pytest.mark.asyncio
    async def test_reconnect_failure(self):
        """reconnect() returns False on failure."""
        mock_ws = AsyncMock()
        connect_fn = AsyncMock(side_effect=[mock_ws, ConnectionError("fail")])
        config = RetryConfig(max_retries=1, initial_delay_s=0.01, jitter=False)
        rws = ReconnectingWebSocket(connect_fn, retry_config=config)

        await rws.start()
        result = await rws.reconnect()

        assert result is False

    @pytest.mark.asyncio
    async def test_reconnect_closes_old_connection(self):
        """reconnect() closes old connection before reconnecting."""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        connect_fn = AsyncMock(side_effect=[mock_ws1, mock_ws2])
        rws = ReconnectingWebSocket(connect_fn)

        await rws.start()
        await rws.reconnect()

        mock_ws1.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reconnect_handles_close_error(self):
        """reconnect() handles close error on old connection."""
        mock_ws1 = AsyncMock()
        mock_ws1.close.side_effect = Exception("close failed")
        mock_ws2 = AsyncMock()
        connect_fn = AsyncMock(side_effect=[mock_ws1, mock_ws2])
        rws = ReconnectingWebSocket(connect_fn)

        await rws.start()
        # Should not raise
        result = await rws.reconnect()

        assert result is True
        assert rws._connection is mock_ws2
