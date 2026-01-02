"""WebSocket Retry - Exponential backoff reconnection logic.

Provides robust WebSocket connections with automatic retry for:
- Initial connection failures
- Connection drops during operation
- Graceful degradation under network issues

Reference: Implementation-v3.0.md §4.3
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Callable, TypeVar

from src.observability.logging import get_logger

logger = get_logger(__name__)

# Type for the connection result
T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    initial_delay_s: float = 0.5
    max_delay_s: float = 10.0
    backoff_factor: float = 2.0
    jitter: bool = True


class RetryExhausted(Exception):
    """All retry attempts failed."""

    def __init__(self, attempts: int, last_error: Exception | None = None):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Connection failed after {attempts} attempts")


async def with_retry(
    connect_fn: Callable[[], T],
    config: RetryConfig | None = None,
    operation_name: str = "connect",
    session_id: str | None = None,
) -> T:
    """Execute a connection function with exponential backoff retry.

    Args:
        connect_fn: Async function that establishes connection
        config: Retry configuration
        operation_name: Name for logging
        session_id: Session ID for logging

    Returns:
        Result of connect_fn

    Raises:
        RetryExhausted: If all retries fail

    Example:
        ws = await with_retry(
            lambda: websockets.connect(url),
            config=RetryConfig(max_retries=5),
            operation_name="tts_connect",
            session_id="session-123",
        )
    """
    if config is None:
        config = RetryConfig()

    delay = config.initial_delay_s
    last_error: Exception | None = None

    for attempt in range(1, config.max_retries + 1):
        try:
            result = await connect_fn()
            if attempt > 1:
                logger.info(
                    f"{operation_name}_reconnected",
                    session_id=session_id,
                    attempt=attempt,
                )
            return result

        except asyncio.CancelledError:
            raise

        except Exception as e:
            last_error = e
            if attempt == config.max_retries:
                logger.error(
                    f"{operation_name}_retry_exhausted",
                    session_id=session_id,
                    attempts=attempt,
                    error=str(e),
                )
                raise RetryExhausted(attempt, e)

            # Calculate delay with optional jitter
            actual_delay = delay
            if config.jitter:
                import random
                actual_delay = delay * (0.5 + random.random())

            logger.warning(
                f"{operation_name}_retry",
                session_id=session_id,
                attempt=attempt,
                max_retries=config.max_retries,
                delay_s=actual_delay,
                error=str(e),
            )

            await asyncio.sleep(actual_delay)

            # Increase delay for next attempt
            delay = min(delay * config.backoff_factor, config.max_delay_s)

    # Should never reach here
    raise RetryExhausted(config.max_retries, last_error)


class ReconnectingWebSocket:
    """WebSocket wrapper with automatic reconnection.

    Wraps a WebSocket connection and automatically reconnects on failure.
    Useful for long-lived connections like TTS or ASR.

    Usage:
        async def connect():
            return await websockets.connect(url)

        rws = ReconnectingWebSocket(connect, session_id="session-123")
        await rws.start()

        # Use the connection
        ws = rws.connection
        await ws.send(data)

        # If connection drops, it will auto-reconnect
        await rws.stop()
    """

    def __init__(
        self,
        connect_fn: Callable,
        session_id: str | None = None,
        retry_config: RetryConfig | None = None,
        on_connect: Callable | None = None,
        on_disconnect: Callable | None = None,
    ) -> None:
        """Initialize reconnecting WebSocket.

        Args:
            connect_fn: Async function that returns a WebSocket connection
            session_id: Session ID for logging
            retry_config: Retry configuration
            on_connect: Callback when connected/reconnected
            on_disconnect: Callback when disconnected
        """
        self._connect_fn = connect_fn
        self._session_id = session_id
        self._retry_config = retry_config or RetryConfig()
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect

        self._connection = None
        self._running = False
        self._monitor_task: asyncio.Task | None = None

    @property
    def connection(self):
        """Current WebSocket connection."""
        return self._connection

    @property
    def is_connected(self) -> bool:
        """Whether currently connected."""
        return self._connection is not None and self._running

    async def start(self) -> None:
        """Start connection with retry."""
        self._running = True

        self._connection = await with_retry(
            self._connect_fn,
            config=self._retry_config,
            operation_name="websocket_connect",
            session_id=self._session_id,
        )

        if self._on_connect:
            try:
                if inspect.iscoroutinefunction(self._on_connect):
                    await self._on_connect()
                else:
                    self._on_connect()
            except Exception as e:
                logger.warning(
                    "websocket_on_connect_error",
                    session_id=self._session_id,
                    error=str(e),
                )

    async def stop(self) -> None:
        """Stop connection and monitoring."""
        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
            self._connection = None

        if self._on_disconnect:
            try:
                if inspect.iscoroutinefunction(self._on_disconnect):
                    await self._on_disconnect()
                else:
                    self._on_disconnect()
            except Exception as e:
                logger.warning(
                    "websocket_on_disconnect_error",
                    session_id=self._session_id,
                    error=str(e),
                )

    async def reconnect(self) -> bool:
        """Attempt to reconnect.

        Returns:
            True if reconnected successfully
        """
        if not self._running:
            return False

        # Close existing connection
        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
            self._connection = None

        try:
            self._connection = await with_retry(
                self._connect_fn,
                config=self._retry_config,
                operation_name="websocket_reconnect",
                session_id=self._session_id,
            )

            if self._on_connect:
                try:
                    if inspect.iscoroutinefunction(self._on_connect):
                        await self._on_connect()
                    else:
                        self._on_connect()
                except Exception as e:
                    logger.warning(
                        "websocket_on_reconnect_error",
                        session_id=self._session_id,
                        error=str(e),
                    )

            return True

        except RetryExhausted:
            return False
