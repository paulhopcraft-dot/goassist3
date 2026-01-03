"""vLLM Client - Streaming LLM inference with fast abort.

Provides interface to vLLM serving runtime for:
- Streaming token output
- Fast cancellation (for barge-in)
- Prefix caching (for conversation efficiency)

Reference: TMF v3.0 §3.2, Addendum A §A5
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

import httpx
from openai import AsyncOpenAI

from src.config.constants import TMF
from src.config.settings import get_settings
from src.exceptions import LLMGenerationError
from src.utils.async_timeout import AsyncTimeoutError, timeout_async_iterator


@dataclass
class LLMConfig:
    """Configuration for vLLM client."""

    base_url: str = "http://localhost:8000/v1"
    model: str = "mistral-7b-awq"
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95
    timeout_s: float = 30.0
    stream: bool = True


@dataclass
class LLMResponse:
    """Response from LLM generation."""

    text: str
    finish_reason: str | None = None
    tokens_used: int = 0
    is_complete: bool = False


class VLLMClient:
    """vLLM client for streaming LLM inference.

    Features:
    - Streaming token output for low TTFA
    - Fast abort for barge-in support
    - OpenAI-compatible API
    - Prefix caching support

    Usage:
        client = VLLMClient()
        await client.start()

        async for token in client.generate_stream(messages):
            yield token

        # On barge-in
        await client.abort()

        await client.stop()
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        if config is None:
            settings = get_settings()
            config = LLMConfig(
                base_url=settings.llm_base_url,
                model=settings.llm_model_path.split("/")[-1],  # Extract model name
            )

        self._config = config
        self._client: AsyncOpenAI | None = None
        self._current_task: asyncio.Task | None = None
        self._abort_event: asyncio.Event = asyncio.Event()
        self._running: bool = False
        self._aborted: bool = False

    async def start(self) -> None:
        """Initialize vLLM client connection."""
        self._client = AsyncOpenAI(
            base_url=self._config.base_url,
            api_key="EMPTY",  # vLLM doesn't require API key
            timeout=self._config.timeout_s,
        )
        self._running = True
        self._abort_event.clear()
        self._aborted = False

    async def stop(self) -> None:
        """Stop client and cleanup."""
        await self.abort()
        if self._client:
            await self._client.close()
            self._client = None
        self._running = False

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate streaming response from LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional generation parameters

        Yields:
            Token strings as they become available

        Raises:
            LLMGenerationError: If client not started, generation fails, or times out

        Note:
            Streaming is subject to timeout_s (default 30s) per TMF §3.2.
        """
        if not self._running or not self._client:
            raise LLMGenerationError("Client not started", model=self._config.model)

        self._abort_event.clear()

        try:
            # Merge kwargs with defaults
            params = {
                "model": self._config.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self._config.max_tokens),
                "temperature": kwargs.get("temperature", self._config.temperature),
                "top_p": kwargs.get("top_p", self._config.top_p),
                "stream": True,
            }

            # Create streaming request
            response = await self._client.chat.completions.create(**params)

            # Wrap streaming iteration with timeout
            async for chunk in timeout_async_iterator(
                self._iterate_response(response),
                timeout_s=self._config.timeout_s,
                operation="LLM streaming",
            ):
                # Check for abort
                if self._abort_event.is_set():
                    break

                yield chunk

        except AsyncTimeoutError as e:
            raise LLMGenerationError(
                f"Streaming timed out after {self._config.timeout_s}s",
                model=self._config.model,
            )
        except asyncio.CancelledError:
            raise
        except LLMGenerationError:
            raise
        except Exception as e:
            if not self._abort_event.is_set():
                raise LLMGenerationError(str(e), model=self._config.model)

    async def _iterate_response(self, response) -> AsyncIterator[str]:
        """Iterate over response chunks, extracting content.

        Args:
            response: OpenAI streaming response object

        Yields:
            Token strings from response chunks
        """
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> LLMResponse:
        """Generate complete response (non-streaming).

        Args:
            messages: List of message dicts
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse with complete text

        Raises:
            LLMGenerationError: If client not started or generation fails
        """
        if not self._running or not self._client:
            raise LLMGenerationError("Client not started", model=self._config.model)

        text_parts: list[str] = []

        async for token in self.generate_stream(messages, **kwargs):
            text_parts.append(token)

        return LLMResponse(
            text="".join(text_parts),
            is_complete=True,
        )

    async def abort(self) -> None:
        """Abort current generation immediately.

        Called on barge-in to stop LLM generation.
        Must complete quickly to meet 150ms barge-in contract.
        Idempotent - safe to call multiple times.
        """
        # Idempotency check - don't abort twice
        if self._aborted:
            return

        self._aborted = True
        self._abort_event.set()

        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await asyncio.wait_for(self._current_task, timeout=0.1)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

    @property
    def is_running(self) -> bool:
        """Whether client is ready for generation."""
        return self._running


def build_messages(
    system_prompt: str,
    conversation: list[dict[str, str]],
    user_input: str,
) -> list[dict[str, str]]:
    """Build message list for LLM.

    Args:
        system_prompt: System prompt with persona/rules
        conversation: Previous conversation turns
        user_input: Current user input

    Returns:
        List of message dicts for LLM API
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation)
    messages.append({"role": "user", "content": user_input})
    return messages


async def create_vllm_client(**kwargs) -> VLLMClient:
    """Factory function to create and start vLLM client.

    Args:
        **kwargs: Configuration options

    Returns:
        Started VLLMClient instance
    """
    config = LLMConfig(**kwargs) if kwargs else None
    client = VLLMClient(config)
    await client.start()
    return client
