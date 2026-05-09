"""
Halüsinasyon önleme katmanı.

LLM'in ürettiği brifing metnindeki sayıların payload'da gerçekten
var olup olmadığını doğrular. "Dün 12 sipariş" diyorsa payload'da
12 olmalı; LLM 15 uydurmuşsa fail.

Tasarım: kapsayıcı (permissive) doğrulama. Tüm sayıları kontrol
etmiyoruz — sadece "anlamlı" sayılar (siparişler, stok miktarları).
Tarih/saat sayıları (08:00, 2026) whitelist ile geçilir.
"""
from __future__ import annotations

from app.validators.number_extractor import extract_numbers

# Brifingde geçmesi normal olan sabit sayılar (saat, yıl vs.)
WHITELIST_NUMBERS: set[float] = {0, 1, 8, 24, 2025, 2026}


def _payload_numbers(payload: dict) -> set[float]:
    """Payload'dan brifingde geçebilecek tüm sayıları toplar."""
    nums: set[float] = set()
    od = payload.get("order_data", {}) or {}
    for k in (
        "new_orders_yesterday",
        "pending_to_prepare_today",
        "ready_to_ship_today",
    ):
        if k in od and od[k] is not None:
            nums.add(float(od[k]))
    if "total_revenue_yesterday" in od and od["total_revenue_yesterday"]:
        nums.add(float(od["total_revenue_yesterday"]))

    for s in payload.get("stock_data", []) or []:
        if "current_quantity" in s:
            nums.add(float(s["current_quantity"]))
        if "threshold" in s:
            nums.add(float(s["threshold"]))

    for d in payload.get("supplier_drafts", []) or []:
        if d.get("suggested_quantity"):
            nums.add(float(d["suggested_quantity"]))

    return nums


def validate_briefing(
    text: str, payload: dict
) -> tuple[bool, list[str]]:
    """
    Returns: (is_valid, reasons_if_invalid)
    """
    reasons: list[str] = []

    # 1. Boş veya çok kısa metin
    if not text or len(text.strip()) < 20:
        reasons.append("text_too_short")
        return False, reasons

    # 2. Çok uzun metin (WhatsApp limiti)
    if len(text) > 700:
        reasons.append(f"text_too_long:{len(text)}")
        return False, reasons

    # 3. "Günaydın" ile başlamıyor
    if not text.strip().startswith("Günaydın"):
        reasons.append("missing_greeting")
        # bu kritik değil, geçebilir; ama loglayalım

    # 4. Sayı kontrolü — halüsinasyon
    extracted = extract_numbers(text)
    allowed = _payload_numbers(payload) | WHITELIST_NUMBERS
    hallucinated = extracted - allowed
    if hallucinated:
        reasons.append(
            f"hallucinated_numbers:{sorted(hallucinated)}"
        )
        return False, reasons

    return (len([r for r in reasons if not r.startswith("missing_greeting")]) == 0), reasons
