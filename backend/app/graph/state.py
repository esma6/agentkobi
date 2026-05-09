"""
LangGraph için merkezi state tanımı.

Her node bu state'in bir kısmını okur, bir kısmını günceller.
TypedDict + Annotated[..., operator.add] kullanımı:
  - Annotated[list, operator.add]  -> reducer: yeni listeyi mevcuda ekler
  - Diğer alanlar  -> son yazan kazanır (overwrite semantics)

Tasarım kararı: Tek bir AgentState yerine "shared bus" pattern.
Her ajanın çıktısı state'in farklı bir alanına yazılır; orkestratör
bunları birleştirir. Bu, ajanlar arası gevşek bağ (loose coupling)
sağlar.
"""
from __future__ import annotations

import operator
from datetime import date
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    # --- Girdi ---
    business_id: str
    business_name: str
    owner_name: str
    trigger_source: str  # "cron" | "manual" | "test"
    briefing_date: date

    # --- Ajan çıktıları (her biri kendi node'u tarafından doldurulur) ---
    order_data: dict[str, Any]
    stock_data: list[dict[str, Any]]
    shipping_data: dict[str, Any]
    supplier_drafts: list[dict[str, Any]]
    customer_signals: dict[str, Any]

    # --- RAG sonuçları (tarihsel benzer brifingler) ---
    rag_context: list[str]

    # --- LLM çıktısı ---
    briefing_draft: str       # ham LLM çıktısı
    briefing_final: str       # validator'dan geçmiş final metin
    used_fallback: bool       # template fallback'e düştü mü?

    # --- Hata/log akışı (reducer ile biriktirilir) ---
    errors: Annotated[list[str], operator.add]
    trace: Annotated[list[dict[str, Any]], operator.add]

    # --- Kontrol bayrakları ---
    is_quiet_day: bool
    requires_human_review: bool
