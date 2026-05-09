"""
LangGraph node fonksiyonları.

Her node:
  1. State'ten ihtiyacı olanı okur
  2. İlgili ajanı/servisi çağırır
  3. State'e yeni alan(lar) yazıp döner

Node'lar saf fonksiyondur (state in -> state out). Yan etkiler
(DB yazma, mesaj gönderme) servis katmanına delege edilir.

Utku'nun ajanları (`app.agents.*`) bu modülden çağrılır.
Henüz hazır değillerse stub döndürürler — graph yine de uçtan uca akar.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def _trace(node_name: str, **details: Any) -> dict[str, Any]:
    return {
        "node": node_name,
        "ts": datetime.utcnow().isoformat(),
        **details,
    }


# --------------------------------------------------------------------------
# Ajan node'ları
# --------------------------------------------------------------------------

async def order_node(state: AgentState) -> dict[str, Any]:
    """Sipariş ajanını çağırır, order_data alanını günceller."""
    try:
        from app.agents.order_agent import run as run_order_agent
        result = await run_order_agent(state["business_id"])
    except (ImportError, AttributeError):
        logger.warning("order_agent henüz hazır değil, stub döndürülüyor")
        result = {
            "new_orders_yesterday": 0,
            "pending_to_prepare_today": 0,
            "ready_to_ship_today": 0,
        }
    return {
        "order_data": result,
        "trace": [_trace("order_node", count=result.get("new_orders_yesterday"))],
    }


async def stock_node(state: AgentState) -> dict[str, Any]:
    try:
        from app.agents.stock_agent import run as run_stock_agent
        result = await run_stock_agent(state["business_id"])
    except (ImportError, AttributeError):
        logger.warning("stock_agent henüz hazır değil, stub döndürülüyor")
        result = []
    return {
        "stock_data": result,
        "trace": [_trace("stock_node", alerts=len(result))],
    }


async def shipping_node(state: AgentState) -> dict[str, Any]:
    try:
        from app.agents.shipping_agent import run as run_shipping_agent
        result = await run_shipping_agent(state["business_id"])
    except (ImportError, AttributeError):
        result = {"to_ship": 0, "delayed": 0}
    return {
        "shipping_data": result,
        "trace": [_trace("shipping_node")],
    }


async def supplier_node(state: AgentState) -> dict[str, Any]:
    try:
        from app.agents.supplier_agent import run as run_supplier_agent
        result = await run_supplier_agent(state["business_id"])
    except (ImportError, AttributeError):
        result = []
    return {
        "supplier_drafts": result,
        "trace": [_trace("supplier_node", drafts=len(result))],
    }


# --------------------------------------------------------------------------
# RAG node
# --------------------------------------------------------------------------

async def rag_node(state: AgentState) -> dict[str, Any]:
    """Geçmiş benzer brifingleri vector store'dan çeker."""
    from app.rag.retriever import retrieve_similar_briefings

    query = (
        f"siparişler:{state.get('order_data', {}).get('new_orders_yesterday', 0)} "
        f"stok_uyarisi:{len(state.get('stock_data', []))} "
        f"taslak:{len(state.get('supplier_drafts', []))}"
    )
    docs = await retrieve_similar_briefings(query, k=3)
    return {
        "rag_context": docs,
        "trace": [_trace("rag_node", retrieved=len(docs))],
    }


# --------------------------------------------------------------------------
# Aggregator + LLM (briefing) node
# --------------------------------------------------------------------------

def aggregator_node(state: AgentState) -> dict[str, Any]:
    """Toplanan verilerden 'sakin gün mü?' kararını verir."""
    orders = state.get("order_data", {}) or {}
    is_quiet = (
        orders.get("new_orders_yesterday", 0) == 0
        and orders.get("pending_to_prepare_today", 0) == 0
        and orders.get("ready_to_ship_today", 0) == 0
        and not state.get("stock_data")
        and not state.get("supplier_drafts")
    )
    return {
        "is_quiet_day": is_quiet,
        "trace": [_trace("aggregator_node", is_quiet=is_quiet)],
    }


async def briefing_llm_node(state: AgentState) -> dict[str, Any]:
    """Utku'nun briefing_agent'ını çağırır. Hazır değilse template fallback."""
    if state.get("is_quiet_day"):
        text = (
            "Günaydın! Bugün takvim sakin: hazırlanacak paket veya "
            "kargoya verilecek sipariş yok, stoklar da yerinde. İyi günler!"
        )
        return {
            "briefing_draft": text,
            "trace": [_trace("briefing_llm_node", path="quiet_day_template")],
        }

    try:
        from app.agents.briefing_agent import run as run_briefing_agent
        text = await run_briefing_agent(
            order_data=state.get("order_data", {}),
            stock_data=state.get("stock_data", []),
            supplier_drafts=state.get("supplier_drafts", []),
            rag_context=state.get("rag_context", []),
        )
    except (ImportError, AttributeError):
        from app.validators.fallback import render_template_briefing
        text = render_template_briefing(
            order_data=state.get("order_data", {}),
            stock_data=state.get("stock_data", []),
            supplier_drafts=state.get("supplier_drafts", []),
        )
        return {
            "briefing_draft": text,
            "used_fallback": True,
            "trace": [_trace("briefing_llm_node", path="template_fallback_no_agent")],
        }

    return {
        "briefing_draft": text,
        "trace": [_trace("briefing_llm_node", path="llm")],
    }


# --------------------------------------------------------------------------
# Validator node
# --------------------------------------------------------------------------

def validator_node(state: AgentState) -> dict[str, Any]:
    """Halüsinasyon kontrolü. Geçemezse template'e düşer."""
    from app.validators.briefing_validator import validate_briefing
    from app.validators.fallback import render_template_briefing

    draft = state.get("briefing_draft", "")
    payload = {
        "order_data": state.get("order_data", {}),
        "stock_data": state.get("stock_data", []),
        "supplier_drafts": state.get("supplier_drafts", []),
    }

    is_valid, reasons = validate_briefing(draft, payload)
    if is_valid:
        return {
            "briefing_final": draft,
            "used_fallback": False,
            "trace": [_trace("validator_node", valid=True)],
        }

    # Halüsinasyon var -> deterministik template fallback
    fallback_text = render_template_briefing(
        order_data=payload["order_data"],
        stock_data=payload["stock_data"],
        supplier_drafts=payload["supplier_drafts"],
    )
    return {
        "briefing_final": fallback_text,
        "used_fallback": True,
        "errors": [f"validator_failed: {'; '.join(reasons)}"],
        "trace": [_trace("validator_node", valid=False, reasons=reasons)],
    }
