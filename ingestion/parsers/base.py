"""Shared data types for all parsers."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BasePage:
    """A single extracted page / section from a document."""
    text: str
    page_number: int = 0
    section: Optional[str] = None
    extra: dict = field(default_factory=dict)
