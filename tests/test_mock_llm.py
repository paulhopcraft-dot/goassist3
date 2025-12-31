"""Tests for MockLLMClient.

Verifies the mock LLM backend works correctly for offline testing.
"""

import pytest

from src.llm.mock_client import (
    MockLLMClient,
    MockLLMConfig,
    create_mock_llm_client,
    CANNED_RESPONSES,
    PATTERN_RESPONSES,
)
from src.llm.vllm_client import LLMResponse


class TestMockLLMConfig:
    """Tests for MockLLMConfig."""

    def test_default_config(self):
        """Default config has reasonable values."""
        config = MockLLMConfig()
        assert config.delay_ms == 50
        assert config.tokens_per_response == 20
        assert config.stream is True

    def test_custom_config(self):
        """Custom config values are applied."""
        config = MockLLMConfig(delay_ms=10, tokens_per_response=5, stream=False)
        assert config.delay_ms == 10
        assert config.tokens_per_response == 5
        assert config.stream is False


class TestMockLLMClient:
    """Tests for MockLLMClient."""

    @pytest.fixture
    def client(self):
        """Create a mock client."""
        return MockLLMClient(MockLLMConfig(delay_ms=1))  # Fast for tests

    @pytest.mark.asyncio
    async def test_start_stop(self, client):
        """Client can start and stop."""
        assert not client.is_running

        await client.start()
        assert client.is_running

        await client.stop()
        assert not client.is_running

    @pytest.mark.asyncio
    async def test_generate_requires_start(self, client):
        """Generate fails if client not started."""
        with pytest.raises(RuntimeError, match="Client not started"):
            async for _ in client.generate_stream([]):
                pass

    @pytest.mark.asyncio
    async def test_generate_stream_returns_tokens(self, client):
        """Streaming generation returns tokens."""
        await client.start()

        messages = [{"role": "user", "content": "Hello"}]
        tokens = []
        async for token in client.generate_stream(messages):
            tokens.append(token)

        assert len(tokens) > 0
        text = "".join(tokens)
        assert len(text) > 0

        await client.stop()

    @pytest.mark.asyncio
    async def test_generate_returns_response(self, client):
        """Non-streaming generation returns LLMResponse."""
        await client.start()

        messages = [{"role": "user", "content": "Hello"}]
        response = await client.generate(messages)

        assert isinstance(response, LLMResponse)
        assert len(response.text) > 0
        assert response.is_complete is True

        await client.stop()

    @pytest.mark.asyncio
    async def test_pattern_matching_hello(self, client):
        """Recognizes hello pattern."""
        await client.start()

        messages = [{"role": "user", "content": "Hello there!"}]
        response = await client.generate(messages)

        assert "GoAssist" in response.text or "Hello" in response.text

        await client.stop()

    @pytest.mark.asyncio
    async def test_pattern_matching_name(self, client):
        """Recognizes name pattern."""
        await client.start()

        messages = [{"role": "user", "content": "What is your name?"}]
        response = await client.generate(messages)

        assert "GoAssist" in response.text

        await client.stop()

    @pytest.mark.asyncio
    async def test_pattern_matching_help(self, client):
        """Recognizes help pattern."""
        await client.start()

        messages = [{"role": "user", "content": "I need help"}]
        response = await client.generate(messages)

        assert "help" in response.text.lower()

        await client.stop()

    @pytest.mark.asyncio
    async def test_pattern_matching_bye(self, client):
        """Recognizes bye pattern."""
        await client.start()

        messages = [{"role": "user", "content": "Goodbye!"}]
        response = await client.generate(messages)

        assert "bye" in response.text.lower() or "great day" in response.text.lower()

        await client.stop()

    @pytest.mark.asyncio
    async def test_fallback_to_canned_response(self, client):
        """Falls back to canned response for unknown input."""
        await client.start()

        messages = [{"role": "user", "content": "xyzzy plugh"}]
        response = await client.generate(messages)

        # Should be one of the canned responses
        assert response.text in CANNED_RESPONSES

        await client.stop()

    @pytest.mark.asyncio
    async def test_abort_stops_generation(self, client):
        """Abort stops ongoing generation."""
        await client.start()

        messages = [{"role": "user", "content": "Tell me a long story"}]

        tokens = []
        async for token in client.generate_stream(messages):
            tokens.append(token)
            if len(tokens) > 5:
                await client.abort()
                break

        # Should have stopped before getting full response
        text = "".join(tokens)
        assert len(text) < 100  # Truncated

        await client.stop()

    @pytest.mark.asyncio
    async def test_empty_messages(self, client):
        """Handles empty message list."""
        await client.start()

        response = await client.generate([])
        assert response.text in CANNED_RESPONSES

        await client.stop()

    @pytest.mark.asyncio
    async def test_multiple_generations(self, client):
        """Can generate multiple responses."""
        await client.start()

        for i in range(3):
            messages = [{"role": "user", "content": f"Message {i}"}]
            response = await client.generate(messages)
            assert len(response.text) > 0

        await client.stop()


class TestCreateMockLLMClient:
    """Tests for factory function."""

    @pytest.mark.asyncio
    async def test_creates_started_client(self):
        """Factory returns started client."""
        client = await create_mock_llm_client()
        assert client.is_running
        await client.stop()

    @pytest.mark.asyncio
    async def test_accepts_config_kwargs(self):
        """Factory accepts config kwargs."""
        client = await create_mock_llm_client(delay_ms=5)
        assert client.is_running
        assert client._config.delay_ms == 5
        await client.stop()


class TestLLMFactory:
    """Tests for LLM factory function."""

    @pytest.mark.asyncio
    async def test_create_mock_client(self):
        """Factory creates mock client when engine=mock."""
        from src.llm import create_llm_client, MockLLMClient

        client = await create_llm_client(engine="mock")
        assert isinstance(client, MockLLMClient)
        assert client.is_running
        await client.stop()

    @pytest.mark.asyncio
    async def test_create_vllm_client(self):
        """Factory creates vLLM client when engine=vllm."""
        from src.llm import create_llm_client, VLLMClient

        client = await create_llm_client(engine="vllm")
        assert isinstance(client, VLLMClient)
        assert client.is_running
        await client.stop()
