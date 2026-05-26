"""UrivDocs — api/routes/query.py"""
from __future__ import annotations
import asyncio, json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger
from api.schemas import QueryRequest

router = APIRouter(prefix="/api", tags=["query"])

def _retriever():
    from api.main import get_retriever
    return get_retriever()

def _llm():
    from api.main import get_llm
    return get_llm()

@router.post("/ask")
async def ask(req: QueryRequest):
    loop = asyncio.get_event_loop()
    llm  = _llm()

    # For short follow-up questions, enrich retrieval query with last user message
    retrieval_query = req.question
    if req.history and len(req.question.split()) < 8:
        last_user = [m for m in req.history[-4:] if m.role == "user"]
        if last_user:
            retrieval_query = f"{last_user[-1].content} {req.question}"

    try:
        chunks = await loop.run_in_executor(
            None,
            lambda: _retriever().retrieve(
                retrieval_query,
                top_k=req.top_k,
                source_filter=req.source_filter,
            )
        )
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return JSONResponse({"answer": f"⚠️ Retrieval error: {e}. Please try again.", "sources": [], "model": llm.model})

    if not chunks:
        return JSONResponse({
            "answer": "I cannot find information about this in the uploaded documents. Please make sure you have uploaded a relevant document, or try rephrasing your question.",
            "sources": [],
            "model": llm.model,
        })

    from models.prompt_builder import build_rag_prompt
    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]
    prompt = build_rag_prompt(req.question, chunks, history=history_dicts)

    return StreamingResponse(
        _stream(prompt, chunks, llm),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )

async def _stream(prompt: str, chunks: list, llm):
    sources = [{k: v for k, v in c.items() if k != "embedding"} for c in chunks]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
    token_count = 0
    try:
        async for token in llm.stream(prompt):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
            token_count += 1
            if token_count % 10 == 0:
                await asyncio.sleep(0)
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
    logger.info(f"Streamed {token_count} tokens")
    yield "data: [DONE]\n\n"
