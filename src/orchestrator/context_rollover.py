"""Context Rollover - Pinned prefix + rolling window + summary state.

TMF v3.0 §3.2: Context Management
- Hard cap: 8192 tokens
- Rollover threshold: 7500 tokens (93.75%)
- Pinned prefix never evicted
- Summary state preserves key facts from evicted context

Structure:
┌─────────────────────────────────────────────────────────┐
│                    8192 TOKEN CAP                       │
├─────────────────────────────────────────────────────────┤
│  PINNED PREFIX (never evicted)                         │
│  - System prompt + safety rules                        │
│  - Canonical persona/role definition                   │
│  - Minimal session grounding turns                     │
├─────────────────────────────────────────────────────────┤
│  ROLLING WINDOW (active turns)                         │
│  - Recent user/assistant exchanges                     │
│  - Context-relevant tool call results                  │
├─────────────────────────────────────────────────────────┤
│  SESSION STATE BLOCK (on rollover)                     │
│  - Summarized older turns                              │
│  - Key facts from evicted context                      │
└─────────────────────────────────────────────────────────┘

Reference: Implementation-v3.0.md §5.2
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from src.config.constants import TMF
from src.llm.vllm_client import VLLMClient


@dataclass
class Message:
    """A conversation message."""

    role: str  # "system", "user", "assistant"
    content: str
    token_count: int = 0
    is_pinned: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class ContextWindow:
    """Managed context window with rollover support.

    Maintains:
    - Pinned prefix (system prompt, always included)
    - Rolling window of recent messages
    - Summary state from evicted messages

    Usage:
        context = ContextWindow(
            system_prompt="You are a helpful assistant...",
            llm_client=vllm_client,
        )

        # Add messages
        context.add_user_message("Hello")
        context.add_assistant_message("Hi there!")

        # Get messages for LLM (handles rollover automatically)
        messages = await context.get_messages()
    """

    system_prompt: str
    llm_client: VLLMClient | None = None
    max_tokens: int = TMF.LLM_MAX_CONTEXT_TOKENS
    rollover_threshold: int = TMF.CONTEXT_ROLLOVER_THRESHOLD
    summarization_timeout_s: float = TMF.CONTEXT_SUMMARIZATION_TIMEOUT_S

    # Internal state
    _pinned_messages: list[Message] = field(default_factory=list, init=False)
    _rolling_messages: list[Message] = field(default_factory=list, init=False)
    _summary_state: str = field(default="", init=False)
    _total_tokens: int = field(default=0, init=False)
    _pinned_tokens: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        """Initialize with system prompt as pinned."""
        system_message = Message(
            role="system",
            content=self.system_prompt,
            token_count=self._estimate_tokens(self.system_prompt),
            is_pinned=True,
        )
        self._pinned_messages.append(system_message)
        self._pinned_tokens = system_message.token_count
        self._total_tokens = self._pinned_tokens

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses simple heuristic: ~4 characters per token.
        In production, use tiktoken for accurate counts.
        """
        # Simple estimate: ~4 chars per token on average
        return max(1, len(text) // 4)

    @property
    def total_tokens(self) -> int:
        """Current total token count."""
        return self._total_tokens

    @property
    def available_tokens(self) -> int:
        """Tokens available before hitting max."""
        return self.max_tokens - self._total_tokens

    @property
    def needs_rollover(self) -> bool:
        """Whether rollover should be triggered."""
        return self._total_tokens >= self.rollover_threshold

    def add_user_message(self, content: str, metadata: dict | None = None) -> Message:
        """Add a user message to the context.

        Args:
            content: Message content
            metadata: Optional metadata

        Returns:
            Created Message object
        """
        message = Message(
            role="user",
            content=content,
            token_count=self._estimate_tokens(content),
            metadata=metadata or {},
        )
        self._rolling_messages.append(message)
        self._total_tokens += message.token_count
        return message

    def add_assistant_message(self, content: str, metadata: dict | None = None) -> Message:
        """Add an assistant message to the context.

        Args:
            content: Message content
            metadata: Optional metadata

        Returns:
            Created Message object
        """
        message = Message(
            role="assistant",
            content=content,
            token_count=self._estimate_tokens(content),
            metadata=metadata or {},
        )
        self._rolling_messages.append(message)
        self._total_tokens += message.token_count
        return message

    def add_pinned_message(self, role: str, content: str) -> Message:
        """Add a pinned message that won't be evicted.

        Args:
            role: Message role
            content: Message content

        Returns:
            Created Message object
        """
        message = Message(
            role=role,
            content=content,
            token_count=self._estimate_tokens(content),
            is_pinned=True,
        )
        self._pinned_messages.append(message)
        self._pinned_tokens += message.token_count
        self._total_tokens += message.token_count
        return message

    async def get_messages(self) -> list[dict[str, str]]:
        """Get messages for LLM, handling rollover if needed.

        Returns:
            List of message dicts for LLM API

        Note:
            Automatically triggers rollover if threshold exceeded.
        """
        if self.needs_rollover:
            await self._perform_rollover()

        messages = []

        # Add pinned messages first
        for msg in self._pinned_messages:
            messages.append({"role": msg.role, "content": msg.content})

        # Add summary state if present
        if self._summary_state:
            messages.append({
                "role": "system",
                "content": f"[Session Context Summary]\n{self._summary_state}",
            })

        # Add rolling messages
        for msg in self._rolling_messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    async def _perform_rollover(self) -> None:
        """Perform context rollover.

        1. Summarize older messages
        2. Keep most recent messages
        3. Store summary in session state block
        """
        if len(self._rolling_messages) < 4:
            # Not enough messages to rollover
            return

        # Split: summarize first half, keep second half
        split_point = len(self._rolling_messages) // 2
        to_summarize = self._rolling_messages[:split_point]
        to_keep = self._rolling_messages[split_point:]

        # Generate summary
        summary = await self._summarize_messages(to_summarize)

        if summary:
            # Update summary state
            if self._summary_state:
                self._summary_state = f"{self._summary_state}\n\n{summary}"
            else:
                self._summary_state = summary

            # Evict summarized messages
            evicted_tokens = sum(m.token_count for m in to_summarize)
            self._rolling_messages = to_keep
            self._total_tokens -= evicted_tokens
            self._total_tokens += self._estimate_tokens(summary)

    async def _summarize_messages(self, messages: list[Message]) -> str:
        """Summarize a list of messages.

        Args:
            messages: Messages to summarize

        Returns:
            Summary string, or empty if summarization fails

        Note:
            TMF §3.2: 5 second timeout for summarization.
            On failure, reject new turn with error.
        """
        if not messages:
            return ""

        if not self.llm_client:
            # Fallback: simple concatenation
            summary_parts = []
            for msg in messages:
                summary_parts.append(f"{msg.role}: {msg.content[:100]}...")
            return "Previous conversation:\n" + "\n".join(summary_parts)

        # Build summarization prompt
        conversation_text = "\n".join(
            f"{msg.role}: {msg.content}" for msg in messages
        )

        summarization_prompt = [
            {
                "role": "system",
                "content": (
                    "Summarize the following conversation excerpt concisely. "
                    "Preserve key facts, decisions, and action items. "
                    "Be brief but complete."
                ),
            },
            {"role": "user", "content": conversation_text},
        ]

        try:
            # Generate summary with timeout
            summary_parts = []
            async for token in asyncio.wait_for(
                self.llm_client.generate_stream(summarization_prompt, max_tokens=200),
                timeout=self.summarization_timeout_s,
            ):
                summary_parts.append(token)

            return "".join(summary_parts)

        except asyncio.TimeoutError:
            # TMF §3.2: Reject new turn on timeout
            raise RuntimeError("Context summarization timed out")
        except Exception as e:
            raise RuntimeError(f"Context summarization failed: {e}")

    def clear(self) -> None:
        """Clear all non-pinned messages."""
        evicted_tokens = sum(m.token_count for m in self._rolling_messages)
        self._rolling_messages = []
        self._summary_state = ""
        self._total_tokens = self._pinned_tokens

    @property
    def message_count(self) -> int:
        """Total number of messages (pinned + rolling)."""
        return len(self._pinned_messages) + len(self._rolling_messages)

    @property
    def turn_count(self) -> int:
        """Number of conversation turns (user+assistant pairs)."""
        user_messages = sum(
            1 for m in self._rolling_messages if m.role == "user"
        )
        return user_messages


def create_context_window(
    system_prompt: str,
    llm_client: VLLMClient | None = None,
    **kwargs,
) -> ContextWindow:
    """Factory function to create context window.

    Args:
        system_prompt: System prompt for the session
        llm_client: Optional vLLM client for summarization
        **kwargs: Additional configuration

    Returns:
        Configured ContextWindow instance
    """
    return ContextWindow(
        system_prompt=system_prompt,
        llm_client=llm_client,
        **kwargs,
    )
