"""UrivDocs — vectorstore/chroma_store.py"""
from __future__ import annotations
import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from loguru import logger
from vectorstore.store import BaseVectorStore

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./storage/vectordb")
COLLECTION_NAME = "urivdocs"


class ChromaStore(BaseVectorStore):
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        count = self.collection.count()
        logger.info(f"ChromaStore ready — {count} chunks indexed")

    def upsert(self, chunks: List[dict]) -> None:
        if not chunks:
            return
        ids        = [c["id"]        for c in chunks]
        embeddings = [c["embedding"] for c in chunks]
        documents  = [c["text"]      for c in chunks]
        metadatas  = [
            {
                "source":      c["source"],
                "page_number": c["page_number"],
                "section":     c["section"],
                "chunk_index": c["chunk_index"],
                "token_count": c["token_count"],
            }
            for c in chunks
        ]
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"ChromaStore upserted {len(chunks)} chunks")

    def search(self, query_vector: List[float], top_k: int = 5,
               source_filter: Optional[str] = None) -> List[dict]:
        # ── Guard: never query an empty collection ──────────────────
        count = self.collection.count()
        if count == 0:
            logger.warning("ChromaStore: collection is empty — no results")
            return []

        # Clamp top_k to available docs to avoid Chroma HNSW errors
        top_k = min(top_k, count)

        where = {"source": source_filter} if source_filter else None

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"ChromaStore query error: {e}")
            return []

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append({
                "text":        doc,
                "score":       round(1 - dist, 4),
                "source":      meta["source"],
                "page_number": meta["page_number"],
                "section":     meta.get("section", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "token_count": meta.get("token_count", 0),
            })
        return hits

    def delete_source(self, source: str) -> None:
        try:
            self.collection.delete(where={"source": source})
            logger.info(f"Deleted chunks for: {source}")
        except Exception as e:
            logger.warning(f"Delete error (may be empty): {e}")

    def list_sources(self) -> List[str]:
        try:
            if self.collection.count() == 0:
                return []
            results = self.collection.get(include=["metadatas"])
            return sorted(list({m["source"] for m in results["metadatas"]}))
        except Exception as e:
            logger.warning(f"list_sources error: {e}")
            return []
