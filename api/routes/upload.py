"""UrivDocs — api/routes/upload.py
Files are saved locally for ingestion, then uploaded to S3 for persistent storage.
If S3 is not configured, local storage is used (works out of the box).
"""
from __future__ import annotations
import asyncio, os, uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from loguru import logger
from api.schemas import UploadResponse

router = APIRouter(prefix="/api", tags=["upload"])

UPLOAD_DIR    = Path(os.getenv("UPLOAD_DIR", "./storage/uploads"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 2048))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ingestion_status: dict[str, dict] = {}
_loader  = None
_indexer = None


def _get_loader():
    global _loader
    if _loader is None:
        from ingestion.loader import DocumentLoader
        _loader = DocumentLoader()
    return _loader


def _get_indexer():
    global _indexer
    if _indexer is None:
        from vectorstore.indexer import Indexer
        _indexer = Indexer()
    return _indexer


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    filename = file.filename or f"upload_{uuid.uuid4()}"
    dest     = UPLOAD_DIR / filename

    # Stream to disk
    size = 0
    with open(dest, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            size += len(chunk)

    size_mb = size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        dest.unlink()
        raise HTTPException(413, f"File too large ({size_mb:.1f} MB). Max {MAX_UPLOAD_MB} MB.")

    logger.info(f"Saved '{filename}' ({size_mb:.2f} MB) — queuing ingestion")
    ingestion_status[filename] = {"status": "processing", "chunks": 0, "size_mb": round(size_mb, 2)}

    background_tasks.add_task(_ingest_background, dest, filename)

    return UploadResponse(
        filename=filename,
        chunks_indexed=0,
        message=f"File uploaded ({size_mb:.1f} MB). Indexing in background.",
    )


@router.get("/upload/status/{filename}")
async def ingestion_status_check(filename: str):
    return ingestion_status.get(filename, {"status": "not_found"})


async def _ingest_background(path: Path, filename: str):
    loop = asyncio.get_event_loop()
    try:
        # 1. Upload to S3 (non-blocking)
        try:
            from storage_s3 import upload_to_s3, USE_S3
            if USE_S3:
                await loop.run_in_executor(None, upload_to_s3, path, filename)
        except Exception as e:
            logger.warning(f"S3 upload skipped: {e}")

        # 2. Ingest locally (parse + embed + index)
        count = await loop.run_in_executor(None, _ingest_sync, path, filename)
        ingestion_status[filename] = {"status": "done", "chunks": count}
        logger.info(f"✓ Indexed '{filename}' — {count} chunks")
    except Exception as e:
        ingestion_status[filename] = {"status": "error", "error": str(e)}
        logger.error(f"Ingestion failed '{filename}': {e}")
        import traceback
        logger.debug(traceback.format_exc())


def _ingest_sync(path: Path, filename: str) -> int:
    loader  = _get_loader()
    indexer = _get_indexer()
    chunks  = loader.load(path, original_filename=filename)
    return indexer.index(chunks)
