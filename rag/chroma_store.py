"""ChromaDB vector store — stub for Phase 1, ready for Phase 3 RAG."""

from typing import Optional

from langchain_core.documents import Document


_vector_store = None


def get_vector_store():
    """Get or create the ChromaDB vector store instance.

    Uses BAAI/bge-large-en-v1.5 embeddings as specified in AGENTS.md.
    """
    global _vector_store

    if _vector_store is not None:
        return _vector_store

    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5"
        )

        _vector_store = Chroma(
            collection_name="research_findings",
            embedding_function=embeddings,
            persist_directory="./chroma_db",
        )

        return _vector_store
    except ImportError:
        return None


def store_documents(documents: list[Document], collection: str = "research_findings") -> bool:
    """Store documents in the vector database."""
    try:
        store = get_vector_store()
        if store is None:
            return False

        store.add_documents(documents)
        return True
    except Exception:
        return False


def query_similar(query: str, k: int = 5) -> list[Document]:
    """Query the vector store for similar documents."""
    try:
        store = get_vector_store()
        if store is None:
            return []

        return store.similarity_search(query, k=k)
    except Exception:
        return []
