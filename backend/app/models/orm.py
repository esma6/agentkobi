"""
ORM modelleri. CSV verisinin yapısıyla 1-1 eşleşir.

Önemli kararlar:
1. id'ler UUID — string olarak tutuyoruz çünkü mevcut CSV'lerde string UUID var
   ve PostgreSQL'in native UUID tipi yerine String(36) kullanmak, Alembic ve
   asyncpg ile en az sürtünme veriyor (özellikle demo için).
2. created_at/updated_at — TIMESTAMP WITHOUT TIME ZONE; Türkiye tek timezone'da
   olduğumuz için UTC dönüşümü demo için ek karmaşıklık.
3. Index'ler — business_id, status gibi sık filtrelenen alanlara index.
4. Relationships — şu an minimal; ihtiyaç doğdukça eklenecek.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Index,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Business(Base):
    """İşletme (KOBİ). Multi-tenant ayrımı için ana tablo."""
    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_customers_business_id", "business_id"),
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer, default=0)
    unit: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_products_business_id", "business_id"),
        Index("ix_products_sku", "sku"),
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id"), nullable=False
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=Decimal("0"))
    shipping_provider: Mapped[str | None] = mapped_column(String(64))
    tracking_number: Mapped[str | None] = mapped_column(String(64))
    shipping_status: Mapped[str | None] = mapped_column(String(64))
    estimated_delivery: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_orders_business_id", "business_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")

    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
    )


class SupplierDraft(Base):
    """LLM tarafından üretilen tedarikçi sipariş taslağı. Onay bekler."""
    __tablename__ = "supplier_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id"), nullable=False
    )
    product_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("products.id")
    )
    supplier_email: Mapped[str | None] = mapped_column(String(255))
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(512))
    body: Mapped[str | None] = mapped_column(Text)
    suggested_quantity: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        Index("ix_supplier_drafts_business_id", "business_id"),
        Index("ix_supplier_drafts_status", "status"),
    )
