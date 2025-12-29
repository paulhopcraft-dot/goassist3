"""RAG (Retrieval-Augmented Generation) System.

Provides domain knowledge retrieval for the voice assistant.
Supports multiple backends with automatic fallback.

Knowledge Sources:
1. Quick Memory (session) - handled by orchestrator/context_rollover.py
2. Domain Knowledge (RAG) - THIS MODULE
3. LLM (reasoning) - handled by llm/vllm_client.py

Reference: PRD v3.0 §5, Implementation v3.0 §5
"""

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A document in the knowledge base."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class SearchResult:
    """A search result from the knowledge base."""

    document: Document
    score: float  # Similarity score (0-1, higher is better)
    context: str = ""  # Extracted context snippet


class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...


class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embeddings provider."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self._model = model
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI()
        return self._client

    async def embed(self, text: str) -> list[float]:
        client = await self._get_client()
        response = await client.embeddings.create(
            input=text,
            model=self._model,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        client = await self._get_client()
        response = await client.embeddings.create(
            input=texts,
            model=self._model,
        )
        return [item.embedding for item in response.data]


class LocalEmbeddings(EmbeddingProvider):
    """Local embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model

    async def embed(self, text: str) -> list[float]:
        model = self._get_model()
        # Run in executor to not block event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: model.encode(text).tolist()
        )
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: model.encode(texts).tolist()
        )
        return embeddings


class VectorStore(ABC):
    """Abstract base for vector stores."""

    @abstractmethod
    async def add(self, documents: list[Document]) -> None:
        """Add documents to the store."""
        ...

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        k: int = 5,
    ) -> list[SearchResult]:
        """Search for similar documents."""
        ...

    @abstractmethod
    async def delete(self, doc_ids: list[str]) -> None:
        """Delete documents by ID."""
        ...


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store using cosine similarity."""

    def __init__(self):
        self._documents: dict[str, Document] = {}

    async def add(self, documents: list[Document]) -> None:
        for doc in documents:
            self._documents[doc.id] = doc

    async def search(
        self,
        query_embedding: list[float],
        k: int = 5,
    ) -> list[SearchResult]:
        import numpy as np

        if not self._documents:
            return []

        query = np.array(query_embedding)
        results = []

        for doc in self._documents.values():
            if doc.embedding is None:
                continue

            doc_emb = np.array(doc.embedding)
            # Cosine similarity
            similarity = np.dot(query, doc_emb) / (
                np.linalg.norm(query) * np.linalg.norm(doc_emb)
            )
            results.append(SearchResult(
                document=doc,
                score=float(similarity),
                context=doc.content[:500],
            ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]

    async def delete(self, doc_ids: list[str]) -> None:
        for doc_id in doc_ids:
            self._documents.pop(doc_id, None)


class ChromaVectorStore(VectorStore):
    """ChromaDB vector store."""

    def __init__(
        self,
        collection_name: str = "goassist_knowledge",
        persist_directory: str | None = None,
    ):
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        self._client = None
        self._collection = None

    async def _get_collection(self):
        if self._collection is None:
            import chromadb

            if self._persist_directory:
                self._client = chromadb.PersistentClient(
                    path=self._persist_directory
                )
            else:
                self._client = chromadb.Client()

            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    async def add(self, documents: list[Document]) -> None:
        collection = await self._get_collection()

        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        embeddings = [doc.embedding for doc in documents if doc.embedding]
        metadatas = [doc.metadata for doc in documents]

        collection.add(
            ids=ids,
            documents=contents,
            embeddings=embeddings if embeddings else None,
            metadatas=metadatas,
        )

    async def search(
        self,
        query_embedding: list[float],
        k: int = 5,
    ) -> list[SearchResult]:
        collection = await self._get_collection()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        for i, doc_id in enumerate(results["ids"][0]):
            # ChromaDB returns distance, convert to similarity
            distance = results["distances"][0][i]
            similarity = 1 - distance  # Cosine distance to similarity

            doc = Document(
                id=doc_id,
                content=results["documents"][0][i],
                metadata=results["metadatas"][0][i] if results["metadatas"] else {},
            )

            search_results.append(SearchResult(
                document=doc,
                score=similarity,
                context=doc.content[:500],
            ))

        return search_results

    async def delete(self, doc_ids: list[str]) -> None:
        collection = await self._get_collection()
        collection.delete(ids=doc_ids)


class RAGSystem:
    """Retrieval-Augmented Generation system.

    Manages domain knowledge retrieval for the voice assistant.

    Usage:
        rag = RAGSystem()
        await rag.initialize()

        # Add documents
        await rag.add_documents([
            Document(id="1", content="..."),
            Document(id="2", content="..."),
        ])

        # Query
        results = await rag.query("What is the return policy?", k=3)

        # Use in prompt
        context = rag.format_context(results)
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize RAG system with auto-detected backends."""
        if self._initialized:
            return

        # Auto-detect embedding provider
        if self._embedding_provider is None:
            self._embedding_provider = await self._auto_detect_embeddings()

        # Auto-detect vector store
        if self._vector_store is None:
            self._vector_store = await self._auto_detect_vector_store()

        self._initialized = True
        logger.info("RAG system initialized")

    async def _auto_detect_embeddings(self) -> EmbeddingProvider:
        """Auto-detect best available embedding provider."""
        # Try OpenAI first
        try:
            from openai import AsyncOpenAI
            logger.info("Using OpenAI embeddings")
            return OpenAIEmbeddings()
        except ImportError:
            pass

        # Try sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Using local sentence-transformers embeddings")
            return LocalEmbeddings()
        except ImportError:
            pass

        raise RuntimeError(
            "No embedding provider available. "
            "Install openai or sentence-transformers."
        )

    async def _auto_detect_vector_store(self) -> VectorStore:
        """Auto-detect best available vector store."""
        # Try ChromaDB
        try:
            import chromadb
            logger.info("Using ChromaDB vector store")
            return ChromaVectorStore()
        except ImportError:
            pass

        # Fallback to in-memory
        logger.info("Using in-memory vector store")
        return InMemoryVectorStore()

    async def add_documents(
        self,
        documents: list[Document],
        chunk: bool = True,
    ) -> None:
        """Add documents to the knowledge base.

        Args:
            documents: Documents to add
            chunk: If True, split documents into chunks
        """
        if not self._initialized:
            await self.initialize()

        # Chunk documents if requested
        if chunk:
            chunked_docs = []
            for doc in documents:
                chunks = self._chunk_text(doc.content)
                for i, chunk_text in enumerate(chunks):
                    chunk_doc = Document(
                        id=f"{doc.id}_chunk_{i}",
                        content=chunk_text,
                        metadata={**doc.metadata, "parent_id": doc.id, "chunk": i},
                    )
                    chunked_docs.append(chunk_doc)
            documents = chunked_docs

        # Generate embeddings
        texts = [doc.content for doc in documents]
        embeddings = await self._embedding_provider.embed_batch(texts)

        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding

        # Store documents
        await self._vector_store.add(documents)
        logger.info(f"Added {len(documents)} documents to knowledge base")

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self._chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self._chunk_size
            chunk = text[start:end]

            # Try to end at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(". ")
                if last_period > self._chunk_size // 2:
                    end = start + last_period + 1
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - self._chunk_overlap

        return chunks

    async def query(
        self,
        question: str,
        k: int = 5,
        threshold: float = 0.5,
    ) -> list[SearchResult]:
        """Query the knowledge base.

        Args:
            question: User's question
            k: Number of results to return
            threshold: Minimum similarity score

        Returns:
            List of relevant documents
        """
        if not self._initialized:
            await self.initialize()

        # Generate query embedding
        query_embedding = await self._embedding_provider.embed(question)

        # Search vector store
        results = await self._vector_store.search(query_embedding, k=k)

        # Filter by threshold
        results = [r for r in results if r.score >= threshold]

        return results

    def format_context(
        self,
        results: list[SearchResult],
        max_chars: int = 2000,
    ) -> str:
        """Format search results as context for LLM.

        Args:
            results: Search results
            max_chars: Maximum context length

        Returns:
            Formatted context string
        """
        if not results:
            return ""

        context_parts = []
        total_chars = 0

        for result in results:
            content = result.context or result.document.content[:500]

            if total_chars + len(content) > max_chars:
                break

            context_parts.append(f"[Relevance: {result.score:.2f}]\n{content}")
            total_chars += len(content)

        return "\n\n---\n\n".join(context_parts)

    async def add_file(self, file_path: Path | str) -> None:
        """Add a file to the knowledge base.

        Supports: .txt, .md, .pdf (if pypdf installed)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = ""

        if file_path.suffix in (".txt", ".md"):
            content = file_path.read_text()

        elif file_path.suffix == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                content = "\n".join(
                    page.extract_text() for page in reader.pages
                )
            except ImportError:
                raise RuntimeError("PDF support requires pypdf: pip install pypdf")

        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Create document with file hash as ID
        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
        doc = Document(
            id=doc_id,
            content=content,
            metadata={"source": str(file_path), "filename": file_path.name},
        )

        await self.add_documents([doc])


# Global RAG instance
_rag_instance: RAGSystem | None = None


async def get_rag_system() -> RAGSystem:
    """Get or create the global RAG system instance."""
    global _rag_instance

    if _rag_instance is None:
        _rag_instance = RAGSystem()
        await _rag_instance.initialize()

    return _rag_instance


async def query_knowledge(
    question: str,
    k: int = 3,
) -> str:
    """Convenience function to query knowledge base.

    Args:
        question: User's question
        k: Number of results

    Returns:
        Formatted context for LLM
    """
    rag = await get_rag_system()
    results = await rag.query(question, k=k)
    return rag.format_context(results)
