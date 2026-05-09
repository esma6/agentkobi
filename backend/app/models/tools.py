from langchain_core.tools import tool

from app.db.loader import orders_df, products_df, critical_df, drafts_df

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