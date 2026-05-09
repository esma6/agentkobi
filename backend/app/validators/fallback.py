"""
Deterministik şablon brifing üretici.

Validator fail ettiğinde veya LLM tamamen down olduğunda devreye girer.
LLM kullanmaz — saf string formatlama. Asla halüsinasyon yapmaz.
"""
from __future__ import annotations


def render_template_briefing(
    order_data: dict,
    stock_data: list[dict],
    supplier_drafts: list[dict],
) -> str:
    parts: list[str] = ["Günaydın!"]

    new_orders = (order_data or {}).get("new_orders_yesterday", 0)
    to_prep = (order_data or {}).get("pending_to_prepare_today", 0)
    to_ship = (order_data or {}).get("ready_to_ship_today", 0)

    if new_orders:
        parts.append(f"Dün {new_orders} yeni sipariş geldi.")
    if to_prep or to_ship:
        if to_prep and to_ship:
            parts.append(
                f"Bugün {to_prep} paket hazırlanmalı, "
                f"{to_ship} sipariş kargoya verilmeli."
            )
        elif to_prep:
            parts.append(f"Bugün {to_prep} paket hazırlanmalı.")
        else:
            parts.append(f"Bugün {to_ship} sipariş kargoya verilmeli.")

    if stock_data:
        first = stock_data[0]
        parts.append(
            f"{first.get('product_name', 'Bir ürün')} stoğu kritik "
            f"({first.get('current_quantity', '?')} {first.get('unit', '')})."
        )

    if supplier_drafts:
        parts.append("Tedarikçi taslakları onayınızı bekliyor.")

    if len(parts) == 1:
        # hiç içerik yok
        return (
            "Günaydın! Bugün takvim sakin: hazırlanacak paket veya "
            "kargoya verilecek sipariş yok, stoklar da yerinde. İyi günler!"
        )

    parts.append("İyi günler!")
    return " ".join(parts)
