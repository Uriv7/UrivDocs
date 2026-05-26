"""
UrivDocs — ingestion/chunker.py
Smaller chunks = better precision for factual/structured documents.
256 tokens per chunk, 32 overlap.
"""
from __future__ import annotations
import os, uuid
from typing import List
import tiktoken
from loguru import logger
from ingestion.parsers.base import BasePage

CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE",    "256"))  # smaller = more precise
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "32"))


class Chunker:
    def __init__(self):
        self.enc = tiktoken.get_encoding("cl100k_base")

    def chunk(self, pages: List[BasePage], source: str) -> List[dict]:
        all_chunks: List[dict] = []

        for page in pages:
            tokens = self.enc.encode(page.text)

            if len(tokens) <= CHUNK_SIZE:
                all_chunks.append(self._make(
                    text=page.text, tokens=tokens,
                    source=source, page_number=page.page_number,
                    section=page.section, chunk_index=0,
                ))
                continue

            start, idx = 0, 0
            while start < len(tokens):
                end         = min(start + CHUNK_SIZE, len(tokens))
                chunk_toks  = tokens[start:end]
                chunk_text  = self.enc.decode(chunk_toks)
                all_chunks.append(self._make(
                    text=chunk_text, tokens=chunk_toks,
                    source=source, page_number=page.page_number,
                    section=page.section, chunk_index=idx,
                ))
                if end == len(tokens):
                    break
                start += CHUNK_SIZE - CHUNK_OVERLAP
                idx   += 1

        logger.debug(f"Chunker: {len(all_chunks)} chunks for '{source}'")
        return all_chunks

    def _make(self, text, tokens, source, page_number, section, chunk_index) -> dict:
        return {
            "id":          str(uuid.uuid4()),
            "text":        text,
            "source":      source,
            "page_number": page_number,
            "section":     section or "",
            "chunk_index": chunk_index,
            "token_count": len(tokens),
        }
