"""Tests for Context Rollover.

Tests the context window management with rollover support.
Reference: TMF v3.0 §3.2
"""

import pytest

from src.orchestrator.context_rollover import (
    Message,
    ContextWindow,
    create_context_window,
)
from src.config.constants import TMF


class TestMessage:
    """Tests for Message dataclass."""

    def test_basic_message(self):
        """Create basic message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.token_count == 0
        assert msg.is_pinned is False
        assert msg.metadata == {}

    def test_message_with_all_fields(self):
        """Create message with all fields."""
        msg = Message(
            role="assistant",
            content="Hi there",
            token_count=5,
            is_pinned=True,
            metadata={"key": "value"},
        )
        assert msg.role == "assistant"
        assert msg.content == "Hi there"
        assert msg.token_count == 5
        assert msg.is_pinned is True
        assert msg.metadata == {"key": "value"}


class TestContextWindow:
    """Tests for ContextWindow."""

    def test_init_with_system_prompt(self):
        """Initializes with system prompt pinned."""
        context = ContextWindow(system_prompt="You are helpful.")

        assert context.message_count == 1
        assert len(context._pinned_messages) == 1
        assert context._pinned_messages[0].role == "system"
        assert context._pinned_messages[0].content == "You are helpful."
        assert context._pinned_messages[0].is_pinned is True

    def test_token_estimation(self):
        """Token estimation works correctly."""
        context = ContextWindow(system_prompt="Test")

        # ~4 chars per token
        assert context._estimate_tokens("Hello world!") == 3  # 12 chars / 4
        assert context._estimate_tokens("A") >= 1  # Minimum 1 token
        assert context._estimate_tokens("") >= 1  # Edge case

    def test_add_user_message(self):
        """Can add user messages."""
        context = ContextWindow(system_prompt="System")
        initial_tokens = context.total_tokens

        msg = context.add_user_message("Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.is_pinned is False
        assert context.message_count == 2
        assert context.total_tokens > initial_tokens

    def test_add_assistant_message(self):
        """Can add assistant messages."""
        context = ContextWindow(system_prompt="System")
        initial_tokens = context.total_tokens

        msg = context.add_assistant_message("Hi there!")

        assert msg.role == "assistant"
        assert msg.content == "Hi there!"
        assert msg.is_pinned is False
        assert context.message_count == 2
        assert context.total_tokens > initial_tokens

    def test_add_pinned_message(self):
        """Can add additional pinned messages."""
        context = ContextWindow(system_prompt="System")

        msg = context.add_pinned_message("user", "Important context")

        assert msg.is_pinned is True
        assert len(context._pinned_messages) == 2

    def test_add_message_with_metadata(self):
        """Messages can have metadata."""
        context = ContextWindow(system_prompt="System")

        msg = context.add_user_message("Hello", metadata={"timestamp": 12345})

        assert msg.metadata == {"timestamp": 12345}

    def test_turn_count(self):
        """Turn count tracks user messages."""
        context = ContextWindow(system_prompt="System")

        assert context.turn_count == 0

        context.add_user_message("Hello")
        assert context.turn_count == 1

        context.add_assistant_message("Hi")
        assert context.turn_count == 1  # Only counts user messages

        context.add_user_message("How are you?")
        assert context.turn_count == 2

    def test_available_tokens(self):
        """Available tokens calculated correctly."""
        context = ContextWindow(
            system_prompt="Short",
            max_tokens=1000,
        )

        available = context.available_tokens
        assert available > 0
        assert available < 1000  # System prompt uses some

        # Adding messages decreases available
        context.add_user_message("Hello")
        assert context.available_tokens < available

    def test_needs_rollover_threshold(self):
        """Rollover triggered at threshold."""
        context = ContextWindow(
            system_prompt="X",
            max_tokens=100,
            rollover_threshold=50,  # Trigger at 50 tokens
        )

        assert not context.needs_rollover

        # Add enough content to exceed threshold
        for i in range(20):
            context.add_user_message("This is a message with some content " * 3)
            if context.needs_rollover:
                break

        assert context.needs_rollover

    @pytest.mark.asyncio
    async def test_get_messages_basic(self):
        """Get messages returns correct format."""
        context = ContextWindow(system_prompt="You are helpful.")

        context.add_user_message("Hello")
        context.add_assistant_message("Hi!")

        messages = await context.get_messages()

        assert len(messages) == 3
        assert messages[0] == {"role": "system", "content": "You are helpful."}
        assert messages[1] == {"role": "user", "content": "Hello"}
        assert messages[2] == {"role": "assistant", "content": "Hi!"}

    @pytest.mark.asyncio
    async def test_get_messages_order(self):
        """Messages are in correct order."""
        context = ContextWindow(system_prompt="System")

        context.add_user_message("First")
        context.add_assistant_message("Response 1")
        context.add_user_message("Second")
        context.add_assistant_message("Response 2")

        messages = await context.get_messages()

        assert len(messages) == 5
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "First"
        assert messages[2]["content"] == "Response 1"
        assert messages[3]["content"] == "Second"
        assert messages[4]["content"] == "Response 2"

    def test_clear(self):
        """Clear removes non-pinned messages."""
        context = ContextWindow(system_prompt="System")

        context.add_user_message("Hello")
        context.add_assistant_message("Hi")
        context.add_user_message("Bye")

        assert context.message_count == 4

        context.clear()

        assert context.message_count == 1  # Only system prompt
        assert len(context._rolling_messages) == 0
        assert context._summary_state == ""

    def test_clear_preserves_pinned(self):
        """Clear preserves pinned messages."""
        context = ContextWindow(system_prompt="System")

        context.add_pinned_message("user", "Important")
        context.add_user_message("Regular")

        context.clear()

        assert len(context._pinned_messages) == 2
        assert len(context._rolling_messages) == 0

    @pytest.mark.asyncio
    async def test_rollover_with_no_llm(self):
        """Rollover works without LLM (fallback summarization)."""
        context = ContextWindow(
            system_prompt="X",
            llm_client=None,
            max_tokens=200,
            rollover_threshold=100,
        )

        # Add enough messages to trigger rollover
        for i in range(10):
            context.add_user_message(f"User message number {i} with some content")
            context.add_assistant_message(f"Response number {i} from assistant")

        # Trigger rollover via get_messages
        if context.needs_rollover:
            await context.get_messages()

        # Summary state should be populated
        assert context._summary_state != "" or len(context._rolling_messages) < 20

    @pytest.mark.asyncio
    async def test_rollover_keeps_recent_messages(self):
        """Rollover keeps recent messages."""
        context = ContextWindow(
            system_prompt="X",
            llm_client=None,
            max_tokens=200,
            rollover_threshold=20,  # Very low threshold to trigger rollover
        )

        # Add messages with longer content to exceed threshold
        for i in range(8):
            context.add_user_message(f"This is a longer message number {i} with more content")
            context.add_assistant_message(f"This is a longer response number {i} with more content")

        original_count = len(context._rolling_messages)

        # Ensure rollover is triggered
        assert context.needs_rollover, f"Expected rollover, total_tokens={context.total_tokens}"
        await context._perform_rollover()

        # Should have fewer messages after rollover
        assert len(context._rolling_messages) < original_count


class TestCreateContextWindow:
    """Tests for factory function."""

    def test_creates_context(self):
        """Factory creates context window."""
        context = create_context_window(system_prompt="Hello")
        assert isinstance(context, ContextWindow)
        assert context.system_prompt == "Hello"

    def test_accepts_kwargs(self):
        """Factory accepts additional kwargs."""
        context = create_context_window(
            system_prompt="Hello",
            max_tokens=4096,
            rollover_threshold=3500,
        )
        assert context.max_tokens == 4096
        assert context.rollover_threshold == 3500

    def test_defaults_to_tmf_constants(self):
        """Defaults use TMF constants."""
        context = create_context_window(system_prompt="Hello")
        assert context.max_tokens == TMF.LLM_MAX_CONTEXT_TOKENS
        assert context.rollover_threshold == TMF.CONTEXT_ROLLOVER_THRESHOLD


class TestContextWindowIntegration:
    """Integration tests for context window."""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Full conversation with messages and retrieval."""
        context = create_context_window(
            system_prompt="You are a helpful assistant.",
        )

        # Simulate conversation
        context.add_user_message("What's the weather?")
        context.add_assistant_message("I don't have access to weather data.")
        context.add_user_message("Tell me a joke.")
        context.add_assistant_message("Why did the chicken cross the road?")
        context.add_user_message("Why?")
        context.add_assistant_message("To get to the other side!")

        messages = await context.get_messages()

        assert len(messages) == 7  # 1 system + 6 conversation
        assert messages[0]["role"] == "system"
        assert context.turn_count == 3

    @pytest.mark.asyncio
    async def test_pinned_plus_rolling(self):
        """Pinned and rolling messages work together."""
        context = create_context_window(
            system_prompt="Base system prompt.",
        )

        context.add_pinned_message("system", "Additional context.")
        context.add_user_message("Hello")
        context.add_assistant_message("Hi!")

        messages = await context.get_messages()

        # Pinned messages come first
        assert messages[0]["content"] == "Base system prompt."
        assert messages[1]["content"] == "Additional context."
        # Then rolling
        assert messages[2]["content"] == "Hello"
        assert messages[3]["content"] == "Hi!"
