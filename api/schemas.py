"""UrivDocs — api/schemas.py"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class SourceChunk(BaseModel):
    text: str
    source: str
    page_number: int
    section: str
    score: float
    chunk_index: int


class ChatMessage(BaseModel):
    role: str       # "user" or "assistant"
    content: str


class UploadResponse(BaseModel):
    filename: str
    chunks_indexed: int
    message: str


class QueryRequest(BaseModel):
    question: str
    source_filter: Optional[str] = None
    top_k: int = 5
    stream: bool = False
    history: List[ChatMessage] = []   # conversation history for follow-ups


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    model: str


class DocumentInfo(BaseModel):
    filename: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int


class DeleteResponse(BaseModel):
    message: str
    source: str


class HealthResponse(BaseModel):
    status: str
    llm_available: bool
    vector_store: str
    indexed_documents: int
