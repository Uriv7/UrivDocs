"""
UrivDocs — ingestion/parsers/pdf.py
Tries PyMuPDF (fast, handles large PDFs) first.
Falls back to pypdf if PyMuPDF is not available (Python 3.13+).
Both stream page-by-page so 2GB PDFs never fill memory.
"""

from pathlib import Path
from typing import List
from loguru import logger
from ingestion.parsers.base import BasePage


def _parse_with_pymupdf(path: Path) -> List[BasePage]:
    import fitz  # PyMuPDF
    pages = []
    doc = fitz.open(str(path))
    logger.info(f"PyMuPDF: {doc.page_count} pages in {path.name}")
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text")
        if not text.strip():
            blocks = page.get_text("blocks")
            text = "\n".join(b[4] for b in blocks if isinstance(b[4], str))
        if text.strip():
            pages.append(BasePage(text=text.strip(), page_number=i + 1))
        page = None
    doc.close()
    return pages


def _parse_with_pypdf(path: Path) -> List[BasePage]:
    from pypdf import PdfReader
    pages = []
    reader = PdfReader(str(path))
    logger.info(f"pypdf: {len(reader.pages)} pages in {path.name}")
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(BasePage(text=text.strip(), page_number=i + 1))
        except Exception as e:
            logger.warning(f"pypdf skipped page {i+1}: {e}")
    return pages


class PDFParser:
    def parse(self, path: Path) -> List[BasePage]:
        # Try PyMuPDF first (much faster, better for large files)
        try:
            import fitz
            pages = _parse_with_pymupdf(path)
            logger.info(f"PyMuPDF extracted {len(pages)} pages from {path.name}")
            return pages
        except ImportError:
            logger.warning("PyMuPDF not available — using pypdf fallback")
        except Exception as e:
            logger.warning(f"PyMuPDF failed ({e}) — using pypdf fallback")

        # Fallback to pypdf
        try:
            pages = _parse_with_pypdf(path)
            logger.info(f"pypdf extracted {len(pages)} pages from {path.name}")
            return pages
        except Exception as e:
            logger.error(f"Both PDF parsers failed for {path.name}: {e}")
            return []
