"""Tests for Session Container.

Tests cover:
- SessionConfig defaults and customization
- SessionMetrics calculations
- Session lifecycle (start/stop)
- Session properties
- Conversation history management
- SessionManager operations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestrator.session import (
    Session,
    SessionConfig,
    SessionMetrics,
    SessionManager,
)
from src.orchestrator.state_machine import SessionState


class TestSessionConfig:
    """Tests for SessionConfig dataclass."""

    def test_default_values(self):
        """Default config has sensible values."""
        config = SessionConfig()
        assert config.system_prompt == "You are a helpful voice assistant."
        assert config.max_context_tokens > 0
        assert config.rollover_threshold > 0
        assert config.enable_avatar is True
        assert config.enable_metrics is True

    def test_custom_values(self):
        """Custom config values are applied."""
        config = SessionConfig(
            system_prompt="You are a pirate.",
            max_context_tokens=2000,
            rollover_threshold=1500,
            enable_avatar=False,
            enable_metrics=False,
        )
        assert config.system_prompt == "You are a pirate."
        assert config.max_context_tokens == 2000
        assert config.rollover_threshold == 1500
        assert config.enable_avatar is False
        assert config.enable_metrics is False


class TestSessionMetrics:
    """Tests for SessionMetrics dataclass."""

    def test_default_values(self):
        """Default metrics are zeroed."""
        metrics = SessionMetrics()
        assert metrics.turns_completed == 0
        assert metrics.total_ttfa_ms == 0.0
        assert metrics.min_ttfa_ms == float("inf")
        assert metrics.max_ttfa_ms == 0.0
        assert metrics.barge_ins == 0
        assert metrics.context_rollovers == 0

    def test_avg_ttfa_ms_zero_turns(self):
        """Average TTFA is 0 with no turns."""
        metrics = SessionMetrics()
        assert metrics.avg_ttfa_ms == 0.0

    def test_avg_ttfa_ms_with_turns(self):
        """Average TTFA calculation is correct."""
        metrics = SessionMetrics(
            turns_completed=4,
            total_ttfa_ms=400.0,
        )
        assert metrics.avg_ttfa_ms == 100.0

    def test_is_warmup_initial(self):
        """Session starts in warmup period."""
        metrics = SessionMetrics()
        metrics.start_time_ms = 0
        # With 0 turns, should be in warmup
        assert metrics.is_warmup is True

    def test_is_warmup_after_3_turns(self):
        """Session exits warmup after 3 turns."""
        metrics = SessionMetrics(turns_completed=3)
        metrics.start_time_ms = 0
        assert metrics.is_warmup is False


class TestSession:
    """Tests for Session class."""

    def test_init_generates_session_id(self):
        """Session generates UUID if not provided."""
        session = Session()
        assert session.session_id is not None
        assert len(session.session_id) > 0
        # UUID format check
        assert "-" in session.session_id

    def test_init_uses_provided_session_id(self):
        """Session uses provided session ID."""
        session = Session(session_id="my-custom-id")
        assert session.session_id == "my-custom-id"

    def test_init_uses_default_config(self):
        """Session uses default config if not provided."""
        session = Session()
        assert session.config.system_prompt == "You are a helpful voice assistant."

    def test_init_uses_custom_config(self):
        """Session uses provided config."""
        config = SessionConfig(system_prompt="Custom prompt")
        session = Session(config=config)
        assert session.config.system_prompt == "Custom prompt"

    def test_initial_state_is_idle(self):
        """Session starts in IDLE state."""
        session = Session()
        assert session.state == SessionState.IDLE

    def test_is_running_false_initially(self):
        """Session is not running initially."""
        session = Session()
        assert session.is_running is False

    def test_context_tokens_zero_before_start(self):
        """Context tokens is 0 before start."""
        session = Session()
        assert session.context_tokens == 0

    def test_conversation_history_empty_initially(self):
        """Conversation history is empty initially."""
        session = Session()
        assert session.conversation_history == []


class TestSessionLifecycle:
    """Tests for Session start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Start sets running flag."""
        session = Session(session_id="lifecycle-test")
        await session.start()
        assert session.is_running is True
        await session.stop()

    @pytest.mark.asyncio
    async def test_double_start_is_noop(self):
        """Starting twice is a no-op."""
        session = Session(session_id="double-start")
        await session.start()
        await session.start()  # Should not raise
        assert session.is_running is True
        await session.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Stop clears running flag."""
        session = Session(session_id="stop-test")
        await session.start()
        await session.stop()
        assert session.is_running is False

    @pytest.mark.asyncio
    async def test_double_stop_is_noop(self):
        """Stopping twice is a no-op."""
        session = Session(session_id="double-stop")
        await session.start()
        await session.stop()
        await session.stop()  # Should not raise
        assert session.is_running is False


class TestSessionConversation:
    """Tests for conversation history management."""

    def test_conversation_history_append_user(self):
        """Append user message to history."""
        session = Session()
        session.conversation_history.append({
            "role": "user",
            "content": "Hello",
        })

        assert len(session.conversation_history) == 1
        assert session.conversation_history[0] == {
            "role": "user",
            "content": "Hello",
        }

    def test_conversation_history_append_assistant(self):
        """Append assistant message to history."""
        session = Session()
        session.conversation_history.append({
            "role": "assistant",
            "content": "Hi there!",
        })

        assert len(session.conversation_history) == 1
        assert session.conversation_history[0] == {
            "role": "assistant",
            "content": "Hi there!",
        }

    def test_conversation_order_preserved(self):
        """Conversation messages maintain order."""
        session = Session()
        session.conversation_history.append({"role": "user", "content": "Hello"})
        session.conversation_history.append({"role": "assistant", "content": "Hi!"})
        session.conversation_history.append({"role": "user", "content": "How are you?"})
        session.conversation_history.append({"role": "assistant", "content": "I'm doing well!"})

        assert len(session.conversation_history) == 4
        assert session.conversation_history[0]["role"] == "user"
        assert session.conversation_history[1]["role"] == "assistant"
        assert session.conversation_history[2]["role"] == "user"
        assert session.conversation_history[3]["role"] == "assistant"


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_init_default_max_sessions(self):
        """Manager initializes with default max sessions."""
        manager = SessionManager()
        assert manager.available_slots > 0

    def test_init_custom_max_sessions(self):
        """Manager initializes with custom max sessions."""
        manager = SessionManager(max_sessions=3)
        assert manager.available_slots == 3

    def test_active_count_initially_zero(self):
        """Active count is 0 initially."""
        manager = SessionManager()
        assert manager.active_count == 0

    @pytest.mark.asyncio
    async def test_create_session_returns_session(self):
        """Create session returns a Session instance."""
        manager = SessionManager(max_sessions=5)
        session = await manager.create_session()

        assert session is not None
        assert isinstance(session, Session)
        assert manager.active_count == 1

        await manager.end_session(session.session_id)

    @pytest.mark.asyncio
    async def test_create_session_with_custom_id(self):
        """Create session with custom ID."""
        manager = SessionManager(max_sessions=5)
        session = await manager.create_session(session_id="custom-123")

        assert session.session_id == "custom-123"

        await manager.end_session("custom-123")

    @pytest.mark.asyncio
    async def test_get_session_returns_session(self):
        """Get session returns existing session."""
        manager = SessionManager(max_sessions=5)
        created = await manager.create_session(session_id="get-test")

        retrieved = manager.get_session("get-test")

        assert retrieved is created

        await manager.end_session("get-test")

    @pytest.mark.asyncio
    async def test_get_session_returns_none_for_unknown(self):
        """Get session returns None for unknown ID."""
        manager = SessionManager(max_sessions=5)
        session = manager.get_session("unknown-id")
        assert session is None

    @pytest.mark.asyncio
    async def test_end_session_removes_session(self):
        """End session removes from manager."""
        manager = SessionManager(max_sessions=5)
        await manager.create_session(session_id="end-test")
        assert manager.active_count == 1

        result = await manager.end_session("end-test")

        assert result is True
        assert manager.active_count == 0
        assert manager.get_session("end-test") is None

    @pytest.mark.asyncio
    async def test_end_session_returns_false_for_unknown(self):
        """End session returns False for unknown ID."""
        manager = SessionManager(max_sessions=5)
        result = await manager.end_session("unknown-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_sessions_returns_ids(self):
        """List sessions returns all session IDs."""
        manager = SessionManager(max_sessions=5)
        await manager.create_session(session_id="session-1")
        await manager.create_session(session_id="session-2")

        sessions = manager.list_sessions()

        assert "session-1" in sessions
        assert "session-2" in sessions

        await manager.end_session("session-1")
        await manager.end_session("session-2")

    @pytest.mark.asyncio
    async def test_max_sessions_enforced(self):
        """Max sessions limit is enforced."""
        manager = SessionManager(max_sessions=2)

        s1 = await manager.create_session(session_id="s1")
        s2 = await manager.create_session(session_id="s2")

        assert s1 is not None
        assert s2 is not None
        assert manager.available_slots == 0

        # Third session should fail
        s3 = await manager.create_session(session_id="s3")
        assert s3 is None

        await manager.end_session("s1")
        await manager.end_session("s2")

    @pytest.mark.asyncio
    async def test_slots_freed_after_end(self):
        """Slots are freed after ending a session."""
        manager = SessionManager(max_sessions=2)

        await manager.create_session(session_id="slot-test")
        assert manager.available_slots == 1

        await manager.end_session("slot-test")
        assert manager.available_slots == 2
