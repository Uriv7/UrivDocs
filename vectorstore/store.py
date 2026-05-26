"""
UrivDocs — vectorstore/store.py
Factory that returns either ChromaStore or QdrantStore
depending on the VECTOR_STORE env variable.
"""

from __future__ import annotations

import os
from typing import List, Optional

from loguru import logger


VECTOR_STORE = os.getenv("VECTOR_STORE", "chroma")


def get_store():
    if VECTOR_STORE == "qdrant":
        from vectorstore.qdrant_store import QdrantStore
        return QdrantStore()
    else:
        from vectorstore.chroma_store import ChromaStore
        return ChromaStore()


class BaseVectorStore:
    def upsert(self, chunks: List[dict]) -> None:
        raise NotImplementedError

    def search(self, query_vector: List[float], top_k: int = 5, source_filter: Optional[str] = None) -> List[dict]:
        raise NotImplementedError

    def delete_source(self, source: str) -> None:
        raise NotImplementedError

    def list_sources(self) -> List[str]:
        raise NotImplementedError
