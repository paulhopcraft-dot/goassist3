"""Tests for CANCEL Control-Plane Message Propagation.

Tests the cancellation controller for barge-in support.
Reference: TMF v3.0 §4.2
"""

import asyncio
import pytest

from src.orchestrator.cancellation import (
    CancelReason,
    CancelMessage,
    CancellationController,
    create_cancel_handler,
)
from src.audio.transport.audio_clock import get_audio_clock


class TestCancelReason:
    """Tests for CancelReason enum."""

    def test_all_reasons_exist(self):
        """All expected reasons exist."""
        assert CancelReason.USER_BARGE_IN.value == "USER_BARGE_IN"
        assert CancelReason.USER_STOP.value == "USER_STOP"
        assert CancelReason.SYSTEM_OVERLOAD.value == "SYSTEM_OVERLOAD"
        assert CancelReason.TIMEOUT.value == "TIMEOUT"
        assert CancelReason.ERROR.value == "ERROR"


class TestCancelMessage:
    """Tests for CancelMessage dataclass."""

    def test_create_message(self):
        """Create cancel message."""
        msg = CancelMessage(
            session_id="session-123",
            reason=CancelReason.USER_BARGE_IN,
            t_event_ms=12345,
        )

        assert msg.session_id == "session-123"
        assert msg.reason == CancelReason.USER_BARGE_IN
        assert msg.t_event_ms == 12345

    def test_to_dict(self):
        """Serialize to dictionary."""
        msg = CancelMessage(
            session_id="session-123",
            reason=CancelReason.USER_STOP,
            t_event_ms=67890,
        )

        d = msg.to_dict()

        assert d["session_id"] == "session-123"
        assert d["type"] == "CANCEL"
        assert d["reason"] == "USER_STOP"
        assert d["t_event_ms"] == 67890

    def test_from_dict(self):
        """Deserialize from dictionary."""
        d = {
            "session_id": "session-456",
            "type": "CANCEL",
            "reason": "SYSTEM_OVERLOAD",
            "t_event_ms": 11111,
        }

        msg = CancelMessage.from_dict(d)

        assert msg.session_id == "session-456"
        assert msg.reason == CancelReason.SYSTEM_OVERLOAD
        assert msg.t_event_ms == 11111

    def test_round_trip(self):
        """to_dict and from_dict are inverses."""
        original = CancelMessage(
            session_id="test-session",
            reason=CancelReason.TIMEOUT,
            t_event_ms=99999,
        )

        d = original.to_dict()
        restored = CancelMessage.from_dict(d)

        assert restored.session_id == original.session_id
        assert restored.reason == original.reason
        assert restored.t_event_ms == original.t_event_ms


class TestCancellationController:
    """Tests for CancellationController."""

    @pytest.fixture
    def controller(self):
        """Create a controller with registered session."""
        clock = get_audio_clock()
        session_id = "test-session"
        clock.start_session(session_id)
        controller = CancellationController(session_id)
        yield controller
        try:
            clock.end_session(session_id)
        except KeyError:
            pass

    def test_init(self, controller):
        """Controller initializes correctly."""
        assert controller.session_id == "test-session"
        assert not controller.is_cancelled
        assert controller.last_cancel is None

    def test_register_handler(self, controller):
        """Can register handlers."""
        handler_called = False

        def handler(msg):
            nonlocal handler_called
            handler_called = True

        controller.register(handler)
        assert len(controller._handlers) == 1

    def test_unregister_handler(self, controller):
        """Can unregister handlers."""
        def handler(msg):
            pass

        controller.register(handler)
        assert len(controller._handlers) == 1

        controller.unregister(handler)
        assert len(controller._handlers) == 0

    @pytest.mark.asyncio
    async def test_cancel_calls_sync_handler(self, controller):
        """Cancel calls synchronous handlers."""
        received = []

        def handler(msg):
            received.append(msg)

        controller.register(handler)
        await controller.cancel(CancelReason.USER_BARGE_IN)

        assert len(received) == 1
        assert received[0].reason == CancelReason.USER_BARGE_IN

    @pytest.mark.asyncio
    async def test_cancel_calls_async_handler(self, controller):
        """Cancel calls async handlers."""
        received = []

        async def handler(msg):
            received.append(msg)

        controller.register(handler)
        await controller.cancel(CancelReason.USER_STOP)

        assert len(received) == 1
        assert received[0].reason == CancelReason.USER_STOP

    @pytest.mark.asyncio
    async def test_cancel_calls_multiple_handlers(self, controller):
        """Cancel calls all registered handlers."""
        sync_called = False
        async_called = False

        def sync_handler(msg):
            nonlocal sync_called
            sync_called = True

        async def async_handler(msg):
            nonlocal async_called
            async_called = True

        controller.register(sync_handler)
        controller.register(async_handler)
        await controller.cancel()

        assert sync_called
        assert async_called

    @pytest.mark.asyncio
    async def test_cancel_sets_is_cancelled(self, controller):
        """Cancel sets is_cancelled flag."""
        assert not controller.is_cancelled

        await controller.cancel()

        assert controller.is_cancelled

    @pytest.mark.asyncio
    async def test_cancel_stores_last_cancel(self, controller):
        """Cancel stores the last cancel message."""
        assert controller.last_cancel is None

        await controller.cancel(CancelReason.ERROR)

        assert controller.last_cancel is not None
        assert controller.last_cancel.reason == CancelReason.ERROR

    @pytest.mark.asyncio
    async def test_reset_clears_cancelled(self, controller):
        """Reset clears is_cancelled flag."""
        await controller.cancel()
        assert controller.is_cancelled

        controller.reset()

        assert not controller.is_cancelled

    @pytest.mark.asyncio
    async def test_handler_error_doesnt_stop_cancel(self, controller):
        """Handler error doesn't stop cancel propagation."""
        second_called = False

        def bad_handler(msg):
            raise ValueError("Handler error")

        def good_handler(msg):
            nonlocal second_called
            second_called = True

        controller.register(bad_handler)
        controller.register(good_handler)

        # Should not raise
        await controller.cancel()

        assert second_called

    @pytest.mark.asyncio
    async def test_cancel_timeout(self, controller):
        """Slow handlers are abandoned after timeout."""
        slow_completed = False

        async def slow_handler(msg):
            nonlocal slow_completed
            await asyncio.sleep(1.0)  # 1 second - way over 150ms
            slow_completed = True

        controller.register(slow_handler)

        # Use short timeout
        result = await controller.cancel(timeout_ms=50)

        assert not result  # Handler didn't complete in time
        # Give a moment for cleanup
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_cancel_returns_true_when_all_complete(self, controller):
        """Cancel returns True when all handlers complete."""
        async def fast_handler(msg):
            pass

        controller.register(fast_handler)
        result = await controller.cancel(timeout_ms=1000)

        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_with_no_handlers(self, controller):
        """Cancel works with no handlers."""
        result = await controller.cancel()
        assert result is True
        assert controller.is_cancelled


class TestCreateCancelHandler:
    """Tests for create_cancel_handler factory."""

    @pytest.mark.asyncio
    async def test_creates_async_handler(self):
        """Creates an async handler."""
        called = False

        def cancel_fn():
            nonlocal called
            called = True

        handler = create_cancel_handler("test", cancel_fn)
        msg = CancelMessage("sess", CancelReason.USER_BARGE_IN, 0)

        await handler(msg)
        assert called

    @pytest.mark.asyncio
    async def test_wraps_async_cancel_fn(self):
        """Wraps async cancel functions."""
        called = False

        async def cancel_fn():
            nonlocal called
            called = True

        handler = create_cancel_handler("test", cancel_fn)
        msg = CancelMessage("sess", CancelReason.USER_BARGE_IN, 0)

        await handler(msg)
        assert called

    @pytest.mark.asyncio
    async def test_handles_cancel_fn_error(self):
        """Doesn't raise if cancel function errors."""
        def cancel_fn():
            raise RuntimeError("Cancel error")

        handler = create_cancel_handler("test", cancel_fn)
        msg = CancelMessage("sess", CancelReason.USER_BARGE_IN, 0)

        # Should not raise
        await handler(msg)
