"""UrivDocs — ingestion/parsers/generic.py"""

from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
from loguru import logger

from ingestion.parsers.base import BasePage

CHARS_PER_PAGE = 3000


class GenericTextParser:
    def parse(self, path: Path) -> List[BasePage]:
        raw = path.read_text(encoding="utf-8", errors="replace")

        # Strip HTML tags if needed
        if path.suffix.lower() in (".html", ".htm"):
            soup = BeautifulSoup(raw, "lxml")
            raw = soup.get_text(separator="\n")

        text = raw.strip()
        if not text:
            return []

        # Split into pages by character count
        pages: List[BasePage] = []
        for i, start in enumerate(range(0, len(text), CHARS_PER_PAGE)):
            chunk_text = text[start : start + CHARS_PER_PAGE]
            pages.append(BasePage(text=chunk_text, page_number=i + 1))

        logger.info(f"Extracted {len(pages)} pages from {path.name}")
        return pages
