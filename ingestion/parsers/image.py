"""UrivDocs — ingestion/parsers/image.py — OCR via Tesseract"""

from pathlib import Path
from typing import List

from PIL import Image
import pytesseract
from loguru import logger

from ingestion.parsers.base import BasePage


class ImageParser:
    def parse(self, path: Path) -> List[BasePage]:
        try:
            img = Image.open(str(path))
            text = pytesseract.image_to_string(img)

            if not text.strip():
                logger.warning(f"OCR returned no text for {path.name}")
                return []

            logger.info(f"OCR extracted {len(text)} chars from {path.name}")
            return [BasePage(text=text.strip(), page_number=1, section="Image OCR")]

        except Exception as e:
            logger.error(f"Image OCR failed for {path.name}: {e}")
            return []
