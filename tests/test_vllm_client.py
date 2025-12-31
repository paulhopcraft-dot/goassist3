"""Tests for VLLMClient.

Tests the vLLM client configuration and helper functions.
Note: Tests that require an actual vLLM server are marked with requires_vllm.
"""

import pytest

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

        with pytest.raises(RuntimeError, match="Client not started"):
            await client.generate([{"role": "user", "content": "Hello"}])

    @pytest.mark.asyncio
    async def test_generate_stream_requires_start(self):
        """Generate stream fails if client not started."""
        client = VLLMClient(LLMConfig())

        with pytest.raises(RuntimeError, match="Client not started"):
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
