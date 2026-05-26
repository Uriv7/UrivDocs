"""UrivDocs — vectorstore/qdrant_store.py"""
from __future__ import annotations
import os
from typing import List, Optional
from loguru import logger

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "urivdocs")
# all-MiniLM-L6-v2 = 384, nomic-embed = 768, bge-large = 1024
# We auto-detect from the first upsert
VECTOR_SIZE = int(os.getenv("EMBEDDING_DIM", "384"))


class QdrantStore:
    def __init__(self):
        from qdrant_client import QdrantClient
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        self._collection_ready = False
        logger.info(f"QdrantStore initialized — collection: {COLLECTION_NAME}")

    def _ensure_collection(self, vector_size: int = VECTOR_SIZE):
        from qdrant_client.models import Distance, VectorParams
        if self._collection_ready:
            return
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {COLLECTION_NAME} (dim={vector_size})")
        self._collection_ready = True

    def upsert(self, chunks: List[dict]) -> None:
        if not chunks:
            return
        from qdrant_client.models import PointStruct
        # Auto-detect vector size from first chunk
        vec_size = len(chunks[0]["embedding"])
        self._ensure_collection(vec_size)

        points = [
            PointStruct(
                id=i,
                vector=c["embedding"],
                payload={
                    "chunk_uuid": c["id"],
                    "text": c["text"],
                    "source": c["source"],
                    "page_number": c["page_number"],
                    "section": c["section"],
                    "chunk_index": c["chunk_index"],
                    "token_count": c["token_count"],
                },
            )
            for i, c in enumerate(chunks)
        ]
        self.client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info(f"QdrantStore upserted {len(chunks)} points")

    def search(self, query_vector: List[float], top_k: int = 5, source_filter: Optional[str] = None) -> List[dict]:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        self._ensure_collection(len(query_vector))
        filt = None
        if source_filter:
            filt = Filter(must=[FieldCondition(key="source", match=MatchValue(value=source_filter))])
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filt,
            with_payload=True,
        )
        return [{
            "text": r.payload["text"],
            "score": round(r.score, 4),
            "source": r.payload["source"],
            "page_number": r.payload["page_number"],
            "section": r.payload["section"],
            "chunk_index": r.payload["chunk_index"],
            "token_count": r.payload["token_count"],
        } for r in results]

    def delete_source(self, source: str) -> None:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(must=[FieldCondition(key="source", match=MatchValue(value=source))]),
        )
        logger.info(f"Deleted source from Qdrant: {source}")

    def list_sources(self) -> List[str]:
        results = self.client.scroll(collection_name=COLLECTION_NAME, with_payload=["source"], limit=10000)
        return sorted(list({p.payload["source"] for p in results[0]}))
