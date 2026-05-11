from __future__ import annotations

from typing import Any

from app.db.loader import drafts_by_business_df


async def run(business_id: str) -> list[dict[str, Any]]:
    """Return supplier drafts waiting for approval."""
    drafts = drafts_by_business_df[drafts_by_business_df["business_id"] == business_id].copy()

    pending = drafts[drafts["status"].fillna("").str.lower() == "pending"]
    pending = pending.sort_values("created_at", ascending=False)

    fields = [
        "id",
        "product_id",
        "product_name",
        "unit",
        "supplier_email",
        "supplier_name",
        "subject",
        "body",
        "suggested_quantity",
        "estimated_cost",
        "status",
        "created_at",
    ]
    existing_fields = [field for field in fields if field in pending.columns]
    return pending[existing_fields].to_dict(orient="records")
