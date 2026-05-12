"""
Seed script — mevcut CSV dosyalarını PostgreSQL'e yükler.
"""
from __future__ import annotations

import asyncio
import math
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy import delete

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.orm import (
    Business,
    Customer,
    Order,
    OrderItem,
    Product,
    SupplierDraft,
)

CSV_DIR = Path(__file__).parent.parent  # app/db/


def _none_if_nan(v):
    """Pandas NaN -> Python None; string 'nan'/'' -> None."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, str) and v.strip().lower() in ("nan", ""):
        return None
    return v


def _s(v):
    """Güvenli string. Pandas bazı sütunları (örn. telefon) int olarak okur;
    SQLAlchemy VARCHAR bekleyince hata verir. Bu helper int/float -> str eder.
    NaN ve boş -> None."""
    v = _none_if_nan(v)
    if v is None:
        return None
    # float (Pandas NaN olmayan sayısal hücreler) -> int'e benzet, sonra string
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _i(v, default=0):
    """Güvenli integer. NaN -> default."""
    v = _none_if_nan(v)
    if v is None:
        return default
    return int(v)


def _dec(v, default=Decimal("0")):
    """Güvenli Decimal. NaN -> default."""
    v = _none_if_nan(v)
    if v is None:
        return default
    return Decimal(str(v))


def _parse_dt(v):
    v = _none_if_nan(v)
    if v is None:
        return None
    try:
        return datetime.fromisoformat(str(v))
    except ValueError:
        return None


async def seed():
    print(">> Seed başlıyor...")
    async with AsyncSessionLocal() as db:
        # 1. Tabloları temizle (FK sırasına dikkat: önce çocuklar)
        print(">> Mevcut veriler temizleniyor...")
        for model in (
            SupplierDraft,
            OrderItem,
            Order,
            Product,
            Customer,
            Business,
        ):
            await db.execute(delete(model))
        await db.commit()

        # 2. Business kaydını ekle (CSV'de yok ama FK için gerekli)
        print(">> Demo business ekleniyor...")
        db.add(Business(
            id=settings.DEMO_BUSINESS_ID,
            name="Demo İşletme",
            owner_name="Demo Sahibi",
        ))
        await db.commit()

        # 3. Customers
        print(">> Müşteriler yükleniyor...")
        cust_df = pd.read_csv(CSV_DIR / "customers.csv", dtype=str, keep_default_na=False)
        # dtype=str: tüm sütunları string olarak oku (telefon int'e çevrilmesin)
        # keep_default_na=False: "NA" string'ini NaN olarak yorumlama
        for _, row in cust_df.iterrows():
            db.add(Customer(
                id=_s(row["id"]),
                business_id=_s(row["business_id"]),
                name=_s(row["name"]),
                phone=_s(row.get("phone")),
                email=_s(row.get("email")),
                address=_s(row.get("address")),
                total_orders=_i(row.get("total_orders"), 0),
                created_at=_parse_dt(row.get("created_at")) or datetime.utcnow(),
            ))
        await db.commit()
        print(f"   {len(cust_df)} müşteri eklendi.")

        # 4. Products
        print(">> Ürünler yükleniyor...")
        prod_df = pd.read_csv(CSV_DIR / "products.csv", dtype=str, keep_default_na=False)
        for _, row in prod_df.iterrows():
            db.add(Product(
                id=_s(row["id"]),
                business_id=_s(row["business_id"]),
                sku=_s(row["sku"]),
                name=_s(row["name"]),
                description=_s(row.get("description")),
                price=_dec(row["price"]),
                stock_quantity=_i(row.get("stock_quantity"), 0),
                reorder_threshold=_i(row.get("reorder_threshold"), 0),
                unit=_s(row.get("unit")),
                created_at=_parse_dt(row.get("created_at")) or datetime.utcnow(),
            ))
        await db.commit()
        print(f"   {len(prod_df)} ürün eklendi.")

        # 5. Orders
        print(">> Siparişler yükleniyor...")
        ord_df = pd.read_csv(CSV_DIR / "orders.csv", dtype=str, keep_default_na=False)
        for _, row in ord_df.iterrows():
            db.add(Order(
                id=_s(row["id"]),
                order_number=_i(row["order_number"]),
                business_id=_s(row["business_id"]),
                customer_id=_s(row.get("customer_id")),
                status=_s(row["status"]),
                total_amount=_dec(row.get("total_amount")),
                shipping_provider=_s(row.get("shipping_provider")),
                tracking_number=_s(row.get("tracking_number")),
                shipping_status=_s(row.get("shipping_status")),
                estimated_delivery=_parse_dt(row.get("estimated_delivery")),
                notes=_s(row.get("notes")),
                created_at=_parse_dt(row.get("created_at")) or datetime.utcnow(),
                updated_at=_parse_dt(row.get("updated_at")) or datetime.utcnow(),
            ))
        await db.commit()
        print(f"   {len(ord_df)} sipariş eklendi.")

        # 6. Order items
        print(">> Sipariş kalemleri yükleniyor...")
        oi_df = pd.read_csv(CSV_DIR / "order_items.csv", dtype=str, keep_default_na=False)
        for _, row in oi_df.iterrows():
            db.add(OrderItem(
                id=_s(row["id"]),
                order_id=_s(row["order_id"]),
                product_id=_s(row["product_id"]),
                quantity=_i(row["quantity"]),
                unit_price=_dec(row["unit_price"]),
                subtotal=_dec(row["subtotal"]),
            ))
        await db.commit()
        print(f"   {len(oi_df)} sipariş kalemi eklendi.")

        # 7. Supplier drafts
        print(">> Tedarikçi taslakları yükleniyor...")
        sd_df = pd.read_csv(CSV_DIR / "supplier_drafts.csv", dtype=str, keep_default_na=False)
        for _, row in sd_df.iterrows():
            sq_raw = _none_if_nan(row.get("suggested_quantity"))
            ec_raw = _none_if_nan(row.get("estimated_cost"))
            db.add(SupplierDraft(
                id=_s(row["id"]),
                business_id=_s(row["business_id"]),
                product_id=_s(row.get("product_id")),
                supplier_email=_s(row.get("supplier_email")),
                supplier_name=_s(row.get("supplier_name")),
                subject=_s(row.get("subject")),
                body=_s(row.get("body")),
                suggested_quantity=int(sq_raw) if sq_raw is not None else None,
                estimated_cost=Decimal(str(ec_raw)) if ec_raw is not None else None,
                status=_s(row.get("status")) or "pending",
                created_at=_parse_dt(row.get("created_at")) or datetime.utcnow(),
                approved_at=_parse_dt(row.get("approved_at")),
                sent_at=_parse_dt(row.get("sent_at")),
            ))
        await db.commit()
        print(f"   {len(sd_df)} taslak eklendi.")

    print(">> Seed tamamlandı. ✅")


if __name__ == "__main__":
    asyncio.run(seed())
