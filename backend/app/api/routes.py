from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db.loader import (
    critical_df,
    drafts_by_business_df,
    orders_by_business_df,
    products_df,
)

try:
    from app.db.loader import customers_df
except ImportError:
    import pandas as pd
    from pathlib import Path
    _DATA = Path(__file__).parent.parent / "db"
    customers_df = pd.read_csv(_DATA / "customers.csv")

router = APIRouter()

BUSINESS_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

STATUS_TR = {
    "pending": "Beklemede",
    "confirmed": "Onaylandı",
    "preparing": "Hazırlanıyor",
    "shipped": "Kargoda",
    "delivered": "Teslim Edildi",
    "cancelled": "İptal",
}


def _nan_safe(val: Any) -> Any:
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def _row_to_dict(row: Any) -> dict:
    return {k: _nan_safe(v) for k, v in row.items()}


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

@router.get("/dashboard/stats")
async def dashboard_stats():
    orders = orders_by_business_df[
        orders_by_business_df["business_id"] == BUSINESS_ID
    ].copy()

    total_orders = len(orders)
    total_revenue = float(orders["total_amount"].sum())
    active_orders = orders[~orders["status"].isin(["cancelled", "delivered"])]
    shipped = orders[orders["status"] == "shipped"]
    cancelled = orders[orders["status"] == "cancelled"]

    status_counts = (
        orders["status"]
        .value_counts()
        .rename(STATUS_TR)
        .to_dict()
    )

    critical_count = len(critical_df)

    # Revenue by status for chart
    status_revenue = (
        orders.groupby("status")["total_amount"]
        .sum()
        .rename(index=STATUS_TR)
        .to_dict()
    )

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "active_orders": len(active_orders),
        "shipped_orders": len(shipped),
        "cancelled_orders": len(cancelled),
        "critical_stock_count": critical_count,
        "status_distribution": status_counts,
        "status_revenue": status_revenue,
    }


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@router.get("/orders")
async def list_orders(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    orders = orders_by_business_df[
        orders_by_business_df["business_id"] == BUSINESS_ID
    ].copy()

    if status:
        orders = orders[orders["status"] == status]

    orders = orders.sort_values("created_at", ascending=False)

    total = len(orders)
    start = (page - 1) * per_page
    end = start + per_page
    page_data = orders.iloc[start:end]

    items = [_row_to_dict(row) for _, row in page_data.iterrows()]
    for item in items:
        item["status_label"] = STATUS_TR.get(item.get("status", ""), item.get("status", ""))

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page),
        "items": items,
    }


# ---------------------------------------------------------------------------
# Products / Stock
# ---------------------------------------------------------------------------

@router.get("/products")
async def list_products(
    low_stock: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    prods = products_df[
        products_df["business_id"] == BUSINESS_ID
    ].copy()

    prods["is_critical"] = prods["stock_quantity"] <= prods["reorder_threshold"]

    if low_stock:
        prods = prods[prods["is_critical"]]

    total = len(prods)
    start = (page - 1) * per_page
    end = start + per_page
    page_data = prods.iloc[start:end]

    items = [_row_to_dict(row) for _, row in page_data.iterrows()]
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page),
        "items": items,
    }


@router.get("/stock/critical")
async def critical_stock():
    items = [_row_to_dict(row) for _, row in critical_df.iterrows()]
    return {"count": len(items), "items": items}


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

@router.get("/customers")
async def list_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    custs = customers_df[
        customers_df["business_id"] == BUSINESS_ID
    ].copy()
    custs = custs.sort_values("total_orders", ascending=False)

    total = len(custs)
    start = (page - 1) * per_page
    end = start + per_page
    page_data = custs.iloc[start:end]

    items = [_row_to_dict(row) for _, row in page_data.iterrows()]
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page),
        "items": items,
    }


# ---------------------------------------------------------------------------
# Supplier drafts
# ---------------------------------------------------------------------------

@router.get("/supplier-drafts")
async def list_supplier_drafts():
    drafts = drafts_by_business_df[
        drafts_by_business_df["business_id"] == BUSINESS_ID
    ] if "business_id" in drafts_by_business_df.columns else drafts_by_business_df
    items = [_row_to_dict(row) for _, row in drafts.iterrows()]
    return {"count": len(items), "items": items}


# ---------------------------------------------------------------------------
# Briefing
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
