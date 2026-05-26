"""
UrivDocs — ingestion/embedder.py
Pre-warmed at startup for zero cold-start latency on first query.
Uses all-MiniLM-L6-v2: 80MB, 384-dim, ~22ms/query on CPU.
"""
from __future__ import annotations
import os
from typing import List
from loguru import logger

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
BATCH_SIZE = 64  # Larger batch = faster bulk embedding during ingestion


class Embedder:
    _model = None

    @classmethod
    def warmup(cls):
        """Pre-load model at startup so first query has no cold-start delay."""
        if cls._model is None:
            cls._get_model_cls()
        # Encode a dummy string to force full model init
        cls._model.encode("warmup", normalize_embeddings=True)
        logger.info(f"Embedding model warmed up: {EMBEDDING_MODEL}")

    @classmethod
    def _get_model_cls(cls):
        if cls._model is None:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL} ({EMBEDDING_DEVICE})")
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(
                EMBEDDING_MODEL,
                device=EMBEDDING_DEVICE,
            )
        return cls._model

    def _get_model(self):
        return self.__class__._get_model_cls()

    def embed(self, chunks: List[dict]) -> List[dict]:
        if not chunks:
            return chunks
        model = self._get_model()
        texts = [c["text"] for c in chunks]
        logger.info(f"Embedding {len(texts)} chunks (batch_size={BATCH_SIZE})...")
        vectors = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        for chunk, vec in zip(chunks, vectors):
            chunk["embedding"] = vec.tolist()
        return chunks

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        vec = model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
        return vec.tolist()
