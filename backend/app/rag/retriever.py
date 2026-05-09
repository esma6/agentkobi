"""LangGraph node'undan çağrılan retrieval fonksiyonu."""
from __future__ import annotations

import logging

from app.rag.faiss_store import load_or_create_store

logger = logging.getLogger(__name__)


async def retrieve_similar_briefings(query: str, k: int = 3) -> list[str]:
    """
    Sorguya benzer geçmiş brifingleri döner.
    Index yoksa boş liste döner — graph akışı bozulmasın.
    """
    store = load_or_create_store()
    if store is None:
        logger.warning(
            "FAISS index henüz oluşturulmamış. "
            "Önce: python -m app.rag.ingest"
        )
        return []

    try:
        docs = store.similarity_search(query, k=k)
        return [d.page_content for d in docs]
    except Exception as e:
        logger.error("FAISS arama hatası: %s", e)
        return []
