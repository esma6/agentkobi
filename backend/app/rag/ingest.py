"""
Geçmiş brifingleri DB'den çekip FAISS'a yükler.

Bu script standalone çalıştırılır:
    python -m app.rag.ingest

Demo için: briefings tablosu boşsa örnek seed brifingleri ekler.
"""
from __future__ import annotations

import asyncio
import logging

from app.rag.faiss_store import create_store_from_texts

logger = logging.getLogger(__name__)


# Demo amaçlı sentetik brifingler (DB henüz dolmamışsa kullanılır)
SEED_BRIEFINGS: list[tuple[str, dict]] = [
    (
        "Günaydın! Dün 8 yeni sipariş geldi. Bugün 3 paket hazırlanmalı. "
        "Stoklar normal seviyede. İyi günler!",
        {"orders": 8, "alerts": 0, "drafts": 0, "type": "moderate"},
    ),
    (
        "Günaydın! Dün 25 sipariş geldi, bugün 15 paket hazırlanmalı ve "
        "8 sipariş kargoya verilmeli. Domates stoğu kritik (20 kg). "
        "İyi günler!",
        {"orders": 25, "alerts": 1, "drafts": 0, "type": "busy"},
    ),
    (
        "Günaydın! Bugün takvim sakin: hazırlanacak paket veya kargoya "
        "verilecek sipariş yok. İyi günler!",
        {"orders": 0, "alerts": 0, "drafts": 0, "type": "quiet"},
    ),
    (
        "Günaydın! Dün 12 yeni sipariş geldi. Bugün 5 paket hazırlanmalı, "
        "3 sipariş kargoya verilmeli. Domates stoğu kritik (30 kg), "
        "tedarikçi e-postası sizi bekliyor. İyi günler!",
        {"orders": 12, "alerts": 1, "drafts": 1, "type": "actionable"},
    ),
]


async def ingest_from_db() -> int:
    """DB'den briefings çek; boşsa seed kullan."""
    try:
        from sqlalchemy import select

        from app.database import get_db
        from app.models import Briefing

        async with get_db() as db:
            result = await db.execute(
                select(Briefing.summary_text, Briefing.raw_data).limit(1000)
            )
            rows = result.all()

        if rows:
            texts = [r[0] for r in rows]
            metas = [r[1] if isinstance(r[1], dict) else {} for r in rows]
            create_store_from_texts(texts, metas)
            logger.info("DB'den %d brifing ingest edildi", len(rows))
            return len(rows)
    except Exception as e:
        logger.warning("DB'den ingest başarısız (%s), seed kullanılıyor", e)

    texts = [t for t, _ in SEED_BRIEFINGS]
    metas = [m for _, m in SEED_BRIEFINGS]
    create_store_from_texts(texts, metas)
    logger.info("Seed verisinden %d brifing ingest edildi", len(texts))
    return len(texts)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    n = asyncio.run(ingest_from_db())
    print(f"Ingest tamamlandı: {n} brifing")
