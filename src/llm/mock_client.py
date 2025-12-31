"""Mock LLM Client - For testing without external LLM service.

Provides canned responses for testing the full pipeline
without requiring vLLM or cloud LLM services.

Usage:
    Set LLM_ENGINE=mock in .env to use this client.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import AsyncIterator

from src.llm.vllm_client import LLMConfig, LLMResponse


# Canned responses for different types of queries
CANNED_RESPONSES = [
    "I understand. Let me help you with that.",
    "That's a great question! Here's what I think...",
    "Thanks for sharing. I'd be happy to assist.",
    "Interesting point! Let me elaborate on that.",
    "I see what you mean. Here's my perspective.",
    "Good question! The answer is quite straightforward.",
    "I appreciate you asking. Here's what I know about that.",
    "That's something I can definitely help with.",
]

# More detailed responses for specific patterns
PATTERN_RESPONSES = {
    "hello": "Hello! I'm GoAssist, your voice assistant. How can I help you today?",
    "hi": "Hi there! What can I do for you?",
    "help": "I'm here to help! You can ask me questions, have a conversation, or just chat. What would you like to talk about?",
    "name": "I'm GoAssist, a speech-to-speech conversational agent. Nice to meet you!",
    "how are you": "I'm doing great, thanks for asking! I'm ready to help you with whatever you need.",
    "bye": "Goodbye! It was nice chatting with you. Have a great day!",
    "thanks": "You're welcome! Is there anything else I can help you with?",
    "thank you": "You're very welcome! Feel free to ask if you need anything else.",
}


@dataclass
class MockLLMConfig:
    """Configuration for mock LLM client."""

    delay_ms: int = 50  # Simulated latency per token
    tokens_per_response: int = 20  # Average tokens in response
    stream: bool = True


class MockLLMClient:
    """Mock LLM client for testing.

    Provides the same interface as VLLMClient but returns
    canned responses without requiring an external service.

    Features:
    - Configurable response delay (simulates network latency)
    - Pattern matching for contextual responses
    - Streaming support with token-by-token output
    - Abort support for barge-in testing

    Usage:
        client = MockLLMClient()
        await client.start()

        async for token in client.generate_stream(messages):
            print(token, end="")

        await client.stop()
    """

    def __init__(self, config: MockLLMConfig | None = None) -> None:
        self._config = config or MockLLMConfig()
        self._abort_event: asyncio.Event = asyncio.Event()
        self._running: bool = False

    async def start(self) -> None:
        """Initialize mock client."""
        self._running = True
        self._abort_event.clear()

    async def stop(self) -> None:
        """Stop mock client."""
        await self.abort()
        self._running = False

    def _get_response(self, messages: list[dict[str, str]]) -> str:
        """Get appropriate response based on input.

        Checks for pattern matches first, then falls back to random canned response.
        """
        if not messages:
            return random.choice(CANNED_RESPONSES)

        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "").lower()
                break

        # Check for pattern matches
        for pattern, response in PATTERN_RESPONSES.items():
            if pattern in user_message:
                return response

        # Fall back to random canned response
        return random.choice(CANNED_RESPONSES)

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate streaming response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Ignored (for API compatibility)

        Yields:
            Token strings with simulated delay
        """
        if not self._running:
            raise RuntimeError("Client not started")

        self._abort_event.clear()

        response = self._get_response(messages)
        words = response.split()

        for i, word in enumerate(words):
            # Check for abort
            if self._abort_event.is_set():
                break

            # Add space before word (except first)
            if i > 0:
                yield " "

            # Yield word character by character for more realistic streaming
            for char in word:
                if self._abort_event.is_set():
                    break
                yield char
                # Small delay between characters
                await asyncio.sleep(self._config.delay_ms / 1000 / len(word))

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> LLMResponse:
        """Generate complete response (non-streaming).

        Args:
            messages: List of message dicts
            **kwargs: Ignored (for API compatibility)

        Returns:
            LLMResponse with complete text
        """
        if not self._running:
            raise RuntimeError("Client not started")

        text_parts: list[str] = []

        async for token in self.generate_stream(messages, **kwargs):
            text_parts.append(token)

        return LLMResponse(
            text="".join(text_parts),
            is_complete=True,
        )

    async def abort(self) -> None:
        """Abort current generation immediately.

        Called on barge-in to stop generation.
        """
        self._abort_event.set()

    @property
    def is_running(self) -> bool:
        """Whether client is ready for generation."""
        return self._running


async def create_mock_llm_client(**kwargs) -> MockLLMClient:
    """Factory function to create and start mock LLM client.

    Args:
        **kwargs: Configuration options

    Returns:
        Started MockLLMClient instance
    """
    config = MockLLMConfig(**kwargs) if kwargs else None
    client = MockLLMClient(config)
    await client.start()
    return client
