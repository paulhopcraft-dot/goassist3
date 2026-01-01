"""Async Timeout Utilities.

Provides timeout wrappers for async operations including:
- Async iterator timeout wrapper
- Operation timeout context manager
- Timeout exception handling

Reference: TODO-IMPROVEMENTS.md Phase 1
"""

import asyncio
from typing import AsyncIterator, TypeVar

from src.exceptions import GoAssistError

T = TypeVar("T")


class AsyncTimeoutError(GoAssistError):
    """Raised when an async operation times out."""

    def __init__(
        self,
        operation: str,
        timeout_s: float,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            message=f"{operation} timed out after {timeout_s}s",
            details={
                "operation": operation,
                "timeout_s": timeout_s,
                **(details or {}),
            },
            recoverable=True,  # Caller can retry
        )
        self.operation = operation
        self.timeout_s = timeout_s


async def timeout_async_iterator(
    iterator: AsyncIterator[T],
    timeout_s: float,
    operation: str = "async iteration",
) -> AsyncIterator[T]:
    """Wrap an async iterator with a total timeout.

    The timeout applies to the entire iteration, not per-item.
    Useful for streaming operations that should complete within
    a bounded time.

    Args:
        iterator: The async iterator to wrap
        timeout_s: Maximum time in seconds for entire iteration
        operation: Name of operation for error messages

    Yields:
        Items from the wrapped iterator

    Raises:
        AsyncTimeoutError: If total time exceeds timeout_s
        asyncio.CancelledError: If cancelled externally

    Example:
        async for token in timeout_async_iterator(
            llm.generate_stream(messages),
            timeout_s=30.0,
            operation="LLM streaming",
        ):
            yield token
    """
    deadline = asyncio.get_event_loop().time() + timeout_s

    try:
        async for item in iterator:
            # Check if we've exceeded the deadline
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                raise AsyncTimeoutError(operation, timeout_s)

            yield item

    except asyncio.TimeoutError:
        raise AsyncTimeoutError(operation, timeout_s)


async def timeout_async_iterator_per_item(
    iterator: AsyncIterator[T],
    timeout_s: float,
    operation: str = "async iteration",
) -> AsyncIterator[T]:
    """Wrap an async iterator with a per-item timeout.

    Each item must be received within timeout_s.
    Useful for streaming where items should arrive regularly.

    Args:
        iterator: The async iterator to wrap
        timeout_s: Maximum time in seconds between items
        operation: Name of operation for error messages

    Yields:
        Items from the wrapped iterator

    Raises:
        AsyncTimeoutError: If any item takes longer than timeout_s
        asyncio.CancelledError: If cancelled externally

    Example:
        async for frame in timeout_async_iterator_per_item(
            animation.generate_frames(audio),
            timeout_s=0.1,
            operation="animation frame",
        ):
            send_frame(frame)
    """
    it = iterator.__aiter__()

    while True:
        try:
            item = await asyncio.wait_for(
                it.__anext__(),
                timeout=timeout_s,
            )
            yield item
        except StopAsyncIteration:
            break
        except asyncio.TimeoutError:
            raise AsyncTimeoutError(operation, timeout_s)


async def with_timeout(
    coro,
    timeout_s: float,
    operation: str = "operation",
) -> T:
    """Execute a coroutine with a timeout.

    Simple wrapper around asyncio.wait_for with custom exception.

    Args:
        coro: Coroutine to execute
        timeout_s: Maximum time in seconds
        operation: Name of operation for error messages

    Returns:
        Result of the coroutine

    Raises:
        AsyncTimeoutError: If operation times out

    Example:
        result = await with_timeout(
            fetch_data(),
            timeout_s=5.0,
            operation="data fetch",
        )
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_s)
    except asyncio.TimeoutError:
        raise AsyncTimeoutError(operation, timeout_s)
