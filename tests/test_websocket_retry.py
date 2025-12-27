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
