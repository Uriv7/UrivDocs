"""UrivDocs — ingestion/parsers/csv_parser.py"""

import csv
from pathlib import Path
from typing import List

from loguru import logger

from ingestion.parsers.base import BasePage

ROWS_PER_PAGE = 50


class CSVParser:
    def parse(self, path: Path) -> List[BasePage]:
        pages: List[BasePage] = []

        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            buffer: List[str] = [" | ".join(headers)]
            page_num = 1

            for i, row in enumerate(reader, 1):
                line = " | ".join(str(v) for v in row.values())
                buffer.append(line)

                if len(buffer) >= ROWS_PER_PAGE:
                    pages.append(BasePage(
                        text="\n".join(buffer),
                        page_number=page_num,
                        section=f"Rows {page_num * ROWS_PER_PAGE - ROWS_PER_PAGE + 1}–{i}",
                    ))
                    buffer = [" | ".join(headers)]
                    page_num += 1

        if len(buffer) > 1:
            pages.append(BasePage(text="\n".join(buffer), page_number=page_num))

        logger.info(f"Extracted {len(pages)} pages from CSV")
        return pages
