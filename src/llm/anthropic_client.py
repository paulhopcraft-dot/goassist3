"""Anthropic Claude Client - Streaming LLM inference with Claude models.

Provides interface to Anthropic's Claude API for:
- Streaming token output
- Fast cancellation (for barge-in)
- High-quality conversation

Reference: TMF v3.0 §3.2, Addendum A §A5
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator

from anthropic import AsyncAnthropic, APIError, APIConnectionError

from src.config.settings import get_settings
from src.exceptions import LLMGenerationError, LLMConnectionError
from src.observability.logging import get_logger
from src.utils.async_timeout import AsyncTimeoutError, timeout_async_iterator

logger = get_logger(__name__)


@dataclass
class AnthropicConfig:
    """Configuration for Anthropic Claude client."""

    api_key: str
    model: str = "claude-sonnet-3-5-20241022"  # Latest Sonnet
    max_tokens: int = 512
    temperature: float = 0.7
    timeout_s: float = 30.0
    stream: bool = True


@dataclass
class LLMResponse:
    """Response from LLM generation."""

    text: str
    finish_reason: str | None = None
    tokens_used: int = 0
    is_complete: bool = False


class AnthropicClient:
    """Anthropic Claude client for streaming LLM inference.

    Features:
    - Streaming token output for low TTFA
    - Fast abort for barge-in support
    - Claude Sonnet/Opus models
    - High-quality conversational AI

    Usage:
        client = AnthropicClient()
        await client.start()

        async for token in client.generate_stream(messages):
            yield token

        # On barge-in
        await client.abort()

        await client.stop()
    """

    def __init__(self, config: AnthropicConfig | None = None) -> None:
        if config is None:
            settings = get_settings()
            api_key = getattr(settings, 'anthropic_api_key', None)
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")

            config = AnthropicConfig(
                api_key=api_key,
                model=getattr(settings, 'anthropic_model', 'claude-sonnet-3-5-20241022'),
            )

        self._config = config
        self._client: AsyncAnthropic | None = None
        self._current_generation: asyncio.Task | None = None
        self._is_running = False

    async def start(self) -> None:
        """Initialize the Anthropic client."""
        if self._is_running:
            logger.warning("Anthropic client already started")
            return

        try:
            self._client = AsyncAnthropic(api_key=self._config.api_key)
            self._is_running = True
            logger.info(
                "Anthropic client started",
                model=self._config.model,
                max_tokens=self._config.max_tokens,
            )
        except Exception as e:
            logger.error("Failed to start Anthropic client", error=str(e))
            raise LLMConnectionError(f"Failed to initialize Anthropic client: {e}")

    async def stop(self) -> None:
        """Stop the Anthropic client."""
        if not self._is_running:
            return

        # Cancel any ongoing generation
        if self._current_generation and not self._current_generation.done():
            self._current_generation.cancel()
            try:
                await self._current_generation
            except asyncio.CancelledError:
                pass

        self._client = None
        self._is_running = False
        logger.info("Anthropic client stopped")

    async def abort(self) -> None:
        """Abort current generation (for barge-in).

        Cancels the streaming request immediately.
        """
        if self._current_generation and not self._current_generation.done():
            logger.info("Aborting Anthropic generation")
            self._current_generation.cancel()
            try:
                await self._current_generation
            except asyncio.CancelledError:
                logger.debug("Generation cancelled successfully")

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Generate streaming response from Claude.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt (passed separately in Anthropic API)

        Yields:
            str: Generated tokens

        Raises:
            LLMGenerationError: If generation fails
            AsyncTimeoutError: If generation times out
        """
        if not self._is_running or self._client is None:
            raise LLMConnectionError("Anthropic client not started")

        # Convert OpenAI-style messages to Anthropic format
        # Anthropic expects alternating user/assistant messages
        anthropic_messages = []
        for msg in messages:
            # Skip system messages (passed separately)
            if msg["role"] == "system":
                if system_prompt is None:
                    system_prompt = msg["content"]
                continue

            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        try:
            logger.debug(
                "Starting Claude generation",
                model=self._config.model,
                message_count=len(anthropic_messages),
                has_system=system_prompt is not None,
            )

            # Create streaming request
            async def _generate():
                async with self._client.messages.stream(
                    model=self._config.model,
                    max_tokens=self._config.max_tokens,
                    temperature=self._config.temperature,
                    messages=anthropic_messages,
                    system=system_prompt or "",
                ) as stream:
                    async for text in stream.text_stream:
                        yield text

            # Wrap in timeout
            async for token in timeout_async_iterator(
                _generate(),
                timeout_s=self._config.timeout_s
            ):
                yield token

            logger.debug("Claude generation complete")

        except asyncio.CancelledError:
            logger.info("Claude generation cancelled (barge-in)")
            raise
        except AsyncTimeoutError:
            logger.error(
                "Claude generation timeout",
                timeout_s=self._config.timeout_s,
            )
            raise LLMGenerationError(
                f"Generation timed out after {self._config.timeout_s}s"
            )
        except APIConnectionError as e:
            logger.error("Claude API connection error", error=str(e))
            raise LLMConnectionError(f"Failed to connect to Anthropic API: {e}")
        except APIError as e:
            logger.error("Claude API error", error=str(e), status_code=e.status_code)
            raise LLMGenerationError(f"Anthropic API error: {e}")
        except Exception as e:
            logger.error("Unexpected error in Claude generation", error=str(e))
            raise LLMGenerationError(f"Unexpected error: {e}")

    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate complete response (non-streaming).

        Args:
            messages: List of message dicts
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with complete text
        """
        full_text = ""
        async for token in self.generate_stream(messages, system_prompt):
            full_text += token

        return LLMResponse(
            text=full_text,
            finish_reason="stop",
            is_complete=True,
        )

    @property
    def is_running(self) -> bool:
        """Check if client is running."""
        return self._is_running

    @property
    def model_name(self) -> str:
        """Get current model name."""
        return self._config.model
