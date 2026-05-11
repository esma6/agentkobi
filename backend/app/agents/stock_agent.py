from __future__ import annotations

from typing import Any

from app.db.loader import products_df


async def run(business_id: str) -> list[dict[str, Any]]:
    """Return products at or below their reorder threshold."""
    products = products_df[products_df["business_id"] == business_id].copy()
    critical = products[products["stock_quantity"] <= products["reorder_threshold"]]
    critical = critical.sort_values(["stock_quantity", "name"], ascending=[True, True])

    alerts: list[dict[str, Any]] = []
    for _, row in critical.iterrows():
        current_quantity = float(row["stock_quantity"])
        reorder_threshold = float(row["reorder_threshold"])
        alerts.append(
            {
                "product_id": row["id"],
                "sku": row["sku"],
                "product_name": row["name"],
                "current_quantity": int(current_quantity)
                if current_quantity.is_integer()
                else current_quantity,
                "reorder_threshold": int(reorder_threshold)
                if reorder_threshold.is_integer()
                else reorder_threshold,
                "missing_quantity": max(reorder_threshold - current_quantity, 0),
                "unit": row["unit"],
            }
        )
    return alerts
