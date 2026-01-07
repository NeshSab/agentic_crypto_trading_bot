"""
Document retrieval and semantic search services.

This module provides advanced document retrieval capabilities using FAISS
vector stores and semantic search. It implements various retrieval strategies
including simple similarity search and RAG fusion for enhanced document
discovery.

Key capabilities:
- FAISS vector store loading and management
- Semantic similarity search with configurable result counts
- LangChain integration for retrieval chains
"""

from __future__ import annotations
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings


def get_embeddings() -> OpenAIEmbeddings:
    """
    Create OpenAI embeddings instance for vector operations.

    Returns
    -------
    OpenAIEmbeddings
        Configured OpenAI embeddings client
    """
    return OpenAIEmbeddings()


def load_vectorstore(index_path: str) -> FAISS:
    """
    Load FAISS vector store from disk.

    Parameters
    ----------
    index_path : str
        Path to the FAISS index directory

    Returns
    -------
    FAISS
        Loaded FAISS vector store instance
    """
    return FAISS.load_local(
        index_path,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def get_semantic_retriever(index_path: str, k: int = 4) -> VectorStoreRetriever:
    """
    Create semantic similarity retriever from vector store.

    Parameters
    ----------
    index_path : str
        Path to the FAISS index directory
    k : int, default 4
        Number of similar documents to retrieve

    Returns
    -------
    VectorStoreRetriever
        Configured retriever for semantic search
    """
    vs = load_vectorstore(index_path)
    return vs.as_retriever(search_type="similarity", search_kwargs={"k": k})


def build_retrieval_runnable(index_path: str, k: int = 2) -> "RunnableLambda":
    """
    Create a retrieval chain using modern LangChain patterns.
    Returns a chain that can be composed with other chains.
    """
    retriever = get_semantic_retriever(index_path, k=k)

    def retrieve_docs(inputs: dict) -> list[Document]:
        query = inputs.get("query", inputs) if isinstance(inputs, dict) else inputs
        return retriever.invoke(str(query))

    return RunnableLambda(retrieve_docs)
