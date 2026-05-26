"""UrivDocs — tests/test_api.py"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.fixture
async def client():
    from api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_root(client):
    res = await client.get("/")
    assert res.status_code == 200
    assert res.json()["app"] == "UrivDocs"


@pytest.mark.asyncio
async def test_list_documents_empty(client):
    with patch("api.routes.documents.retriever") as mock_r:
        mock_r.list_sources.return_value = []
        res = await client.get("/api/documents")
        assert res.status_code == 200
        assert res.json()["total"] == 0


@pytest.mark.asyncio
async def test_ask_no_chunks(client):
    with patch("api.routes.query.retriever") as mock_r, \
         patch("api.routes.query.llm") as mock_llm:
        mock_r.retrieve.return_value = []
        mock_llm.model = "llama3"
        res = await client.post("/api/ask", json={"question": "What is this?"})
        assert res.status_code == 200
        assert "No relevant content" in res.json()["answer"]
