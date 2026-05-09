"""
FAISS vector store wrapper.

FAISS, Facebook'un C++ tabanlı yüksek performanslı
similarity search kütüphanesi. Disk'e .pkl ve .faiss dosyası
olarak kaydedilir, yeniden başlatmada yüklenir.

Tasarım kararı: tek bir global index yerine business_id başına
ayrı index tutulabilir; demo için tek index yeterli.
"""
from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS

from app.rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)

INDEX_DIR = Path(__file__).parent / "data" / "faiss_index"
INDEX_DIR.mkdir(parents=True, exist_ok=True)


def load_or_create_store() -> FAISS | None:
    """Disk'ten yükler; yoksa None döner (henüz ingest yapılmamış)."""
    emb = get_embeddings()
    index_file = INDEX_DIR / "index.faiss"
    if index_file.exists():
        try:
            return FAISS.load_local(
                str(INDEX_DIR),
                emb,
                allow_dangerous_deserialization=True,  # kendi yazdığımız index
            )
        except Exception as e:
            logger.warning("FAISS index yüklenemedi: %s", e)
            return None
    return None


def save_store(store: FAISS) -> None:
    store.save_local(str(INDEX_DIR))
    logger.info("FAISS index kaydedildi: %s", INDEX_DIR)


def create_store_from_texts(
    texts: list[str], metadatas: list[dict] | None = None
) -> FAISS:
    """Sıfırdan index oluşturur."""
    emb = get_embeddings()
    store = FAISS.from_texts(texts=texts, embedding=emb, metadatas=metadatas)
    save_store(store)
    return store
