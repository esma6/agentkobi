from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd

from app.db.loader import orders_by_business_df


async def run(business_id: str) -> dict[str, Any]:
    """Return order counters for the daily briefing."""
    orders = orders_by_business_df[orders_by_business_df["business_id"] == business_id].copy()

    created_at = pd.to_datetime(orders["created_at"], errors="coerce")
    today = date.today()
    yesterday = today - timedelta(days=1)

    statuses = orders["status"].fillna("").str.lower()
    created_dates = created_at.dt.date

    active_orders = orders[~statuses.isin(["cancelled", "delivered"])]
    active_statuses = active_orders["status"].fillna("").str.lower()

    return {
        "new_orders_yesterday": int((created_dates == yesterday).sum()),
        "pending_to_prepare_today": int(active_statuses.isin(["pending", "confirmed"]).sum()),
        "ready_to_ship_today": int((active_statuses == "preparing").sum()),
    }
