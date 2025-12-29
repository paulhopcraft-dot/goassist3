"""Knowledge module.

Provides domain knowledge retrieval (RAG) for the voice assistant.

The three knowledge sources in GoAssist3:
1. Quick Memory (session) - orchestrator/context_rollover.py
2. Domain Knowledge (RAG) - knowledge/rag.py (THIS MODULE)
3. LLM (reasoning) - llm/vllm_client.py

Usage:
    from src.knowledge import get_rag_system, query_knowledge

    # Quick query
    context = await query_knowledge("What is the return policy?")

    # Full RAG access
    rag = await get_rag_system()
    await rag.add_file("docs/policies.pdf")
    results = await rag.query("shipping costs", k=5)

Reference: PRD v3.0 Section 5
"""

from src.knowledge.rag import (
    Document,
    RAGSystem,
    SearchResult,
    get_rag_system,
    query_knowledge,
)

__all__ = [
    "Document",
    "RAGSystem",
    "SearchResult",
    "get_rag_system",
    "query_knowledge",
]
