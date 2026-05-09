"""
LangGraph orkestratörü.

Akış:
    [parallel: order, stock, shipping, supplier]
                 │
                 ▼
            aggregator (is_quiet_day kararı)
                 │
        ┌────────┴────────┐
        │ quiet           │ busy
        ▼                 ▼
   briefing_llm        rag (similar past briefings)
        │                 │
        │                 ▼
        │            briefing_llm
        │                 │
        └────────┬────────┘
                 ▼
             validator
                 │
                 ▼
                END

Çıktı: AgentState — özellikle `briefing_final` alanı tüketicilere
(WhatsApp, dashboard, e-posta) verilir.
"""
from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    aggregator_node,
    briefing_llm_node,
    order_node,
    rag_node,
    shipping_node,
    stock_node,
    supplier_node,
    validator_node,
)
from app.graph.routing import route_after_aggregator, route_after_validator
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def build_graph():
    """Workflow'u kurar ve compile eder."""
    g = StateGraph(AgentState)

    # Node'ları ekle
    g.add_node("order", order_node)
    g.add_node("stock", stock_node)
    g.add_node("shipping", shipping_node)
    g.add_node("supplier", supplier_node)
    g.add_node("aggregator", aggregator_node)
    g.add_node("rag", rag_node)
    g.add_node("briefing_llm", briefing_llm_node)
    g.add_node("validator", validator_node)

    # Giriş: 4 ajan paralel çalışsın
    g.set_entry_point("order")  # paralel fan-out için aşağıdaki edge'leri kullanıyoruz

    # Aslında LangGraph'te paralel için 4 ayrı entry yerine
    # "fan-out from a virtual start" kullanılır:
    g.add_edge("order", "aggregator")
    g.add_edge("stock", "aggregator")
    g.add_edge("shipping", "aggregator")
    g.add_edge("supplier", "aggregator")

    # 4 ajanı START'tan paralel başlatmak için:
    from langgraph.graph import START
    g.add_edge(START, "order")
    g.add_edge(START, "stock")
    g.add_edge(START, "shipping")
    g.add_edge(START, "supplier")

    # Aggregator sonrası dallanma
    g.add_conditional_edges(
        "aggregator",
        route_after_aggregator,
        {
            "rag": "rag",
            "briefing_llm": "briefing_llm",
        },
    )
    g.add_edge("rag", "briefing_llm")
    g.add_edge("briefing_llm", "validator")

    g.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "END": END,
            "human_review": END,  # ileride ayrı node olacak
        },
    )

    return g.compile()


# Modül seviyesinde compile edilmiş graph (singleton)
graph = build_graph()


async def run_workflow(
    business_id: str,
    business_name: str = "Demo İşletme",
    owner_name: str = "Demo Sahibi",
    trigger_source: str = "manual",
) -> dict[str, Any]:
    """Workflow'u tek bir işletme için uçtan uca çalıştırır."""
    from datetime import date

    initial_state: AgentState = {
        "business_id": business_id,
        "business_name": business_name,
        "owner_name": owner_name,
        "trigger_source": trigger_source,
        "briefing_date": date.today(),
        "errors": [],
        "trace": [],
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state
