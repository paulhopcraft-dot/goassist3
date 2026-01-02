"""LLM module - LLM clients and prompt building.

Supports multiple backends:
- vllm: Production backend using vLLM serving
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
    """
    if engine is None:
        from src.config.settings import get_settings
        settings = get_settings()
        engine = settings.llm_engine

    if engine == "mock":
        return await create_mock_llm_client()
    else:
        return await create_vllm_client()


__all__ = [
    "VLLMClient",
    "MockLLMClient",
    "LLMConfig",
    "LLMResponse",
    "MockLLMConfig",
    "build_messages",
    "create_llm_client",
    "create_vllm_client",
    "create_mock_llm_client",
]
