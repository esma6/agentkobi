"""
Pydantic v2 şemaları. API'ye girip çıkan veriler için.

Neden ORM modelinden ayrı?
- ORM modeli DB'yi temsil eder (her şey görünür).
- API şeması dış dünyaya gösterilecek subset'i tanımlar (response için);
  validasyon yapar (request için).
- Bu ayrım sayesinde DB değişse bile public contract aynı kalabilir.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderOut(BaseModel):
    """Response: sipariş listeleme ve detay."""
    model_config = ConfigDict(from_attributes=True)  # ORM nesnesinden okuma

    id: str
    order_number: int
    business_id: str
    customer_id: str | None
    status: str
    status_label: str | None = None  # Türkçe etiket; route'ta dolduruyoruz
    total_amount: Decimal
    shipping_provider: str | None
    tracking_number: str | None
    shipping_status: str | None
    estimated_delivery: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PaginatedOrders(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: list[OrderOut]


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    sku: str
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int
    reorder_threshold: int
    unit: str | None
    is_critical: bool = False  # route'ta dolduruyoruz
    created_at: datetime


class PaginatedProducts(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: list[ProductOut]


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    name: str
    phone: str | None
    email: str | None
    address: str | None
    total_orders: int
    created_at: datetime


class PaginatedCustomers(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: list[CustomerOut]


class DashboardStats(BaseModel):
    total_orders: int
    total_revenue: float
    active_orders: int
    shipped_orders: int
    cancelled_orders: int
    critical_stock_count: int
    status_distribution: dict[str, int]
    status_revenue: dict[str, float]


class SupplierDraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    product_id: str | None
    supplier_email: str | None
    supplier_name: str | None
    subject: str | None
    body: str | None
    suggested_quantity: int | None
    estimated_cost: Decimal | None
    status: str
    created_at: datetime
    approved_at: datetime | None
    sent_at: datetime | None
