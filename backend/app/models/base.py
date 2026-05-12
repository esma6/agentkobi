"""
Tüm ORM modellerinin türediği Declarative Base.

SQLAlchemy 2.0 stili (Mapped/mapped_column) kullanıyoruz çünkü:
- Type hint'leri Pydantic'e doğrudan aktarılabiliyor
- Mypy/IDE desteği eski stilden çok daha iyi
- Resmi 2.0 yolu — eski stil deprecated yolda
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Tüm tablolar bunu miras alır. Alembic autogenerate bunu metadata olarak görür."""
    pass
