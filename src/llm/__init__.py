"""LLM module - LLM clients and prompt building.

Supports multiple backends:
- vllm: Production backend using vLLM serving (self-hosted, e.g., Qwen)
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
        engine: Override engine selection ("mock" or "vllm").
                If None, uses LLM_ENGINE from settings.

    Returns:
        Started LLM client (MockLLMClient or VLLMClient)

    Raises:
        ValueError: If engine is unknown
    """
    if engine is None:
        from src.config.settings import get_settings
        settings = get_settings()
        engine = settings.llm_engine

    if engine == "mock":
        return await create_mock_llm_client()
    elif engine == "vllm":
        return await create_vllm_client()
    else:
        raise ValueError(
            f"Unknown LLM engine: {engine}. "
            f"Available: mock, vllm"
        )


__all__ = [
    # Clients
    "VLLMClient",
    "MockLLMClient",
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
]
