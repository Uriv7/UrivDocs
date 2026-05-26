"""UrivDocs — vectorstore/indexer.py"""

from typing import List
from vectorstore.store import get_store
from loguru import logger


class Indexer:
    def __init__(self):
        self.store = get_store()

    def index(self, chunks: List[dict]) -> int:
        self.store.upsert(chunks)
        return len(chunks)

    def delete(self, source: str) -> None:
        self.store.delete_source(source)
        logger.info(f"Removed '{source}' from index")
