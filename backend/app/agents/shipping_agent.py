from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.db.loader import orders_by_business_df


async def run(business_id: str) -> dict[str, Any]:
    """Return shipping workload and delayed shipment signals."""
    orders = orders_by_business_df[orders_by_business_df["business_id"] == business_id].copy()

    statuses = orders["status"].fillna("").str.lower()
    shipping_statuses = orders["shipping_status"].fillna("").str.lower()
    estimated_delivery = pd.to_datetime(orders["estimated_delivery"], errors="coerce").dt.date
    today = date.today()

    to_ship_mask = statuses == "preparing"
    in_transit_mask = statuses.eq("shipped") & ~shipping_statuses.eq("teslim_edildi")
    delayed_mask = in_transit_mask & estimated_delivery.notna() & (estimated_delivery < today)

    delayed_orders = orders[delayed_mask]

    return {
        "to_ship": int(to_ship_mask.sum()),
        "in_transit": int(in_transit_mask.sum()),
        "delayed": int(delayed_mask.sum()),
        "delayed_orders": delayed_orders[
            [
                "id",
                "order_number",
                "shipping_provider",
                "tracking_number",
                "shipping_status",
                "estimated_delivery",
            ]
        ].to_dict(orient="records"),
    }
