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
        from src.audio.transport.audio_clock import get_audio_clock

        metrics = SessionMetrics()
        metrics.start_time_ms = get_audio_clock().get_absolute_ms()  # Use current time
        # With 0 turns and just started, should be in warmup
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


class TestSessionEventHandlers:
    """Tests for session event handler methods."""

    @pytest.fixture
    async def session(self):
        """Create started session."""
        session = Session(
            session_id="event-test",
            config=SessionConfig(enable_metrics=False),
        )
        await session.start()
        yield session
        await session.stop()

    @pytest.mark.asyncio
    async def test_on_speech_start_not_running(self):
        """on_speech_start does nothing if not running."""
        session = Session(session_id="not-running")
        # Should not raise
        await session.on_speech_start()
        assert session.state == SessionState.IDLE

    @pytest.mark.asyncio
    async def test_on_endpoint_detected_not_running(self):
        """on_endpoint_detected does nothing if not running."""
        session = Session(session_id="not-running")
        # Should not raise
        await session.on_endpoint_detected(1000)
        assert session._current_turn_id == 0

    @pytest.mark.asyncio
    async def test_on_first_audio_byte_no_turn(self):
        """on_first_audio_byte does nothing without turn start."""
        session = Session(session_id="no-turn")
        # turn_start_ms is 0
        await session.on_first_audio_byte(1000)
        # Should not crash

    @pytest.mark.asyncio
    async def test_on_response_ready_not_running(self):
        """on_response_ready does nothing if not running."""
        session = Session(session_id="not-running")
        await session.on_response_ready()
        assert session.state == SessionState.IDLE

    @pytest.mark.asyncio
    async def test_on_response_complete_not_running(self):
        """on_response_complete does nothing if not running."""
        session = Session(session_id="not-running")
        await session.on_response_complete()
        assert session.state == SessionState.IDLE

    @pytest.mark.asyncio
    async def test_on_barge_in_not_running(self):
        """on_barge_in does nothing if not running."""
        session = Session(session_id="not-running")
        await session.on_barge_in()
        assert session._metrics.barge_ins == 0


class TestSessionContextMethods:
    """Tests for context window methods."""

    @pytest.fixture
    async def session(self):
        """Create started session with context."""
        session = Session(
            session_id="context-test",
            config=SessionConfig(enable_metrics=False),
        )
        await session.start()
        yield session
        await session.stop()

    @pytest.mark.asyncio
    async def test_add_user_message(self, session):
        """add_user_message adds to context."""
        session.add_user_message("Hello")
        # Context should have the message
        messages = await session.get_context_messages()
        # At least system + user message
        assert len(messages) >= 1

    @pytest.mark.asyncio
    async def test_add_assistant_message(self, session):
        """add_assistant_message adds to context."""
        session.add_user_message("Hello")
        session.add_assistant_message("Hi there!")
        messages = await session.get_context_messages()
        assert len(messages) >= 2

    @pytest.mark.asyncio
    async def test_get_context_messages_without_context(self):
        """get_context_messages returns empty without context."""
        session = Session(session_id="no-context")
        # Not started, so no context
        messages = await session.get_context_messages()
        assert messages == []

    def test_add_user_message_without_context(self):
        """add_user_message does nothing without context."""
        session = Session(session_id="no-context")
        # Should not raise
        session.add_user_message("Hello")

    def test_add_assistant_message_without_context(self):
        """add_assistant_message does nothing without context."""
        session = Session(session_id="no-context")
        # Should not raise
        session.add_assistant_message("Hi")


class TestSessionCallbacks:
    """Tests for session callback methods."""

    def test_set_audio_output_callback(self):
        """Set audio output callback."""
        session = Session(session_id="callback-test")

        def callback(audio: bytes):
            pass

        session.set_audio_output_callback(callback)
        assert session._on_audio_output is callback

    def test_set_blendshapes_callback(self):
        """Set blendshapes callback."""
        session = Session(session_id="callback-test")

        def callback(blendshapes: dict):
            pass

        session.set_blendshapes_callback(callback)
        assert session._on_blendshapes is callback


class TestSessionManagerExtended:
    """Extended tests for SessionManager."""

    @pytest.mark.asyncio
    async def test_end_all_sessions(self):
        """end_all_sessions ends all and returns count."""
        manager = SessionManager(max_sessions=5)
        await manager.create_session(session_id="s1")
        await manager.create_session(session_id="s2")
        await manager.create_session(session_id="s3")

        assert manager.active_count == 3

        count = await manager.end_all_sessions()

        assert count == 3
        assert manager.active_count == 0

    @pytest.mark.asyncio
    async def test_end_all_sessions_empty(self):
        """end_all_sessions with no sessions returns 0."""
        manager = SessionManager(max_sessions=5)
        count = await manager.end_all_sessions()
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_sessions_by_state(self):
        """get_sessions_by_state filters correctly."""
        manager = SessionManager(max_sessions=5)
        s1 = await manager.create_session(session_id="s1")
        s2 = await manager.create_session(session_id="s2")

        # Both should be IDLE initially
        idle_sessions = manager.get_sessions_by_state(SessionState.IDLE)
        assert len(idle_sessions) == 2

        # None should be LISTENING
        listening_sessions = manager.get_sessions_by_state(SessionState.LISTENING)
        assert len(listening_sessions) == 0

        await manager.end_all_sessions()

    @pytest.mark.asyncio
    async def test_create_session_with_custom_config(self):
        """Create session with custom config."""
        manager = SessionManager(max_sessions=5)
        custom_config = SessionConfig(system_prompt="Custom prompt")
        session = await manager.create_session(config=custom_config)

        assert session.config.system_prompt == "Custom prompt"

        await manager.end_session(session.session_id)


class TestSessionMetricsWarmup:
    """Tests for SessionMetrics warmup behavior."""

    def test_is_warmup_after_60_seconds(self):
        """Session exits warmup after 60 seconds."""
        from unittest.mock import patch, MagicMock

        metrics = SessionMetrics(turns_completed=1)  # Less than 3 turns
        metrics.start_time_ms = 0

        # Mock clock to return 61 seconds elapsed
        mock_clock = MagicMock()
        mock_clock.get_absolute_ms.return_value = 61_000

        with patch("src.orchestrator.session.get_audio_clock", return_value=mock_clock):
            assert metrics.is_warmup is False

    def test_is_warmup_before_60_seconds_with_2_turns(self):
        """Session still in warmup before 60s with < 3 turns."""
        from unittest.mock import patch, MagicMock

        metrics = SessionMetrics(turns_completed=2)
        metrics.start_time_ms = 0

        mock_clock = MagicMock()
        mock_clock.get_absolute_ms.return_value = 30_000  # 30 seconds

        with patch("src.orchestrator.session.get_audio_clock", return_value=mock_clock):
            assert metrics.is_warmup is True


class TestSessionContextTokens:
    """Tests for context_tokens property with context."""

    @pytest.mark.asyncio
    async def test_context_tokens_with_context(self):
        """context_tokens returns value from context window."""
        session = Session(
            session_id="tokens-test",
            config=SessionConfig(enable_metrics=False),
        )
        await session.start()

        # Add some messages to increase token count
        session.add_user_message("Hello, this is a test message.")
        session.add_assistant_message("Hi! How can I help you today?")

        # Should have tokens now
        tokens = session.context_tokens
        assert tokens > 0

        await session.stop()


class TestSessionStartWithComponents:
    """Tests for session start with different components."""

    @pytest.mark.asyncio
    async def test_start_registers_tts_cancel_handler(self):
        """Start registers TTS cancel handler."""
        from unittest.mock import MagicMock, AsyncMock

        session = Session(
            session_id="tts-handler-test",
            config=SessionConfig(enable_metrics=False),
        )

        mock_tts = MagicMock()
        mock_tts.cancel = AsyncMock()

        await session.start(tts=mock_tts)

        # Cancel handler should be registered
        assert len(session._cancellation._handlers) >= 1

        await session.stop()

    @pytest.mark.asyncio
    async def test_start_registers_llm_abort_handler(self):
        """Start registers LLM abort handler."""
        from unittest.mock import MagicMock, AsyncMock

        session = Session(
            session_id="llm-handler-test",
            config=SessionConfig(enable_metrics=False),
        )

        mock_llm = MagicMock()
        mock_llm.abort = AsyncMock()

        await session.start(llm=mock_llm)

        # Abort handler should be registered
        assert len(session._cancellation._handlers) >= 1

        await session.stop()

    @pytest.mark.asyncio
    async def test_start_registers_animation_stop_handler(self):
        """Start registers animation stop handler."""
        from unittest.mock import MagicMock, AsyncMock

        session = Session(
            session_id="animation-handler-test",
            config=SessionConfig(enable_metrics=False),
        )

        mock_animation = MagicMock()
        mock_animation.stop = AsyncMock()

        await session.start(animation=mock_animation)

        # Stop handler should be registered
        assert len(session._cancellation._handlers) >= 1

        await session.stop()


class TestSessionConversationFlow:
    """Tests for full conversation flow."""

    @pytest.mark.asyncio
    async def test_full_turn_flow(self):
        """Test a complete turn through the session."""
        session = Session(
            session_id="turn-flow-test",
            config=SessionConfig(enable_metrics=False),
        )
        await session.start()

        # User starts speaking
        await session.on_speech_start()
        assert session.state == SessionState.LISTENING

        # Endpoint detected
        await session.on_endpoint_detected(1000)
        assert session.state == SessionState.THINKING
        assert session._current_turn_id == 1

        # Response ready
        await session.on_response_ready()
        assert session.state == SessionState.SPEAKING

        # Response complete
        await session.on_response_complete()
        assert session.state == SessionState.LISTENING
        assert session._metrics.turns_completed == 1

        await session.stop()

    @pytest.mark.asyncio
    async def test_barge_in_increments_counter(self):
        """Barge-in increments barge_ins counter."""
        session = Session(
            session_id="barge-in-test",
            config=SessionConfig(enable_metrics=False),
        )
        await session.start()

        # Get to speaking state
        await session.on_speech_start()
        await session.on_endpoint_detected(1000)
        await session.on_response_ready()
        assert session.state == SessionState.SPEAKING

        # User barges in
        await session.on_barge_in()
        assert session._metrics.barge_ins == 1

        await session.stop()

    @pytest.mark.asyncio
    async def test_first_audio_byte_records_ttfa(self):
        """First audio byte records TTFA metrics."""
        session = Session(
            session_id="ttfa-test",
            config=SessionConfig(enable_metrics=False),
        )
        await session.start()

        # Start a turn
        await session.on_speech_start()
        await session.on_endpoint_detected(1000)

        # First audio byte arrives
        await session.on_first_audio_byte(1150)

        # TTFA should be recorded
        assert session._metrics.total_ttfa_ms == 150.0
        assert session._metrics.max_ttfa_ms == 150.0

        await session.stop()

    @pytest.mark.asyncio
    async def test_multiple_turns_track_min_ttfa(self):
        """Multiple turns track minimum TTFA."""
        session = Session(
            session_id="min-ttfa-test",
            config=SessionConfig(enable_metrics=False),
        )
        await session.start()

        # First turn with 200ms TTFA
        await session.on_speech_start()
        await session.on_endpoint_detected(1000)
        await session.on_first_audio_byte(1200)
        await session.on_response_ready()
        await session.on_response_complete()

        # Second turn with 100ms TTFA
        await session.on_speech_start()
        await session.on_endpoint_detected(2000)
        await session.on_first_audio_byte(2100)

        # min_ttfa should be 100
        assert session._metrics.min_ttfa_ms == 100.0

        await session.stop()


class TestSessionStopEdgeCases:
    """Tests for session stop edge cases."""

    @pytest.mark.asyncio
    async def test_stop_handles_clock_keyerror(self):
        """Stop handles KeyError from audio clock gracefully."""
        from unittest.mock import patch, MagicMock

        session = Session(
            session_id="clock-error-test",
            config=SessionConfig(enable_metrics=False),
        )
        await session.start()

        # Mock clock to raise KeyError on end_session
        mock_clock = MagicMock()
        mock_clock.end_session.side_effect = KeyError("session not found")
        mock_clock.get_absolute_ms.return_value = 10000

        with patch("src.orchestrator.session.get_audio_clock", return_value=mock_clock):
            # Should not raise
            await session.stop()

        assert session.is_running is False
