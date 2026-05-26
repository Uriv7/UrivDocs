"""UrivDocs — api/main.py"""
from __future__ import annotations
import asyncio, os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from api.routes import upload, query, documents
from api.schemas import HealthResponse
from vectorstore.store import VECTOR_STORE

_retriever = None
_llm       = None


def get_retriever():
    global _retriever
    if _retriever is None:
        from vectorstore.retriever import Retriever
        _retriever = Retriever()
    return _retriever


def get_llm():
    global _llm
    if _llm is None:
        from models.llm import LocalLLM
        _llm = LocalLLM()
    return _llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("UrivDocs starting — pre-warming models...")
    loop = asyncio.get_event_loop()

    # 1. Warm embedding model (CPU, run in thread pool)
    try:
        from ingestion.embedder import Embedder
        await loop.run_in_executor(None, Embedder.warmup)
        logger.info("✓ Embedding model ready")
    except Exception as e:
        logger.warning(f"Embedding warmup: {e}")

    # 2. Init vector store
    try:
        get_retriever()
        logger.info("✓ VectorStore ready")
    except Exception as e:
        logger.warning(f"VectorStore: {e}")

    # 3. Warm LLM — load model into Ollama RAM so first query is instant
    try:
        llm = get_llm()
        await llm.warmup()
        logger.info("✓ LLM model loaded into RAM")
    except Exception as e:
        logger.warning(f"LLM warmup: {e}")

    logger.info("✓ UrivDocs API ready — all models warm")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="UrivDocs API",
    description="Local AI document intelligence.",
    version="1.0.0",
    lifespan=lifespan,
)

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:4173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(query.router)
app.include_router(documents.router)


@app.get("/health", response_model=HealthResponse)
async def health():
    llm       = get_llm()
    retriever = get_retriever()
    try:    llm_ok    = await llm.health_check()
    except: llm_ok    = False
    try:    doc_count = len(retriever.list_sources())
    except: doc_count = 0
    return HealthResponse(
        status="ok",
        llm_available=llm_ok,
        vector_store=VECTOR_STORE,
        indexed_documents=doc_count,
    )


@app.get("/")
async def root():
    return {"app": "UrivDocs", "version": "1.0.0", "docs": "/docs"}
