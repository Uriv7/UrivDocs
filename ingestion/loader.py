"""
UrivDocs — ingestion/loader.py
Detects file type and routes to the correct parser.
Returns a unified list of ParsedChunk objects.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Optional

from loguru import logger

from ingestion.parsers.pdf import PDFParser
from ingestion.parsers.docx import DocxParser
from ingestion.parsers.csv_parser import CSVParser
from ingestion.parsers.image import ImageParser
from ingestion.parsers.audio import AudioParser
from ingestion.parsers.generic import GenericTextParser
from ingestion.chunker import Chunker
from ingestion.embedder import Embedder


PARSER_MAP = {
    "application/pdf": PDFParser,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser,
    "application/msword": DocxParser,
    "text/csv": CSVParser,
    "image/png": ImageParser,
    "image/jpeg": ImageParser,
    "image/webp": ImageParser,
    "image/tiff": ImageParser,
    "audio/mpeg": AudioParser,
    "audio/wav": AudioParser,
    "audio/ogg": AudioParser,
    "video/mp4": AudioParser,
    "text/plain": GenericTextParser,
    "text/html": GenericTextParser,
    "text/markdown": GenericTextParser,
}


class DocumentLoader:
    def __init__(self):
        self.chunker = Chunker()
        self.embedder = Embedder()

    def load(self, file_path: str | Path, original_filename: Optional[str] = None):
        """
        Main entry point. Parses → chunks → embeds a file.
        Returns list of dicts ready for vectorstore upsert.
        """
        path = Path(file_path)
        filename = original_filename or path.name

        mime_type = self._detect_mime(path)
        logger.info(f"Loading '{filename}' — detected MIME: {mime_type}")

        parser_cls = PARSER_MAP.get(mime_type)
        if parser_cls is None:
            logger.warning(f"No dedicated parser for {mime_type}, falling back to GenericTextParser")
            parser_cls = GenericTextParser

        parser = parser_cls()
        pages = parser.parse(path)
        logger.info(f"Parsed {len(pages)} page(s) from '{filename}'")

        chunks = self.chunker.chunk(pages, source=filename)
        logger.info(f"Generated {len(chunks)} chunks from '{filename}'")

        embedded = self.embedder.embed(chunks)
        logger.info(f"Embedded {len(embedded)} chunks from '{filename}'")

        return embedded

    def _detect_mime(self, path: Path) -> str:
        mime, _ = mimetypes.guess_type(str(path))
        if mime:
            return mime
        # Try extension fallback
        ext = path.suffix.lower()
        ext_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".csv": "text/csv",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".mp4": "video/mp4",
        }
        return ext_map.get(ext, "text/plain")
