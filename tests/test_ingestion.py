"""UrivDocs — tests/test_ingestion.py"""

import tempfile
from pathlib import Path

import pytest
from ingestion.chunker import Chunker
from ingestion.parsers.base import BasePage
from ingestion.parsers.generic import GenericTextParser


def test_chunker_short_text():
    chunker = Chunker()
    pages = [BasePage(text="Hello world", page_number=1)]
    chunks = chunker.chunk(pages, source="test.txt")
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Hello world"
    assert chunks[0]["source"] == "test.txt"
    assert chunks[0]["page_number"] == 1


def test_chunker_long_text_produces_multiple_chunks():
    chunker = Chunker()
    long_text = "word " * 1000
    pages = [BasePage(text=long_text, page_number=1)]
    chunks = chunker.chunk(pages, source="long.txt")
    assert len(chunks) > 1


def test_chunker_preserves_metadata():
    chunker = Chunker()
    pages = [BasePage(text="Some text", page_number=5, section="Introduction")]
    chunks = chunker.chunk(pages, source="doc.pdf")
    assert chunks[0]["page_number"] == 5
    assert chunks[0]["section"] == "Introduction"


def test_generic_parser_reads_txt():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("This is a test document.\nIt has two lines.")
        path = Path(f.name)

    parser = GenericTextParser()
    pages = parser.parse(path)
    assert len(pages) >= 1
    assert "test document" in pages[0].text
    path.unlink()


def test_chunk_ids_are_unique():
    chunker = Chunker()
    pages = [BasePage(text="word " * 200, page_number=1)]
    chunks = chunker.chunk(pages, source="test.txt")
    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids))
