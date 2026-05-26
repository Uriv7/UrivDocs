"""UrivDocs — tests/test_retrieval.py"""

import pytest
from unittest.mock import patch, MagicMock


def test_retriever_calls_store():
    with patch("vectorstore.retriever.get_store") as mock_store_factory, \
         patch("vectorstore.retriever.Embedder") as mock_embedder_cls:

        mock_store = MagicMock()
        mock_store.search.return_value = [{"text": "result", "score": 0.9, "source": "test.pdf", "page_number": 1, "section": "", "chunk_index": 0, "token_count": 50}]
        mock_store_factory.return_value = mock_store

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1] * 768
        mock_embedder_cls.return_value = mock_embedder

        from vectorstore.retriever import Retriever
        r = Retriever()
        results = r.retrieve("test query", top_k=3)

        mock_embedder.embed_query.assert_called_once_with("test query")
        mock_store.search.assert_called_once()
        assert len(results) == 1
        assert results[0]["source"] == "test.pdf"
