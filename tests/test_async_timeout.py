"""Tests for Async Timeout Utilities.

Tests cover:
- AsyncTimeoutError exception
- timeout_async_iterator (total timeout)
- timeout_async_iterator_per_item (per-item timeout)
- with_timeout helper
"""

import asyncio
import pytest

from src.utils.async_timeout import (
    AsyncTimeoutError,
    timeout_async_iterator,
    timeout_async_iterator_per_item,
    with_timeout,
)


class TestAsyncTimeoutError:
    """Tests for AsyncTimeoutError exception."""

    def test_basic_creation(self):
        """Create basic timeout error."""
        error = AsyncTimeoutError("test operation", 5.0)

        assert error.operation == "test operation"
        assert error.timeout_s == 5.0
        assert "test operation" in str(error)
        assert "5.0s" in str(error)

    def test_with_details(self):
        """Create timeout error with details."""
        error = AsyncTimeoutError(
            "LLM streaming",
            30.0,
            details={"model": "llama-3", "tokens": 1000},
        )

        assert error.details["operation"] == "LLM streaming"
        assert error.details["timeout_s"] == 30.0
        assert error.details["model"] == "llama-3"
        assert error.details["tokens"] == 1000

    def test_is_recoverable(self):
        """Timeout errors are recoverable by default."""
        error = AsyncTimeoutError("operation", 1.0)
        assert error.recoverable is True

    def test_to_dict(self):
        """Convert to dictionary."""
        error = AsyncTimeoutError("animation frame", 0.5)
        result = error.to_dict()

        assert result["type"] == "AsyncTimeoutError"
        assert "animation frame" in result["message"]
        assert result["details"]["timeout_s"] == 0.5
        assert result["recoverable"] is True


class TestTimeoutAsyncIterator:
    """Tests for timeout_async_iterator (total timeout)."""

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self):
        """Iterator completes when within timeout."""
        async def quick_iterator():
            for i in range(5):
                yield i
                await asyncio.sleep(0.01)

        results = []
        async for item in timeout_async_iterator(
            quick_iterator(),
            timeout_s=1.0,
            operation="test",
        ):
            results.append(item)

        assert results == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_timeout_on_slow_iteration(self):
        """Raises timeout when total time exceeded."""
        async def slow_iterator():
            for i in range(10):
                yield i
                await asyncio.sleep(0.2)

        with pytest.raises(AsyncTimeoutError) as exc_info:
            async for _ in timeout_async_iterator(
                slow_iterator(),
                timeout_s=0.5,
                operation="slow test",
            ):
                pass

        assert exc_info.value.operation == "slow test"
        assert exc_info.value.timeout_s == 0.5

    @pytest.mark.asyncio
    async def test_empty_iterator(self):
        """Handles empty iterator."""
        async def empty_iterator():
            return
            yield  # Make it a generator

        results = []
        async for item in timeout_async_iterator(
            empty_iterator(),
            timeout_s=1.0,
            operation="empty",
        ):
            results.append(item)

        assert results == []

    @pytest.mark.asyncio
    async def test_cancellation_propagates(self):
        """CancelledError propagates through."""
        async def endless_iterator():
            while True:
                yield 1
                await asyncio.sleep(0.1)

        async def run_with_cancel():
            task = asyncio.current_task()
            asyncio.get_event_loop().call_later(0.1, task.cancel)

            async for _ in timeout_async_iterator(
                endless_iterator(),
                timeout_s=10.0,
                operation="cancel test",
            ):
                pass

        with pytest.raises(asyncio.CancelledError):
            await run_with_cancel()


class TestTimeoutAsyncIteratorPerItem:
    """Tests for timeout_async_iterator_per_item (per-item timeout)."""

    @pytest.mark.asyncio
    async def test_all_items_within_timeout(self):
        """All items complete within per-item timeout."""
        async def regular_iterator():
            for i in range(5):
                yield i
                await asyncio.sleep(0.05)

        results = []
        async for item in timeout_async_iterator_per_item(
            regular_iterator(),
            timeout_s=0.5,
            operation="regular",
        ):
            results.append(item)

        assert results == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_timeout_on_single_slow_item(self):
        """Raises timeout when single item takes too long."""
        async def variable_speed_iterator():
            yield 1
            await asyncio.sleep(0.01)
            yield 2
            await asyncio.sleep(0.5)  # This one is slow
            yield 3

        results = []
        with pytest.raises(AsyncTimeoutError) as exc_info:
            async for item in timeout_async_iterator_per_item(
                variable_speed_iterator(),
                timeout_s=0.1,
                operation="frame",
            ):
                results.append(item)

        # Should have received first two items before timeout
        assert 1 in results
        assert 2 in results
        assert exc_info.value.operation == "frame"

    @pytest.mark.asyncio
    async def test_empty_iterator(self):
        """Handles empty iterator."""
        async def empty_iterator():
            return
            yield

        results = []
        async for item in timeout_async_iterator_per_item(
            empty_iterator(),
            timeout_s=1.0,
            operation="empty",
        ):
            results.append(item)

        assert results == []

    @pytest.mark.asyncio
    async def test_single_item_within_timeout(self):
        """Single item iterator works."""
        async def single_item():
            yield "only"

        results = []
        async for item in timeout_async_iterator_per_item(
            single_item(),
            timeout_s=1.0,
            operation="single",
        ):
            results.append(item)

        assert results == ["only"]


class TestWithTimeout:
    """Tests for with_timeout helper."""

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self):
        """Coroutine completes within timeout."""
        async def quick_task():
            await asyncio.sleep(0.01)
            return "done"

        result = await with_timeout(
            quick_task(),
            timeout_s=1.0,
            operation="quick",
        )

        assert result == "done"

    @pytest.mark.asyncio
    async def test_timeout_on_slow_coroutine(self):
        """Raises timeout on slow coroutine."""
        async def slow_task():
            await asyncio.sleep(10.0)
            return "never"

        with pytest.raises(AsyncTimeoutError) as exc_info:
            await with_timeout(
                slow_task(),
                timeout_s=0.1,
                operation="slow",
            )

        assert exc_info.value.operation == "slow"
        assert exc_info.value.timeout_s == 0.1

    @pytest.mark.asyncio
    async def test_preserves_return_value(self):
        """Return value is preserved."""
        async def returns_dict():
            return {"key": "value", "number": 42}

        result = await with_timeout(
            returns_dict(),
            timeout_s=1.0,
            operation="dict",
        )

        assert result == {"key": "value", "number": 42}

    @pytest.mark.asyncio
    async def test_preserves_exception(self):
        """Exceptions from coroutine propagate."""
        async def raises_error():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await with_timeout(
                raises_error(),
                timeout_s=1.0,
                operation="error",
            )


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @pytest.mark.asyncio
    async def test_llm_streaming_simulation(self):
        """Simulate LLM streaming with timeout."""
        async def mock_llm_stream():
            tokens = ["Hello", " ", "world", "!"]
            for token in tokens:
                await asyncio.sleep(0.02)
                yield token

        result = []
        async for token in timeout_async_iterator(
            mock_llm_stream(),
            timeout_s=1.0,
            operation="LLM streaming",
        ):
            result.append(token)

        assert "".join(result) == "Hello world!"

    @pytest.mark.asyncio
    async def test_animation_frame_simulation(self):
        """Simulate animation frames with per-frame timeout."""
        async def mock_frame_stream():
            for seq in range(30):  # 1 second at 30 FPS
                await asyncio.sleep(1/60)  # ~16ms per frame
                yield {"seq": seq, "blendshapes": {"jawOpen": 0.1}}

        frames = []
        async for frame in timeout_async_iterator_per_item(
            mock_frame_stream(),
            timeout_s=0.5,
            operation="animation frame",
        ):
            frames.append(frame)

        assert len(frames) == 30
        assert frames[0]["seq"] == 0
        assert frames[-1]["seq"] == 29

    @pytest.mark.asyncio
    async def test_context_rollover_simulation(self):
        """Simulate context rollover with timeout."""
        async def mock_summarize():
            await asyncio.sleep(0.05)
            return "Summary of conversation..."

        result = await with_timeout(
            mock_summarize(),
            timeout_s=5.0,
            operation="context summarization",
        )

        assert result == "Summary of conversation..."

    @pytest.mark.asyncio
    async def test_nested_timeouts(self):
        """Nested timeout scenarios work correctly."""
        async def inner_operation():
            await asyncio.sleep(0.02)
            return "inner"

        async def outer_operation():
            result = await with_timeout(
                inner_operation(),
                timeout_s=1.0,
                operation="inner",
            )
            return f"outer_{result}"

        result = await with_timeout(
            outer_operation(),
            timeout_s=2.0,
            operation="outer",
        )

        assert result == "outer_inner"
