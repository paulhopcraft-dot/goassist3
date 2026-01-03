"""LLM module - LLM clients and prompt building.

Supports multiple backends:
- vllm: Production backend using vLLM serving (self-hosted)
- anthropic: Cloud backend using Anthropic Claude API
- mock: Testing backend with canned responses
"""

from __future__ import annotations

from src.llm.vllm_client import (
    VLLMClient,
    LLMConfig,
    LLMResponse,
    build_messages,
    create_vllm_client,
)
from src.llm.mock_client import MockLLMClient, MockLLMConfig, create_mock_llm_client


async def create_llm_client(engine: str | None = None):
    """Factory function to create LLM client based on configuration.

    Args:
        engine: Override engine selection ("mock", "vllm", or "anthropic").
                If None, uses LLM_ENGINE from settings.

    Returns:
        Started LLM client (MockLLMClient, VLLMClient, or AnthropicClient)

    Raises:
        ValueError: If engine is unknown
        RuntimeError: If required configuration missing (e.g., ANTHROPIC_API_KEY)
    """
    if engine is None:
        from src.config.settings import get_settings
        settings = get_settings()
        engine = settings.llm_engine

    if engine == "mock":
        return await create_mock_llm_client()
    elif engine == "vllm":
        return await create_vllm_client()
    elif engine == "anthropic":
        from src.llm.anthropic_client import create_anthropic_client
        return await create_anthropic_client()
    else:
        raise ValueError(
            f"Unknown LLM engine: {engine}. "
            f"Available: mock, vllm, anthropic"
        )


__all__ = [
    # Clients
    "VLLMClient",
    "MockLLMClient",
    # AnthropicClient - lazy import via create_anthropic_client()
    # Configuration
    "LLMConfig",
    "MockLLMConfig",
    # Response types
    "LLMResponse",
    # Utilities
    "build_messages",
    # Factories
    "create_llm_client",
    "create_vllm_client",
    "create_mock_llm_client",
    # create_anthropic_client - imported when needed
]
