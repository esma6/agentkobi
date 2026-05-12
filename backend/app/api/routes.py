"""
REST endpoint'leri. PostgreSQL üzerinden async SQLAlchemy ile çalışır.

Eski CSV-tabanlı route'ları değiştirir. Mevcut frontend kontratı (alan adları,
sayfalama formatı) aynen korunmuştur — frontend tarafında değişiklik gerekmez.
"""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.models.orm import Customer, Order, Product, SupplierDraft
from app.schemas.api import (
    CustomerOut,
    DashboardStats,
    OrderOut,
    PaginatedCustomers,
    PaginatedOrders,
    PaginatedProducts,
    ProductOut,
    SupplierDraftOut,
)

router = APIRouter()

# CSV-tabanlı yapıdaki demo işletme — seed data ile uyumlu.
BUSINESS_ID = settings.DEMO_BUSINESS_ID

STATUS_TR = {
    "pending": "Beklemede",
    "confirmed": "Onaylandı",
    "preparing": "Hazırlanıyor",
    "shipped": "Kargoda",
    "delivered": "Teslim Edildi",
    "cancelled": "İptal",
}


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_session)):
    # Tek bir SELECT yerine birkaç küçük agreggate query — okunabilirlik için.
    # Bu boyutta (binlerce kayıt) performans farkı önemsiz.

    base_q = select(Order).where(Order.business_id == BUSINESS_ID)

    # Toplam sipariş
    total_orders = (await db.execute(
        select(func.count()).select_from(base_q.subquery())
    )).scalar_one()

    # Toplam ciro
    total_revenue = (await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            Order.business_id == BUSINESS_ID
        )
    )).scalar_one()

    # Status dağılımı (count)
    status_rows = (await db.execute(
        select(Order.status, func.count()).where(
            Order.business_id == BUSINESS_ID
        ).group_by(Order.status)
    )).all()
    status_counts_raw = {row[0]: row[1] for row in status_rows}

    # Status dağılımı (revenue)
    revenue_rows = (await db.execute(
        select(Order.status, func.sum(Order.total_amount)).where(
            Order.business_id == BUSINESS_ID
        ).group_by(Order.status)
    )).all()
    status_revenue_raw = {row[0]: float(row[1] or 0) for row in revenue_rows}

    active = sum(
        c for s, c in status_counts_raw.items() if s not in ("cancelled", "delivered")
    )
    shipped = status_counts_raw.get("shipped", 0)
    cancelled = status_counts_raw.get("cancelled", 0)

    # Kritik stok sayısı
    critical_count = (await db.execute(
        select(func.count()).select_from(
            select(Product).where(
                Product.business_id == BUSINESS_ID,
                Product.stock_quantity <= Product.reorder_threshold,
            ).subquery()
        )
    )).scalar_one()

    return DashboardStats(
        total_orders=total_orders,
        total_revenue=round(float(total_revenue), 2),
        active_orders=active,
        shipped_orders=shipped,
        cancelled_orders=cancelled,
        critical_stock_count=critical_count,
        status_distribution={STATUS_TR.get(k, k): v for k, v in status_counts_raw.items()},
        status_revenue={STATUS_TR.get(k, k): v for k, v in status_revenue_raw.items()},
    )


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@router.get("/orders", response_model=PaginatedOrders)
async def list_orders(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    q = select(Order).where(Order.business_id == BUSINESS_ID)
    if status:
        q = q.where(Order.status == status)

    # Toplam sayım (sayfalamadan önce)
    total = (await db.execute(
        select(func.count()).select_from(q.subquery())
    )).scalar_one()

    # Sayfalanmış veri
    q = q.order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()

    items = []
    for r in rows:
        item = OrderOut.model_validate(r)
        item.status_label = STATUS_TR.get(r.status, r.status)
        items.append(item)

    return PaginatedOrders(
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=items,
    )


# ---------------------------------------------------------------------------
# Products / Stock
# ---------------------------------------------------------------------------

@router.get("/products", response_model=PaginatedProducts)
async def list_products(
    low_stock: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    q = select(Product).where(Product.business_id == BUSINESS_ID)
    if low_stock:
        q = q.where(Product.stock_quantity <= Product.reorder_threshold)

    total = (await db.execute(
        select(func.count()).select_from(q.subquery())
    )).scalar_one()

    q = q.order_by(Product.name).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()

    items = []
    for r in rows:
        item = ProductOut.model_validate(r)
        item.is_critical = r.stock_quantity <= r.reorder_threshold
        items.append(item)

    return PaginatedProducts(
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=items,
    )


@router.get("/stock/critical")
async def critical_stock(db: AsyncSession = Depends(get_session)):
    q = select(Product).where(
        Product.business_id == BUSINESS_ID,
        Product.stock_quantity <= Product.reorder_threshold,
    ).order_by(Product.stock_quantity)
    rows = (await db.execute(q)).scalars().all()

    items = []
    for r in rows:
        eksik = max(0, r.reorder_threshold - r.stock_quantity)
        doluluk = (
            round(100 * r.stock_quantity / r.reorder_threshold, 1)
            if r.reorder_threshold > 0
            else 0.0
        )
        items.append({
            "id": r.id,
            "sku": r.sku,
            "name": r.name,
            "unit": r.unit,
            "stock_quantity": r.stock_quantity,
            "reorder_threshold": r.reorder_threshold,
            "eksik_miktar": eksik,
            "doluluk_yuzde": doluluk,
            "price": float(r.price),
        })
    return {"count": len(items), "items": items}


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

@router.get("/customers", response_model=PaginatedCustomers)
async def list_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    q = select(Customer).where(Customer.business_id == BUSINESS_ID)

    total = (await db.execute(
        select(func.count()).select_from(q.subquery())
    )).scalar_one()

    q = q.order_by(Customer.total_orders.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()

    return PaginatedCustomers(
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[CustomerOut.model_validate(r) for r in rows],
    )


# ---------------------------------------------------------------------------
# Supplier drafts
# ---------------------------------------------------------------------------

@router.get("/supplier-drafts")
async def list_supplier_drafts(db: AsyncSession = Depends(get_session)):
    q = select(SupplierDraft).where(SupplierDraft.business_id == BUSINESS_ID)
    rows = (await db.execute(q)).scalars().all()
    items = [SupplierDraftOut.model_validate(r).model_dump() for r in rows]
    return {"count": len(items), "items": items}


# ---------------------------------------------------------------------------
# Briefing (mevcut LangGraph workflow'una bağlı, değiştirmiyoruz)
# ---------------------------------------------------------------------------

class BriefingRequest(BaseModel):
    business_id: str = BUSINESS_ID
    business_name: str = "Demo İşletme"
    owner_name: str = "Demo Sahibi"
    trigger_source: str = "manual"


@router.post("/briefing/run")
async def run_briefing(req: BriefingRequest):
    try:
        from app.graph.orchestrator import run_workflow
        result = await run_workflow(
            business_id=req.business_id,
            business_name=req.business_name,
            owner_name=req.owner_name,
            trigger_source=req.trigger_source,
        )
        return {
            "ok": True,
            "briefing": result.get("briefing_final", ""),
            "used_fallback": result.get("used_fallback", False),
            "errors": result.get("errors", []),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
