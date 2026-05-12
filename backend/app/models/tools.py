from langchain_core.tools import tool
import pandas as pd

from app.db.loader import orders_df, products_df, critical_df, drafts_df, customers_df

@tool
def get_order_by_number(order_number: int) -> dict:
    """Sipariş numarasına göre sipariş detayını getirir."""
    row = orders_df[orders_df["order_number"] == order_number]
    if row.empty:
        return {"error": f"#{order_number} numaralı sipariş bulunamadı."}
    return row.iloc[0].to_dict()

@tool
def get_orders_by_status(status: str) -> list:
    """Belirli bir durumdaki siparişleri listeler.
    status: pending, confirmed, preparing, shipped, delivered, cancelled
    """
    rows = orders_df[orders_df["status"] == status]
    return rows[["order_number","customer_name","total_amount","products_summary"]].to_dict("records")

@tool
def get_critical_stock() -> list:
    """Stoğu kritik eşiğin altında olan ürünleri listeler."""
    return critical_df.to_dict("records")

@tool
def get_delayed_shipments() -> list:
    """Gecikmiş veya sorunlu kargo durumundaki siparişleri getirir."""
    delayed = orders_df[orders_df["shipping_status"] == "şubede_beklemede"]
    return delayed[["order_number","customer_name","customer_phone",
                     "tracking_number","estimated_delivery","products_summary"]].to_dict("records")

@tool
def get_pending_drafts() -> list:
    """Onay bekleyen tedarikçi sipariş taslaklarını getirir."""
    return drafts_df[drafts_df["status"] == "pending"].to_dict("records")

@tool
def get_daily_summary() -> dict:
    """Sabah brifingi için günlük özet üretir."""
    from datetime import date, timedelta
    yesterday = str(date.today() - timedelta(days=1))
    
    new_orders     = len(orders_df[orders_df["created_at"].str.startswith(yesterday)])
    to_prepare     = len(orders_df[orders_df["status"] == "confirmed"])
    ready_to_ship  = len(orders_df[orders_df["status"] == "preparing"])
    delayed        = len(orders_df[orders_df["shipping_status"] == "şubede_beklemede"])
    critical_count = len(critical_df)
    pending_drafts = len(drafts_df[drafts_df["status"] == "pending"])

    return {
        "new_orders_yesterday": new_orders,
        "to_prepare_today": to_prepare,
        "ready_to_ship_today": ready_to_ship,
        "delayed_shipments": delayed,
        "critical_stock_count": critical_count,
        "pending_supplier_drafts": pending_drafts,
    }

@tool
def get_customer_details(customer_id: str) -> dict:
    """Müşteri ID'sine göre müşteri bilgilerini getirir."""
    row = customers_df[customers_df["id"] == customer_id]
    if row.empty:
        return {"error": f"Müşteri bulunamadı."}
    return row.iloc[0].to_dict()

@tool
def get_customer_orders(phone: str) -> list:
    """Müşteri telefon numarasına göre geçmiş siparişlerini listeler."""
    rows = orders_df[orders_df["customer_phone"] == phone]
    return rows[["order_number", "status", "total_amount", "products_summary", "created_at"]].to_dict("records")

@tool
def get_product_details(sku: str) -> dict:
    """SKU'ya göre ürün detaylarını getirir."""
    row = products_df[products_df["sku"] == sku]
    if row.empty:
        return {"error": f"Ürün bulunamadı."}
    return row.iloc[0].to_dict()

@tool
def get_orders_by_date_range(start_date: str, end_date: str) -> list:
    """Belirli bir tarih aralığındaki siparişleri listeler. Format: YYYY-MM-DD"""
    orders_df["created_at_dt"] = pd.to_datetime(orders_df["created_at"])
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date) + pd.Timedelta(days=1)
    mask = (orders_df["created_at_dt"] >= start) & (orders_df["created_at_dt"] < end)
    rows = orders_df[mask]
    return rows[["order_number", "customer_name", "total_amount", "status", "created_at"]].to_dict("records")

@tool
def get_draft_details(draft_id: str) -> dict:
    """Tedarikçi taslak ID'sine göre detay getirir."""
    row = drafts_df[drafts_df["id"] == draft_id]
    if row.empty:
        return {"error": f"Taslak bulunamadı."}
    return row.iloc[0].to_dict()

@tool
def get_top_selling_products(limit: int = 5) -> list:
    """En çok satan ürünleri listeler (sipariş sayısına göre)."""
    all_products = []
    for summary in orders_df["products_summary"].dropna():
        parts = summary.split(", ")
        for part in parts:
            if "(" in part:
                name = part.split("(")[0].strip()
                all_products.append(name)
    
    from collections import Counter
    counts = Counter(all_products)
    top = counts.most_common(limit)
    return [{"product_name": k, "sales_count": v} for k, v in top]

@tool
def calculate_revenue(days: int = 30) -> dict:
    """Son X gün için toplam ciroyu hesaplar."""
    from datetime import date, timedelta
    orders_df["created_at_dt"] = pd.to_datetime(orders_df["created_at"])
    since = pd.to_datetime(date.today() - timedelta(days=days))
    recent = orders_df[orders_df["created_at_dt"] >= since]
    total = recent["total_amount"].sum()
    return {"period_days": days, "total_revenue": float(total), "order_count": len(recent)}

@tool
def get_low_stock_products(threshold: int = 20) -> list:
    """Stok miktarı belirtilen eşiğin altında olan ürünleri listeler."""
    low = products_df[products_df["stock_quantity"] < threshold]
    return low[["sku", "name", "stock_quantity", "unit"]].to_dict("records")