"""UrivDocs — vectorstore/retriever.py"""
from __future__ import annotations
import os
from typing import List, Optional
from loguru import logger

TOP_K     = int(os.getenv("TOP_K",     "5"))     # retrieve more, filter later
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.15")) # lower = catches factual queries


class Retriever:
    def __init__(self):
        from vectorstore.store import get_store
        from ingestion.embedder import Embedder
        self.store    = get_store()
        self.embedder = Embedder()

    def retrieve(self, query: str, top_k: int = TOP_K,
                 source_filter: Optional[str] = None) -> List[dict]:
        query_vector = self.embedder.embed_query(query)
        hits = self.store.search(query_vector, top_k=top_k,
                                 source_filter=source_filter)

        if not hits:
            logger.info(f"No chunks found for: '{query[:60]}'")
            return []

        # Log all scores so we can tune threshold
        scores = [h.get("score", 0) for h in hits]
        logger.info(f"Retrieval scores: {[f'{s:.3f}' for s in scores]} "
                    f"for: '{query[:60]}'")

        # Filter below minimum relevance
        relevant = [h for h in hits if h.get("score", 0) >= MIN_SCORE]

        if not relevant:
            logger.warning(
                f"All scores below MIN_SCORE={MIN_SCORE} "
                f"(top={scores[0]:.3f}) for: '{query[:60]}'"
            )
            return []

        logger.info(f"✓ {len(relevant)} relevant chunks (top={relevant[0]['score']:.3f})")
        return relevant

    def list_sources(self) -> List[str]:
        return self.store.list_sources()
