"""UrivDocs — api/routes/documents.py"""

from fastapi import APIRouter, HTTPException

from api.schemas import DocumentListResponse, DocumentInfo, DeleteResponse
from vectorstore.retriever import Retriever
from vectorstore.indexer import Indexer

router = APIRouter(prefix="/api", tags=["documents"])

retriever = Retriever()
indexer = Indexer()


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    sources = retriever.list_sources()
    docs = [DocumentInfo(filename=s) for s in sources]
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/documents/{filename}", response_model=DeleteResponse)
async def delete_document(filename: str):
    sources = retriever.list_sources()
    if filename not in sources:
        raise HTTPException(404, f"Document '{filename}' not found in index")
    indexer.delete(filename)
    return DeleteResponse(message="Document removed from index", source=filename)
