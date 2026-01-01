"""Tests for VLLMClient.

Tests the vLLM client configuration and helper functions.
Note: Tests that require an actual vLLM server are marked with requires_vllm.
"""

import pytest

from src.exceptions import LLMGenerationError
from src.llm.vllm_client import (
    LLMConfig,
    LLMResponse,
    VLLMClient,
    build_messages,
    create_vllm_client,
)


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_default_config(self):
        """Default config has sensible values."""
        config = LLMConfig()
        assert config.base_url == "http://localhost:8000/v1"
        assert config.model == "mistral-7b-awq"
        assert config.max_tokens == 512
        assert config.temperature == 0.7
        assert config.top_p == 0.95
        assert config.timeout_s == 30.0
        assert config.stream is True

    def test_custom_config(self):
        """Custom config values are applied."""
        config = LLMConfig(
            base_url="http://example.com/v1",
            model="gpt-4",
            max_tokens=1024,
            temperature=0.5,
            top_p=0.9,
            timeout_s=60.0,
            stream=False,
        )
        assert config.base_url == "http://example.com/v1"
        assert config.model == "gpt-4"
        assert config.max_tokens == 1024
        assert config.temperature == 0.5
        assert config.top_p == 0.9
        assert config.timeout_s == 60.0
        assert config.stream is False


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_default_response(self):
        """Default response with just text."""
        response = LLMResponse(text="Hello world")
        assert response.text == "Hello world"
        assert response.finish_reason is None
        assert response.tokens_used == 0
        assert response.is_complete is False

    def test_complete_response(self):
        """Response with all fields."""
        response = LLMResponse(
            text="Hello world",
            finish_reason="stop",
            tokens_used=5,
            is_complete=True,
        )
        assert response.text == "Hello world"
        assert response.finish_reason == "stop"
        assert response.tokens_used == 5
        assert response.is_complete is True


class TestBuildMessages:
    """Tests for build_messages helper function."""

    def test_basic_message(self):
        """Builds messages with system prompt and user input."""
        messages = build_messages(
            system_prompt="You are helpful.",
            conversation=[],
            user_input="Hello",
        )

        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": "You are helpful."}
        assert messages[1] == {"role": "user", "content": "Hello"}

    def test_with_conversation_history(self):
        """Includes conversation history."""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]

        messages = build_messages(
            system_prompt="You are helpful.",
            conversation=history,
            user_input="How are you?",
        )

        assert len(messages) == 4
        assert messages[0] == {"role": "system", "content": "You are helpful."}
        assert messages[1] == {"role": "user", "content": "Hi"}
        assert messages[2] == {"role": "assistant", "content": "Hello!"}
        assert messages[3] == {"role": "user", "content": "How are you?"}

    def test_empty_system_prompt(self):
        """Handles empty system prompt."""
        messages = build_messages(
            system_prompt="",
            conversation=[],
            user_input="Hello",
        )

        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": ""}
        assert messages[1] == {"role": "user", "content": "Hello"}

    def test_long_conversation(self):
        """Handles long conversation history."""
        history = [
            {"role": "user", "content": f"Message {i}"}
            if i % 2 == 0
            else {"role": "assistant", "content": f"Response {i}"}
            for i in range(10)
        ]

        messages = build_messages(
            system_prompt="System",
            conversation=history,
            user_input="Final",
        )

        assert len(messages) == 12  # 1 system + 10 history + 1 user


class TestVLLMClient:
    """Tests for VLLMClient that don't require a server."""

    def test_init_with_config(self):
        """Client initializes with custom config."""
        config = LLMConfig(base_url="http://test:8000/v1", model="test-model")
        client = VLLMClient(config)

        assert client._config.base_url == "http://test:8000/v1"
        assert client._config.model == "test-model"
        assert not client.is_running

    def test_init_default_config(self):
        """Client initializes with default config from settings."""
        client = VLLMClient()
        assert client._config is not None
        assert not client.is_running

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Start sets is_running to True."""
        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        await client.start()
        assert client.is_running
        assert client._client is not None

        await client.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Stop sets is_running to False."""
        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        await client.start()
        await client.stop()

        assert not client.is_running
        assert client._client is None

    @pytest.mark.asyncio
    async def test_generate_requires_start(self):
        """Generate fails if client not started."""
        client = VLLMClient(LLMConfig())

        with pytest.raises(LLMGenerationError, match="Client not started"):
            await client.generate([{"role": "user", "content": "Hello"}])

    @pytest.mark.asyncio
    async def test_generate_stream_requires_start(self):
        """Generate stream fails if client not started."""
        client = VLLMClient(LLMConfig())

        with pytest.raises(LLMGenerationError, match="Client not started"):
            async for _ in client.generate_stream([{"role": "user", "content": "Hello"}]):
                pass

    @pytest.mark.asyncio
    async def test_abort_sets_event(self):
        """Abort sets the abort event."""
        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        await client.start()
        assert not client._abort_event.is_set()

        await client.abort()
        assert client._abort_event.is_set()

        await client.stop()

    @pytest.mark.asyncio
    async def test_start_clears_abort_event(self):
        """Start clears any previous abort event."""
        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        await client.start()
        await client.abort()
        assert client._abort_event.is_set()

        # Restart should clear abort
        await client.stop()
        await client.start()
        assert not client._abort_event.is_set()

        await client.stop()


class TestCreateVLLMClient:
    """Tests for factory function."""

    @pytest.mark.asyncio
    async def test_creates_started_client(self):
        """Factory returns started client."""
        client = await create_vllm_client(base_url="http://localhost:8000/v1")
        assert client.is_running
        await client.stop()

    @pytest.mark.asyncio
    async def test_accepts_config_kwargs(self):
        """Factory accepts config kwargs."""
        client = await create_vllm_client(
            base_url="http://test:8000/v1",
            model="test-model",
            max_tokens=256,
        )
        assert client._config.base_url == "http://test:8000/v1"
        assert client._config.model == "test-model"
        assert client._config.max_tokens == 256
        await client.stop()


class TestVLLMClientStreaming:
    """Tests for streaming generation with mocked OpenAI client."""

    @pytest.mark.asyncio
    async def test_generate_stream_with_mock_client(self):
        """Test streaming with mocked OpenAI client."""
        from unittest.mock import AsyncMock, MagicMock, patch

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        # Create mock chunk response
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello"

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = " world"

        mock_chunk3 = MagicMock()
        mock_chunk3.choices = [MagicMock()]
        mock_chunk3.choices[0].delta.content = None  # End chunk

        async def mock_chunks():
            yield mock_chunk1
            yield mock_chunk2
            yield mock_chunk3

        with patch.object(client, "_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_chunks())
            client._running = True

            tokens = []
            async for token in client.generate_stream([{"role": "user", "content": "Hi"}]):
                tokens.append(token)

            assert tokens == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_generate_stream_aborts_on_event(self):
        """Test streaming aborts when abort event is set."""
        from unittest.mock import AsyncMock, MagicMock, patch

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Token"

        async def mock_chunks():
            yield mock_chunk
            client._abort_event.set()  # Set abort during streaming
            yield mock_chunk

        with patch.object(client, "_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_chunks())
            client._running = True

            tokens = []
            async for token in client.generate_stream([{"role": "user", "content": "Hi"}]):
                tokens.append(token)

            # Should have stopped early
            assert len(tokens) == 1

    @pytest.mark.asyncio
    async def test_generate_stream_handles_empty_choices(self):
        """Test streaming handles empty choices."""
        from unittest.mock import AsyncMock, MagicMock, patch

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        mock_chunk = MagicMock()
        mock_chunk.choices = []  # Empty choices

        async def mock_chunks():
            yield mock_chunk

        with patch.object(client, "_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_chunks())
            client._running = True

            tokens = []
            async for token in client.generate_stream([{"role": "user", "content": "Hi"}]):
                tokens.append(token)

            assert tokens == []


class TestVLLMClientGenerate:
    """Tests for non-streaming generate."""

    @pytest.mark.asyncio
    async def test_generate_collects_tokens(self):
        """Test generate collects all tokens into response."""
        from unittest.mock import AsyncMock, MagicMock, patch

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello"

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = " world"

        async def mock_chunks():
            yield mock_chunk1
            yield mock_chunk2

        with patch.object(client, "_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_chunks())
            client._running = True

            response = await client.generate([{"role": "user", "content": "Hi"}])

            assert response.text == "Hello world"
            assert response.is_complete is True


class TestVLLMClientAbort:
    """Tests for abort functionality."""

    @pytest.mark.asyncio
    async def test_abort_cancels_current_task(self):
        """Test abort cancels current task if present."""
        import asyncio

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)
        await client.start()

        # Create a task
        async def long_task():
            await asyncio.sleep(100)

        client._current_task = asyncio.create_task(long_task())

        await client.abort()

        assert client._abort_event.is_set()
        # Task should be cancelled
        assert client._current_task.cancelled() or client._current_task.done()

        await client.stop()

    @pytest.mark.asyncio
    async def test_abort_handles_no_task(self):
        """Test abort handles case with no current task."""
        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)
        await client.start()

        # No current task
        client._current_task = None

        # Should not raise
        await client.abort()

        assert client._abort_event.is_set()

        await client.stop()

    @pytest.mark.asyncio
    async def test_abort_handles_completed_task(self):
        """Test abort handles completed task."""
        import asyncio

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)
        await client.start()

        # Create and complete a task
        async def quick_task():
            return "done"

        client._current_task = asyncio.create_task(quick_task())
        await asyncio.sleep(0.01)  # Let it complete

        # Should not raise
        await client.abort()

        await client.stop()


class TestVLLMClientErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_generate_stream_raises_on_error(self):
        """Test streaming raises on API error."""
        from unittest.mock import AsyncMock, patch

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        with patch.object(client, "_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(
                side_effect=Exception("API error")
            )
            client._running = True

            with pytest.raises(LLMGenerationError, match="API error"):
                async for _ in client.generate_stream([{"role": "user", "content": "Hi"}]):
                    pass

    @pytest.mark.asyncio
    async def test_generate_stream_cancelled_error_propagates(self):
        """Test CancelledError is properly propagated."""
        from unittest.mock import AsyncMock, patch
        import asyncio

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        with patch.object(client, "_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(
                side_effect=asyncio.CancelledError()
            )
            client._running = True

            with pytest.raises(asyncio.CancelledError):
                async for _ in client.generate_stream([{"role": "user", "content": "Hi"}]):
                    pass


class TestVLLMClientKwargs:
    """Tests for generate_stream kwargs handling."""

    @pytest.mark.asyncio
    async def test_generate_stream_uses_kwargs(self):
        """Test generate_stream uses provided kwargs."""
        from unittest.mock import AsyncMock, MagicMock, patch

        config = LLMConfig(base_url="http://localhost:8000/v1")
        client = VLLMClient(config)

        async def mock_chunks():
            return
            yield  # Empty generator

        with patch.object(client, "_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_chunks())
            client._running = True

            async for _ in client.generate_stream(
                [{"role": "user", "content": "Hi"}],
                max_tokens=100,
                temperature=0.5,
                top_p=0.8,
            ):
                pass

            # Verify kwargs were passed
            call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
            assert call_kwargs["max_tokens"] == 100
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["top_p"] == 0.8
