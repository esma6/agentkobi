"""
Async SQLAlchemy oturum yöneticisi.

Neden async?
- FastAPI native async; senkron driver kullanırsak event loop'u bloklarız.
- asyncpg, Python'un en hızlı Postgres sürücüsü (psycopg2'den ~3x).
- LangGraph node'ları da async — tutarlılık.

Pattern:
- engine: process başına 1 (singleton)
- AsyncSessionLocal: factory; her istekte yeni session
- get_session: FastAPI Depends için generator
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# echo=False üretimde; debug için True yapabilirsin
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # ölü bağlantıları otomatik temizle
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # commit sonrası nesneler hala kullanılabilir
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency. Her istek için tek bir session.

    Kullanım:
        @router.get("/...")
        async def handler(db: AsyncSession = Depends(get_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        # commit'i endpoint'in kendisi yapar (gerekirse)
